from __future__ import annotations

import pandas as pd


def detect(frame: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = frame.copy()
    detector = config["detector"]
    grouped = result.groupby("point")[detector["series"]]
    result["rolling_mean"] = grouped.transform(lambda values: values.rolling(detector["window"], min_periods=3).mean())
    result["rolling_std"] = grouped.transform(lambda values: values.rolling(detector["window"], min_periods=3).std())
    result["anomaly"] = result[detector["series"]] > result["rolling_mean"] + detector["k"] * result["rolling_std"]
    events = result[result["anomaly"]][["timestamp", "point", detector["series"], "rolling_mean", "rolling_std"]].copy()
    events["hour"] = events["timestamp"].dt.hour
    return result, events


def hourly_histogram(events: pd.DataFrame) -> pd.DataFrame:
    counts = events.groupby("hour").size().reindex(range(24), fill_value=0)
    return counts.rename("detections").rename_axis("hour").reset_index()
