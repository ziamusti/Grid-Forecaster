from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/"
    "model_data_with_energy_lags_2015_2025.csv"
)

OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("Lade Datensatz ...")

data = pd.read_csv(INPUT_FILE)

data["timestamp_utc"] = pd.to_datetime(
    data["timestamp_utc"],
    utc=True,
)

year = data["timestamp_utc"].dt.year

train = data[
    (year >= 2015) & (year <= 2022)
].copy()

validation = data[
    year == 2023
].copy()

test = data[
    (year >= 2024) & (year <= 2025)
].copy()


train_file = OUTPUT_DIR / "train_energy_2015_2022.csv"
validation_file = (
    OUTPUT_DIR / "validation_energy_2023.csv"
)
test_file = OUTPUT_DIR / "test_energy_2024_2025.csv"


train.to_csv(train_file, index=False)
validation.to_csv(validation_file, index=False)
test.to_csv(test_file, index=False)


print(
    f"Training: {len(train)} Zeilen -> {train_file}"
)
print(
    f"Validierung: {len(validation)} Zeilen"
    f" -> {validation_file}"
)
print(
    f"Test: {len(test)} Zeilen -> {test_file}"
)
print(
    "Gesamt:",
    len(train) + len(validation) + len(test),
)