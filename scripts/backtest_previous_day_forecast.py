"""Backtest of the national main model with ARCHIVED day-ahead weather forecasts; no training.

For the hours after the training end (27.10.2026) that have no genuine live
forecast, the weather input is taken from the Open-Meteo Previous Runs API:
`<variable>_previous_day1` is "the value predicted 24 hours before valid time"
(https://open-meteo.com/en/docs/previous-runs-api, default model Best Match).
This rebuilds what a day-ahead forecast would have seen, but afterwards: it is
a reconstruction, not a live forecast, and is reported separately.

Inputs are built exactly like predict_price_backtest.py / predict_price_forecast.py
(same 23 stations, 137 features, 168 h SMARD/price lags, capacity, calendar);
only the weather source differs. The final main model
(xgboost_selfco2_separate, training end 26.10.2026) is applied with the same
post-processing as predict_xgb_forecast.py (source shares >= 0, sum <= 100 %,
CO2 >= 0, renewable share = sum of the six sources).
"""
import argparse
import ast
import csv
import hashlib
import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from predict_price_backtest import CAPACITY, all_dirs, load_price_series, load_smard
from predict_xgb_forecast import MODEL, SOURCES
from prepare_stage0 import BERLIN, WEATHER, capacity_reference, daylight, holidays, number

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
VARIABLES = {'temperature_2m': '°C', 'cloud_cover': '%', 'wind_speed_100m': 'm/s',
             'shortwave_radiation': 'W/m²', 'sunshine_duration': 's'}
API = 'https://previous-runs-api.open-meteo.com/v1/forecast'


def download(start, end_inclusive, out):
    tree = ast.parse((ROOT / 'archive/legacy_2026-10-20/src/download_weather_2026.py').read_text())
    locations = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'LOCATIONS' for t in n.targets))
    assert len(locations) == 23
    out.mkdir(parents=True)
    hours = int((end_inclusive + timedelta(days=1) - start).total_seconds() // 3600)
    expected = [(start + timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(hours)]
    manifest = dict(source='Open-Meteo Previous Runs API, *_previous_day1 (predicted 24 h before valid time)',
                    endpoint=API, start_utc=start.isoformat(), end_inclusive_day=end_inclusive.date().isoformat(),
                    hours=hours, retrieved_at_utc=datetime.now(UTC).isoformat(),
                    retrospective=True, archived_forecast=True, operational=False, stations={})
    weather = {}
    for station, (lat, lon, sea) in sorted(locations.items()):
        params = dict(latitude=lat, longitude=lon, hourly=','.join(f'{v}_previous_day1' for v in VARIABLES),
                      start_date=start.date().isoformat(), end_date=end_inclusive.date().isoformat(),
                      timezone='GMT', wind_speed_unit='ms', cell_selection='sea' if sea else 'land')
        url = API + '?' + urlencode(params)
        for attempt in range(5):
            try:
                with urlopen(url, timeout=60) as response:
                    body = response.read()
                data = json.loads(body)
                if data.get('error'):
                    raise ValueError(data.get('reason'))
                break
            except (HTTPError, URLError, TimeoutError):
                if attempt == 4:
                    raise
                time.sleep(min(2 ** (attempt + 1), 20))
        (out / f'{station}.json').write_bytes(body)
        assert data['utc_offset_seconds'] == 0 and data['hourly']['time'] == expected, station
        table = {}
        for variable, unit in VARIABLES.items():
            key = f'{variable}_previous_day1'
            assert data['hourly_units'][key] == unit, (station, key)
            values = data['hourly'][key]
            assert all(v is not None and math.isfinite(v) for v in values), (station, key, sum(v is None for v in values))
            for t, v in zip(expected, values):
                table.setdefault(t, {})[variable] = v
        assert all(0 <= r['sunshine_duration'] <= 3600 and 0 <= r['cloud_cover'] <= 100 for r in table.values())
        weather[station] = table
        manifest['stations'][station] = dict(file=f'{station}.json', url=url, sha256=hashlib.sha256(body).hexdigest(),
                                             latitude=data['latitude'], longitude=data['longitude'])
        print(station, hours, 'Stunden geprueft', flush=True)
        time.sleep(.3)
    manifest['complete'] = len(manifest['stations']) == 23
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return weather, expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-10-27', help='first UTC day')
    parser.add_argument('--end', default='2026-11-11', help='last UTC day (inclusive)')
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    last = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=UTC)
    tag = f'{start:%Y%m%d}_{last:%Y%m%d}'
    weather_dir = ROOT / f'data/raw/weather_previous_day1_{tag}'
    out = ROOT / f'reports/backtest_previous_day1_{tag}_v1'
    for path in (weather_dir, out):
        if path.exists():
            raise FileExistsError(f'{path} existiert bereits; kein Ueberschreiben.')

    bundle = joblib.load(MODEL)
    assert pd.Timestamp(bundle['training_end']) < start
    features = bundle['features']
    weather, stamps = download(start, last, weather_dir)

    gen, load = {}, {}
    for smard_dir in all_dirs(ROOT / 'data/raw/smard_range'):
        g, l = load_smard(smard_dir)
        gen.update(g); load.update(l)
    price_dirs = [p for base in ROOT.glob('data/raw/energycharts_price*') if base.is_dir() for p in base.glob('*') if p.is_dir()]
    price_series = load_price_series(price_dirs)
    with CAPACITY.open() as f:
        capacity = {r['reference_date_exclusive']: r for r in csv.DictReader(f)}

    records = []
    for stamp in stamps:
        t = datetime.strptime(stamp, '%Y-%m-%dT%H:%M').replace(tzinfo=UTC)
        local = t.astimezone(BERLIN); lag = t - timedelta(hours=168)
        ref = str(capacity_reference(t)); c = capacity[ref]
        row = dict(target_time_utc=t.isoformat(), target_time_berlin=local.isoformat(),
                   energy_lag_time_utc=lag.isoformat(), capacity_reference_date=ref,
                   hour_local=local.hour, weekday=local.weekday(), month=local.month,
                   is_national_holiday=int(local.date() in holidays(local.year)),
                   daylight_hours_approx=daylight(local.date()))
        for station, table in weather.items():
            w = table[stamp]
            for original, feature in WEATHER.items():
                row[station + '__' + feature] = w[original.split(' (')[0]]
            row[station + '__sunshine_duration_preceding_hour_s'] = w['sunshine_duration']
        for tech in ['pv', 'wind_onshore', 'wind_offshore']:
            row[tech + '_net_mw_reconstructed'] = number(c[tech + '_net_mw'])
        for key, val in gen[lag].items():
            row[key + '_mwh_lag168h'] = val
        row['grid_load_mwh_lag168h'] = load[lag]
        row['price_eur_mwh_lag168h'] = price_series.get(lag)
        records.append(row)
    frame = pd.DataFrame(records)
    x = frame[features].to_numpy(float)
    assert np.isfinite(x).all(), 'fehlende Eingabe'

    values = {}
    with threadpool_limits(limits=1):
        for target in bundle['targets']:
            z = bundle['pipelines'][target].predict(x)
            values[target] = z * bundle['target_std'][target] + bundle['target_mean'][target]
    pred = frame[['target_time_utc', 'target_time_berlin']].copy()
    pred['predicted_co2_gco2eq_kwh'] = np.clip(values['target_co2_gco2eq_kwh'], 0, None)
    shares = pd.DataFrame({f'predicted_{s}_share_pct': np.clip(values[f'target_{s}_share_pct'], 0, None) for s in SOURCES})
    shares = shares.mul((100 / shares.sum(axis=1)).clip(upper=1), axis=0)
    pred[shares.columns] = shares
    pred['predicted_renewable_share_pct'] = shares.sum(axis=1)
    pred['predicted_renewable_share_direct_pct'] = values['target_renewable_share_pct']

    out.mkdir(parents=True)
    frame[['target_time_utc', 'target_time_berlin', 'energy_lag_time_utc', 'capacity_reference_date', *features]].to_csv(
        out / 'inputs.csv', index=False)
    pred.to_csv(out / 'predictions.csv', index=False)
    (out / 'run.json').write_text(json.dumps(dict(
        status='complete', created_utc=datetime.now(UTC).isoformat(), hours=len(pred),
        target_start_utc=start.isoformat(), target_end_exclusive_utc=(last + timedelta(days=1)).isoformat(),
        model=str(MODEL.relative_to(ROOT)), model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        model_training_end=bundle['training_end'], refit=False,
        weather_source='Open-Meteo Previous Runs API, *_previous_day1 (archived forecast, 24 h before valid time)',
        weather_dir=str(weather_dir.relative_to(ROOT)),
        weather_manifest_sha256=hashlib.sha256((weather_dir / 'manifest.json').read_bytes()).hexdigest(),
        clipping='source shares >= 0, scaled to 100 % if their sum exceeds it; CO2 >= 0',
        limitations=['Reconstruction after the fact with archived forecasts, not a live forecast',
                     'Best Match model mix of the archive may differ from the live Forecast API',
                     'SMARD/price lag inputs are current revised snapshots, not as-issued']), indent=2))
    print(pred[['target_time_utc', 'predicted_co2_gco2eq_kwh', 'predicted_renewable_share_pct']].describe().round(1))
    print(out)


if __name__ == '__main__':
    main()
