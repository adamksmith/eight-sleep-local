import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "eight_sleep_local"
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """
    Called if the user adds the configuration via configuration.yaml
    or if discovered automatically. Typically we rely on async_setup_entry
    with ConfigEntries, but for a basic example, you might implement manual config here.
    """
    # We won't implement manual config in this example, so just return True
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    This sets up the integration from a ConfigEntry (if you had a config_flow),
    or from an automatically created entry. We'll forward to sensor platform.
    """
    hass.data.setdefault(DOMAIN, {})
    # Store any needed data about the config entry if needed
    # For example, host/port might be in entry.data

    _LOGGER.debug("Setting up Eight Sleep Local integration")

    # Forward entry setup to the sensor platform (and any other platforms you have)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Handle removal of an entry.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
