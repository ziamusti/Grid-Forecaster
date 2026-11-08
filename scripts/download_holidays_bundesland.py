"""Download German public holidays per Bundesland (2015-2026); no training.

Source: Nager.Date public holidays API (date.nager.at), free, no key. Each
holiday entry marks whether it is nationwide ("global": true) or lists the
specific DE-XX subdivision codes it applies to ("counties"). These codes
match the lowercase suffixes already used in scripts/bundesland.py.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/raw/holidays_bundesland'
URL = 'https://date.nager.at/api/v3/PublicHolidays/{year}/DE'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    manifest = dict(retrieved_at_utc=now.isoformat(), endpoint=URL, years=[])
    for year in range(2015, 2027):
        dest = OUT / f'{year}.json'
        if not dest.exists():
            with urlopen(Request(URL.format(year=year), headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=30) as response:
                body = response.read()
            dest.write_bytes(body)
            time.sleep(0.3)
        data = json.loads(dest.read_text())
        manifest['years'].append(dict(year=year, count=len(data)))
        print(year, len(data), 'Feiertage', flush=True)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(OUT)


if __name__ == '__main__':
    main()
