"""Retrospective inference on 72 unseen UTC hours; no fitting or target access."""
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from prepare_stage0 import TECH, WEATHER, capacity_reference, daylight, holidays, number

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'reports/final_hist_gradient_boosting_2015_2026_v1'
SMARD = ROOT / 'data/raw/smard_prediction_inputs/20261025T200051Z'
WEATHER_DIR = ROOT / 'data/raw/weather_prediction_20260924_20260926_era5'
CAPACITY = ROOT / 'data/processed/stage0_v2_sunshine/mastr_monthly_reconstructed.csv'
OUT = ROOT / 'reports/hist_prediction_20260924_26_v1'
BERLIN = ZoneInfo('Europe/Berlin')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError('Prediction output already exists; no overwrite')
    sources = [CAPACITY, SMARD/'generation.csv', SMARD/'load.csv', WEATHER_DIR/'manifest.json', MODEL/'run.json']
    weather_manifest = json.loads((WEATHER_DIR/'manifest.json').read_text())
    assert weather_manifest['complete'] and len(weather_manifest['stations']) == 23
    weather = {}
    for station in weather_manifest['stations']:
        p = WEATHER_DIR/(station+'.json')
        assert sha(p) == weather_manifest['stations'][station]['sha256']
        sources.append(p)
        d = json.loads(p.read_text())['hourly']
        weather[station] = {t: {k: d[k][i] for k in d if k != 'time'} for i,t in enumerate(d['time'])}
    energy = {}
    for filename, mapping in [('generation.csv', TECH), ('load.csv', {'Netzlast':'grid_load'})]:
        with (SMARD/filename).open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            columns = {k: next(c for c in reader.fieldnames if c.startswith(k+' [MWh]')) for k in mapping}
            for row in reader:
                t = datetime.strptime(row['Datum von'],'%d.%m.%Y %H:%M').replace(tzinfo=BERLIN).astimezone(timezone.utc)
                dest = energy.setdefault(t, {})
                for label,key in mapping.items():
                    val = number(row[columns[label]], german=True)
                    if key == 'nuclear' and val is None and t.astimezone(BERLIN).date() >= datetime(2023,4,16).date():
                        val = 0.0
                    assert val is not None and np.isfinite(val), (t,key)
                    assert key not in dest, 'Duplicate energy source hour'
                    dest[key] = val
    with CAPACITY.open() as f:
        capacity = {r['reference_date_exclusive']:r for r in csv.DictReader(f)}
    times = pd.date_range('2026-09-24','2026-09-26T23:00',freq='h',tz='UTC')
    records = []
    for stamp in times:
        t = stamp.to_pydatetime(); local = t.astimezone(BERLIN); lag = t-timedelta(hours=168)
        ref = str(capacity_reference(t)); c = capacity[ref]
        row = dict(target_time_utc=t.isoformat(),target_time_berlin=local.isoformat(),
                   energy_lag_time_utc=lag.isoformat(),capacity_reference_date=ref,
                   hour_local=local.hour,weekday=local.weekday(),month=local.month,
                   is_national_holiday=int(local.date() in holidays(local.year)),
                   daylight_hours_approx=daylight(local.date()))
        for station, table in weather.items():
            w = table[t.strftime('%Y-%m-%dT%H:%M')]
            for original, feature in WEATHER.items():
                row[station+'__'+feature] = w[original.split(' (')[0]]
            row[station+'__sunshine_duration_preceding_hour_s'] = w['sunshine_duration']
        for tech in ['pv','wind_onshore','wind_offshore']:
            row[tech+'_net_mw_reconstructed'] = float(c[tech+'_net_mw'])
        for key,val in energy[lag].items():
            row[key+'_mwh_lag168h'] = val
        records.append(row)
    frame = pd.DataFrame(records)
    results = frame[['target_time_utc','target_time_berlin']].copy()
    run = json.loads((MODEL/'run.json').read_text())
    features = run['features']
    assert len(features) == 136 and len(frame) == 72
    x = frame[features].to_numpy(float)
    assert np.isfinite(x).all()
    model_hashes = {}
    for target in ['target_co2_gco2eq_kwh','target_renewable_share_pct']:
        p = MODEL/('hist_gradient_boosting_'+target+'.joblib')
        model_hashes[str(p.relative_to(ROOT))] = sha(p)
        expected = next(r['model_sha256'] for r in run['models'] if r['target']==target)
        assert sha(p) == expected
        bundle = joblib.load(p)
        assert bundle['features'] == features
        assert pd.Timestamp(bundle['training_end']) < times[0]
        with threadpool_limits(limits=1):
            pred = bundle['pipeline'].predict(x)
        assert pred.shape == (72,) and np.isfinite(pred).all()
        results['predicted_'+target.removeprefix('target_')] = pred
    OUT.mkdir()
    frame[['target_time_utc','target_time_berlin','energy_lag_time_utc','capacity_reference_date']+features].to_csv(OUT/'inputs.csv',index=False)
    results.to_csv(OUT/'predictions.csv',index=False)
    report = dict(status='complete',created_utc=datetime.now(timezone.utc).isoformat(),hours=72,
        feature_count=len(features),training_end=run['training_end'],model_hashes=model_hashes,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},script_sha256=sha(Path(__file__)),
        retrospective_era5=True,targets_read=False,refit=False,clipping=False,
        limitations=['Actual historical weather; not an as-issued forecast',
                     'Revised SMARD snapshot and reconstructed MaStR capacity proxy'],
        summary={c:dict(min=float(results[c].min()),max=float(results[c].max()),mean=float(results[c].mean())) for c in results.columns if c.startswith('predicted_')})
    for rel,digest in model_hashes.items(): assert sha(ROOT/rel)==digest
    (OUT/'run.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['summary'],indent=2))
    print(OUT)


if __name__ == '__main__':
    main()
