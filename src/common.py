from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


def load_config(path: str | Path = "config/config.json") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Konfigurasi tidak ditemukan: {config_path}")
    with config_path.open(encoding="utf-8") as file:
        config = json.load(file)
    for key in ("timezone", "date_range", "weather", "quake", "network", "paths"):
        if key not in config:
            raise ValueError(f"Konfigurasi kehilangan kunci wajib: {key}")
    return config


def setup_logging(log_file: str | Path) -> logging.Logger:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    return logger


def ensure_directories(config: dict[str, Any]) -> None:
    paths = config["paths"]
    for directory in (paths["raw_dir"], Path(paths["ground_truth"]).parent, paths["output_dir"]):
        Path(directory).mkdir(parents=True, exist_ok=True)
