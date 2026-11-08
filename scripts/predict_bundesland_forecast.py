"""Operational inference for the pooled per-Bundesland models (CO2 + Gruenanteil).

Reuses the same real Open-Meteo weather FORECAST already downloaded for the
national price model (data/raw/weather_forecast_<date>_<days>d, same 23
stations) - just picks each Bundesland's 1-2 assigned stations
(scripts/bundesland.py). No price/SMARD lag features: the pooled Bundesland
models never used them. Capacity: data/live_capacity/
mastr_monthly_reconstructed_bundesland.csv (periodically-refreshed snapshot,
same convention as the national live_capacity file - not auto-updated daily).
Holidays: data/raw/holidays_bundesland (static through 2026).
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundesland import BUNDESLAENDER
from build_bundesland_stage0 import LAND_STATIONS, LAND_LAT, WEATHER_FEATURES, load_holiday_sets
from prepare_stage0 import WEATHER, capacity_reference, daylight, BERLIN

ROOT = Path(__file__).resolve().parents[1]
CAPACITY = ROOT / 'data/live_capacity/mastr_monthly_reconstructed_bundesland.csv'
MODELS = {
    'target_co2_gco2eq_kwh': dict(
        dir=ROOT / 'reports/final_hist_gradient_boosting_bundesland_co2_2015_2026_v1',
        file='hist_gradient_boosting_bundesland_co2_target_co2_gco2eq_kwh.joblib',
        column='predicted_co2_gco2eq_kwh'),
    'target_renewable_share_pct': dict(
        dir=ROOT / 'reports/final_hist_gradient_boosting_bundesland_renewable_share_2015_2026_v1',
        file='hist_gradient_boosting_bundesland_renewable_share_target_renewable_share_pct.joblib',
        column='predicted_renewable_share_pct'),
}
UTC = timezone.utc


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_capacity():
    frame = pd.read_csv(CAPACITY)
    frame['reference_date_exclusive'] = frame['reference_date_exclusive'].astype(str)
    return {(r.reference_date_exclusive, r.bundesland): r for r in frame.itertuples()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-start', required=True, help='UTC start day (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=3)
    parser.add_argument('--weather-dir', type=Path, required=True)
    args = parser.parse_args()
    start = datetime.strptime(args.target_start, '%Y-%m-%d').replace(tzinfo=UTC)
    hours = args.days * 24
    times = pd.date_range(start, periods=hours, freq='h')
    out = ROOT / f'reports/forecast_bundesland_{start:%Y%m%d}_{args.days}d_v1'
    if out.exists():
        raise FileExistsError('Prediction output already exists; no overwrite')

    weather_manifest = json.loads((args.weather_dir / 'manifest.json').read_text())
    assert weather_manifest['complete'] and len(weather_manifest['stations']) == 23
    assert weather_manifest['operational'] is True and weather_manifest['retrospective'] is False
    weather = {}
    for station in weather_manifest['stations']:
        d = json.loads((args.weather_dir / (station + '.json')).read_text())['hourly']
        offset = d['time'].index(times[0].strftime('%Y-%m-%dT%H:%M'))
        sliced = {k: v[offset:offset + hours] for k, v in d.items()}
        assert sliced['time'] == [t.strftime('%Y-%m-%dT%H:%M') for t in times]
        weather[station] = {t: {k: sliced[k][i] for k in sliced if k != 'time'} for i, t in enumerate(sliced['time'])}

    capacity = load_capacity()
    years = sorted({t.year for t in times} | {t.year - 1 for t in times} | {t.year + 1 for t in times})
    holidays_by_land_year = load_holiday_sets(years)

    bundles = {}
    for target, cfg in MODELS.items():
        run = json.loads((cfg['dir'] / 'run.json').read_text())
        bundle = joblib.load(cfg['dir'] / cfg['file'])
        assert bundle['features'] == run['features']
        assert pd.Timestamp(bundle['training_end']) < times[0]
        bundles[target] = bundle

    records = []
    for land in BUNDESLAENDER:
        stations = LAND_STATIONS[land][:2]
        lat = LAND_LAT[land]
        land_holidays = {y: holidays_by_land_year[y][land] for y in holidays_by_land_year}
        for stamp in times:
            t = stamp.to_pydatetime()
            local = t.astimezone(BERLIN)
            ref = str(capacity_reference(t))
            cap = capacity.get((ref, land))
            if cap is None:
                raise KeyError(f'Keine Kapazitaet fuer {land} / {ref}')
            is_holiday = int(any(local.date() in land_holidays.get(y, set())
                                  for y in (local.year - 1, local.year, local.year + 1)))
            row = dict(target_time_utc=t.isoformat(), target_time_berlin=local.isoformat(),
                       bundesland=land, capacity_reference_date=ref,
                       hour_local=local.hour, weekday=local.weekday(), month=local.month,
                       daylight_hours_approx=daylight(local.date(), lat),
                       is_regional_holiday=is_holiday,
                       pv_net_mw_reconstructed=cap.pv_net_mw,
                       wind_onshore_net_mw_reconstructed=cap.wind_onshore_net_mw,
                       wind_offshore_net_mw_reconstructed=cap.wind_offshore_net_mw)
            for slot, station in enumerate(stations, start=1):
                w = weather[station][t.strftime('%Y-%m-%dT%H:%M')]
                for original, feature in WEATHER.items():
                    row[f'station{slot}__{feature}'] = w[original.split(' (')[0]]
                row[f'station{slot}__sunshine_duration_preceding_hour_s'] = w['sunshine_duration']
            if len(stations) < 2:
                for feat in WEATHER_FEATURES:
                    row[f'station2__{feat}'] = float('nan')
            records.append(row)

    frame = pd.DataFrame(records)
    assert len(frame) == hours * len(BUNDESLAENDER)

    results = frame[['target_time_utc', 'target_time_berlin', 'bundesland']].copy()
    model_info = {}
    for target, bundle in bundles.items():
        features = bundle['features']
        x = frame[features]
        must_be_finite = [c for c in features if c != 'bundesland' and not c.startswith('station2__')]
        assert np.isfinite(x[must_be_finite].to_numpy(float)).all()
        assert x['bundesland'].notna().all()
        with threadpool_limits(limits=1):
            pred = bundle['pipeline'].predict(x)
        assert pred.shape == (len(frame),) and np.isfinite(pred).all()
        results[MODELS[target]['column']] = pred
        model_info[target] = dict(model=str((MODELS[target]['dir'] / MODELS[target]['file']).relative_to(ROOT)),
                                   training_end=bundle['training_end'],
                                   model_sha256=sha(MODELS[target]['dir'] / MODELS[target]['file']))

    out.mkdir()
    frame.to_csv(out / 'inputs.csv', index=False)
    results.to_csv(out / 'predictions.csv', index=False)
    report = dict(status='complete', created_utc=datetime.now(UTC).isoformat(), hours=hours,
                  bundeslaender=list(BUNDESLAENDER), pooled=True,
                  target_start_utc=times[0].isoformat(),
                  target_end_exclusive_utc=(times[-1] + pd.Timedelta(hours=1)).isoformat(),
                  weather_source='Open-Meteo Forecast API (operational, not ERA5)',
                  weather_manifest_sha256=sha(args.weather_dir / 'manifest.json'),
                  capacity_source=str(CAPACITY.relative_to(ROOT)),
                  models=model_info, operational=True, retrospective_era5=False,
                  targets_read=False, refit=False, clipping=False,
                  limitations=['Gepooltes Modell (ein Modell je Zielgroesse fuer alle 16 Bundeslaender)',
                               'Kapazitaet je Bundesland ist ein periodisch aktualisierter Snapshot, '
                               'nicht taeglich automatisch aktualisiert',
                               'Reale Wettervorhersage, noch nicht veroeffentlichte Ist-Werte; '
                               'Vorhersagegenauigkeit des Wetters selbst hier nicht bewertet'])
    (out / 'run.json').write_text(json.dumps(report, indent=2))
    print(results.groupby('bundesland')[[MODELS[t]['column'] for t in MODELS]].mean().to_string())
    print(out)


if __name__ == '__main__':
    main()
