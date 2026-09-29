from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from xgboost import XGBRegressor


TRAIN_FILE = Path(
    "data/processed/train_energy_2015_2022.csv"
)

VALIDATION_FILE = Path(
    "data/processed/validation_energy_2023.csv"
)

REPORT_DIR = Path("reports")
MODEL_DIR = Path("models")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "renewable_share_of_generation_pct"


WEATHER_FEATURES = [
    "temperature_2m_land_mean_c",
    "cloud_cover_land_mean_pct",
    "wind_speed_100m_land_mean_ms",
    "shortwave_radiation_land_mean_wm2",
    "wind_speed_100m_offshore_mean_ms",
]


CALENDAR_FEATURES = [
    "hour_local",
    "weekday",
    "month",
    "is_weekend",
    "is_public_holiday",
    "daylight_hours",
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

LAGS = [72, 168]

ENERGY_FEATURES = [
    f"{column}_lag_{lag}h"
    for lag in LAGS
    for column in ENERGY_COLUMNS
]


FEATURES = (
    WEATHER_FEATURES
    + ENERGY_FEATURES
    + CALENDAR_FEATURES
)


print("Lade kombinierte Daten ...")

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)

x_train = train[FEATURES]
y_train = train[TARGET]

x_validation = validation[FEATURES]
y_validation = validation[TARGET]


print("Trainiere kombiniertes XGBoost-Modell ...")

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
    early_stopping_rounds=50,
)

model.fit(
    x_train,
    y_train,
    eval_set=[(x_validation, y_validation)],
    verbose=False,
)


print("Erstelle Vorhersagen für 2023 ...")

predictions = model.predict(x_validation)
predictions = np.clip(predictions, 0, 100)

mae = mean_absolute_error(
    y_validation,
    predictions,
)

rmse = mean_squared_error(
    y_validation,
    predictions,
) ** 0.5

r2 = r2_score(
    y_validation,
    predictions,
)


result = pd.DataFrame(
    {
        "timestamp_utc": validation["timestamp_utc"],
        "actual": y_validation,
        "prediction": predictions,
    }
)

result.to_csv(
    REPORT_DIR / "combined_model_predictions_2023.csv",
    index=False,
)


importance = pd.DataFrame(
    {
        "feature": FEATURES,
        "importance": model.feature_importances_,
    }
).sort_values(
    "importance",
    ascending=False,
)

importance.to_csv(
    REPORT_DIR / "combined_model_feature_importance.csv",
    index=False,
)


joblib.dump(
    model,
    MODEL_DIR / "combined_xgboost.joblib",
)


with (
    REPORT_DIR / "combined_model_metrics.txt"
).open("w", encoding="utf-8") as file:
    file.write(f"MAE: {mae:.3f} Prozentpunkte\n")
    file.write(f"RMSE: {rmse:.3f} Prozentpunkte\n")
    file.write(f"R2: {r2:.3f}\n")
    file.write(
        f"Beste Iteration: {model.best_iteration}\n"
    )


print()
print("Ergebnis des kombinierten Modells:")
print(f"MAE: {mae:.3f} Prozentpunkte")
print(f"RMSE: {rmse:.3f} Prozentpunkte")
print(f"R2: {r2:.3f}")
print(f"Beste Iteration: {model.best_iteration}")
print()

print("Vergleich:")
print("Wettermodell MAE: 13.335")
print("Energiemarktmodell MAE: 13.876")
print()

print(
    "Modell gespeichert: "
    "models/combined_xgboost.joblib"
)