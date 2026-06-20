from __future__ import annotations

import json
import os
from pathlib import Path

from platformdirs import user_config_path, user_data_path, user_log_path
from pydantic import ValidationError

from manotron.schemas import ManotronSettings

APP_NAME = "manotron"
CONFIG_ENV = "MANOTRON_CONFIG"
DB_ENV = "MANOTRON_DB_PATH"


def config_path() -> Path:
    configured = os.environ.get(CONFIG_ENV)
    if configured:
        return Path(configured).expanduser()
    return user_config_path(APP_NAME, appauthor=False) / "config.json"


def data_dir() -> Path:
    return user_data_path(APP_NAME, appauthor=False)


def log_dir() -> Path:
    return user_log_path(APP_NAME, appauthor=False)


def default_db_path() -> Path:
    configured = os.environ.get(DB_ENV)
    if configured:
        return Path(configured).expanduser()
    return data_dir() / "manotron.sqlite3"


def default_settings() -> ManotronSettings:
    return ManotronSettings(db_path=str(default_db_path()))


def load_settings() -> ManotronSettings:
    path = config_path()
    if not path.exists():
        settings = default_settings()
    else:
        try:
            settings = ManotronSettings.model_validate_json(path.read_text())
        except (OSError, ValidationError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read config at {path}: {exc}") from exc

    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        settings.openai_api_key = env_key

    env_db = os.environ.get(DB_ENV)
    if env_db:
        settings.db_path = str(Path(env_db).expanduser())

    return settings


def save_settings(settings: ManotronSettings) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    Path(settings.db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    path.write_text(settings.model_dump_json(indent=2) + "\n")
    path.chmod(0o600)
    return path

