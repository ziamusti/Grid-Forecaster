from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path("reports/energy_model_predictions_2023.csv")

OUTPUT_DIR = Path("reports/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "energy_model_test_full_year_2023.png"
OUTPUT_DATA = Path("reports/energy_model_test_daily_2023.csv")


data = pd.read_csv(INPUT_FILE)
data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True)

# Alle 8.760 Teststunden werden zu Tagesmitteln zusammengefasst,
# damit der Verlauf des vollständigen Jahres lesbar bleibt.
daily = (
    data.set_index("timestamp_utc")[["actual", "prediction"]]
    .resample("D")
    .mean()
    .reset_index()
)

daily.to_csv(OUTPUT_DATA, index=False)

plt.figure(figsize=(16, 7))

plt.plot(
    daily["timestamp_utc"],
    daily["actual"],
    label="Tatsächlicher Grünanteil (Tagesmittel)",
    linewidth=1.4,
)

plt.plot(
    daily["timestamp_utc"],
    daily["prediction"],
    label="Vorhersage des Energiemarktmodells (Tagesmittel)",
    linewidth=1.4,
)

plt.xlabel("Testzeitraum")
plt.ylabel("Erneuerbaren-Anteil (%)")
plt.title(
    "Energiemarktmodell: tatsächlicher und vorhergesagter Grünanteil\n"
    "Unbekanntes Testjahr 2023 – Tagesmittelwerte aus 8.760 Stunden"
)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(OUTPUT_FILE, dpi=200)
plt.close()

print(f"Teststunden: {len(data)}")
print(f"Dargestellte Tage: {len(daily)}")
print(f"Erstellt: {OUTPUT_DATA}")
print(f"Erstellt: {OUTPUT_FILE}")
