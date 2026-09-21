from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def _default_config_dir() -> Path:
    configured = os.getenv("FORESTWATCH_CONFIG_DIR")
    if configured:
        return Path(configured).expanduser()

    working_tree = Path.cwd() / "configs"
    if working_tree.is_dir():
        return working_tree

    source_tree = Path(__file__).resolve().parents[2] / "configs"
    return source_tree


def load_yaml_config(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    """Load one YAML configuration file from the configured project directory."""
    path_name = Path(name)

    if path_name.is_absolute() or path_name.name != name or path_name.suffix != ".yaml":
        raise ValueError("Configuration name must be a simple .yaml filename.")

    root = (config_dir or _default_config_dir()).expanduser()
    path = root / name

    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")

    return data
