from __future__ import annotations

import pandas as pd
from scipy.stats import pearsonr, spearmanr


METEOROLOGY = ["temperature_2m", "relative_humidity_2m", "surface_pressure", "precipitation"]


def analyze(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    statistics = frame.groupby("point")[METEOROLOGY + ["earthquake_count", "max_magnitude"]].agg(
        ["mean", "std", "min", "max"]
    )
    rows = []
    for weather in METEOROLOGY:
        for quake in ("earthquake_count", "max_magnitude"):
            pair = frame[[weather, quake]].dropna()
            if len(pair) < 3 or pair[weather].nunique() < 2 or pair[quake].nunique() < 2:
                continue
            pearson = pearsonr(pair[weather], pair[quake])
            spearman = spearmanr(pair[weather], pair[quake])
            rows.append({"weather_parameter": weather, "quake_measure": quake,
                          "pearson_r": pearson.statistic, "pearson_p": pearson.pvalue,
                          "spearman_r": spearman.statistic, "spearman_p": spearman.pvalue,
                          "n": len(pair)})
    return statistics, pd.DataFrame(rows)
