from datetime import datetime, timezone
import csv
import json
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
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

VARIABLES = [
    "temperature_2m",
    "cloud_cover",
    "wind_speed_100m",
    "shortwave_radiation",
]

API_URL = "https://api.open-meteo.com/v1/forecast"

OUTPUT_DIR = Path("data/forecast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

run_id = datetime.now(
    timezone.utc
).strftime("%Y%m%dT%H%M%SZ")

RAW_DIR = OUTPUT_DIR / "raw" / run_id
RAW_DIR.mkdir(parents=True, exist_ok=True)

responses = {}


for name, (latitude, longitude, is_sea) in LOCATIONS.items():
    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(VARIABLES),
        "forecast_hours": 72,
        "timezone": "GMT",
        "wind_speed_unit": "ms",
    }

    if is_sea:
        parameters["cell_selection"] = "sea"

    url = API_URL + "?" + urlencode(parameters)

    print(f"Lade Prognose für {name} ...")

    request = Request(
        url,
        headers={
            "User-Agent": "Grid-Forecaster/1.0"
        },
    )

    for attempt in range(1, 4):
        try:
            with urlopen(
                request,
                timeout=120,
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )

            break

        except HTTPError as error:
            if error.code == 429 and attempt < 3:
                print(
                    "Zu viele Anfragen. "
                    "Warte 60 Sekunden ..."
                )
                sleep(60)
            else:
                raise

        except URLError:
            if attempt < 3:
                print(
                    "Verbindungsfehler. "
                    "Warte 30 Sekunden ..."
                )
                sleep(30)
            else:
                raise

    raw_file = RAW_DIR / f"{name}.json"

    raw_file.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    hourly = payload["hourly"]
    times = hourly["time"]

    responses[name] = {
        timestamp: {
            variable: hourly[variable][index]
            for variable in VARIABLES
        }
        for index, timestamp in enumerate(times)
    }

    sleep(2)


land_names = [
    name
    for name, (_, _, is_sea) in LOCATIONS.items()
    if not is_sea
]

offshore_names = [
    name
    for name, (_, _, is_sea) in LOCATIONS.items()
    if is_sea
]


common_times = set(
    responses[land_names[0]]
)

for location_data in responses.values():
    common_times &= set(location_data)

timestamps = sorted(common_times)


rows = []

for timestamp in timestamps:
    land_rows = [
        responses[name][timestamp]
        for name in land_names
    ]

    offshore_rows = [
        responses[name][timestamp]
        for name in offshore_names
    ]

    row = {
        "timestamp_utc": timestamp,
        "temperature_2m_land_mean_c": round(
            sum(
                item["temperature_2m"]
                for item in land_rows
            )
            / len(land_rows),
            4,
        ),
        "cloud_cover_land_mean_pct": round(
            sum(
                item["cloud_cover"]
                for item in land_rows
            )
            / len(land_rows),
            4,
        ),
        "wind_speed_100m_land_mean_ms": round(
            sum(
                item["wind_speed_100m"]
                for item in land_rows
            )
            / len(land_rows),
            4,
        ),
        "shortwave_radiation_land_mean_wm2": round(
            sum(
                item["shortwave_radiation"]
                for item in land_rows
            )
            / len(land_rows),
            4,
        ),
        "wind_speed_100m_offshore_mean_ms": round(
            sum(
                item["wind_speed_100m"]
                for item in offshore_rows
            )
            / len(offshore_rows),
            4,
        ),
    }

    rows.append(row)


fieldnames = [
    "timestamp_utc",
    "temperature_2m_land_mean_c",
    "cloud_cover_land_mean_pct",
    "wind_speed_100m_land_mean_ms",
    "shortwave_radiation_land_mean_wm2",
    "wind_speed_100m_offshore_mean_ms",
]

archive_file = (
    OUTPUT_DIR
    / f"weather_forecast_72h_{run_id}.csv"
)

latest_file = (
    OUTPUT_DIR
    / "weather_forecast_72h_latest.csv"
)


for output_file in [archive_file, latest_file]:
    with output_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


print()
print("Wetterprognose erfolgreich geladen.")
print(f"Standorte: {len(LOCATIONS)}")
print(f"Prognosestunden: {len(rows)}")
print(f"Erste Stunde: {rows[0]['timestamp_utc']}")
print(f"Letzte Stunde: {rows[-1]['timestamp_utc']}")
print(f"Gespeichert: {archive_file}")
print(f"Aktuelle Datei: {latest_file}")