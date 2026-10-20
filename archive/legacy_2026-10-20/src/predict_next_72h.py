from datetime import date, timedelta
import csv
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd


WEATHER_FILE = Path(
    "data/forecast/weather_forecast_72h_latest.csv"
)

SMARD_FILE = Path(
    "data/processed/smard_hourly_2026.csv"
)

MODEL_FILE = Path(
    "models/production_xgboost_168h.joblib"
)

METADATA_FILE = Path(
    "reports/production_model_metadata.json"
)

OUTPUT_DIR = Path("reports/live_forecasts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BERLIN = ZoneInfo("Europe/Berlin")
GERMANY_LATITUDE = 51.1657

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


def easter_sunday(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (
        19 * a + b - d - g + 15
    ) % 30
    i = c // 4
    k = c % 4
    l = (
        32 + 2 * e + 2 * i - h - k
    ) % 7
    m = (
        a + 11 * h + 22 * l
    ) // 451

    month = (
        h + l - 7 * m + 114
    ) // 31

    day = (
        (h + l - 7 * m + 114) % 31
    ) + 1

    return date(year, month, day)


def nationwide_holidays(year):
    easter = easter_sunday(year)

    return {
        date(year, 1, 1),
        easter - timedelta(days=2),
        easter + timedelta(days=1),
        date(year, 5, 1),
        easter + timedelta(days=39),
        easter + timedelta(days=50),
        date(year, 10, 3),
        date(year, 12, 25),
        date(year, 12, 26),
    }


def daylight_hours(current_date):
    day_of_year = current_date.timetuple().tm_yday

    declination = 23.44 * math.sin(
        math.radians(
            (360 / 365)
            * (284 + day_of_year)
        )
    )

    latitude = math.radians(
        GERMANY_LATITUDE
    )

    declination = math.radians(
        declination
    )

    cosine_hour_angle = (
        -math.tan(latitude)
        * math.tan(declination)
    )

    cosine_hour_angle = max(
        -1,
        min(1, cosine_hour_angle),
    )

    hour_angle = math.degrees(
        math.acos(cosine_hour_angle)
    )

    return round(
        2 * hour_angle / 15,
        4,
    )


print("Lade Wetterprognose ...")

forecast = pd.read_csv(WEATHER_FILE)

forecast["timestamp_utc"] = pd.to_datetime(
    forecast["timestamp_utc"],
    utc=True,
)


print("Lade aktuelle SMARD-Daten ...")

smard = pd.read_csv(SMARD_FILE)

smard["timestamp_utc"] = pd.to_datetime(
    smard["timestamp_utc"],
    utc=True,
)


# Für jede zukünftige Stunde wird der exakt
# 168 Stunden ältere Stromwert gesucht.
forecast["lag_timestamp_utc"] = (
    forecast["timestamp_utc"]
    - pd.Timedelta(hours=168)
)

lagged_smard = smard[
    ["timestamp_utc"] + ENERGY_COLUMNS
].copy()

lagged_smard = lagged_smard.rename(
    columns={
        "timestamp_utc": "lag_timestamp_utc",
        **{
            column: f"{column}_lag_168h"
            for column in ENERGY_COLUMNS
        },
    }
)

forecast = forecast.merge(
    lagged_smard,
    on="lag_timestamp_utc",
    how="left",
)


print("Erstelle Kalendermerkmale ...")

holidays = nationwide_holidays(2026)

local_times = forecast[
    "timestamp_utc"
].dt.tz_convert(BERLIN)

forecast["timestamp_local"] = local_times

forecast["hour_local"] = (
    local_times.dt.hour
)

forecast["weekday"] = (
    local_times.dt.weekday
)

forecast["month"] = (
    local_times.dt.month
)

forecast["is_weekend"] = (
    forecast["weekday"] >= 5
).astype(int)

forecast["is_public_holiday"] = [
    int(timestamp.date() in holidays)
    for timestamp in local_times
]

forecast["daylight_hours"] = [
    daylight_hours(timestamp.date())
    for timestamp in local_times
]


metadata = json.loads(
    METADATA_FILE.read_text(
        encoding="utf-8"
    )
)

features = metadata["features"]


missing_columns = [
    column
    for column in features
    if column not in forecast.columns
]

if missing_columns:
    raise ValueError(
        "Fehlende Modellspalten: "
        f"{missing_columns}"
    )


missing_values = forecast[
    features
].isna().sum()

missing_values = missing_values[
    missing_values > 0
]

if not missing_values.empty:
    raise ValueError(
        "Nicht verfügbare Eingabewerte:\n"
        f"{missing_values}"
    )


print("Lade Produktionsmodell ...")

model = joblib.load(MODEL_FILE)


print("Erstelle 72-Stunden-Prognose ...")

predictions = model.predict(
    forecast[features]
)

forecast[
    "predicted_renewable_share_pct"
] = np.clip(
    predictions,
    0,
    100,
)


result_columns = [
    "timestamp_utc",
    "timestamp_local",
    "predicted_renewable_share_pct",
]

result = forecast[result_columns].copy()

result = result.sort_values(
    "timestamp_utc"
)


run_id = pd.Timestamp.now(
    tz="UTC"
).strftime("%Y%m%dT%H%M%SZ")

archive_file = (
    OUTPUT_DIR
    / f"grid_forecast_72h_{run_id}.csv"
)

latest_file = (
    OUTPUT_DIR
    / "grid_forecast_72h_latest.csv"
)


for output_file in [
    archive_file,
    latest_file,
]:
    result.to_csv(
        output_file,
        index=False,
    )


best_hours = result.nlargest(
    10,
    "predicted_renewable_share_pct",
)


print()
print("72-Stunden-Prognose erfolgreich.")
print(f"Prognosestunden: {len(result)}")
print(f"Erste Stunde: {result.iloc[0]['timestamp_local']}")
print(f"Letzte Stunde: {result.iloc[-1]['timestamp_local']}")
print()
print("Die 10 grünsten vorhergesagten Stunden:")
print(
    best_hours[
        [
            "timestamp_local",
            "predicted_renewable_share_pct",
        ]
    ].to_string(index=False)
)
print()
print(f"Gespeichert: {archive_file}")
print(f"Aktuelle Datei: {latest_file}")