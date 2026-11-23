from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


def _get(url: str, params: dict[str, Any], network: dict[str, Any], logger) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, network["max_retries"] + 1):
        try:
            response = requests.get(url, params=params, timeout=network["timeout_s"])
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            logger.warning("Percobaan jaringan %d/%d gagal: %s", attempt, network["max_retries"], error)
            if attempt < network["max_retries"]:
                time.sleep(network["backoff_s"] * attempt)
    raise RuntimeError(f"Permintaan gagal setelah retry: {last_error}") from last_error


def acquire(config: dict[str, Any], logger) -> tuple[list[Path], Path]:
    raw_dir = Path(config["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    date_range = config["date_range"]
    weather_files: list[Path] = []
    for point in config["weather"]["points"]:
        target = raw_dir / f"weather_{point['name']}.json"
        params = {
            "latitude": point["lat"], "longitude": point["lon"],
            "start_date": date_range["start"], "end_date": date_range["end"],
            "hourly": ",".join(config["weather"]["hourly"]),
            "timezone": config["timezone"],
        }
        try:
            response = _get(config["weather"]["endpoint"], params, config["network"], logger)
            target.write_text(response.text, encoding="utf-8")
            logger.info("Cuaca mentah disimpan: %s", target)
        except (RuntimeError, OSError) as error:
            if not target.is_file():
                raise RuntimeError(f"Cuaca gagal dan salinan lokal tidak tersedia: {target}") from error
            logger.warning("Memakai salinan cuaca lokal: %s", target)
        weather_files.append(target)

    quake_file = raw_dir / "earthquakes.csv"
    params = {
        "format": "csv", "starttime": date_range["start"], "endtime": date_range["end"],
        "minmagnitude": config["quake"]["min_magnitude"],
        "minlatitude": config["quake"]["bbox"]["minlat"], "maxlatitude": config["quake"]["bbox"]["maxlat"],
        "minlongitude": config["quake"]["bbox"]["minlon"], "maxlongitude": config["quake"]["bbox"]["maxlon"],
    }
    try:
        response = _get(config["quake"]["endpoint"], params, config["network"], logger)
        quake_file.write_text(response.text, encoding="utf-8")
        logger.info("Gempa mentah disimpan: %s", quake_file)
    except (RuntimeError, OSError) as error:
        if not quake_file.is_file():
            raise RuntimeError(f"Gempa gagal dan salinan lokal tidak tersedia: {quake_file}") from error
        logger.warning("Memakai salinan gempa lokal: %s", quake_file)
    return weather_files, quake_file


def load_weather(path: str | Path, point: dict[str, Any]) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    hourly = payload.get("hourly", {})
    frame = pd.DataFrame(hourly)
    frame["point"] = point["name"]
    frame["lat"], frame["lon"] = point["lat"], point["lon"]
    return frame


def load_quakes(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)
