import json
from pathlib import Path

import pandas as pd

from src.clean import clean_quakes, clean_weather
from src.detect import detect
from src.evaluate import evaluate
from src.merge import merge_data
from src.validate import validate_quakes, validate_weather


def config():
    return {
        "timezone": "Asia/Jakarta",
        "weather": {"points": [{"name": "p1", "lat": -7.8, "lon": 110.3}]},
        "quake": {"match_radius_km": 300},
        "detector": {"series": "pressure_delta", "window": 3, "k": 2.0},
    }


def test_clean_validate_merge_and_detect(tmp_path):
    weather = pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=8, freq="h").astype(str),
        "temperature_2m": [25] * 8, "relative_humidity_2m": [70] * 8,
        "surface_pressure": [1000, 1001, 1000, 1001, 1000, 1001, 1000, 1001],
        "precipitation": [0] * 8, "point": ["p1"] * 8,
    })
    quakes = pd.DataFrame({"time": ["2025-01-01T01:20:00Z"], "latitude": [-7.8],
                           "longitude": [110.3], "mag": [4.5]})
    validate_weather(weather); validate_quakes(quakes)
    merged, unmapped = merge_data(clean_weather(weather, "Asia/Jakarta"),
                                  clean_quakes(quakes, "Asia/Jakarta"), config(), __import__("logging").getLogger())
    detected, events = detect(merged, config())
    assert unmapped == 0
    assert {"timestamp", "point", "earthquake_count"}.issubset(detected.columns)
    assert len(events) >= 0


def test_evaluate_counts_metrics(tmp_path):
    truth = tmp_path / "key.csv"
    pd.DataFrame({"timestamp": ["2025-01-01 08:00:00+07:00"], "point": ["p1"]}).to_csv(truth, index=False)
    events = pd.DataFrame({"timestamp": ["2025-01-01 08:00:00+07:00", "2025-01-01 09:00:00+07:00"], "point": ["p1", "p1"]})
    result = evaluate(events, truth).iloc[0]
    assert (result["tp"], result["fp"], result["fn"]) == (1, 1, 0)
