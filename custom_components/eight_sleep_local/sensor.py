import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from . import DOMAIN
from custom_components.eight_sleep_local.localEight.device import LocalEightSleep

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=5)  # Poll every 5 seconds (adjust as desired)

# 1) Mappings for LEFT side
LEFT_SENSOR_MAP = {
    "current_temp_f": "currentTemperatureF",
    "target_temp_f": "targetTemperatureF",
    "seconds_remaining": "secondsRemaining",
    "is_alarm_vibrating": "isAlarmVibrating",
    "is_on": "isOn",
}

# 2) Mappings for RIGHT side
RIGHT_SENSOR_MAP = {
    "current_temp_f": "currentTemperatureF",
    "target_temp_f": "targetTemperatureF",
    "seconds_remaining": "secondsRemaining",
    "is_alarm_vibrating": "isAlarmVibrating",
    "is_on": "isOn",
}

# 3) Mappings for HUB-level sensors
HUB_SENSOR_MAP = {
    "is_priming": "isPriming",
    "water_level": "waterLevel",
    "sensor_label": "sensorLabel",
}


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    Set up sensors from a config entry. We:
      1. Create the LocalEightSleep client.
      2. Create a DataUpdateCoordinator for periodic data fetching.
      3. Create separate sensors for:
         - The left side
         - The right side
         - The hub
      4. Add them all to Home Assistant.
    """

    # Read host/port from the config entry
    host = entry.data.get("host", "localhost")
    port = entry.data.get("port", 8080)

    client = LocalEightSleep(host=host, port=port)
    await client.start()

    # Create a DataUpdateCoordinator
    coordinator = EightSleepDataUpdateCoordinator(
        hass, client=client, update_interval=UPDATE_INTERVAL
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # 1) Create sensors for the LEFT device
    left_entities = [
        EightSleepSensor(coordinator, side="left", attribute_key=attr_key)
        for attr_key in LEFT_SENSOR_MAP
    ]

    # 2) Create sensors for the RIGHT device
    right_entities = [
        EightSleepSensor(coordinator, side="right", attribute_key=attr_key)
        for attr_key in RIGHT_SENSOR_MAP
    ]

    # 3) Create sensors for the HUB device (non-side-specific)
    hub_entities = [
        EightSleepSensor(coordinator, side="hub", attribute_key=attr_key)
        for attr_key in HUB_SENSOR_MAP
    ]

    # Add them all
    async_add_entities(left_entities + right_entities + hub_entities)


class EightSleepDataUpdateCoordinator(DataUpdateCoordinator):
    """
    Coordinates updates for the local Eight Sleep data by calling `update_device_data`.
    """

    def __init__(self, hass: HomeAssistant, client: LocalEightSleep, update_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="eight_sleep_local_coordinator",
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self):
        """
        Actually fetch the latest data from the local device.
        """
        try:
            await self.client.update_device_data()
            return self.client.device_data  # coordinator.data = latest JSON
        except Exception as err:
            _LOGGER.error("Error updating Eight Sleep local data: %s", err)
            raise err


class EightSleepSensor(CoordinatorEntity, SensorEntity):
    """
    A sensor representing either:
      - Left side attribute
      - Right side attribute
      - Hub attribute

    `side` determines which portion of JSON to read:
      - "left"  -> data["left"]
      - "right" -> data["right"]
      - "hub"   -> data at the root of the JSON
    """

    def __init__(self, coordinator, side: str, attribute_key: str):
        super().__init__(coordinator)
        self.side = side
        self.attribute_key = attribute_key

        # Build a user-friendly name. "left_current_temp_f" -> "Left Current Temp F"
        # or "hub_is_priming" -> "Hub Is Priming"
        side_label = side.capitalize()
        attr_label = attribute_key.replace("_", " ").title()

        self._attr_name = f"Eight Sleep {side_label} {attr_label}"

        # For a stable unique_id, incorporate side + attribute
        # e.g., "eight_sleep_left_current_temp_f"
        self._attr_unique_id = f"eight_sleep_{side}_{attribute_key}"

    @property
    def native_value(self):
        """
        Return the sensor's current value from coordinator.data.
        """
        data = self.coordinator.data or {}

        # If it's a side-based attribute...
        if self.side in ("left", "right"):
            side_data = data.get(self.side, {})

            # Map the attribute_key to the JSON key
            if self.side == "left":
                json_key = LEFT_SENSOR_MAP.get(self.attribute_key)
            else:  # "right"
                json_key = RIGHT_SENSOR_MAP.get(self.attribute_key)

            return side_data.get(json_key) if json_key else None

        # Otherwise, it's the HUB device. We read from the root.
        if self.side == "hub":
            json_key = HUB_SENSOR_MAP.get(self.attribute_key)
            return data.get(json_key) if json_key else None

        return None

    @property
    def device_info(self):
        """
        Return separate device_info so that:
          - left side = "Eight Sleep – Left"
          - right side = "Eight Sleep – Right"
          - hub        = "Eight Sleep – Hub"
        Each device_info has a unique identifier, so all sensors for that side
        or the hub group under a separate device in HA.
        """
        host = self.coordinator.client._host
        port = self.coordinator.client._port

        # e.g., "eight_sleep_left_device_192.168.1.50_8080"
        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"eight_sleep_{self.side}_device_{host}_{port}",
                )
            },
            "name": f"Eight Sleep – {self.side.capitalize()}",
            "manufacturer": "Eight Sleep (Local)",
            "model": "Pod vLocal",
        }