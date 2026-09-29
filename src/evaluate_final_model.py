from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


TEST_FILE = Path(
    "data/processed/test_energy_2024_2025.csv"
)

MODEL_FILE = Path(
    "models/combined_xgboost.joblib"
)

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

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


print("Lade eingefrorenes Modell ...")

model = joblib.load(MODEL_FILE)

print("Lade unbekannte Testdaten 2024–2025 ...")

test = pd.read_csv(TEST_FILE)

x_test = test[FEATURES]
y_test = test[TARGET]


print("Erstelle endgültige Testvorhersagen ...")

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
    REPORT_DIR
    / "final_model_predictions_2024_2025.csv",
    index=False,
)


with (
    REPORT_DIR
    / "final_model_test_metrics_2024_2025.txt"
).open("w", encoding="utf-8") as file:
    file.write(
        "Unabhängiger Testzeitraum: 2024–2025\n"
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


print()
print("Endgültiger unabhängiger Test 2024–2025:")
print(f"Teststunden: {len(test)}")
print(f"MAE: {mae:.3f} Prozentpunkte")
print(f"RMSE: {rmse:.3f} Prozentpunkte")
print(f"R2: {r2:.3f}")
print()
print(
    "Erstellt: reports/"
    "final_model_test_metrics_2024_2025.txt"
)