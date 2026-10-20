import csv
from pathlib import Path


RAW_DIR = Path("data/raw/weather")
OUTPUT_FILE = Path(
    "data/processed/weather_germany_hourly_2015_2025.csv"
)

VARIABLES = [
    "temperature_2m (°C)",
    "cloud_cover (%)",
    "wind_speed_100m (m/s)",
    "shortwave_radiation (W/m²)",
]


def read_weather_file(file_path):
    data = {}

    with file_path.open("r", encoding="utf-8", newline="") as file:
        # Die ersten drei Zeilen enthalten Open-Meteo-Metadaten.
        next(file)
        next(file)
        next(file)

        reader = csv.DictReader(file)

        for row in reader:
            timestamp = row["time"]

            data[timestamp] = {
                variable: float(row[variable])
                for variable in VARIABLES
            }

    return data


land_files = sorted(
    file_path
    for file_path in RAW_DIR.glob("*_2015_2025.csv")
    if "offshore" not in file_path.name
)

offshore_files = sorted(
    RAW_DIR.glob("*_offshore_2015_2025.csv")
)

print(f"Landstandorte: {len(land_files)}")
print(f"Offshore-Standorte: {len(offshore_files)}")

land_data = {
    file_path.stem: read_weather_file(file_path)
    for file_path in land_files
}

offshore_data = {
    file_path.stem: read_weather_file(file_path)
    for file_path in offshore_files
}

first_land_location = next(iter(land_data))
timestamps = sorted(land_data[first_land_location])

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
    fieldnames = [
        "timestamp_utc",
        "temperature_2m_land_mean_c",
        "cloud_cover_land_mean_pct",
        "wind_speed_100m_land_mean_ms",
        "shortwave_radiation_land_mean_wm2",
        "wind_speed_100m_offshore_mean_ms",
    ]

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    for timestamp in timestamps:
        land_rows = [
            location_data[timestamp]
            for location_data in land_data.values()
        ]

        offshore_rows = [
            location_data[timestamp]
            for location_data in offshore_data.values()
        ]

        writer.writerow(
            {
                "timestamp_utc": timestamp,
                "temperature_2m_land_mean_c": round(
                    sum(row["temperature_2m (°C)"] for row in land_rows)
                    / len(land_rows),
                    4,
                ),
                "cloud_cover_land_mean_pct": round(
                    sum(row["cloud_cover (%)"] for row in land_rows)
                    / len(land_rows),
                    4,
                ),
                "wind_speed_100m_land_mean_ms": round(
                    sum(row["wind_speed_100m (m/s)"] for row in land_rows)
                    / len(land_rows),
                    4,
                ),
                "shortwave_radiation_land_mean_wm2": round(
                    sum(
                        row["shortwave_radiation (W/m²)"]
                        for row in land_rows
                    )
                    / len(land_rows),
                    4,
                ),
                "wind_speed_100m_offshore_mean_ms": round(
                    sum(
                        row["wind_speed_100m (m/s)"]
                        for row in offshore_rows
                    )
                    / len(offshore_rows),
                    4,
                ),
            }
        )

print(f"Erstellt: {OUTPUT_FILE}")
print(f"Stunden: {len(timestamps)}")
