from pathlib import Path

import pandas as pd


HISTORY_FILE = Path(
    "data/processed/model_data_clean_2015_2025.csv"
)

DATA_2026_FILE = Path(
    "data/processed/model_data_with_calendar_2026.csv"
)

OUTPUT_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2026.csv"
)

TIME_COLUMN = "timestamp_utc"

ENERGY_COLUMNS = [
    "renewable_share_of_generation_pct",
    "renewable_generation_mwh",
    "total_generation_mwh",
    "grid_load_mwh",
    "wind_onshore_mwh",
    "wind_offshore_mwh",
    "solar_mwh",
    "natural_gas_mwh",
    "hard_coal_mwh",
    "lignite_mwh",
]

LAGS = [72, 168]


print("Lade historische Daten bis 2025 ...")

history = pd.read_csv(HISTORY_FILE)

print("Lade Testdaten 2026 ...")

data_2026 = pd.read_csv(DATA_2026_FILE)


history[TIME_COLUMN] = pd.to_datetime(
    history[TIME_COLUMN],
    utc=True,
)

data_2026[TIME_COLUMN] = pd.to_datetime(
    data_2026[TIME_COLUMN],
    utc=True,
)


# Historische Daten und 2026 gemeinsam verwenden,
# damit die ersten Stunden 2026 Vergangenheitswerte
# aus dem Dezember 2025 erhalten.
all_data = pd.concat(
    [history, data_2026],
    ignore_index=True,
)

all_data = all_data.sort_values(TIME_COLUMN)

all_data = all_data.drop_duplicates(
    subset=[TIME_COLUMN],
    keep="last",
)


for lag_hours in LAGS:
    print(
        f"Erstelle Merkmale für "
        f"{lag_hours} Stunden Vergangenheit ..."
    )

    lagged = all_data[
        [TIME_COLUMN] + ENERGY_COLUMNS
    ].copy()

    lagged[TIME_COLUMN] = (
        lagged[TIME_COLUMN]
        + pd.Timedelta(hours=lag_hours)
    )

    lagged = lagged.rename(
        columns={
            column: f"{column}_lag_{lag_hours}h"
            for column in ENERGY_COLUMNS
        }
    )

    all_data = all_data.merge(
        lagged,
        on=TIME_COLUMN,
        how="left",
    )


lag_columns = [
    f"{column}_lag_{lag_hours}h"
    for lag_hours in LAGS
    for column in ENERGY_COLUMNS
]


# Nur das Jahr 2026 als Zukunftstest auswählen.
test_2026 = all_data[
    all_data[TIME_COLUMN].dt.year == 2026
].copy()

rows_before = len(test_2026)

test_2026 = test_2026.dropna(
    subset=lag_columns
).copy()

rows_after = len(test_2026)


test_2026.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print(f"2026-Zeilen vorher: {rows_before}")
print(
    "Entfernte Zeilen ohne vollständige "
    f"Vergangenheitswerte: {rows_before - rows_after}"
)
print(f"2026-Zeilen danach: {rows_after}")
print(f"Erstellt: {OUTPUT_FILE}")
