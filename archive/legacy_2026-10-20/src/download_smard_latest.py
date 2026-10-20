#!/usr/bin/env python3
"""Lädt die aktuellen stündlichen SMARD-Daten ohne Anmeldung herunter."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "smard"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = (
    "https://www.smard.de/"
    "nip-download-manager/nip/download/market-data"
)

BERLIN = ZoneInfo("Europe/Berlin")

DATASETS = {
    "Erzeugung": {
        "module_ids": [
            1004066,
            1001226,
            1001225,
            1004067,
            1004068,
            1001228,
            1001224,
            1001223,
            1004069,
            1004071,
            1004070,
            1001227,
        ],
        "latest_name": "Realisierte_Erzeugung_2026_latest.csv",
        "expected_prefix": "Realisierte_Erzeugung_",
    },
    "Stromverbrauch": {
        "module_ids": [
            5000410,
            5005140,
            5004387,
            5004359,
        ],
        "latest_name": "Realisierter_Stromverbrauch_2026_latest.csv",
        "expected_prefix": "Realisierter_Stromverbrauch_",
    },
}


def milliseconds(value: datetime) -> int:
    """Wandelt einen Zeitzonen-Zeitpunkt in Unix-Millisekunden um."""

    return int(value.timestamp() * 1000)


def response_filename(content_disposition: str, fallback: str) -> str:
    """Liest den vom SMARD-Server gelieferten Dateinamen aus."""

    match = re.search(r'filename="?([^";]+)', content_disposition)
    return Path(match.group(1)).name if match else fallback


def download_dataset(
    label: str,
    configuration: dict[str, object],
    timestamp_from: int,
    timestamp_to: int,
) -> None:
    """Lädt einen SMARD-Datensatz und speichert Archiv und latest-Datei."""

    payload = {
        "request_form": [
            {
                "moduleIds": configuration["module_ids"],
                "region": "DE",
                "resolution": "hour",
                "format": "CSV",
                "timestamp_from": timestamp_from,
                "timestamp_to": timestamp_to,
                "type": "discrete",
                "language": "de",
            }
        ]
    }

    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Grid-Forecaster/1.0",
        },
        method="POST",
    )

    print(f"Lade {label} von SMARD herunter ...")

    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=180) as response:
                content = response.read()
                disposition = response.headers.get(
                    "Content-Disposition",
                    "",
                )
            break
        except (HTTPError, URLError, TimeoutError) as error:
            if attempt == 3:
                raise RuntimeError(
                    f"SMARD-Download für {label} fehlgeschlagen."
                ) from error
            wait_seconds = 15 * attempt
            print(
                f"Downloadversuch {attempt} fehlgeschlagen. "
                f"Warte {wait_seconds} Sekunden ..."
            )
            sleep(wait_seconds)

    if not content.startswith(b"\xef\xbb\xbf") and b"Datum von" not in content[:500]:
        raise ValueError(
            f"Die Antwort für {label} sieht nicht wie eine SMARD-CSV aus."
        )

    fallback = str(configuration["latest_name"])
    archive_name = response_filename(disposition, fallback)

    expected_prefix = str(configuration["expected_prefix"])
    if not archive_name.startswith(expected_prefix):
        raise ValueError(
            f"Unerwarteter SMARD-Dateiname: {archive_name}"
        )

    archive_file = OUTPUT_DIR / archive_name
    latest_file = OUTPUT_DIR / str(configuration["latest_name"])

    temporary_file = latest_file.with_suffix(".csv.tmp")
    temporary_file.write_bytes(content)
    temporary_file.replace(latest_file)

    if archive_file != latest_file:
        archive_file.write_bytes(content)

    print(f"Archiv: {archive_file.relative_to(PROJECT_ROOT)}")
    print(f"Aktuell: {latest_file.relative_to(PROJECT_ROOT)}")


def main() -> None:
    now = datetime.now(BERLIN)
    start = datetime(now.year, 1, 1, tzinfo=BERLIN)

    # Das Ende ist exklusiv. Mit dem morgigen Tagesanfang wird der
    # heutige Tag angefragt; SMARD liefert nur bereits verfügbare Werte.
    end = datetime(
        now.year,
        now.month,
        now.day,
        tzinfo=BERLIN,
    ) + timedelta(days=1)

    print(
        "SMARD-Zeitraum: "
        f"{start:%d.%m.%Y %H:%M} bis {end:%d.%m.%Y %H:%M}"
    )

    for label, configuration in DATASETS.items():
        download_dataset(
            label,
            configuration,
            milliseconds(start),
            milliseconds(end),
        )

    print("SMARD-Download erfolgreich abgeschlossen.")


if __name__ == "__main__":
    main()
