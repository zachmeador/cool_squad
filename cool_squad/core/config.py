import os
from pathlib import Path

# Default data directory is '_data' in the project root
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "_data")

# Environment variable that can override the default data directory
ENV_DATA_DIR = "COOL_SQUAD_DATA_DIR"

# Autonomous thinking configuration
# These can be overridden with environment variables
AUTONOMOUS_THINKING_ENABLED = os.environ.get("AUTONOMOUS_THINKING_ENABLED", "true").lower() == "true"
BOT_MIN_THINKING_INTERVAL = int(os.environ.get("BOT_MIN_THINKING_INTERVAL", "300"))  # 5 minutes
BOT_MAX_THINKING_INTERVAL = int(os.environ.get("BOT_MAX_THINKING_INTERVAL", "900"))  # 15 minutes
BOT_AUTONOMOUS_SPEAKING_ENABLED = os.environ.get("BOT_AUTONOMOUS_SPEAKING_ENABLED", "false").lower() == "true"
BOT_AUTONOMOUS_SPEAKING_CHANCE = float(os.environ.get("BOT_AUTONOMOUS_SPEAKING_CHANCE", "0.1"))  # 10% chance

def get_data_dir():
    """Get the data directory from environment variable or use default."""
    return os.environ.get(ENV_DATA_DIR, DEFAULT_DATA_DIR)

# Create data directory if it doesn't exist
def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = get_data_dir()
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    return data_dir 