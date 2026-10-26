"""Fetch real provider actuals (CO2, renewable share) for 2026-09-30..2026-10-02; no model involved."""
import csv
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from prepare_stage0 import TECH, number, renewables
from download_smard_prediction_inputs import URL as SMARD_URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/actuals_20260930_02_v1'
UTC = timezone.utc
BERLIN = ZoneInfo('Europe/Berlin')


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def fetch_smard(start, end):
    modules = [1004066, 1001226, 1001225, 1004067, 1004068, 1001228,
               1001224, 1001223, 1004069, 1004071, 1004070, 1001227]
    payload = {'request_form': [dict(moduleIds=modules, region='DE', resolution='hour',
                format='CSV', timestamp_from=int(start.timestamp()*1000),
                timestamp_to=int(end.timestamp()*1000), type='discrete', language='de')]}
    request = Request(SMARD_URL, data=json.dumps(payload).encode(), method='POST',
                      headers={'Content-Type': 'application/json', 'User-Agent': 'Grid-Forecaster/1.0'})
    with urlopen(request, timeout=180) as response:
        body = response.read()
    reader = csv.DictReader(io.StringIO(body.decode('utf-8-sig')), delimiter=';')
    columns = {k: next(c for c in reader.fieldnames if c.startswith(k + ' [MWh]')) for k in TECH}
    generation = {}
    nuclear_zeros = 0
    for row in reader:
        t = datetime.strptime(row['Datum von'], '%d.%m.%Y %H:%M').replace(tzinfo=BERLIN).astimezone(UTC)
        if not start <= t < end:
            continue
        assert t not in generation
        vals = {tech: number(row[columns[label]], german=True) for label, tech in TECH.items()}
        if vals['nuclear'] is None:
            vals['nuclear'] = 0.0
            nuclear_zeros += 1
        value = renewables(vals)
        assert value is not None and 0 <= value <= 100
        generation[t] = value
    return generation, body, payload, nuclear_zeros


def fetch_co2(start, end):
    values = {}
    for line in (ROOT / '.env').read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep:
            values[key.strip()] = value.strip().strip('"\'')
    token = values.get('ELECTRICITY_MAPS_API_KEY', '')
    if not token:
        raise SystemExit('API-Key fehlt')
    fmt = lambda dt: dt.isoformat().replace('+00:00', 'Z')
    params = dict(zone='DE', temporalGranularity='hourly', flowTraced='false',
                  emissionFactorType='lifecycle', start=fmt(start), end=fmt(end))
    url = 'https://api.electricitymaps.com/v4/carbon-intensity/past-range?' + urlencode(params)
    with urlopen(Request(url, headers={'auth-token': token}), timeout=60) as response:
        body = response.read().replace(token.encode(), b'[REDACTED]')
    data = json.loads(body)
    co2 = {}
    estimated = 0
    for row in data['data']:
        t = datetime.fromisoformat(row['datetime'].replace('Z', '+00:00'))
        if start <= t < end:
            assert t not in co2
            assert row['zone'] == 'DE' and row['flowTraced'] is False
            assert row['emissionFactorType'] == 'lifecycle'
            if row['isEstimated']:
                estimated += 1
            assert row['carbonIntensity'] is not None
            co2[t] = row['carbonIntensity']
    return co2, body, estimated


def main():
    if OUT.exists():
        raise FileExistsError('Actuals already fetched; no overwrite')
    start = datetime(2026, 9, 30, tzinfo=UTC)
    end = start + timedelta(hours=72)
    expected = [start + timedelta(hours=i) for i in range(72)]

    generation, smard_body, smard_payload, nuclear_zeros = fetch_smard(start, end)
    co2, co2_body, estimated = fetch_co2(start, end)

    missing_smard = [t for t in expected if t not in generation]
    missing_co2 = [t for t in expected if t not in co2]

    OUT.mkdir(parents=True)
    now = datetime.now(UTC)
    raw_smard = ROOT / 'data/raw/smard_actuals_20260930_02' / now.strftime('%Y%m%dT%H%M%SZ')
    raw_smard.mkdir(parents=True)
    (raw_smard / 'generation.csv').write_bytes(smard_body)
    raw_co2 = ROOT / 'data/raw/electricitymaps_actuals_20260930_02' / now.strftime('%Y%m%dT%H%M%SZ')
    raw_co2.mkdir(parents=True)
    (raw_co2 / 'carbon_intensity.json').write_bytes(co2_body)

    rows = []
    for t in expected:
        rows.append(dict(target_time_utc=t.isoformat(),
                          target_time_berlin=t.astimezone(BERLIN).isoformat(),
                          actual_co2_gco2eq_kwh=co2.get(t),
                          actual_renewable_share_pct=generation.get(t)))
    with (OUT / 'actuals.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    manifest = dict(hours=72, start_utc=start.isoformat(), end_exclusive_utc=end.isoformat(),
        nuclear_zero_hours=nuclear_zeros, co2_estimated_hours=estimated,
        missing_smard_hours=[t.isoformat() for t in missing_smard],
        missing_co2_hours=[t.isoformat() for t in missing_co2],
        sources=dict(smard_sha256=sha(smard_body), co2_sha256=sha(co2_body),
                     smard_payload=smard_payload, smard_raw=str(raw_smard.relative_to(ROOT)),
                     co2_raw=str(raw_co2.relative_to(ROOT))),
        script_sha256=sha(Path(__file__).read_bytes()))
    (OUT / 'run.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(OUT)


if __name__ == '__main__':
    main()
