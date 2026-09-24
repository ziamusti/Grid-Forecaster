import csv
from datetime import datetime, timezone
from pathlib import Path


SMARD_FILE = Path(
    "data/processed/smard_hourly_2015_2025.csv"
)

WEATHER_FILE = Path(
    "data/processed/weather_germany_hourly_2015_2025.csv"
)

OUTPUT_FILE = Path(
    "data/processed/model_data_hourly_2015_2025.csv"
)


def normalize_weather_timestamp(timestamp):
    parsed = datetime.fromisoformat(timestamp)
    parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


with SMARD_FILE.open("r", encoding="utf-8", newline="") as file:
    smard_reader = csv.DictReader(file)
    smard_rows = list(smard_reader)
    smard_columns = smard_reader.fieldnames

smard_data = {
    row["timestamp_utc"]: row
    for row in smard_rows
}


with WEATHER_FILE.open("r", encoding="utf-8", newline="") as file:
    weather_reader = csv.DictReader(file)
    weather_rows = list(weather_reader)
    weather_columns = weather_reader.fieldnames

weather_data = {
    normalize_weather_timestamp(row["timestamp_utc"]): row
    for row in weather_rows
}


common_timestamps = sorted(
    set(smard_data) & set(weather_data)
)

weather_feature_columns = [
    column
    for column in weather_columns
    if column != "timestamp_utc"
]

output_columns = smard_columns + weather_feature_columns

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=output_columns)
    writer.writeheader()

    for timestamp in common_timestamps:
        combined_row = dict(smard_data[timestamp])

        for column in weather_feature_columns:
            combined_row[column] = weather_data[timestamp][column]

        writer.writerow(combined_row)


print(f"SMARD-Stunden: {len(smard_data)}")
print(f"Wetter-Stunden: {len(weather_data)}")
print(f"Gemeinsame Stunden: {len(common_timestamps)}")
print(f"Erstellt: {OUTPUT_FILE}")

