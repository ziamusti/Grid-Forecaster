"""Backtest of the Bundesland main model with ARCHIVED day-ahead weather forecasts; no training.

Same idea as backtest_previous_day_forecast.py (national): the weather input
is the Open-Meteo Previous Runs API value predicted 24 h before each hour
(`*_previous_day1`), already downloaded by that script to
data/raw/weather_previous_day1_<start>_<end>/. A reconstruction after the
fact, not a live forecast; reported separately.

Inputs are built like predict_bundesland_backtest.py (stage 1: up to two
weather stations per Bundesland, capacity, calendar, regional holidays) plus
the stage-2 inputs like predict_bundesland_xgb_forecast.py (national 168 h
lags taken from the national archived-forecast backtest inputs, own-state
Energy-Charts generation 336 h earlier). The final Bundesland model
(XGBoost stage 2, training end 26.10.2026) is applied with the same limits
(source shares >= 0, sum <= 100 %, CO2 >= 0, renewable share = sum of the
five sources).
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from build_bundesland_stage0 import LAND_LAT, LAND_STATIONS, WEATHER_FEATURES, load_holiday_sets
from build_bundesland_v2 import NATIONAL_LAGS, RAW, STATE_LAGS, TECHS, load_generation
from bundesland import BUNDESLAENDER
from predict_bundesland_backtest import load_capacity
from predict_bundesland_xgb_forecast import MODEL, SOURCES
from prepare_stage0 import BERLIN, WEATHER, capacity_reference, daylight

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
VARIABLES = ['temperature_2m', 'cloud_cover', 'wind_speed_100m', 'shortwave_radiation', 'sunshine_duration']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-10-27')
    parser.add_argument('--end', default='2026-11-11', help='last UTC day (inclusive)')
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    last = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=UTC)
    tag = f'{start:%Y%m%d}_{last:%Y%m%d}'
    weather_dir = ROOT / f'data/raw/weather_previous_day1_{tag}'
    national_dir = ROOT / f'reports/backtest_previous_day1_{tag}_v1'
    out = ROOT / f'reports/backtest_bundesland_previous_day1_{tag}_v1'
    if out.exists():
        raise FileExistsError(f'{out} existiert bereits; kein Ueberschreiben.')
    times = pd.date_range(start, last + pd.Timedelta(hours=23), freq='h')

    manifest = json.loads((weather_dir / 'manifest.json').read_text())
    assert manifest['complete'] and manifest['archived_forecast'] and len(manifest['stations']) == 23
    weather = {}
    for station in manifest['stations']:
        hourly = json.loads((weather_dir / f'{station}.json').read_text())['hourly']
        assert hourly['time'] == [t.strftime('%Y-%m-%dT%H:%M') for t in times], station
        weather[station] = {t: {v: hourly[f'{v}_previous_day1'][i] for v in VARIABLES}
                            for i, t in enumerate(hourly['time'])}

    capacity = load_capacity()
    years = sorted({t.year for t in times} | {t.year - 1 for t in times} | {t.year + 1 for t in times})
    holidays_by_land_year = load_holiday_sets(years)
    records = []
    for land in BUNDESLAENDER:
        stations = LAND_STATIONS[land][:2]
        land_holidays = {y: holidays_by_land_year[y][land] for y in holidays_by_land_year}
        for stamp in times:
            t = stamp.to_pydatetime(); local = t.astimezone(BERLIN)
            ref = str(capacity_reference(t)); cap = capacity[(ref, land)]
            row = dict(target_time_utc=t.isoformat(), target_time_berlin=local.isoformat(), bundesland=land,
                       capacity_reference_date=ref, hour_local=local.hour, weekday=local.weekday(), month=local.month,
                       daylight_hours_approx=daylight(local.date(), LAND_LAT[land]),
                       is_regional_holiday=int(any(local.date() in land_holidays.get(y, set())
                                                   for y in (local.year - 1, local.year, local.year + 1))),
                       pv_net_mw_reconstructed=cap.pv_net_mw, wind_onshore_net_mw_reconstructed=cap.wind_onshore_net_mw,
                       wind_offshore_net_mw_reconstructed=cap.wind_offshore_net_mw)
            for slot, station in enumerate(stations, start=1):
                w = weather[station][t.strftime('%Y-%m-%dT%H:%M')]
                for original, feature in WEATHER.items():
                    row[f'station{slot}__{feature}'] = w[original.split(' (')[0]]
                row[f'station{slot}__sunshine_duration_preceding_hour_s'] = w['sunshine_duration']
            if len(stations) < 2:
                for feature in WEATHER_FEATURES:
                    row[f'station2__{feature}'] = float('nan')
            records.append(row)
    frame = pd.DataFrame(records)
    assert len(frame) == len(times) * len(BUNDESLAENDER)
    frame['target_time_utc'] = pd.to_datetime(frame.target_time_utc, utc=True)

    national = pd.read_csv(national_dir / 'inputs.csv', usecols=['target_time_utc', *NATIONAL_LAGS])
    national['target_time_utc'] = pd.to_datetime(national.target_time_utc, utc=True)
    frame = frame.merge(national, on='target_time_utc', how='left', validate='many_to_one')
    lag_times = frame.target_time_utc - pd.Timedelta(hours=336)
    weeks = {(t.isocalendar()[0], t.isocalendar()[1]) for t in pd.concat([lag_times, lag_times + pd.Timedelta(days=1)])}
    paths = [RAW / str(y) / f'week_{y}_{w:02d}.json' for y, w in sorted(weeks)]
    assert all(p.exists() for p in paths), [str(p) for p in paths if not p.exists()]
    generation = load_generation(paths)[TECHS]
    generation.columns = STATE_LAGS
    frame[STATE_LAGS] = generation.reindex(pd.MultiIndex.from_arrays([lag_times, frame.bundesland])).to_numpy()

    bundle = joblib.load(MODEL)
    assert pd.Timestamp(bundle['training_end']) < start
    required = [f for f in bundle['features'] if f not in bundle['categories'] and not f.startswith('station2__')]
    missing = frame[required].isna().sum()
    assert not missing.any(), f'Fehlende Eingaben: {missing[missing > 0].to_dict()}'
    x = frame[bundle['features']]
    with threadpool_limits(limits=1):
        values = {t: bundle['pipelines'][t].predict(x) * bundle['target_std'][t] + bundle['target_mean'][t]
                  for t in bundle['targets']}

    pred = frame[['target_time_utc', 'target_time_berlin', 'bundesland']].copy()
    pred['target_time_utc'] = pred.target_time_utc.dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    pred['predicted_co2_gco2eq_kwh'] = np.clip(values['target_co2_gco2eq_kwh'], 0, None)
    shares = pd.DataFrame({f'predicted_{s}_share_pct': np.clip(values[f'target_{s}_share_pct'], 0, None) for s in SOURCES})
    shares = shares.mul((100 / shares.sum(axis=1)).clip(upper=1), axis=0)
    pred[shares.columns] = shares
    pred['predicted_renewable_share_pct'] = shares.sum(axis=1)
    assert pred.filter(like='predicted_').notna().all().all()

    out.mkdir(parents=True)
    frame.assign(target_time_utc=pred.target_time_utc).to_csv(out / 'inputs.csv', index=False)
    pred.to_csv(out / 'predictions.csv', index=False)
    (out / 'run.json').write_text(json.dumps(dict(
        status='complete', created_utc=datetime.now(UTC).isoformat(), rows=len(pred), hours=len(times),
        target_start_utc=start.isoformat(), target_end_exclusive_utc=(last + pd.Timedelta(days=1)).isoformat(),
        model=str(MODEL.relative_to(ROOT)), model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        model_training_end=bundle['training_end'], refit=False,
        weather_source='Open-Meteo Previous Runs API, *_previous_day1 (archived forecast, 24 h before valid time)',
        weather_dir=str(weather_dir.relative_to(ROOT)), national_inputs=str(national_dir.relative_to(ROOT)),
        state_generation_weeks=[p.name for p in paths],
        clipping='source shares >= 0, scaled to 100 % if their sum exceeds it; CO2 >= 0',
        limitations=['Reconstruction after the fact with archived forecasts, not a live forecast',
                     'Lag inputs (SMARD, prices, Energy-Charts) are current snapshots, not as-issued']), indent=2))
    print(pred.groupby('bundesland')[['predicted_co2_gco2eq_kwh', 'predicted_renewable_share_pct']].mean().round(1).to_string())
    print(out)


if __name__ == '__main__':
    main()
