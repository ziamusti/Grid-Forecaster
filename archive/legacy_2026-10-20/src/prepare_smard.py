#!/usr/bin/env python3
"""Prepare the downloaded hourly SMARD generation and load data.

The script intentionally uses only Python's standard library so the raw data can
be validated before the project's Python data-science environment is installed.
It creates one analysis-ready CSV for the complete years 2015 through 2025 and
a Markdown quality report. Raw downloads are never modified.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "smard"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "smard_hourly_2015_2025.csv"
REPORT_FILE = PROJECT_ROOT / "reports" / "smard_data_quality.md"
START_YEAR = 2015
END_YEAR = 2025
BERLIN = ZoneInfo("Europe/Berlin")

GENERATION_COLUMNS = {
    "Biomasse [MWh] Berechnete Auflösungen": "biomass_mwh",
    "Wasserkraft [MWh] Berechnete Auflösungen": "hydro_mwh",
    "Wind Offshore [MWh] Berechnete Auflösungen": "wind_offshore_mwh",
    "Wind Onshore [MWh] Berechnete Auflösungen": "wind_onshore_mwh",
    "Photovoltaik [MWh] Berechnete Auflösungen": "solar_mwh",
    "Sonstige Erneuerbare [MWh] Berechnete Auflösungen": "other_renewables_mwh",
    "Kernenergie [MWh] Berechnete Auflösungen": "nuclear_mwh",
    "Braunkohle [MWh] Berechnete Auflösungen": "lignite_mwh",
    "Steinkohle [MWh] Berechnete Auflösungen": "hard_coal_mwh",
    "Erdgas [MWh] Berechnete Auflösungen": "natural_gas_mwh",
    "Pumpspeicher [MWh] Berechnete Auflösungen": "pumped_storage_generation_mwh",
    "Sonstige Konventionelle [MWh] Berechnete Auflösungen": "other_conventional_mwh",
}

CONSUMPTION_COLUMNS = {
    "Netzlast [MWh] Berechnete Auflösungen": "grid_load_mwh",
    "Netzlast inkl. Pumpspeicher [MWh] Berechnete Auflösungen": "grid_load_including_pumped_storage_mwh",
    "Pumpspeicher [MWh] Berechnete Auflösungen": "pumped_storage_consumption_mwh",
    "Residuallast [MWh] Berechnete Auflösungen": "residual_load_mwh",
}

RENEWABLE_COLUMNS = (
    "biomass_mwh",
    "hydro_mwh",
    "wind_offshore_mwh",
    "wind_onshore_mwh",
    "solar_mwh",
    "other_renewables_mwh",
)
TOTAL_GENERATION_COLUMNS = tuple(GENERATION_COLUMNS.values())


def parse_local_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d.%m.%Y %H:%M")


def parse_german_decimal(value: str) -> Decimal | None:
    value = value.strip()
    if not value or value == "-":
        return None
    try:
        return Decimal(value.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"Ungültiger SMARD-Zahlenwert: {value!r}") from exc


def decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")


def utc_key(local_start: datetime, occurrence: int) -> datetime:
    """Convert SMARD local time to UTC, preserving both autumn DST hours."""
    fold_zero = local_start.replace(tzinfo=BERLIN, fold=0)
    fold_one = local_start.replace(tzinfo=BERLIN, fold=1)
    ambiguous = fold_zero.utcoffset() != fold_one.utcoffset()
    if occurrence > 0 and not ambiguous:
        raise ValueError(f"Unerwarteter doppelter lokaler Zeitstempel: {local_start}")
    if occurrence > 1:
        raise ValueError(f"Mehr als zwei Vorkommen eines Zeitstempels: {local_start}")
    aware = local_start.replace(tzinfo=BERLIN, fold=occurrence if ambiguous else 0)
    return aware.astimezone(timezone.utc)


def read_rows(path: Path, column_map: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    local_occurrences: Counter[datetime] = Counter()

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        missing_headers = set(column_map) - set(reader.fieldnames or [])
        if missing_headers:
            raise ValueError(f"Fehlende Spalten in {path.name}: {sorted(missing_headers)}")

        for raw in reader:
            local_start = parse_local_datetime(raw["Datum von"])
            if not START_YEAR <= local_start.year <= END_YEAR:
                continue
            occurrence = local_occurrences[local_start]
            local_occurrences[local_start] += 1
            start_utc = utc_key(local_start, occurrence)
            row: dict[str, object] = {
                "timestamp_utc": start_utc,
                "timestamp_local": local_start,
                "local_time_occurrence": occurrence + 1,
            }
            for source, target in column_map.items():
                row[target] = parse_german_decimal(raw[source])
            rows.append(row)
    return rows


def generation_files() -> list[Path]:
    selected: list[Path] = []
    for year in range(START_YEAR, END_YEAR + 1):
        candidates = sorted(
            path
            for path in RAW_DIR.glob(f"Realisierte_Erzeugung_{year}01010000_*.csv")
            if "Kopie" not in path.name
        )
        if len(candidates) != 1:
            raise ValueError(
                f"Für {year} wurde genau eine Erzeugungsdatei erwartet, gefunden: "
                f"{[path.name for path in candidates]}"
            )
        selected.append(candidates[0])
    return selected


def consumption_files() -> list[Path]:
    files = sorted(RAW_DIR.glob("Realisierter_Stromverbrauch_*.csv"))
    if not files:
        raise ValueError("Keine Dateien zum realisierten Stromverbrauch gefunden.")
    return files


def load_dataset(files: list[Path], columns: dict[str, str]) -> tuple[dict[datetime, dict[str, object]], list[str]]:
    combined: dict[datetime, dict[str, object]] = {}
    conflicts: list[str] = []
    for path in files:
        for row in read_rows(path, columns):
            key = row["timestamp_utc"]
            assert isinstance(key, datetime)
            if key in combined:
                if combined[key] != row:
                    conflicts.append(f"{key.isoformat()} ({path.name})")
                continue
            combined[key] = row
    return combined, conflicts


def missing_counts(rows: list[dict[str, object]], columns: list[str]) -> dict[str, int]:
    return {column: sum(row.get(column) is None for row in rows) for column in columns}


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    gen_files = generation_files()
    load_files = consumption_files()
    generation, generation_conflicts = load_dataset(gen_files, GENERATION_COLUMNS)
    consumption, consumption_conflicts = load_dataset(load_files, CONSUMPTION_COLUMNS)

    generation_keys = set(generation)
    consumption_keys = set(consumption)
    common_keys = sorted(generation_keys & consumption_keys)
    generation_only = sorted(generation_keys - consumption_keys)
    consumption_only = sorted(consumption_keys - generation_keys)

    output_rows: list[dict[str, object]] = []
    for key in common_keys:
        gen = generation[key]
        load = consumption[key]
        row = {**gen}
        row.update({name: load[name] for name in CONSUMPTION_COLUMNS.values()})

        # Nach dem deutschen Atomausstieg bedeutet ein leeres SMARD-Feld
        # für Kernenergie 0 MWh und nicht einen unbekannten Messwert.
        timestamp_local = row["timestamp_local"]
        if (
            isinstance(timestamp_local, datetime)
            and timestamp_local >= datetime(2023, 4, 16)
            and row["nuclear_mwh"] is None
        ):
            row["nuclear_mwh"] = Decimal("0")

        renewable_values = [row[name] for name in RENEWABLE_COLUMNS]
        if all(isinstance(value, Decimal) for value in renewable_values):
            renewable_total = sum(renewable_values, Decimal("0"))
        else:
            renewable_total = None
        generation_values = [row[name] for name in TOTAL_GENERATION_COLUMNS]
        if all(isinstance(value, Decimal) for value in generation_values):
            total_generation = sum(generation_values, Decimal("0"))
        else:
            total_generation = None

        if (
            isinstance(renewable_total, Decimal)
            and isinstance(total_generation, Decimal)
            and total_generation != 0
        ):
            renewable_share = (
                renewable_total / total_generation * Decimal("100")
            ).quantize(Decimal("0.000001"))
        else:
            renewable_share = None

        row["renewable_generation_mwh"] = renewable_total
        row["total_generation_mwh"] = total_generation
        row["renewable_share_of_generation_pct"] = renewable_share
        output_rows.append(row)

    output_columns = [
        "timestamp_utc",
        "timestamp_local",
        "local_time_occurrence",
        *GENERATION_COLUMNS.values(),
        *CONSUMPTION_COLUMNS.values(),
        "renewable_generation_mwh",
        "total_generation_mwh",
        "renewable_share_of_generation_pct",
    ]
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_columns)
        writer.writeheader()
        for row in output_rows:
            formatted: dict[str, object] = {}
            for column in output_columns:
                value = row[column]
                if isinstance(value, datetime):
                    formatted[column] = value.isoformat()
                elif isinstance(value, Decimal) or value is None:
                    formatted[column] = decimal_text(value)
                else:
                    formatted[column] = value
            writer.writerow(formatted)

    numeric_columns = [
        *GENERATION_COLUMNS.values(),
        *CONSUMPTION_COLUMNS.values(),
        "renewable_generation_mwh",
        "total_generation_mwh",
        "renewable_share_of_generation_pct",
    ]
    missing = missing_counts(output_rows, numeric_columns)
    utc_gaps = []
    for previous, current in zip(common_keys, common_keys[1:]):
        hours = (current - previous).total_seconds() / 3600
        if hours != 1:
            utc_gaps.append((previous.isoformat(), current.isoformat(), hours))

    shares = [
        row["renewable_share_of_generation_pct"]
        for row in output_rows
        if isinstance(row["renewable_share_of_generation_pct"], Decimal)
    ]
    shares_over_100 = sum(value > 100 for value in shares)
    missing_target_times = [
        row["timestamp_local"]
        for row in output_rows
        if row["renewable_share_of_generation_pct"] is None
    ]
    if missing_target_times:
        missing_target_note = (
            f"Die fehlenden Zielwerte reichen von "
            f"`{missing_target_times[0].isoformat()}` bis "
            f"`{missing_target_times[-1].isoformat()}` (lokale Zeit)."
        )
    else:
        missing_target_note = "Die vorläufige Zielvariable enthält keine fehlenden Werte."

    lines = [
        "# SMARD-Datenqualitätsbericht",
        "",
        "## Umfang",
        "",
        f"- Untersuchungszeitraum: {START_YEAR}-01-01 bis {END_YEAR}-12-31",
        f"- Zusammengeführte Stunden: {len(output_rows):,}".replace(",", "."),
        f"- Erster UTC-Zeitstempel: {common_keys[0].isoformat() if common_keys else '-'}",
        f"- Letzter UTC-Zeitstempel: {common_keys[-1].isoformat() if common_keys else '-'}",
        f"- Lücken in der stündlichen UTC-Zeitachse: {len(utc_gaps)}",
        f"- Nur in Erzeugungsdaten vorhandene Stunden: {len(generation_only)}",
        f"- Nur in Verbrauchsdaten vorhandene Stunden: {len(consumption_only)}",
        f"- Widersprüchliche Erzeugungs-Duplikate: {len(generation_conflicts)}",
        f"- Widersprüchliche Verbrauchs-Duplikate: {len(consumption_conflicts)}",
        "",
        "## Verwendete Rohdateien",
        "",
        "### Erzeugung",
        "",
        *[f"- `{path.name}`" for path in gen_files],
        "",
        "### Stromverbrauch",
        "",
        *[f"- `{path.name}`" for path in load_files],
        "",
        "## Fehlende Werte",
        "",
        "| Spalte | Fehlende Werte |",
        "|---|---:|",
        *[f"| `{column}` | {count} |" for column, count in missing.items()],
        "",
        missing_target_note,
        "",
        "## Zielvariable",
        "",
        "Die Zielvariable ist die Summe aus Biomasse, Wasserkraft, Wind Offshore, Wind Onshore, "
        "Photovoltaik und sonstigen Erneuerbaren geteilt durch die gesamte Stromerzeugung.",
        "",
        f"- Kleinster berechenbarer Anteil: {decimal_text(min(shares) if shares else None)} %",
        f"- Größter berechenbarer Anteil: {decimal_text(max(shares) if shares else None)} %",
        f"- Stunden über 100 %: {shares_over_100}",
        "",
        "Die Zielvariable beschreibt den erneuerbaren Anteil an der gesamten in Deutschland "
        "erfassten Stromerzeugung.",
        "",
        "## Hinweise",
        "",
        "- Lokale Zeitstempel wurden mit der Zeitzone `Europe/Berlin` in eindeutige UTC-Zeitstempel umgerechnet.",
        "- Beide Stunden bei der Zeitumstellung im Herbst bleiben erhalten.",
        "- Rohdateien wurden nicht verändert oder gelöscht.",
        "- Dateien mit `Kopie` sowie das unvollständige Jahr 2026 wurden nicht verarbeitet.",
    ]
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Erstellt: {OUTPUT_FILE.relative_to(PROJECT_ROOT)} ({len(output_rows)} Zeilen)")
    print(f"Erstellt: {REPORT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"UTC-Lücken: {len(utc_gaps)}")
    print(f"Fehlende Zielwerte: {missing['renewable_share_of_generation_pct']}")


if __name__ == "__main__":
    main()
