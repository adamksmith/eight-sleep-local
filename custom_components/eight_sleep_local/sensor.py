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
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import TEMP_FAHRENHEIT

from . import DOMAIN
from .local_eight_sleep import LocalEightSleep

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=5)  # Poll every 30s (adjust as desired)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """
    This is called by Home Assistant to set up sensors.
    We'll:
      1. Create a LocalEightSleep client.
      2. Create a DataUpdateCoordinator to poll that client.
      3. Create sensor entities for the left side and the right side,
         and pass them to Home Assistant.
    """

    # Example of retrieving config from the entry
    host = entry.data.get("host", "localhost")
    port = entry.data.get("port", 8080)

    client = LocalEightSleep(host=host, port=port)

    await client.start()
    # Create a coordinator to manage fetching data
    coordinator = EightSleepDataUpdateCoordinator(hass, client=client, update_interval=UPDATE_INTERVAL)

    # Initialize the coordinator (fetch initial data)
    await coordinator.async_config_entry_first_refresh()

    # Create sensor entities for left & right sides
    left_entities = [
        EightSleepTempSensor(coordinator, "left_current_temp_f", side="left"),
        EightSleepTempSensor(coordinator, "left_target_temp_f", side="left"),
        EightSleepSensor(coordinator, "left_seconds_remaining", side="left"),
        EightSleepSensor(coordinator, "left_is_alarm_vibrating", side="left"),
        EightSleepSensor(coordinator, "left_is_on", side="left"),
    ]

    right_entities = [
        EightSleepTempSensor(coordinator, "right_current_temp_f", side="right"),
        EightSleepTempSensor(coordinator, "right_target_temp_f", side="right"),
        EightSleepSensor(coordinator, "right_seconds_remaining", side="right"),
        EightSleepSensor(coordinator, "right_is_alarm_vibrating", side="right"),
        EightSleepSensor(coordinator, "right_is_on", side="right"),
    ]

    # Add them all
    async_add_entities(left_entities + right_entities)

    # Optionally, you could add other sensors like is_priming, water_level, etc. as separate sensors.


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
        This is called automatically by the DataUpdateCoordinator at intervals.
        """
        try:
            await self.client.update_device_data()
            return self.client.device_data  # store the latest JSON in 'data'
        except Exception as err:
            _LOGGER.error("Error updating Eight Sleep local data: %s", err)
            raise err


class EightSleepSensor(CoordinatorEntity, SensorEntity):
    """
    A sensor for one side of the bed.
    Reads from the coordinator's .data property.
    """

    def __init__(self, coordinator, attribute_name, side):
        super().__init__(coordinator)
        self._attr_name = f"Eight Sleep {side.capitalize()} {attribute_name}"
        self._attr_unique_id = f"eight_sleep_{side}_{attribute_name}"
        self.side = side
        self.attribute_name = attribute_name

    @property
    def native_value(self):
        """
        Return the sensor's current value from coordinator.data.
        For example, if self.attribute_name is 'left_current_temp_f',
        we read that from the coordinator’s data if available.
        """
        data = self.coordinator.data or {}
        # We can rely on the local_eight_sleep properties, or parse directly from JSON:
        # But we used property names in local_eight_sleep, so let's do direct JSON read:

        # If you prefer using the LocalEightSleep object properties (e.g. self.client.left_current_temp_f),
        # you can do so, but typically we'd use the coordinator.data snapshot for performance.

        # Example if attribute_name = "left_current_temp_f", we can parse:
        if self.attribute_name == "left_current_temp_f":
            left_side = data.get("left", {})
            return left_side.get("currentTemperatureF")
        elif self.attribute_name == "left_target_temp_f":
            left_side = data.get("left", {})
            return left_side.get("targetTemperatureF")
        elif self.attribute_name == "left_seconds_remaining":
            left_side = data.get("left", {})
            return left_side.get("secondsRemaining")
        elif self.attribute_name == "left_is_alarm_vibrating":
            left_side = data.get("left", {})
            return left_side.get("isAlarmVibrating")
        elif self.attribute_name == "left_is_on":
            left_side = data.get("left", {})
            return left_side.get("isOn")

        elif self.attribute_name == "right_current_temp_f":
            right_side = data.get("right", {})
            return right_side.get("currentTemperatureF")
        elif self.attribute_name == "right_target_temp_f":
            right_side = data.get("right", {})
            return right_side.get("targetTemperatureF")
        elif self.attribute_name == "right_seconds_remaining":
            right_side = data.get("right", {})
            return right_side.get("secondsRemaining")
        elif self.attribute_name == "right_is_alarm_vibrating":
            right_side = data.get("right", {})
            return right_side.get("isAlarmVibrating")
        elif self.attribute_name == "right_is_on":
            right_side = data.get("right", {})
            return right_side.get("isOn")

        # fallback
        return None

    @property
    def device_info(self):
        """
        Return a device dictionary so that left and right sensors
        group under distinct devices in Home Assistant's device registry.
        """
        # We’ll differentiate the left and right side by unique IDs
        # and by naming them “Eight Sleep – Left” vs “Eight Sleep – Right”
        return {
            "identifiers": {(DOMAIN, f"eight_sleep_{self.side}_device")},
            "name": f"Eight Sleep – {self.side.capitalize()}",
            "manufacturer": "Eight Sleep (Local)",
            "model": "Pod vLocal",  # You can set a custom model or read from device data
        }
class EightSleepTempSensor(SensorEntity):
    """Define a basic Eight Sleep Sensor."""

    def __init__(self, coordinator, sensor_key, side="left"):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._sensor_key = sensor_key
        self._side = side

        # Give this sensor a name based on side/key
        self._attr_name = f"{side.capitalize()} {sensor_key.replace('_', ' ')}"

        # If this sensor is measuring temperature in Fahrenheit:
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = TEMP_FAHRENHEIT
        self._attr_state_class = SensorStateClass.MEASUREMENT

        # If you have a unique ID available:
        self._attr_unique_id = f"eight_sleep_{side}_{sensor_key}"

    @property
    def native_value(self):
        """Return the current value for this sensor."""
        # Pull the latest data from the coordinator (example).
        # Adjust the path to match how your data is exposed.
        return self._coordinator.data.get(self._sensor_key, None)

    async def async_update(self):
        """Use coordinator to update the data."""
        await self._coordinator.async_request_refresh()