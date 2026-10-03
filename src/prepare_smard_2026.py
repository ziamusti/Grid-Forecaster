#!/usr/bin/env python3
"""Bereitet die SMARD-Daten für den Zukunftstest 2026 auf."""

from pathlib import Path

import prepare_smard as shared


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "smard"

GENERATION_FILE = RAW_DIR / (
    "Realisierte_Erzeugung_"
    "202601010000_202609300000_Stunde.csv"
)

CONSUMPTION_FILE = RAW_DIR / (
    "Realisierter_Stromverbrauch_"
    "202601010000_202609300000_Stunde.csv"
)


def generation_files() -> list[Path]:
    """Gibt die Erzeugungsdatei 2026 zurück."""

    if not GENERATION_FILE.exists():
        raise FileNotFoundError(
            f"Erzeugungsdatei fehlt: {GENERATION_FILE}"
        )

    return [GENERATION_FILE]


def consumption_files() -> list[Path]:
    """Gibt die Verbrauchsdatei 2026 zurück."""

    if not CONSUMPTION_FILE.exists():
        raise FileNotFoundError(
            f"Verbrauchsdatei fehlt: {CONSUMPTION_FILE}"
        )

    return [CONSUMPTION_FILE]


def main() -> None:
    shared.START_YEAR = 2026
    shared.END_YEAR = 2026

    shared.OUTPUT_FILE = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "smard_hourly_2026.csv"
    )

    shared.REPORT_FILE = (
        PROJECT_ROOT
        / "reports"
        / "smard_data_quality_2026.md"
    )

    shared.generation_files = generation_files
    shared.consumption_files = consumption_files

    shared.main()

    report = shared.REPORT_FILE.read_text(
        encoding="utf-8"
    )

    report = report.replace(
        "2026-01-01 bis 2026-12-31",
        "2026-01-01 bis 2026-09-24",
    )

    shared.REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
    