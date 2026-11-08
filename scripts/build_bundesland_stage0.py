"""Build the pooled per-Bundesland Stage-0 table (16 states stacked); no training.

Reuses already-built pieces instead of re-deriving them:
- Weather per station: read straight out of stage0_v4_oct26/hourly_{year}.csv
  (already merged ERA5 + sunshine for all 23 stations); just pick the 1-2
  stations assigned to each Bundesland (scripts/bundesland.py), as separate
  columns (station_a__*, station_b__* - NaN for the 11 single-station
  Laender, which HistGradientBoostingRegressor handles natively).
- Capacity: data/processed/mastr_capacity_bundesland_20261105 (built by
  update_mastr_capacity_bundesland.py).
- Holidays: data/raw/holidays_bundesland (Nager.Date API).
- Targets: data/processed/bundesland_targets (computed by
  compute_bundesland_targets.py). Loads +/-1 year to cover the ISO-week
  year-boundary gap in that output.

Row = (hour, Bundesland). "Bundesland" is a categorical input feature, same
treatment as hour_local/weekday/month (OneHotEncoder downstream) - this is
the pooled design, 16x the rows of a single-state table, one shared model
per target instead of 16 separate ones.
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundesland import BUNDESLAENDER, BUNDESLAND_SUFFIX, STATION_BUNDESLAND
from prepare_stage0 import BERLIN

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/stage0_v4_oct26'
CAPACITY_PATH = ROOT / 'data/processed/mastr_capacity_bundesland_20261105/mastr_monthly_reconstructed_bundesland.csv'
HOLIDAYS_DIR = ROOT / 'data/raw/holidays_bundesland'
TARGETS_DIR = ROOT / 'data/processed/bundesland_targets'
WEATHER_FEATURES = ['temperature_2m_c', 'cloud_cover_pct', 'wind_speed_100m_ms',
                    'shortwave_radiation_wm2', 'sunshine_duration_preceding_hour_s']
UTC = timezone.utc

STATION_LAT = {
    'kiel': 54.32, 'hamburg': 53.55, 'rostock': 54.09, 'hannover': 52.38, 'berlin': 52.52,
    'muenster': 51.96, 'koeln': 50.94, 'leipzig': 51.34, 'dresden': 51.05, 'frankfurt': 50.11,
    'nuernberg': 49.45, 'stuttgart': 48.78, 'freiburg': 48.00, 'muenchen': 48.14, 'bremen': 53.08,
    'schwerin': 53.63, 'potsdam': 52.39, 'magdeburg': 52.13, 'erfurt': 50.98, 'mainz': 50.00,
    'saarbruecken': 49.24,
}
LAND_STATIONS = defaultdict(list)
for station, land in STATION_BUNDESLAND.items():
    LAND_STATIONS[land].append(station)
for land in LAND_STATIONS:
    LAND_STATIONS[land].sort()
LAND_LAT = {land: sum(STATION_LAT[s] for s in stations) / len(stations)
           for land, stations in LAND_STATIONS.items()}


def daylight(day, latitude):
    n = day.timetuple().tm_yday
    decl = math.radians(23.44 * math.sin(2 * math.pi * (284 + n) / 365.2425))
    angle = max(-1, min(1, -math.tan(math.radians(latitude)) * math.tan(decl)))
    return round(24 * math.acos(angle) / math.pi, 6)


def load_holiday_sets(years):
    by_land_year = {}
    for year in years:
        path = HOLIDAYS_DIR / f'{year}.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        sets = {land: set() for land in BUNDESLAENDER}
        for h in data:
            d = date.fromisoformat(h['date'])
            if h['global']:
                for land in BUNDESLAENDER:
                    sets[land].add(d)
            else:
                for county in (h['counties'] or []):
                    code = county.replace('DE-', '').lower()
                    land = next((l for l, suf in BUNDESLAND_SUFFIX.items() if suf == code), None)
                    if land:
                        sets[land].add(d)
        by_land_year[year] = sets
    return by_land_year


def load_capacity():
    rows = defaultdict(dict)
    with CAPACITY_PATH.open() as f:
        for r in csv.DictReader(f):
            d = date.fromisoformat(r['reference_date_exclusive'])
            rows[r['bundesland']][d] = dict(
                pv_net_mw_reconstructed=float(r['pv_net_mw']),
                wind_onshore_net_mw_reconstructed=float(r['wind_onshore_net_mw']),
                wind_offshore_net_mw_reconstructed=float(r['wind_offshore_net_mw']))
    return rows


def capacity_reference(t):
    origin = (t - timedelta(hours=72)).astimezone(BERLIN)
    return date(origin.year, origin.month, 1)


def load_targets(years):
    frames = []
    for year in years:
        path = TARGETS_DIR / f'{year}.csv'
        if path.exists():
            frames.append(pd.read_csv(path))
    df = pd.concat(frames, ignore_index=True)
    return df.drop_duplicates(['target_time_utc', 'bundesland'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/processed/bundesland_pooled_v1')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    args.output.mkdir(parents=True)

    capacity = load_capacity()
    all_years = list(range(2015, 2027))

    for year in all_years:
        base = pd.read_csv(BASE / f'hourly_{year}.csv',
                           usecols=lambda c: '__' in c or c in ('target_time_utc', 'hour_local', 'weekday', 'month'))
        targets = load_targets([year - 1, year, year + 1])
        holidays = load_holiday_sets([year - 1, year, year + 1])
        times = pd.to_datetime(base.target_time_utc, utc=True)
        pieces = []
        for land in BUNDESLAENDER:
            stations = LAND_STATIONS[land]
            piece = pd.DataFrame({'target_time_utc': base.target_time_utc, 'hour_local': base.hour_local,
                                  'weekday': base.weekday, 'month': base.month})
            piece['bundesland'] = land
            for slot, station in enumerate(stations[:2], start=1):
                for feat in WEATHER_FEATURES:
                    piece[f'station{slot}__{feat}'] = base[f'{station}__{feat}']
            if len(stations) < 2:
                for feat in WEATHER_FEATURES:
                    piece[f'station2__{feat}'] = float('nan')
            lat = LAND_LAT[land]
            piece['daylight_hours_approx'] = [daylight(t.astimezone(BERLIN).date(), lat) for t in times]
            cap = capacity[land]
            refs = [str(capacity_reference(t)) for t in times]
            piece['capacity_reference_date'] = refs
            cap_df = pd.DataFrame([cap.get(date.fromisoformat(r), dict(
                pv_net_mw_reconstructed=None, wind_onshore_net_mw_reconstructed=None,
                wind_offshore_net_mw_reconstructed=None)) for r in refs])
            piece = pd.concat([piece.reset_index(drop=True), cap_df.reset_index(drop=True)], axis=1)
            land_holidays = {y: holidays[y][land] for y in holidays}
            local_dates = [t.astimezone(BERLIN).date() for t in times]
            piece['is_regional_holiday'] = [int(any(d in land_holidays.get(y, set())
                                                     for y in (d.year - 1, d.year, d.year + 1)))
                                            for d in local_dates]
            land_targets = targets.loc[targets.bundesland == land, ['target_time_utc', 'target_co2_gco2eq_kwh', 'target_renewable_share_pct']]
            piece = piece.merge(land_targets, on='target_time_utc', how='left')
            pieces.append(piece)
        year_df = pd.concat(pieces, ignore_index=True)
        year_df.to_csv(args.output / f'hourly_{year}.csv', index=False)
        complete = year_df[['pv_net_mw_reconstructed', 'target_co2_gco2eq_kwh']].notna().all(axis=1).sum()
        print(year, 'Zeilen:', len(year_df), 'vollstaendig:', complete, flush=True)
    print(args.output)


if __name__ == '__main__':
    main()
