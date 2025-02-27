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

UPDATE_INTERVAL = timedelta(seconds=5)

# Use the string "temperature" directly for the device class.
DEVICE_CLASS_TEMPERATURE = "temperature"

SENSOR_TYPES = {
    "current_temp_f": {
        "name": "Current Temperature",
        "unit": "°F",
        "json_key": "currentTemperatureF",
        "device_class": DEVICE_CLASS_TEMPERATURE,
    },
    "target_temp_f": {
        "name": "Target Temperature",
        "unit": "°F",
        "json_key": "targetTemperatureF",
        "device_class": DEVICE_CLASS_TEMPERATURE,
    },
    "seconds_remaining": {
        "name": "Seconds Remaining",
        "unit": "s",
        "json_key": "secondsRemaining"
    },
    "is_alarm_vibrating": {
        "name": "Alarm Vibrating",
        "unit": None,
        "json_key": "isAlarmVibrating"
    },
    "is_on": {
        "name": "Device On",
        "unit": None,
        "json_key": "isOn"
    },
}

# Which attributes do we want on the left side, right side, and hub?
LEFT_ATTRIBUTES = ("current_temp_f", "target_temp_f", "seconds_remaining", "is_alarm_vibrating", "is_on")
RIGHT_ATTRIBUTES = LEFT_ATTRIBUTES  # same set as left
HUB_ATTRIBUTES = ("is_priming", "water_level")  # if you also define them in SENSOR_TYPES

async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    host = entry.data.get("host", "localhost")
    port = entry.data.get("port", 8080)

    client = LocalEightSleep(host=host, port=port)
    await client.start()

    coordinator = EightSleepDataUpdateCoordinator(
        hass, client=client, update_interval=UPDATE_INTERVAL
    )
    await coordinator.async_config_entry_first_refresh()

    # Build sensors for left, right, hub
    left_entities = [
        EightSleepSensor(coordinator, side="left", attribute_key=attr_key)
        for attr_key in LEFT_ATTRIBUTES
        if attr_key in SENSOR_TYPES  # only create sensors for keys in SENSOR_TYPES
    ]
    right_entities = [
        EightSleepSensor(coordinator, side="right", attribute_key=attr_key)
        for attr_key in RIGHT_ATTRIBUTES
        if attr_key in SENSOR_TYPES
    ]
    hub_entities = [
        EightSleepSensor(coordinator, side="hub", attribute_key=attr_key)
        for attr_key in HUB_ATTRIBUTES
        if attr_key in SENSOR_TYPES
    ]

    async_add_entities(left_entities + right_entities + hub_entities)


class EightSleepDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: LocalEightSleep, update_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="eight_sleep_local_coordinator",
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self):
        try:
            await self.client.update_device_data()
            return self.client.device_data
        except Exception as err:
            _LOGGER.error("Error updating Eight Sleep local data: %s", err)
            raise err


class EightSleepSensor(CoordinatorEntity, SensorEntity):
    """
    A sensor for either 'left', 'right', or 'hub' using one attribute from SENSOR_TYPES.
    """

    def __init__(self, coordinator, side: str, attribute_key: str):
        super().__init__(coordinator)
        self.side = side
        self.attribute_key = attribute_key

        # Get the sensor info from our global dictionary
        sensor_info = SENSOR_TYPES[self.attribute_key]
        friendly_name = sensor_info["name"]
        unit_of_measurement = sensor_info["unit"]

        # For display: e.g. "Eight Sleep Left Current Temperature (F)"
        self._attr_name = f"{friendly_name}"
        self._attr_unique_id = f"eight_sleep_{side}_{attribute_key}"
        self._attr_native_unit_of_measurement = unit_of_measurement

        # Set the device class for temperature sensors so Home Assistant treats them correctly.
        if sensor_info.get("device_class"):
            self._attr_device_class = sensor_info.get("device_class")

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        sensor_info = SENSOR_TYPES[self.attribute_key]
        json_key = sensor_info.get("json_key")

        if self.side in ("left", "right"):
            side_data = data.get(self.side, {})
            return side_data.get(json_key)
        elif self.side == "hub":
            # For hub-level data
            return data.get(json_key)

        return None

    @property
    def device_info(self):
        """
        Return different device_info for left, right, or hub, so each is a separate "device."
        """
        host = self.coordinator.client._host
        port = self.coordinator.client._port

        return {
            "identifiers": {(DOMAIN, f"eight_sleep_{self.side}_device_{host}_{port}")},
            "name": f"Eight Sleep – {self.side.capitalize()}",
            "manufacturer": "Eight Sleep (Local)",
            "model": "Pod vLocal",
        }
