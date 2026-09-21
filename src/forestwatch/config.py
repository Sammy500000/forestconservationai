from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"


def load_yaml_config(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name

    if path.suffix != ".yaml":
        raise ValueError("Configuration files must use the .yaml extension.")
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")

    return data
