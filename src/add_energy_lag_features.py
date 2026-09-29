from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/model_data_clean_2015_2025.csv"
)

OUTPUT_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2015_2025.csv"
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


print("Lade Datensatz ...")

data = pd.read_csv(INPUT_FILE)

data[TIME_COLUMN] = pd.to_datetime(
    data[TIME_COLUMN],
    utc=True,
)

data = data.sort_values(TIME_COLUMN)


for lag_hours in LAGS:
    print(
        f"Erstelle Merkmale für "
        f"{lag_hours} Stunden Vergangenheit ..."
    )

    lagged = data[
        [TIME_COLUMN] + ENERGY_COLUMNS
    ].copy()

    # Der alte Zeitpunkt wird dem zukünftigen Zielzeitpunkt
    # zugeordnet.
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

    data = data.merge(
        lagged,
        on=TIME_COLUMN,
        how="left",
    )


lag_columns = [
    f"{column}_lag_{lag_hours}h"
    for lag_hours in LAGS
    for column in ENERGY_COLUMNS
]

rows_before = len(data)

# Nur Zeilen entfernen, für die vergangene Stromwerte fehlen.
data = data.dropna(subset=lag_columns).copy()

rows_after = len(data)

data.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print(f"Zeilen vorher: {rows_before}")
print(
    f"Entfernte Zeilen ohne vollständige "
    f"Vergangenheitswerte: {rows_before - rows_after}"
)
print(f"Zeilen danach: {rows_after}")
print(f"Erstellt: {OUTPUT_FILE}")
