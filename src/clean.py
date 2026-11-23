from __future__ import annotations

import re

import pandas as pd


def clean_weather(frame: pd.DataFrame, timezone: str) -> pd.DataFrame:
    result = frame.copy()
    result["time"] = result["time"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    result["timestamp"] = pd.to_datetime(result["time"], errors="coerce")
    if result["timestamp"].dt.tz is None:
        result["timestamp"] = result["timestamp"].dt.tz_localize(timezone)
    else:
        result["timestamp"] = result["timestamp"].dt.tz_convert(timezone)
    numeric = ["temperature_2m", "relative_humidity_2m", "surface_pressure", "precipitation"]
    result[numeric] = result[numeric].apply(pd.to_numeric, errors="coerce")
    return result.dropna(subset=["timestamp", "point"]).drop_duplicates(["point", "timestamp"])


def clean_quakes(frame: pd.DataFrame, timezone: str) -> pd.DataFrame:
    result = frame.copy()
    result["time"] = result["time"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    result["timestamp"] = pd.to_datetime(result["time"], errors="coerce", utc=True).dt.tz_convert(timezone)
    for column in ("latitude", "longitude", "mag"):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.dropna(subset=["timestamp", "latitude", "longitude", "mag"]).drop_duplicates("id" if "id" in result else "timestamp")
