from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


LIMITATIONS = (
    "Korelasi bersifat eksploratif: data cuaca adalah reanalisis, bukan pengukuran stasiun; "
    "resolusi spasialnya kasar; jumlah gempa dapat kecil; dan korelasi tidak membuktikan kausalitas."
)


def write_report(frame, statistics, correlations, metrics, histogram, events, config, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    events.to_csv(output / "anomaly_events.csv", index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    statistics.to_csv(output / "hourly_statistics.csv")
    correlations.to_csv(output / "correlations.csv", index=False)
    histogram.to_csv(output / "anomaly_hourly.csv", index=False)

    first = frame.sort_values("timestamp")
    fig, axis = plt.subplots(figsize=(11, 4))
    axis.plot(first["timestamp"], first["surface_pressure"], label="Tekanan udara")
    axis.set(title="Deret waktu tekanan udara dan anomali", xlabel="Waktu (Asia/Jakarta)", ylabel="Tekanan (hPa)")
    anomaly_rows = first[first["anomaly"]]
    axis.scatter(anomaly_rows["timestamp"], anomaly_rows["surface_pressure"], color="red", label="Anomali")
    axis.legend(); fig.tight_layout(); fig.savefig(output / "pressure_anomalies.png"); plt.close(fig)

    fig, axis = plt.subplots(figsize=(8, 4))
    axis.bar(histogram["hour"], histogram["detections"])
    axis.set(title="Deteksi anomali per jam", xlabel="Jam (Asia/Jakarta)", ylabel="Jumlah deteksi")
    fig.tight_layout(); fig.savefig(output / "anomaly_by_hour.png"); plt.close(fig)

    fig, axis = plt.subplots(figsize=(7, 5))
    if not correlations.empty:
        axis.scatter(correlations["pearson_r"], correlations["spearman_r"])
    axis.axhline(0, color="grey", linewidth=0.8); axis.axvline(0, color="grey", linewidth=0.8)
    axis.set(title="Sebaran korelasi cuaca dan gempa", xlabel="Pearson r", ylabel="Spearman rho")
    fig.tight_layout(); fig.savefig(output / "correlations.png"); plt.close(fig)

    metric = metrics.iloc[0]
    report = f"""# Laporan Pipeline Cuaca dan Gempa

Rentang: {config['date_range']['start']} sampai {config['date_range']['end']} ({config['timezone']})

## Ringkasan
- Baris terproses: {len(frame)}
- Precision: {metric['precision']:.3f}
- Recall: {metric['recall']:.3f}

## Statistik dan korelasi
Detail disimpan pada `hourly_statistics.csv` dan `correlations.csv`.

## Batasan
{LIMITATIONS}

## Sumber
- Cuaca: Open-Meteo Historical Weather API (CC BY 4.0).
- Gempa: USGS FDSN Event API.
"""
    (output / "report.md").write_text(report, encoding="utf-8")
