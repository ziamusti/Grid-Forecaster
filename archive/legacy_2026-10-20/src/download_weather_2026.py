from pathlib import Path
from time import sleep
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LOCATIONS = {
    "kiel": (54.32, 10.12, False),
    "hamburg": (53.55, 9.99, False),
    "rostock": (54.09, 12.10, False),
    "hannover": (52.38, 9.73, False),
    "berlin": (52.52, 13.41, False),
    "muenster": (51.96, 7.63, False),
    "koeln": (50.94, 6.96, False),
    "leipzig": (51.34, 12.37, False),
    "dresden": (51.05, 13.74, False),
    "frankfurt": (50.11, 8.68, False),
    "nuernberg": (49.45, 11.08, False),
    "stuttgart": (48.78, 9.18, False),
    "freiburg": (48.00, 7.84, False),
    "muenchen": (48.14, 11.58, False),
    "bremen": (53.08, 8.80, False),
    "schwerin": (53.63, 11.41, False),
    "potsdam": (52.39, 13.06, False),
    "magdeburg": (52.13, 11.63, False),
    "erfurt": (50.98, 11.03, False),
    "mainz": (50.00, 8.27, False),
    "saarbruecken": (49.24, 7.00, False),
    "nordsee_offshore": (54.00, 7.00, True),
    "ostsee_offshore": (54.60, 13.00, True),
}


OUTPUT_DIR = Path("data/raw/weather")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


for name, (latitude, longitude, is_sea) in LOCATIONS.items():
    output_file = OUTPUT_DIR / f"{name}_2026.csv"

    if output_file.exists():
        print(f"Bereits vorhanden: {output_file}")
        continue

    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2026-01-01",
        "end_date": "2026-09-23",
        "hourly": (
            "temperature_2m,cloud_cover,"
            "wind_speed_100m,shortwave_radiation"
        ),
        "models": "era5",
        "wind_speed_unit": "ms",
        "timezone": "GMT",
        "format": "csv",
    }

    if is_sea:
        parameters["cell_selection"] = "sea"

    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        + urlencode(parameters)
    )

    print(f"Lade {name} herunter ...")

    request = Request(
        url,
        headers={"User-Agent": "Grid-Forecaster/1.0"},
    )

    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=120) as response:
                output_file.write_bytes(response.read())

            print(f"Gespeichert: {output_file}")
            break

        except HTTPError as error:
            if error.code == 429 and attempt < 3:
                print("Zu viele Anfragen. Warte 60 Sekunden ...")
                sleep(60)
            else:
                raise

    sleep(10)
