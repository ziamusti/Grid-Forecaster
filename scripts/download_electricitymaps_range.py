"""Download fresh Electricity Maps CO2 raw data for an arbitrary continuous date range; no training."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='UTC start day (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='UTC end day inclusive (YYYY-MM-DD)')
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    last = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=UTC)
    end = last + timedelta(days=1)
    hours = int((end - start).total_seconds() / 3600)
    values = {}
    for line in (ROOT / '.env').read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep:
            values[key.strip()] = value.strip().strip('"\'')
    token = values.get('ELECTRICITY_MAPS_API_KEY', '')
    if not token:
        raise SystemExit('API-Key fehlt')
    now = datetime.now(UTC)
    output = ROOT / 'data/raw/electricitymaps_range' / now.strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True)
    fmt = lambda dt: dt.isoformat().replace('+00:00', 'Z')
    records = {}
    cursor = start
    requests = []
    while cursor < end:
        stop = min(cursor + timedelta(days=10), end)
        params = dict(zone='DE', temporalGranularity='hourly', flowTraced='false',
                      emissionFactorType='lifecycle', start=fmt(cursor), end=fmt(stop))
        url = 'https://api.electricitymaps.com/v4/carbon-intensity/past-range?' + urlencode(params)
        for attempt in range(6):
            try:
                with urlopen(Request(url, headers={'auth-token': token}), timeout=60) as response:
                    body = response.read().replace(token.encode(), b'[REDACTED]')
                break
            except HTTPError as error:
                if error.code == 429 or error.code >= 500:
                    time.sleep(min(2 ** (attempt+1), 30)); continue
                raise SystemExit('Abruf gestoppt: HTTP ' + str(error.code))
            except (URLError, TimeoutError):
                time.sleep(min(2 ** (attempt+1), 30))
        else:
            raise SystemExit('Abruf nach Wiederholungen gestoppt.')
        path = output / (cursor.strftime('%Y%m%dT%H') + '.json')
        path.write_bytes(body)
        data = json.loads(body)
        for row in data['data']:
            stamp = datetime.fromisoformat(row['datetime'].replace('Z', '+00:00'))
            assert row['zone'] == 'DE' and row['flowTraced'] is False and row['emissionFactorType'] == 'lifecycle'
            if start <= stamp < end:
                records[stamp] = row
        requests.append(dict(file=path.name, url=url, rows=len(data['data'])))
        cursor = stop
        print('bis', fmt(cursor), 'Stunden bisher:', len(records), flush=True)
    expected = {start + timedelta(hours=i) for i in range(hours)}
    missing = sorted(expected - records.keys())
    manifest = dict(zone='DE', basis='production', emissionFactorType='lifecycle', unit='gCO2eq/kWh',
                    start_utc=start.isoformat(), end_exclusive_utc=end.isoformat(),
                    retrieved_at_utc=now.isoformat(), expected_hours=hours, unique_hours=len(records),
                    missing_hours=[t.isoformat() for t in missing],
                    null_values=sum(r.get('carbonIntensity') is None for r in records.values()),
                    estimated_hours=sum(r.get('isEstimated') is True for r in records.values()),
                    requests=requests)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps({k: v for k, v in manifest.items() if k != 'requests'}, indent=2), flush=True)
    print(output, flush=True)


if __name__ == '__main__':
    main()
