import asyncio
import atexit
import logging
from typing import Any, Optional, List, Dict

import aiohttp
from aiohttp.client import ClientError, ClientSession, ClientTimeout

_LOGGER = logging.getLogger(__name__)

# You can adjust the default timeout to your preference
DEFAULT_TIMEOUT = 10
CLIENT_TIMEOUT = ClientTimeout(total=DEFAULT_TIMEOUT)


class LocalEightSleep:
    """
    A refactored version of the EightSleep client that:
      - Does NOT authenticate
      - Fetches device status from a local unauthenticated endpoint
      - Expects a JSON response from /api/deviceStatus
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 8080,
            client_session: ClientSession | None = None,
            check_data: bool = False,
    ) -> None:
        """
        Initialize the local Eight Sleep API client.

        :param host: Hostname or IP of the local device
        :param port: Port number
        :param client_session: An optional aiohttp.ClientSession
        :param check_data: If True, fetch device data immediately at init
        """
        self._host = host
        self._port = port
        self._api_session: ClientSession | None = client_session
        self._internal_session: bool = False  # Indicates if we created the session
        self._device_json_list: List[Dict[str, Any]] = []

        # Optionally fetch the data right away
        if check_data:
            # This is a synchronous call if done at __init__
            # Usually you'd do this in an async context, so in that case
            # you might prefer to do:
            #   asyncio.create_task(self._init_data())
            # or remove this parameter entirely.
            asyncio.run(self._init_data())

        # Run cleanup on exit
        atexit.register(self.at_exit)

    async def _init_data(self):
        """Helper to fetch data in an async-safe way during init if requested."""
        await self.start()
        await self.update_device_data()

    def at_exit(self) -> None:
        """
        Ensures the session is closed on exit.
        Because we're dealing with async, we need to handle both:
          - Already-running event loops
          - Potentially no event loop
        """
        try:
            loop = asyncio.get_running_loop()
            asyncio.run_coroutine_threadsafe(self.stop(), loop).result()
        except RuntimeError:
            asyncio.run(self.stop())

    async def start(self) -> bool:
        """
        Initialize the client session if needed.
        """
        _LOGGER.debug("Starting local EightSleep client.")
        if not self._api_session:
            self._api_session = ClientSession(timeout=CLIENT_TIMEOUT)
            self._internal_session = True
        return True

    async def stop(self) -> None:
        """
        Close the client session if we own it.
        """
        if self._internal_session and self._api_session:
            _LOGGER.debug("Closing local EightSleep session.")
            await self._api_session.close()
            self._api_session = None
        else:
            _LOGGER.debug("No-op: Session either not created or externally managed.")

    async def update_device_data(self) -> None:
        """
        Fetch the status from the local /api/deviceStatus endpoint.
        Store the response in a rolling 10-element list (_device_json_list).
        """
        url = f"http://{self._host}:{self._port}/api/deviceStatus"
        _LOGGER.debug(f"Fetching device data from {url}")

        assert self._api_session is not None, "Session not initialized. Call `start()` first."

        try:
            async with self._api_session.get(url) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Received unexpected status code: {resp.status}")
                    return
                data = await resp.json()
                self.handle_device_json(data)
        except (ClientError, asyncio.TimeoutError, ConnectionRefusedError) as err:
            _LOGGER.error(f"Error fetching local device data: {err}")

    def handle_device_json(self, data: Dict[str, Any]) -> None:
        """
        Keep a rolling history of up to 10 responses in `_device_json_list`.
        """
        self._device_json_list.insert(0, data)
        self._device_json_list = self._device_json_list[:10]

    @property
    def device_data(self) -> Dict[str, Any]:
        """
        Return the most recent device status JSON, if any.
        """
        if self._device_json_list:
            return self._device_json_list[0]
        return {}

    @property
    def device_data_history(self) -> List[Dict[str, Any]]:
        """
        Return the rolling list of device status responses.
        """
        return self._device_json_list

    # -------------------------------------------------------------------------
    # Below are convenience properties to pull out the fields from the JSON.
    # Adjust/extend these as you see fit. This matches the sample JSON structure
    # you provided:
    #
    # {
    #   "left": {
    #     "currentTemperatureF": 83,
    #     "targetTemperatureF": 90,
    #     "secondsRemaining": 300,
    #     "isAlarmVibrating": true,
    #     "isOn": true
    #   },
    #   "right": {...},
    #   "waterLevel": "true",
    #   "isPriming": false,
    #   "settings": {...},
    #   "sensorLabel": "\"00000-0000-000-00000\""
    # }
    # -------------------------------------------------------------------------

    @property
    def is_priming(self) -> bool:
        """
        Indicates if the device is currently priming.
        """
        return self.device_data.get("isPriming", False)

    @property
    def water_level(self) -> str:
        """
        Indicates water level status. It's a string in your sample ("true"/"false").
        You could convert to bool if you prefer.
        """
        return self.device_data.get("waterLevel", "false")

    @property
    def left_current_temp_f(self) -> Optional[int]:
        """
        The 'currentTemperatureF' on the left side (if present).
        """
        left_side = self.device_data.get("left", {})
        return left_side.get("currentTemperatureF")

    @property
    def left_target_temp_f(self) -> Optional[int]:
        left_side = self.device_data.get("left", {})
        return left_side.get("targetTemperatureF")

    @property
    def left_seconds_remaining(self) -> Optional[int]:
        left_side = self.device_data.get("left", {})
        return left_side.get("secondsRemaining")

    @property
    def left_is_alarm_vibrating(self) -> bool:
        left_side = self.device_data.get("left", {})
        return left_side.get("isAlarmVibrating", False)

    @property
    def left_is_on(self) -> bool:
        left_side = self.device_data.get("left", {})
        return left_side.get("isOn", False)

    @property
    def right_current_temp_f(self) -> Optional[int]:
        right_side = self.device_data.get("right", {})
        return right_side.get("currentTemperatureF")

    @property
    def right_target_temp_f(self) -> Optional[int]:
        right_side = self.device_data.get("right", {})
        return right_side.get("targetTemperatureF")

    @property
    def right_seconds_remaining(self) -> Optional[int]:
        right_side = self.device_data.get("right", {})
        return right_side.get("secondsRemaining")

    @property
    def right_is_alarm_vibrating(self) -> bool:
        right_side = self.device_data.get("right", {})
        return right_side.get("isAlarmVibrating", False)

    @property
    def right_is_on(self) -> bool:
        right_side = self.device_data.get("right", {})
        return right_side.get("isOn", False)

    @property
    def sensor_label(self) -> str:
        """
        A label or ID for the sensor, if present in the JSON.
        """
        return self.device_data.get("sensorLabel", "")

    @property
    def settings(self) -> Dict[str, Any]:
        """
        The `settings` object from the JSON.
        """
        return self.device_data.get("settings", {})


# Example usage (if you had a local running device):
# async def main():
#     client = LocalEightSleep(host="192.168.1.100", port=3000)
#     await client.start()
#     await client.update_device_data()
#     print("Left side current temp (F):", client.left_current_temp_f)
#     print("Is priming:", client.is_priming)
#     await client.stop()
#
# asyncio.run(main())
