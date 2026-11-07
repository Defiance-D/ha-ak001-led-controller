
"""Config flow for the AK001 LED Controller integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DEFAULT_PORT, DOMAIN
from .protocol import AK001Protocol

_LOGGER = logging.getLogger(__name__)


class AK001ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AK001."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]

            try:
                protocol = AK001Protocol(host, port)
                await protocol.async_get_status()

            except (OSError, TimeoutError):
                errors["cannot_connect"] = "cannot_connect"

            except (ConnectionError, ValueError):
                errors["invalid_response"] = "invalid_response"

            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"AK001 ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(
                    CONF_PORT,
                    default=DEFAULT_PORT,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=65535),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
