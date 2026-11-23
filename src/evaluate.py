from __future__ import annotations

from pathlib import Path

import pandas as pd


def evaluate(events: pd.DataFrame, ground_truth_path: str | Path) -> pd.DataFrame:
    truth = pd.read_csv(ground_truth_path)
    detected = set(zip(events["timestamp"].astype(str), events["point"]))
    expected = set(zip(truth["timestamp"].astype(str), truth["point"]))
    tp, fp, fn = len(detected & expected), len(detected - expected), len(expected - detected)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return pd.DataFrame([{"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}])
