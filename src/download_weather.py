from pathlib import Path
from time import sleep
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LOCATIONS = {
    "kiel": (54.32, 10.12),
    "hamburg": (53.55, 9.99),
    "rostock": (54.09, 12.10),
    "hannover": (52.38, 9.73),
    "berlin": (52.52, 13.41),
    "muenster": (51.96, 7.63),
    "koeln": (50.94, 6.96),
    "leipzig": (51.34, 12.37),
    "dresden": (51.05, 13.74),
    "frankfurt": (50.11, 8.68),
    "nuernberg": (49.45, 11.08),
    "stuttgart": (48.78, 9.18),
    "freiburg": (48.00, 7.84),
    "muenchen": (48.14, 11.58),
    "bremen": (53.08, 8.80),
    "schwerin": (53.63, 11.41),
    "potsdam": (52.39, 13.06),
    "magdeburg": (52.13, 11.63),
    "erfurt": (50.98, 11.03),
    "mainz": (50.00, 8.27),
    "saarbruecken": (49.24, 7.00),
}


OUTPUT_DIR = Path("data/raw/weather")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


for name, (latitude, longitude) in LOCATIONS.items():
    output_file = OUTPUT_DIR / f"{name}_2015_2025.csv"

    if output_file.exists():
        print(f"Bereits vorhanden: {output_file}")
        continue

    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2015-01-01",
        "end_date": "2025-12-31",
        "hourly": (
            "temperature_2m,cloud_cover,"
            "wind_speed_100m,shortwave_radiation"
        ),
        "models": "era5",
        "wind_speed_unit": "ms",
        "timezone": "GMT",
        "format": "csv",
    }

    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        + urlencode(parameters)
    )

    print(f"Lade {name} herunter ...")

    request = Request(
        url,
        headers={"User-Agent": "Grid-Forecaster/1.0"},
    )

    with urlopen(request) as response:
        output_file.write_bytes(response.read())

    print(f"Gespeichert: {output_file}")

    # Kurze Pause, damit die API nicht zu viele Anfragen erhält.
    sleep(10)