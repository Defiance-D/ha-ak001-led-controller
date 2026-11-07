
"""Constants for the AK001 LED Controller integration."""

DOMAIN = "ak001_led"
NAME = "AK001 LED Controller"

DEFAULT_PORT = 5577
DEFAULT_TIMEOUT = 5

CONF_HOST = "host"
CONF_PORT = "port"

# Confirmed controller commands
CMD_POWER_ON = bytes.fromhex("71 23 0F")
CMD_POWER_OFF = bytes.fromhex("71 24 0F")
CMD_QUERY = bytes.fromhex("81 8A 8B")

# Controller protocol
WRAPPER_PREFIX = bytes.fromhex("B0 B1 B2 B3")
STATUS_PREFIX = bytes.fromhex("EA 81")

# Confirmed color write mode
COLOR_WRITE_MODE = 0xA1
