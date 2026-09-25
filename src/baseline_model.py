from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


TRAIN_FILE = Path("data/processed/train_2015_2022.csv")
VALIDATION_FILE = Path("data/processed/validation_2023.csv")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "renewable_share_of_generation_pct"


# Daten laden
train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)

# Durchschnitt für jede Kombination aus Wochentag und Stunde
hourly_average = (
    train.groupby(["weekday", "hour_local"])[TARGET]
    .mean()
    .rename("prediction")
    .reset_index()
)

# Vorhersagen für 2023 erstellen
result = validation.merge(
    hourly_average,
    on=["weekday", "hour_local"],
    how="left",
)

# Ersatzwert, falls eine Kombination fehlen sollte
result["prediction"] = result["prediction"].fillna(train[TARGET].mean())

# Modell bewerten
actual = result[TARGET]
prediction = result["prediction"]

mae = mean_absolute_error(actual, prediction)
rmse = mean_squared_error(actual, prediction) ** 0.5
r2 = r2_score(actual, prediction)

# Ergebnisse speichern
result[
    ["timestamp_utc", TARGET, "prediction"]
].to_csv(
    REPORT_DIR / "baseline_predictions_2023.csv",
    index=False,
)

with (REPORT_DIR / "baseline_metrics.txt").open(
    "w", encoding="utf-8"
) as file:
    file.write(f"MAE: {mae:.3f} Prozentpunkte\n")
    file.write(f"RMSE: {rmse:.3f} Prozentpunkte\n")
    file.write(f"R2: {r2:.3f}\n")

print(f"MAE: {mae:.3f} Prozentpunkte")
print(f"RMSE: {rmse:.3f} Prozentpunkte")
print(f"R2: {r2:.3f}")
print("Erstellt: reports/baseline_predictions_2023.csv")
print("Erstellt: reports/baseline_metrics.txt")
