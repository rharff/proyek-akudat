from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from src.acquire import acquire, load_quakes, load_weather
from src.analyze import analyze
from src.clean import clean_quakes, clean_weather
from src.common import ensure_directories, load_config, setup_logging
from src.detect import detect, hourly_histogram
from src.evaluate import evaluate
from src.inject import inject, save_ground_truth
from src.merge import merge_data
from src.report import write_report
from src.validate import validate_config_and_inputs, validate_quakes, validate_weather


def run(config_path: str = "config/config.json") -> int:
    try:
        config = load_config(config_path)
        ensure_directories(config)
        logger = setup_logging(config["paths"]["log_file"])
        logger.info("Pipeline dimulai")
        weather_files, quake_file = acquire(config, logger)
        validate_config_and_inputs(config, weather_files, quake_file)
        weather = pd.concat(
            [load_weather(path, point) for path, point in zip(weather_files, config["weather"]["points"])],
            ignore_index=True,
        )
        quakes = load_quakes(quake_file)
        validate_weather(weather); validate_quakes(quakes)
        weather = clean_weather(weather, config["timezone"])
        quakes = clean_quakes(quakes, config["timezone"])
        merged, unmapped = merge_data(weather, quakes, config, logger)
        statistics, correlations = analyze(merged)
        injected, key = inject(merged, config)
        save_ground_truth(key, config["paths"]["ground_truth"])
        detected, events = detect(injected, config)
        metrics = evaluate(events, config["paths"]["ground_truth"])
        write_report(detected, statistics, correlations, metrics, hourly_histogram(events), events,
                     config, config["paths"]["output_dir"])
        logger.info("Pipeline selesai: %d baris, %d gempa tidak terpetakan", len(detected), unmapped)
        return 0
    except (FileNotFoundError, ValueError, AssertionError, RuntimeError, OSError, KeyError) as error:
        log_path = Path("logs/pipeline.log")
        if log_path.parent.exists():
            with log_path.open("a", encoding="utf-8") as file:
                file.write(f" ERROR Pipeline dihentikan: {error}\n")
        print(f"Pipeline dihentikan: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
