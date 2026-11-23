from __future__ import annotations

from pathlib import Path

import pandas as pd


WEATHER_COLUMNS = {"time", "temperature_2m", "relative_humidity_2m", "surface_pressure", "precipitation", "point"}
QUAKE_COLUMNS = {"time", "latitude", "longitude", "mag"}


def validate_config_and_inputs(config, weather_files, quake_file) -> None:
    assert config["weather"]["points"], "Minimal satu titik cuaca diperlukan"
    assert config["date_range"]["start"] < config["date_range"]["end"], "Rentang tanggal tidak valid"
    for path in (*weather_files, quake_file):
        if not Path(path).is_file():
            raise FileNotFoundError(f"Berkas input tidak ditemukan: {path}")


def validate_weather(frame: pd.DataFrame) -> None:
    missing = WEATHER_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Kolom cuaca hilang: {sorted(missing)}")
    assert len(frame.columns) >= 6, "Kolom cuaca terlalu sedikit"
    assert frame["temperature_2m"].notna().all(), "Suhu mengandung null"
    assert frame["relative_humidity_2m"].dropna().between(0, 100).all(), "Kelembapan di luar rentang"
    assert frame["time"].notna().all(), "Timestamp cuaca null"


def validate_quakes(frame: pd.DataFrame) -> None:
    missing = QUAKE_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Kolom gempa hilang: {sorted(missing)}")
    assert len(frame.columns) >= 4, "Kolom gempa terlalu sedikit"
    assert frame[["time", "latitude", "longitude"]].notna().all().all(), "Kunci gempa null"
    assert frame["mag"].dropna().between(-2, 10).all(), "Magnitudo tidak valid"
