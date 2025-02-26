# config_flow.py
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_HOST, CONF_PORT, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

class EightSleepLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the local Eight Sleep integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step where the user enters host & port."""
        errors = {}

        if user_input is not None:
            # If you want to verify the host/port (e.g., check connectivity),
            # you can do so here. Otherwise, just create the entry.

            # Example (very minimal):
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # Optionally, do some quick sanity checks:
            if not host:
                errors["base"] = "host_required"
            elif not (0 < port < 65536):
                errors["base"] = "invalid_port"
            else:
                # All good—create the entry
                return self.async_create_entry(
                    title="Eight Sleep Local",
                    data=user_input,
                )

        # Show the form when first time or if errors found
        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
