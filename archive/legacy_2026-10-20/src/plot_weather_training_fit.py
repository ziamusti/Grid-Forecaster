from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


TRAIN_FILE = Path("data/processed/train_2015_2022.csv")
MODEL_FILE = Path("models/weather_xgboost.joblib")

REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DATA = REPORT_DIR / "weather_training_fit_monthly_2015_2022.csv"
OUTPUT_FIGURE = FIGURE_DIR / "weather_training_fit_2015_2022.png"

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


print("Lade Trainingsdaten 2015–2022 ...")
data = pd.read_csv(TRAIN_FILE)
data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True)

print("Lade Wetter-XGBoost-Modell ...")
model = joblib.load(MODEL_FILE)

print("Erstelle Vorhersagen für die bekannten Trainingsdaten ...")
data["prediction"] = np.clip(model.predict(data[FEATURES]), 0, 100)

mae = mean_absolute_error(data[TARGET], data["prediction"])
rmse = mean_squared_error(data[TARGET], data["prediction"]) ** 0.5
r2 = r2_score(data[TARGET], data["prediction"])

# Monatliche Mittelwerte machen den achtjährigen Verlauf lesbar.
monthly = (
    data.set_index("timestamp_utc")[[TARGET, "prediction"]]
    .resample("MS")
    .mean()
    .reset_index()
    .rename(columns={TARGET: "actual"})
)

monthly.to_csv(OUTPUT_DATA, index=False)

plt.figure(figsize=(16, 7))

plt.plot(
    monthly["timestamp_utc"],
    monthly["actual"],
    label="Tatsächlicher Grünanteil (Monatsmittel)",
    linewidth=1.8,
)

plt.plot(
    monthly["timestamp_utc"],
    monthly["prediction"],
    label="Vorhersage des Wettermodells (Monatsmittel)",
    linewidth=1.8,
)

plt.xlabel("Trainingszeitraum")
plt.ylabel("Erneuerbaren-Anteil (%)")
plt.title(
    "Wettermodell: tatsächlicher und vorhergesagter Grünanteil\n"
    "Bekannte Trainingsdaten 2015–2022 – monatliche Mittelwerte"
)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(OUTPUT_FIGURE, dpi=200)
plt.close()

print(f"Trainings-MAE: {mae:.3f} Prozentpunkte")
print(f"Trainings-RMSE: {rmse:.3f} Prozentpunkte")
print(f"Trainings-R2: {r2:.3f}")
print(f"Erstellt: {OUTPUT_DATA}")
print(f"Erstellt: {OUTPUT_FIGURE}")
