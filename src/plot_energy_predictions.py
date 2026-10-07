from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path(
    "reports/energy_model_predictions_2023.csv"
)

OUTPUT_DIR = Path("reports/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "energy_model_predictions_january_2023.png"
)


data = pd.read_csv(INPUT_FILE)

data["timestamp_utc"] = pd.to_datetime(
    data["timestamp_utc"],
    utc=True,
)

# Für eine gut lesbare Darstellung werden die ersten 14 Tage gezeigt.
start = pd.Timestamp("2023-01-01", tz="UTC")
end = pd.Timestamp("2023-01-15", tz="UTC")

selected = data[
    (data["timestamp_utc"] >= start)
    & (data["timestamp_utc"] < end)
].copy()


plt.figure(figsize=(14, 6))

plt.plot(
    selected["timestamp_utc"],
    selected["actual"],
    label="Tatsächlicher Grünanteil",
    linewidth=1.5,
)

plt.plot(
    selected["timestamp_utc"],
    selected["prediction"],
    label="Vorhersage des Energiemarktmodells",
    linewidth=1.5,
)

plt.xlabel("Zeitpunkt")
plt.ylabel("Erneuerbaren-Anteil (%)")
plt.title(
    "Tatsächlicher und vorhergesagter Grünanteil\n"
    "Energiemarktmodell – 1. bis 14. Januar 2023"
)

plt.legend()
plt.grid(alpha=0.3)
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    OUTPUT_FILE,
    dpi=200,
)

plt.close()

print(f"Erstellt: {OUTPUT_FILE}")
