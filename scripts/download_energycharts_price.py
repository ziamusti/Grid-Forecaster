"""Download unchanged Day-ahead spot price (Energy-Charts API) for DE; no training.

Zone switches from DE-AT-LU to DE-LU on 2018-10-01 (Austria decoupling); both
pulled unchanged as reported by the API, no own re-labelling of earlier data.
"""
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://api.energy-charts.info/v2/price'
SWITCH = date(2018, 10, 1)
START = date(2015, 1, 1)
END = date(2026, 10, 27)  # today (exclusive handling below): last full day requested separately


def zone_for(year):
    return 'DE-AT-LU' if year < SWITCH.year or (year == SWITCH.year) else 'DE-LU'


def fetch(zone, start, end, out_dir):
    params = urlencode(dict(bzn=zone, start=start.isoformat(), end=end.isoformat()))
    url = BASE + '?' + params
    path = out_dir / f'{zone}_{start.isoformat()}_{end.isoformat()}.json'
    if path.exists():
        return path, json.loads(path.read_bytes())
    for attempt in range(8):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=60) as response:
                body = response.read()
            data = json.loads(body)
            path.write_bytes(body)
            return path, data
        except HTTPError as error:
            if error.code == 429:
                wait = int(error.headers.get('Retry-After', '10'))
                print(f'  429, warte {wait}s', flush=True)
                time.sleep(wait + 1)
                continue
            if error.code == 404:
                print(f'  404 (keine Daten) fuer {zone} {start}..{end}', flush=True)
                return None, None
            raise SystemExit(f'Abruf gestoppt: HTTP {error.code} fuer {url}')
        except (URLError, TimeoutError):
            time.sleep(10)
    raise SystemExit('Abruf nach Wiederholungen gestoppt.')


def main():
    now = datetime.now(timezone.utc)
    out_dir = ROOT / 'data/raw/energycharts_price' / now.strftime('%Y%m%dT%H%M%SZ')
    out_dir.mkdir(parents=True)
    manifest = dict(endpoint=BASE, retrieved_at_utc=now.isoformat(), start=START.isoformat(),
                     end=END.isoformat(), switch_date=SWITCH.isoformat(), files=[])
    cursor = START
    while cursor <= END:
        year_end = date(cursor.year, 12, 31)
        chunk_end = min(year_end, END)
        zone = zone_for(cursor.year)
        print(cursor, '..', chunk_end, zone, flush=True)
        path, data = fetch(zone, cursor, chunk_end, out_dir)
        if path is not None:
            manifest['files'].append(dict(file=path.name, zone=zone, start=cursor.isoformat(),
                end=chunk_end.isoformat(), rows=len(data['data']), resolution=data['resolution'],
                license=data.get('license')))
        (out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        cursor = date(cursor.year + 1, 1, 1)
        time.sleep(31)  # /price allows 2 req/min; stay safely under that
    print(out_dir, flush=True)


if __name__ == '__main__':
    main()
