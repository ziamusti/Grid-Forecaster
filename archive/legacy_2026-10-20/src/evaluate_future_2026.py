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
    "data/processed/"
    "model_data_with_energy_lags_2015_2025.csv"
)

TEST_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2026.csv"
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


print("Lade Trainingsdaten 2015–2025 ...")

train = pd.read_csv(TRAIN_FILE)

print("Lade unbekannte Zukunftsdaten 2026 ...")

test = pd.read_csv(TEST_FILE)


x_train = train[FEATURES]
y_train = train[TARGET]

x_test = test[FEATURES]
y_test = test[TARGET]


print("Trainiere festgelegtes Modell mit 2015–2025 ...")

# Dieselben Einstellungen wie beim ausgewählten
# kombinierten Modell. Die Einstellungen werden nicht
# anhand der Testdaten 2026 verändert.
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
)

model.fit(
    x_train,
    y_train,
    verbose=False,
)


print("Erstelle unbekannte Vorhersagen für 2026 ...")

predictions = model.predict(x_test)
predictions = np.clip(predictions, 0, 100)


mae = mean_absolute_error(
    y_test,
    predictions,
)

rmse = mean_squared_error(
    y_test,
    predictions,
) ** 0.5

r2 = r2_score(
    y_test,
    predictions,
)


result = pd.DataFrame(
    {
        "timestamp_utc": test["timestamp_utc"],
        "actual": y_test,
        "prediction": predictions,
        "absolute_error": np.abs(
            y_test.to_numpy() - predictions
        ),
    }
)

result.to_csv(
    REPORT_DIR / "future_predictions_2026.csv",
    index=False,
)


with (
    REPORT_DIR / "future_test_metrics_2026.txt"
).open("w", encoding="utf-8") as file:
    file.write(
        "Training: 2015–2025\n"
    )
    file.write(
        "Unabhängiger Zukunftstest: "
        "Januar–September 2026\n"
    )
    file.write(
        f"Teststunden: {len(test)}\n"
    )
    file.write(
        f"MAE: {mae:.3f} Prozentpunkte\n"
    )
    file.write(
        f"RMSE: {rmse:.3f} Prozentpunkte\n"
    )
    file.write(f"R2: {r2:.3f}\n")


joblib.dump(
    model,
    MODEL_DIR
    / "combined_xgboost_trained_through_2025.joblib",
)


print()
print("Zukunftstest 2026:")
print("Training: 2015–2025")
print(f"Teststunden 2026: {len(test)}")
print(f"MAE: {mae:.3f} Prozentpunkte")
print(f"RMSE: {rmse:.3f} Prozentpunkte")
print(f"R2: {r2:.3f}")
print()

print(
    "Erstellt: "
    "reports/future_test_metrics_2026.txt"
)
print(
    "Modell gespeichert: "
    "models/"
    "combined_xgboost_trained_through_2025.joblib"
)