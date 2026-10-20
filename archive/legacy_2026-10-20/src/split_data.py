import csv
from pathlib import Path

input_file = Path(
    "data/processed/model_data_clean_2015_2025.csv"
)

output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

train_file = output_dir / "train_2015_2022.csv"
validation_file = output_dir / "validation_2023.csv"
test_file = output_dir / "test_2024_2025.csv"

with input_file.open("r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    fieldnames = reader.fieldnames
    rows = list(reader)

train_rows = []
validation_rows = []
test_rows = []

for row in rows:
    year = int(row["timestamp_utc"][:4])

    if 2015 <= year <= 2022:
        train_rows.append(row)
    elif year == 2023:
        validation_rows.append(row)
    elif 2024 <= year <= 2025:
        test_rows.append(row)


def write_csv(path, selected_rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_rows)


write_csv(train_file, train_rows)
write_csv(validation_file, validation_rows)
write_csv(test_file, test_rows)

print(f"Training: {len(train_rows)} Zeilen -> {train_file}")
print(
    f"Validierung: {len(validation_rows)} Zeilen"
    f" -> {validation_file}"
)
print(f"Test: {len(test_rows)} Zeilen -> {test_file}")
print(
    "Gesamt:",
    len(train_rows) + len(validation_rows) + len(test_rows),
)
