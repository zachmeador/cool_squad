import os
from pathlib import Path

# Default data directory is '_data' in the project root
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "_data")

# Environment variable that can override the default data directory
ENV_DATA_DIR = "COOL_SQUAD_DATA_DIR"

def get_data_dir():
    """Get the data directory from environment variable or use default."""
    return os.environ.get(ENV_DATA_DIR, DEFAULT_DATA_DIR)

# Create data directory if it doesn't exist
def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = get_data_dir()
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    return data_dir 