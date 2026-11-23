from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def inject(frame: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = frame.copy()
    eligible = result.index[result["pressure_delta"].notna()]
    count = min(config["inject"]["n_anomalies"], len(eligible))
    rng = np.random.default_rng(config["inject"]["seed"])
    selected = rng.choice(eligible, size=count, replace=False)
    sigma = result["pressure_delta"].std()
    result.loc[selected, "pressure_delta"] += config["inject"]["magnitude_sigma"] * (sigma if pd.notna(sigma) else 1.0)
    key = result.loc[selected, ["timestamp", "point"]].sort_values(["timestamp", "point"]).drop_duplicates()
    key["timestamp"] = key["timestamp"].astype(str)
    return result, key


def save_ground_truth(key: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    key.to_csv(path, index=False)
