
"""TCP communication with the AK001 LED controller."""

import asyncio
import colorsys
import logging

from .const import (
    CMD_POWER_OFF,
    CMD_POWER_ON,
    CMD_QUERY,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    STATUS_PREFIX,
)

_LOGGER = logging.getLogger(__name__)


class AK001Protocol:
    """Communicate with an AK001 controller over TCP."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._counter = 0


    def build_rgb_command(
        self,
        red: int,
        green: int,
        blue: int,
    ) -> bytes:
        """Build a confirmed AK001 RGB command."""
        if not all(
            isinstance(value, int) and 0 <= value <= 255
            for value in (red, green, blue)
        ):
            raise ValueError("RGB values must be integers from 0 to 255")

        hue, saturation, value = colorsys.rgb_to_hsv(
            red / 255,
            green / 255,
            blue / 255,
        )

        # AK001 uses hue in half-degrees and saturation/value in percent.
        h = int(hue * 180)
        s = int(saturation * 100)
        v = int(value * 100)

        # Confirmed inner command for RGB color changes.
        inner = bytes(
            [
                0xE0,
                0x01,
                0x00,
                0xA1,
                h,
                s,
                v,
                0x00,
                0x00,
                0x00,
                0x00,
                0x14,
                0x00,
                0x00,
            ]
        )

        counter = self._counter
        self._counter = (self._counter + 1) & 0xFF

        # AK001 outer wrapper.
        packet = bytes(
            [
                0xB0,
                0xB1,
                0xB2,
                0xB3,
                0x00,
                0x01,
                0x02,
                counter,
                (len(inner) >> 8) & 0xFF,
                len(inner) & 0xFF,
            ]
        ) + inner

        # Checksum: sum of all preceding bytes modulo 256.
        checksum = sum(packet) & 0xFF

        return packet + bytes([checksum])

    async def async_set_rgb(
        self,
        red: int,
        green: int,
        blue: int,
    ) -> bytes:
        """Set the RGB color."""
        command = self.build_rgb_command(red, green, blue)
        return await self.async_send_command(command)


    async def async_send_command(
        self,
        command: bytes,
        response_timeout: float = 1.0,
    ) -> bytes:
        """Send a command and return any received response."""
        writer = None

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )

            writer.write(command)
            await asyncio.wait_for(
                writer.drain(),
                timeout=self.timeout,
            )

            try:
                response = await asyncio.wait_for(
                    reader.read(256),
                    timeout=response_timeout,
                )
            except asyncio.TimeoutError:
                response = b""

            return response

        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.error(
                "Communication error with AK001 at %s:%s: %s",
                self.host,
                self.port,
                err,
            )
            raise

        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass

    async def async_turn_on(self) -> bytes:
        """Turn the controller on."""
        return await self.async_send_command(CMD_POWER_ON)

    async def async_turn_off(self) -> bytes:
        """Turn the controller off."""
        return await self.async_send_command(CMD_POWER_OFF)

    async def async_get_status(self) -> bytes:
        """Request controller status."""
        response = await self.async_send_command(
            CMD_QUERY,
            response_timeout=self.timeout,
        )

        if not response.startswith(STATUS_PREFIX):
            raise ConnectionError(
                f"Unexpected status response: {response.hex(' ')}"
            )

        return response

    @staticmethod
    def parse_status(response: bytes) -> dict:
        """Parse the known fields of an AK001 status response."""
        if not response.startswith(STATUS_PREFIX):
            raise ValueError("Invalid AK001 status response")

        if len(response) < 14:
            raise ValueError("AK001 status response is too short")

        return {
            "is_on": response[6] == 0x23,
            "preset_pattern": response[7],
            "speed": response[9],
            "hue": response[11] * 2,
            "saturation": response[12],
            "value": response[13],
            "raw": response,
        }
