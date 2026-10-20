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


print("Trainiere XGBoost-Modell ...")

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

# Der Grünanteil liegt fachlich zwischen 0 und 100 Prozent.
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
    REPORT_DIR / "xgboost_predictions_2023.csv",
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
    REPORT_DIR / "xgboost_feature_importance.csv",
    index=False,
)


joblib.dump(
    model,
    MODEL_DIR / "weather_xgboost.joblib",
)


with (
    REPORT_DIR / "xgboost_metrics.txt"
).open("w", encoding="utf-8") as file:
    file.write(f"MAE: {mae:.3f} Prozentpunkte\n")
    file.write(f"RMSE: {rmse:.3f} Prozentpunkte\n")
    file.write(f"R2: {r2:.3f}\n")
    file.write(
        f"Beste Iteration: {model.best_iteration}\n"
    )


print()
print("Ergebnis des XGBoost-Modells:")
print(f"MAE: {mae:.3f} Prozentpunkte")
print(f"RMSE: {rmse:.3f} Prozentpunkte")
print(f"R2: {r2:.3f}")
print(f"Beste Iteration: {model.best_iteration}")
print()

print("Bisheriger Vergleich:")
print("Baseline MAE: 19.143")
print("Lineare Regression MAE: 13.796")
print("Random Forest MAE: 13.335")
print()

print(
    "Modell gespeichert: "
    "models/weather_xgboost.joblib"
)
