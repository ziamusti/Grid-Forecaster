from pathlib import Path
import json

import joblib
import pandas as pd
from xgboost import XGBRegressor


HISTORICAL_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2015_2025.csv"
)

DATA_2026_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2026.csv"
)

MODEL_DIR = Path("models")
REPORT_DIR = Path("reports")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = (
    MODEL_DIR / "production_xgboost_168h.joblib"
)

METADATA_FILE = (
    REPORT_DIR / "production_model_metadata.json"
)

TARGET = "renewable_share_of_generation_pct"


WEATHER_FEATURES = [
    "temperature_2m_land_mean_c",
    "cloud_cover_land_mean_pct",
    "wind_speed_100m_land_mean_ms",
    "shortwave_radiation_land_mean_wm2",
    "wind_speed_100m_offshore_mean_ms",
]


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

ENERGY_FEATURES = [
    f"{column}_lag_168h"
    for column in ENERGY_COLUMNS
]


CALENDAR_FEATURES = [
    "hour_local",
    "weekday",
    "month",
    "is_weekend",
    "is_public_holiday",
    "daylight_hours",
]


FEATURES = (
    WEATHER_FEATURES
    + ENERGY_FEATURES
    + CALENDAR_FEATURES
)


print("Lade Daten 2015–2025 ...")

historical = pd.read_csv(HISTORICAL_FILE)

print("Lade Daten 2026 ...")

data_2026 = pd.read_csv(DATA_2026_FILE)


data = pd.concat(
    [historical, data_2026],
    ignore_index=True,
)

data["timestamp_utc"] = pd.to_datetime(
    data["timestamp_utc"],
    utc=True,
)

data = data.sort_values("timestamp_utc")

data = data.drop_duplicates(
    subset=["timestamp_utc"],
    keep="last",
)


x_train = data[FEATURES]
y_train = data[TARGET]


print(
    "Trainiere endgültiges operatives "
    "168h-XGBoost-Modell ..."
)

model = XGBRegressor(
    objective="reg:squarederror",
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=6,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
)

model.fit(
    x_train,
    y_train,
    verbose=False,
)


joblib.dump(
    model,
    MODEL_FILE,
)


metadata = {
    "model": "XGBRegressor",
    "purpose": "Operative 72-hour forecast",
    "energy_lag_hours": 168,
    "training_rows": len(data),
    "training_start_utc": (
        data["timestamp_utc"].min().isoformat()
    ),
    "training_end_utc": (
        data["timestamp_utc"].max().isoformat()
    ),
    "target": TARGET,
    "features": FEATURES,
}

METADATA_FILE.write_text(
    json.dumps(
        metadata,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


print()
print("Produktionsmodell erfolgreich trainiert.")
print(f"Trainingsstunden: {len(data)}")
print(
    "Trainingszeitraum: "
    f"{data['timestamp_utc'].min()} bis "
    f"{data['timestamp_utc'].max()}"
)
print(f"Modell gespeichert: {MODEL_FILE}")
print(f"Metadaten gespeichert: {METADATA_FILE}")
