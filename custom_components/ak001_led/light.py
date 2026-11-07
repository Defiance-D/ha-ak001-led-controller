
"""Light platform for the AK001 LED Controller."""

import logging

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .protocol import AK001Protocol

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AK001 light."""
    protocol: AK001Protocol = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([AK001Light(protocol, entry.entry_id)])


class AK001Light(LightEntity):
    """Representation of an AK001 LED controller."""

    _attr_has_entity_name = True
    _attr_name = "LED"

    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        protocol: AK001Protocol,
        entry_id: str,
    ) -> None:
        """Initialize the light."""
        self._protocol = protocol
        self._attr_unique_id = f"{entry_id}_light"
        self._attr_is_on = False
        self._attr_available = True
        self._attr_rgb_color = (255, 255, 255)
        self._attr_brightness = 255

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the light on and set color or brightness."""
        try:
            if not self._attr_is_on:
                await self._protocol.async_turn_on()

            rgb_color = kwargs.get("rgb_color")
            brightness = kwargs.get("brightness")

            if rgb_color is not None:
                self._attr_rgb_color = tuple(rgb_color)

            if brightness is not None:
                self._attr_brightness = brightness

            if rgb_color is not None or brightness is not None:
                red, green, blue = self._attr_rgb_color

                await self._protocol.async_set_rgb(
                    red,
                    green,
                    blue,
                    self._attr_brightness,
                )

            self._attr_is_on = True
            self._attr_available = True

            await self.async_update()

        except (OSError, TimeoutError, ConnectionError, ValueError) as err:
            self._attr_available = False
            self.async_write_ha_state()

            raise HomeAssistantError(
                f"Unable to control AK001: {err}"
            ) from err

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        try:
            await self._protocol.async_turn_off()

            self._attr_is_on = False
            self._attr_available = True

            await self.async_update()

        except (OSError, TimeoutError, ConnectionError, ValueError) as err:
            self._attr_available = False
            self.async_write_ha_state()

            raise HomeAssistantError(
                f"Unable to turn off AK001: {err}"
            ) from err

    async def async_update(self) -> None:
        """Read the current state from the controller."""
        try:
            status = await self._protocol.async_get_status()
            parsed = self._protocol.parse_status(status)

        except (OSError, TimeoutError, ConnectionError, ValueError) as err:
            _LOGGER.warning("Unable to read AK001 status: %s", err)
            self._attr_available = False
            return

        self._attr_available = True
        self._attr_is_on = parsed["is_on"]
