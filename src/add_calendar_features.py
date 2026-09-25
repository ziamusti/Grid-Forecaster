import csv
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


INPUT_FILE = Path(
    "data/processed/model_data_hourly_2015_2025.csv"
)

OUTPUT_FILE = Path(
    "data/processed/model_data_with_calendar_2015_2025.csv"
)

BERLIN_TIMEZONE = ZoneInfo("Europe/Berlin")

# Ungefährer geografischer Mittelpunkt Deutschlands
GERMANY_LATITUDE = 51.1657


def easter_sunday(year):
    """Berechnet das Datum des Ostersonntags."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return date(year, month, day)


def nationwide_holidays(year):
    """Bundesweit geltende gesetzliche Feiertage."""
    easter = easter_sunday(year)

    return {
        date(year, 1, 1),       # Neujahr
        easter - timedelta(days=2),   # Karfreitag
        easter + timedelta(days=1),   # Ostermontag
        date(year, 5, 1),       # Tag der Arbeit
        easter + timedelta(days=39),  # Christi Himmelfahrt
        easter + timedelta(days=50),  # Pfingstmontag
        date(year, 10, 3),      # Tag der Deutschen Einheit
        date(year, 12, 25),     # 1. Weihnachtstag
        date(year, 12, 26),     # 2. Weihnachtstag
    }


def daylight_hours(current_date):
    """Näherungsweise Tageslänge am Mittelpunkt Deutschlands."""
    day_of_year = current_date.timetuple().tm_yday

    declination = 23.44 * math.sin(
        math.radians((360 / 365) * (284 + day_of_year))
    )

    latitude_radians = math.radians(GERMANY_LATITUDE)
    declination_radians = math.radians(declination)

    cosine_hour_angle = (
        -math.tan(latitude_radians)
        * math.tan(declination_radians)
    )

    cosine_hour_angle = max(-1, min(1, cosine_hour_angle))
    hour_angle = math.degrees(math.acos(cosine_hour_angle))

    return round(2 * hour_angle / 15, 4)


holidays = set()

for year in range(2015, 2026):
    holidays.update(nationwide_holidays(year))


with INPUT_FILE.open("r", encoding="utf-8", newline="") as input_file:
    reader = csv.DictReader(input_file)
    rows = list(reader)
    original_columns = reader.fieldnames


calendar_columns = [
    "hour_local",
    "weekday",
    "month",
    "is_weekend",
    "is_public_holiday",
    "daylight_hours",
]

output_columns = original_columns + calendar_columns


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
    newline="",
) as output_file:
    writer = csv.DictWriter(
        output_file,
        fieldnames=output_columns,
    )
    writer.writeheader()

    for row in rows:
        timestamp_utc = datetime.fromisoformat(
            row["timestamp_utc"]
        )

        local_time = timestamp_utc.astimezone(
            BERLIN_TIMEZONE
        )

        local_date = local_time.date()
        weekday = local_time.weekday()

        row["hour_local"] = local_time.hour
        row["weekday"] = weekday
        row["month"] = local_time.month
        row["is_weekend"] = int(weekday >= 5)
        row["is_public_holiday"] = int(
            local_date in holidays
        )
        row["daylight_hours"] = daylight_hours(
            local_date
        )

        writer.writerow(row)


print(f"Eingabezeilen: {len(rows)}")
print(f"Erstellt: {OUTPUT_FILE}")
