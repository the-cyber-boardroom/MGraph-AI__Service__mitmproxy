"""Configuration — loads from .env file in the project directory."""

import os
from pathlib import Path

ENV_FILE = '.env'

DEFAULTS = {
    'CACHE_SERVICE_BASE_URL'      : '',
    'CACHE_SERVICE_API_KEY_NAME'  : '',
    'CACHE_SERVICE_API_KEY_VALUE' : '',
    'CACHE_NAMESPACE'             : '',
    'INJECT_CACHE_KEY'            : 'inject',
}


def load_env(project_dir: str = '.') -> dict:
    """Load config from .env file. Returns dict of config values."""
    config = dict(DEFAULTS)
    env_path = Path(project_dir) / ENV_FILE

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    config[key] = value

    # Also check environment variables (override .env)
    for key in DEFAULTS:
        env_val = os.environ.get(key)
        if env_val:
            config[key] = env_val

    return config


def validate_config(config: dict) -> list:
    """Return list of missing required fields."""
    required = ['CACHE_SERVICE_BASE_URL',
                'CACHE_SERVICE_API_KEY_NAME',
                'CACHE_SERVICE_API_KEY_VALUE',
                'CACHE_NAMESPACE']
    return [k for k in required if not config.get(k)]
