"""Fill the Day-ahead price gap after the last bulk download; no training."""
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://api.energy-charts.info/v2/price'


def main():
    start = date(2026, 10, 27)
    end = date(2026, 11, 8)  # exclusive-ish upper bound; only what is actually returned is used
    now = datetime.now(timezone.utc)
    out_dir = ROOT / 'data/raw/energycharts_price_gap' / now.strftime('%Y%m%dT%H%M%SZ')
    out_dir.mkdir(parents=True)
    params = urlencode(dict(bzn='DE-LU', start=start.isoformat(), end=end.isoformat()))
    url = BASE + '?' + params
    path = out_dir / f'DE-LU_{start.isoformat()}_{end.isoformat()}.json'
    for attempt in range(6):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=60) as response:
                body = response.read()
            break
        except HTTPError as error:
            if error.code == 429:
                time.sleep(int(error.headers.get('Retry-After', '10')) + 1)
                continue
            raise SystemExit(f'Abruf gestoppt: HTTP {error.code}')
        except (URLError, TimeoutError):
            time.sleep(10)
    else:
        raise SystemExit('Abruf nach Wiederholungen gestoppt.')
    data = json.loads(body)
    path.write_bytes(body)
    manifest = dict(endpoint=BASE, retrieved_at_utc=now.isoformat(), start=start.isoformat(), end=end.isoformat(),
                    rows=len(data['data']), resolution=data['resolution'], license=data.get('license'), file=path.name)
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(out_dir)


if __name__ == '__main__':
    main()
