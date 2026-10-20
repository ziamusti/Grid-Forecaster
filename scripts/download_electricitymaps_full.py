"""Download unchanged hourly DE production/lifecycle responses; no training."""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def main():
    values = {}
    for line in (ROOT / '.env').read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep:
            values[key.strip()] = value.strip().strip('\"\'')
    token = values.get('ELECTRICITY_MAPS_API_KEY', '')
    if not token:
        raise SystemExit('API-Key fehlt')
    now = datetime.now(UTC)
    start = datetime(2015, 1, 1, tzinfo=ZoneInfo('Europe/Berlin')).astimezone(UTC)
    end = now.replace(minute=0, second=0, microsecond=0)
    output = ROOT / 'data/raw/electricitymaps' / ('full_DE_' + end.strftime('%Y%m%dT%H%MZ'))
    output.mkdir(parents=True, exist_ok=True)
    print('Ordner:', output, flush=True)
    records = {}
    duplicates = 0
    requests = []
    cursor = start
    while cursor < end:
        stop = min(cursor + timedelta(days=10), end)
        fmt = lambda dt: dt.isoformat().replace('+00:00', 'Z')
        params = dict(zone='DE', temporalGranularity='hourly', flowTraced='false',
                      emissionFactorType='lifecycle', start=fmt(cursor), end=fmt(stop))
        url = 'https://api.electricitymaps.com/v4/carbon-intensity/past-range?' + urlencode(params)
        path = output / (cursor.strftime('%Y%m%dT%H') + '.json')
        if path.exists():
            body = path.read_bytes()
        else:
            for attempt in range(6):
                try:
                    with urlopen(Request(url, headers={'auth-token': token}), timeout=45) as response:
                        body = response.read().replace(token.encode(), b'[REDACTED]')
                    break
                except HTTPError as error:
                    if error.code == 429 or error.code >= 500:
                        time.sleep(min(2 ** (attempt + 1), 30))
                        continue
                    raise SystemExit('Abruf gestoppt: HTTP ' + str(error.code))
                except (URLError, TimeoutError):
                    time.sleep(min(2 ** (attempt + 1), 30))
            else:
                raise SystemExit('Abruf nach Wiederholungen gestoppt; gespeicherte Blöcke bleiben erhalten.')
            json.loads(body)
            path.write_bytes(body)
        data = json.loads(body)
        rows = data.get('data', [])
        for row in rows:
            stamp = datetime.fromisoformat(row['datetime'].replace('Z', '+00:00'))
            if stamp in records:
                duplicates += 1
            records[stamp] = row
        requests.append(dict(file=path.name, url=url, rows=len(rows)))
        cursor = stop
        if len(requests) % 20 == 0 or cursor == end:
            print('Bloecke:', len(requests), 'bis:', fmt(cursor), 'Stunden:', len(records), flush=True)
    expected = set()
    cursor = start
    while cursor < end:
        expected.add(cursor)
        cursor += timedelta(hours=1)
    missing = sorted(expected - records.keys())
    summary = dict(zone='DE', basis='production', emissionFactorType='lifecycle',
                   unit='gCO2eq/kWh', start_utc=start.isoformat(), end_exclusive_utc=end.isoformat(),
                   retrieved_at_utc=now.isoformat(), expected_hours=len(expected),
                   unique_hours=len(records), missing_hours=[x.isoformat() for x in missing],
                   duplicate_hours=duplicates,
                   null_values=sum(r.get('carbonIntensity') is None for r in records.values()),
                   estimated_hours=sum(r.get('isEstimated') is True for r in records.values()),
                   outside_requested_range=sum(t not in expected for t in records), requests=requests)
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != 'requests'}), flush=True)


if __name__ == '__main__':
    main()
