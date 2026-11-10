"""Retroactive inference for the national price-feature CO2 model, using real
ERA5 archive weather (not a forecast) for a past date range that fell in the
gap between the historical build (stage0 up to 2026-10-26) and when the live
pipeline started (2026-11-10). Mirrors predict_price_forecast.py, just reads
an archive-format weather manifest instead of a forecast-format one and
takes a --start/--end range instead of --target-start/--days.
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from prepare_stage0 import TECH, WEATHER, capacity_reference, daylight, holidays, number, local_to_utc, BERLIN

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'reports/final_hist_gradient_boosting_price_2015_20261026_v1'
CAPACITY = ROOT / 'data/live_capacity/mastr_monthly_reconstructed.csv'
PRICE_FEATURE = 'price_eur_mwh_lag168h'
UTC = timezone.utc


def all_dirs(glob_root: Path) -> list:
    candidates = sorted(p for p in glob_root.glob('*') if p.is_dir() and (p / 'manifest.json').exists())
    if not candidates:
        raise FileNotFoundError(f'Kein vollstaendiger Download-Ordner gefunden unter {glob_root}')
    return candidates


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_smard(smard_dir: Path):
    gen, load = {}, {}
    seen = defaultdict(int)
    with (smard_dir / 'generation.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        mapping = {name: next(k for k in reader.fieldnames if k.startswith(name + ' [MWh]')) for name in TECH}
        for raw in reader:
            t = local_to_utc(raw['Datum von'], seen)
            row = {TECH[name]: number(raw[col], german=True) for name, col in mapping.items()}
            if t.astimezone(BERLIN).date() >= date(2023, 4, 16) and row['nuclear'] is None:
                row['nuclear'] = 0.0
            gen[t] = row
    seen = defaultdict(int)
    with (smard_dir / 'load.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        col = next(k for k in reader.fieldnames if k.startswith('Netzlast [MWh]'))
        for raw in reader:
            t = local_to_utc(raw['Datum von'], seen)
            load[t] = number(raw[col], german=True)
    return gen, load


def load_price_series(price_dirs):
    buckets = {}
    for price_dir in price_dirs:
        for path in sorted(price_dir.glob('*.json')):
            if path.name == 'manifest.json':
                continue
            payload = json.loads(path.read_text())
            assert payload['unit'] == 'EUR / MWh'
            for entry in payload['data']:
                t = datetime.fromisoformat(entry['timestamp']).astimezone(UTC)
                hour = t.replace(minute=0, second=0, microsecond=0)
                value = entry['values']['day_ahead_price']
                if value is None:
                    continue
                buckets.setdefault(hour, []).append(float(value))
    return {k: sum(v) / len(v) for k, v in buckets.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='UTC start day (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='UTC end day inclusive (YYYY-MM-DD)')
    parser.add_argument('--weather-dir', type=Path, required=True)
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    last = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=UTC)
    hours = int((last + timedelta(days=1) - start).total_seconds() / 3600)
    times = pd.date_range(start, periods=hours, freq='h')
    out = ROOT / f'reports/backtest_price_{start:%Y%m%d}_{last:%Y%m%d}_v1'
    if out.exists():
        raise FileExistsError('Backtest output already exists; no overwrite')

    weather_manifest = json.loads((args.weather_dir / 'manifest.json').read_text())
    assert weather_manifest['retrospective'] is True and len(weather_manifest['stations']) == 23
    weather = {}
    for station in weather_manifest['stations']:
        p = args.weather_dir / (station + '.json')
        d = json.loads(p.read_text())['hourly']
        offset = d['time'].index(times[0].strftime('%Y-%m-%dT%H:%M'))
        sliced = {k: v[offset:offset+hours] for k, v in d.items()}
        assert sliced['time'] == [t.strftime('%Y-%m-%dT%H:%M') for t in times]
        weather[station] = {t: {k: sliced[k][i] for k in sliced if k != 'time'} for i, t in enumerate(sliced['time'])}

    gen, load = {}, {}
    for smard_dir in all_dirs(ROOT / 'data/raw/smard_range'):
        g, l = load_smard(smard_dir)
        gen.update(g); load.update(l)
    price_dirs = [p for base in ROOT.glob('data/raw/energycharts_price*') if base.is_dir() for p in base.glob('*') if p.is_dir()]
    price_series = load_price_series(price_dirs)
    with CAPACITY.open() as f:
        capacity = {r['reference_date_exclusive']: r for r in csv.DictReader(f)}

    run = json.loads((MODEL / 'run.json').read_text())
    features = run['features']
    assert len(features) == 137 and PRICE_FEATURE in features

    records = []
    for stamp in times:
        t = stamp.to_pydatetime(); local = t.astimezone(BERLIN); lag = t - timedelta(hours=168)
        ref = str(capacity_reference(t)); c = capacity[ref]
        row = dict(target_time_utc=t.isoformat(), target_time_berlin=local.isoformat(),
                   energy_lag_time_utc=lag.isoformat(), capacity_reference_date=ref,
                   hour_local=local.hour, weekday=local.weekday(), month=local.month,
                   is_national_holiday=int(local.date() in holidays(local.year)),
                   daylight_hours_approx=daylight(local.date()))
        for station, table in weather.items():
            w = table[t.strftime('%Y-%m-%dT%H:%M')]
            for original, feature in WEATHER.items():
                row[station + '__' + feature] = w[original.split(' (')[0]]
            row[station + '__sunshine_duration_preceding_hour_s'] = w['sunshine_duration']
        for tech in ['pv', 'wind_onshore', 'wind_offshore']:
            row[tech + '_net_mw_reconstructed'] = number(c[tech + '_net_mw'])
        for key, val in gen[lag].items():
            row[key + '_mwh_lag168h'] = val
        row['grid_load_mwh_lag168h'] = load[lag]
        row[PRICE_FEATURE] = price_series.get(lag)
        records.append(row)
    assert all(r[PRICE_FEATURE] is not None for r in records), 'Preis fehlt fuer mindestens eine Lag-Stunde'

    frame = pd.DataFrame(records)
    x = frame[features].to_numpy(float)
    assert np.isfinite(x).all() and len(frame) == hours
    bundle = joblib.load(MODEL / 'hist_gradient_boosting_target_co2_gco2eq_kwh.joblib')
    assert bundle['features'] == features
    assert pd.Timestamp(bundle['training_end']) < times[0]
    with threadpool_limits(limits=1):
        pred = bundle['pipeline'].predict(x)
    assert pred.shape == (hours,) and np.isfinite(pred).all()

    results = frame[['target_time_utc', 'target_time_berlin']].copy()
    results['predicted_co2_gco2eq_kwh'] = pred
    out.mkdir()
    frame[['target_time_utc', 'target_time_berlin', 'energy_lag_time_utc', 'capacity_reference_date'] + features].to_csv(out / 'inputs.csv', index=False)
    results.to_csv(out / 'predictions.csv', index=False)
    report = dict(status='complete', created_utc=datetime.now(UTC).isoformat(), hours=hours,
        target_start_utc=times[0].isoformat(), target_end_exclusive_utc=(times[-1] + pd.Timedelta(hours=1)).isoformat(),
        model_training_end=bundle['training_end'], model_sha256=sha(MODEL / 'hist_gradient_boosting_target_co2_gco2eq_kwh.joblib'),
        weather_source='Open-Meteo Archive API (real ERA5 history, not a forecast)',
        weather_manifest_sha256=sha(args.weather_dir / 'manifest.json'),
        operational=False, retrospective_era5=True, targets_read=False, refit=False, clipping=False,
        purpose='Backtest: fills the gap between the historical dataset (ends 2026-10-26) '
                'and the live pipeline (started 2026-11-10) - not a genuine forecast, '
                'the model never saw this period during training or evaluation either way',
        limitations=['Real ERA5 history, not a forecast issued in advance',
                     'SMARD/price lag inputs are fresh current-snapshot revisions, not as-issued history',
                     'Only CO2 predicted here; renewable share added separately by predict_renewable_forecast.py'])
    (out / 'run.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(predicted_co2_gco2eq_kwh=dict(min=float(pred.min()), max=float(pred.max()), mean=float(pred.mean()))), indent=2))
    print(out)


if __name__ == '__main__':
    main()
