"""Evaluate frozen predictions against provider observations; no fitting."""
import csv
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from prepare_stage0 import TECH, number, renewables
from download_smard_prediction_inputs import URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/hist_comparison_20260927_v1'
PRED = ROOT / 'reports/hist_prediction_20260927_29_v1/predictions.csv'
CO2 = ROOT / 'data/raw/electricitymaps/full_DE_20261020T2100Z/20260919T23.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError('Comparison already exists; no overwrite')
    start = datetime(2026, 9, 27, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    pred_hash = sha(PRED)
    frame = pd.read_csv(PRED)
    frame['time_utc'] = pd.to_datetime(frame.target_time_utc, utc=True)
    frame = frame.loc[(frame.time_utc >= start) & (frame.time_utc < end)].copy()
    expected = pd.date_range(start, periods=24, freq='h')
    assert list(frame.time_utc) == list(expected)
    payload = {'request_form': [dict(
        moduleIds=[1004066, 1001226, 1001225, 1004067, 1004068, 1001228,
                   1001224, 1001223, 1004069, 1004071, 1004070, 1001227],
        region='DE', resolution='hour', format='CSV', type='discrete', language='de',
        timestamp_from=int(start.timestamp()*1000), timestamp_to=int(end.timestamp()*1000))]}
    request = Request(URL, data=json.dumps(payload).encode(), method='POST',
                      headers={'Content-Type': 'application/json', 'User-Agent': 'Grid-Forecaster/1.0'})
    with urlopen(request, timeout=180) as response:
        body = response.read()
    now = datetime.now(timezone.utc)
    raw = ROOT / 'data/raw/smard_comparison_20260927' / now.strftime('%Y%m%dT%H%M%SZ')
    raw.mkdir(parents=True, exist_ok=False)
    (raw/'generation.csv').write_bytes(body)
    raw_manifest = dict(endpoint=URL, request=payload, retrieved_at_utc=now.isoformat(),
                        sha256=sha(raw/'generation.csv'))
    (raw/'manifest.json').write_text(json.dumps(raw_manifest, indent=2))
    reader = csv.DictReader(io.StringIO(body.decode('utf-8-sig')), delimiter=';')
    columns = {k: next(c for c in reader.fieldnames if c.startswith(k+' [MWh]')) for k in TECH}
    generation = {}
    nuclear_zeros = 0
    for row in reader:
        t = datetime.strptime(row['Datum von'], '%d.%m.%Y %H:%M').replace(
            tzinfo=ZoneInfo('Europe/Berlin')).astimezone(timezone.utc)
        if not start <= t < end:
            continue
        assert t not in generation
        vals = {tech: number(row[columns[label]], german=True) for label, tech in TECH.items()}
        if vals['nuclear'] is None:
            vals['nuclear'] = 0.0  # Existing post-2023 German nuclear phase-out rule.
            nuclear_zeros += 1
        value = renewables(vals)
        assert value is not None and np.isfinite(value) and 0 <= value <= 100
        generation[t] = value
    co2 = {}
    for row in json.loads(CO2.read_text())['data']:
        t = pd.Timestamp(row['datetime'])
        if start <= t < end:
            assert t not in co2
            assert row['zone'] == 'DE' and row['flowTraced'] is False
            assert row['emissionFactorType'] == 'lifecycle'
            assert row['isEstimated'] is False
            assert row['carbonIntensity'] is not None and np.isfinite(row['carbonIntensity'])
            co2[t] = row['carbonIntensity']
    assert set(generation) == set(co2) == set(expected)
    frame['actual_co2_gco2eq_kwh'] = frame.time_utc.map(co2)
    frame['actual_renewable_share_pct'] = frame.time_utc.map(generation)
    metrics = {}
    for target in ['co2_gco2eq_kwh', 'renewable_share_pct']:
        diff = frame['predicted_'+target] - frame['actual_'+target]
        frame['error_'+target] = diff
        metrics[target] = dict(mae=float(diff.abs().mean()), rmse=float(np.sqrt((diff**2).mean())),
            bias=float(diff.mean()), predicted_mean=float(frame['predicted_'+target].mean()),
            actual_mean=float(frame['actual_'+target].mean()))
    assert sha(PRED) == pred_hash
    OUT.mkdir()
    frame.drop(columns='time_utc').to_csv(OUT/'comparison.csv', index=False)
    manifest = dict(hours=24, start_utc=start.isoformat(), end_exclusive_utc=end.isoformat(),
        error_definition='prediction minus provider actual', metrics=metrics, nuclear_zero_hours=nuclear_zeros,
        estimated_co2_hours=0, retrospective_era5=True, refit=False,
        sources={str(p.relative_to(ROOT)): sha(p) for p in [PRED, CO2, CO2.parent/'manifest.json',
                  raw/'generation.csv', raw/'manifest.json']}, script_sha256=sha(Path(__file__)))
    (OUT/'run.json').write_text(json.dumps(manifest, indent=2))
    print(frame.to_string(index=False))
    print(json.dumps(metrics, indent=2))
    print(OUT)


if __name__ == '__main__':
    main()
