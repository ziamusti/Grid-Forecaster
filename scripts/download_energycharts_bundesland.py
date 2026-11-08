"""Download per-Bundesland hourly generation data from energy-charts.info; no training.

Weekly JSON files, each containing one series per (technology, Bundesland)
pair, e.g. id 'biomass_by' = Biomasse in Bayern. Source per file metadata:
ENTSO-E, Laenderarbeitskreis Energiebilanzen, Foederal Erneuerbar, ERA5,
MaStR (a Fraunhofer ISE estimate, not a direct measurement - there is no
metering infrastructure that measures generation per Bundesland).
"""
import argparse
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.energy-charts.info/charts/power/data/de_bl'
OUT = ROOT / 'data/raw/energycharts_bundesland'


def iso_weeks_in_year(year):
    return date(year, 12, 28).isocalendar()[1]


def fetch(url, timeout=60):
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=timeout) as response:
                return response.read()
        except HTTPError as error:
            if error.code == 404:
                return None
            if attempt == 3:
                raise
            time.sleep(min(2 ** (attempt + 1), 15))
        except (URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(min(2 ** (attempt + 1), 15))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start-year', type=int, default=2015)
    parser.add_argument('--end-year', type=int, default=datetime.now(timezone.utc).year)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    current_year, current_week = now.isocalendar()[0], now.isocalendar()[1]

    fetched, missing, failed = 0, 0, []
    for year in range(args.start_year, args.end_year + 1):
        year_dir = OUT / str(year)
        year_dir.mkdir(exist_ok=True)
        max_week = iso_weeks_in_year(year)
        if year == current_year:
            max_week = min(max_week, current_week)
        for week in range(1, max_week + 1):
            dest = year_dir / f'week_{year}_{week:02d}.json'
            if dest.exists():
                continue
            url = f'{BASE}/week_{year}_{week:02d}.json'
            try:
                body = fetch(url)
            except Exception as error:
                failed.append((year, week, str(error)))
                continue
            if body is None:
                missing += 1
                continue
            dest.write_bytes(body)
            fetched += 1
            time.sleep(0.2)
        print(year, 'done', flush=True)

    manifest = dict(retrieved_at_utc=now.isoformat(), endpoint=BASE,
                    start_year=args.start_year, end_year=args.end_year,
                    fetched=fetched, missing_404=missing, failed=failed,
                    license_note='Fraunhofer ISE energy-charts.info; per-Bundesland generation is a model estimate (ENTSO-E, Laenderarbeitskreis Energiebilanzen, Foederal Erneuerbar, ERA5, MaStR), not a direct measurement')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('fetched:', fetched, 'missing_404:', missing, 'failed:', len(failed))
    print(OUT)


if __name__ == '__main__':
    main()
