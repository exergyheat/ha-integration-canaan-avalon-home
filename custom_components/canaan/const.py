"""Constants for the Canaan Avalon Miner integration."""
from homeassistant.const import Platform

DOMAIN = "canaan"

# Platforms
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.SELECT, Platform.BUTTON, Platform.LIGHT]

# Configuration
CONF_IP = "host"
CONF_NAME = "name"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MODEL = "model"

# Defaults
DEFAULT_PORT = 4028
DEFAULT_SCAN_INTERVAL = 15  # seconds

# Units
TERA_HASH_PER_SECOND = "TH/s"

# Model Types
MODEL_MINI3 = "mini3"
MODEL_NANO3S = "nano3s"
MODEL_Q = "q"
MODEL_UNKNOWN = "unknown"

# Model display names
MODEL_NAMES = {
    MODEL_MINI3: "Avalon Mini 3",
    MODEL_NANO3S: "Avalon Nano 3s",
    MODEL_Q: "Avalon Q",
    MODEL_UNKNOWN: "Avalon Miner",
}

# Work Modes for Mini 3 (heating appliance)
WORK_MODE_HEATING = 0
WORK_MODE_MINING = 1
WORK_MODE_NIGHT = 2

WORK_MODES_MINI3 = {
    "Heating": WORK_MODE_HEATING,
    "Mining": WORK_MODE_MINING,
    "Night": WORK_MODE_NIGHT,
}

# Work Modes for Nano 3s (performance levels)
WORK_MODE_LOW = 0
WORK_MODE_MID = 1
WORK_MODE_HIGH = 2

WORK_MODES_NANO3S = {
    "Low": WORK_MODE_LOW,
    "Mid": WORK_MODE_MID,
    "High": WORK_MODE_HIGH,
}

# Legacy alias for backwards compatibility
WORK_MODES = WORK_MODES_MINI3

# Work Levels for Mini 3 only (Super/Eco)
WORK_LEVEL_SUPER_MINI3 = 0
WORK_LEVEL_ECO_MINI3 = -1

WORK_LEVELS_MINI3 = {
    "Super": WORK_LEVEL_SUPER_MINI3,
    "Eco": WORK_LEVEL_ECO_MINI3,
}

# Work Levels for Avalon Q (Eco/Standard/Super)
# Note: Q uses WORKMODE field for levels, not WORKLEVEL
WORK_LEVEL_ECO_Q = 0
WORK_LEVEL_STANDARD_Q = 1
WORK_LEVEL_SUPER_Q = 2

WORK_LEVELS_Q = {
    "Eco": WORK_LEVEL_ECO_Q,
    "Standard": WORK_LEVEL_STANDARD_Q,
    "Super": WORK_LEVEL_SUPER_Q,
}

# Legacy alias - keep for Mini 3
WORK_LEVELS = WORK_LEVELS_MINI3

# State mapping for Mini 3 / Q
STATE_MAP = {
    0: "Initializing",
    1: "Working",
    2: "Idle",
    3: "Fault",
}

# Mode mapping for Mini 3 (heating modes)
MODE_MAP_MINI3 = {
    0: "Heating",
    1: "Mining",
    2: "Night",
}

# Mode mapping for Nano 3s (performance levels)
MODE_MAP_NANO3S = {
    0: "Low",
    1: "Mid",
    2: "High",
}

# Mode mapping for Avalon Q (uses WORKMODE field for performance levels)
MODE_MAP_Q = {
    0: "Eco",
    1: "Standard",
    2: "Super",
}

# Legacy alias
MODE_MAP = MODE_MAP_MINI3

# Level mapping for Mini 3 (uses WORKLEVEL field)
LEVEL_MAP_MINI3 = {
    0: "Super",
    -1: "Eco",
}

# Legacy alias
LEVEL_MAP = LEVEL_MAP_MINI3

# LED Effects for Nano 3s
LED_EFFECT_OFF = 0
LED_EFFECT_ON = 1
LED_EFFECT_FLASH = 2
LED_EFFECT_BREATH = 3
LED_EFFECT_LOOP = 4

LED_EFFECTS = {
    "Off": LED_EFFECT_OFF,
    "On": LED_EFFECT_ON,
    "Flash": LED_EFFECT_FLASH,
    "Breath": LED_EFFECT_BREATH,
    "Loop": LED_EFFECT_LOOP,
}

LED_EFFECT_MAP = {
    0: "Off",
    1: "On",
    2: "Flash",
    3: "Breath",
    4: "Loop",
}

# Models that support specific features
MODELS_WITH_WORK_MODE = [MODEL_MINI3]  # Only Mini 3 has heating/mining/night modes
MODELS_WITH_WORK_LEVEL = [MODEL_MINI3]  # Only Mini 3 has super/eco levels
MODELS_WITH_Q_LEVELS = [MODEL_Q]  # Q uses workmode field for eco/standard/super levels
MODELS_WITH_NANO3_LEVELS = [MODEL_NANO3S]  # Nano 3S has Low/Mid/High work modes
MODELS_WITH_LED = [MODEL_NANO3S]
