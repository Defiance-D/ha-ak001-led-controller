
"""TCP communication with the AK001 LED controller."""

import asyncio
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
