from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


TRAIN_FILE = Path("data/processed/train_2015_2022.csv")
VALIDATION_FILE = Path(
    "data/processed/validation_2023.csv"
)

REPORT_DIR = Path("reports")
MODEL_DIR = Path("models")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "renewable_share_of_generation_pct"

FEATURES = [
    "temperature_2m_land_mean_c",
    "cloud_cover_land_mean_pct",
    "wind_speed_100m_land_mean_ms",
    "shortwave_radiation_land_mean_wm2",
    "wind_speed_100m_offshore_mean_ms",
    "hour_local",
    "weekday",
    "month",
    "is_weekend",
    "is_public_holiday",
    "daylight_hours",
]


print("Lade Daten ...")

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)

x_train = train[FEATURES]
y_train = train[TARGET]

x_validation = validation[FEATURES]
y_validation = validation[TARGET]


print("Trainiere HistGradientBoosting-Modell ...")

model = HistGradientBoostingRegressor(
    learning_rate=0.05,
    max_iter=500,
    max_leaf_nodes=31,
    max_depth=None,
    min_samples_leaf=20,
    l2_regularization=0.1,
    random_state=42,
    early_stopping=False,
)

model.fit(x_train, y_train)


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
    REPORT_DIR
    / "hist_gradient_boosting_predictions_2023.csv",
    index=False,
)


joblib.dump(
    model,
    MODEL_DIR
    / "weather_hist_gradient_boosting.joblib",
)


with (
    REPORT_DIR
    / "hist_gradient_boosting_metrics.txt"
).open("w", encoding="utf-8") as file:
    file.write(f"MAE: {mae:.3f} Prozentpunkte\n")
    file.write(f"RMSE: {rmse:.3f} Prozentpunkte\n")
    file.write(f"R2: {r2:.3f}\n")


print()
print("Ergebnis des HistGradientBoosting-Modells:")
print(f"MAE: {mae:.3f} Prozentpunkte")
print(f"RMSE: {rmse:.3f} Prozentpunkte")
print(f"R2: {r2:.3f}")
print()

print("Bisheriger Vergleich:")
print("Baseline MAE: 19.143")
print("Lineare Regression MAE: 13.796")
print("Random Forest MAE: 13.335")
print("XGBoost MAE: 13.335")
print()

print(
    "Modell gespeichert: "
    "models/weather_hist_gradient_boosting.joblib"
)