#!/usr/bin/env python3
"""Aktualisiert alle Daten und erzeugt eine neue 72-Stunden-Prognose."""

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("Aktuelle SMARD-Daten herunterladen", "download_smard_latest.py"),
    ("SMARD-Daten aufbereiten", "prepare_smard_2026.py"),
    ("Aktuelle Wetterprognose herunterladen", "download_weather_forecast.py"),
    ("72-Stunden-Prognose erstellen", "predict_next_72h.py"),
]


def main() -> None:
    for number, (description, script_name) in enumerate(STEPS, start=1):
        script = PROJECT_ROOT / "src" / script_name

        print()
        print(f"[{number}/{len(STEPS)}] {description}")

        subprocess.run(
            [sys.executable, str(script)],
            cwd=PROJECT_ROOT,
            check=True,
        )

    print()
    print("Live-Prognose vollständig aktualisiert.")
    print(
        "Streamlit-Datei: "
        "reports/live_forecasts/grid_forecast_72h_latest.csv"
    )


if __name__ == "__main__":
    main()
