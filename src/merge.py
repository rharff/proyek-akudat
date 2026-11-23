from __future__ import annotations

import numpy as np
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    return 2 * radius * np.arcsin(np.sqrt(np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2))


def merge_data(weather: pd.DataFrame, quakes: pd.DataFrame, config: dict, logger) -> tuple[pd.DataFrame, int]:
    points = config["weather"]["points"]
    quake_copy = quakes.copy()
    quake_copy["timestamp"] = quake_copy["timestamp"].dt.round("h")
    mapped: list[dict] = []
    unmapped = 0
    for row in quake_copy.itertuples():
        distances = [haversine_km(row.latitude, row.longitude, p["lat"], p["lon"]) for p in points]
        index = int(np.argmin(distances))
        if distances[index] > config["quake"]["match_radius_km"]:
            unmapped += 1
            continue
        mapped.append({"timestamp": row.timestamp, "point": points[index]["name"], "mag": row.mag})
    logger.warning("Gempa tidak terpetakan: %d", unmapped)
    events = pd.DataFrame(mapped)
    base = weather.copy()
    if events.empty:
        base["earthquake_count"], base["max_magnitude"] = 0, np.nan
    else:
        summary = events.groupby(["point", "timestamp"]).agg(
            earthquake_count=("mag", "size"), max_magnitude=("mag", "max")
        ).reset_index()
        base = base.merge(summary, on=["point", "timestamp"], how="left")
        base[["earthquake_count", "max_magnitude"]] = base[["earthquake_count", "max_magnitude"]].fillna({"earthquake_count": 0})
    base["pressure_delta"] = base.groupby("point")["surface_pressure"].diff()
    return base.sort_values(["point", "timestamp"]).reset_index(drop=True), unmapped
