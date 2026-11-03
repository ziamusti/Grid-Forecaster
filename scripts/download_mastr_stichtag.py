"""Download the official MaStR Stichtag (fixed-date) full export ZIP; no training.

The download page (https://www.marktstammdatenregister.de/MaStR/Datendownload)
is plain HTML with direct anchor links, no login/JS/captcha needed. Monthly
Stichtag exports (1st of each month) match our monthly capacity granularity,
so this is preferred over the >3GB daily export.
"""
import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PAGE_URL = 'https://www.marktstammdatenregister.de/MaStR/Datendownload'
STICHTAG_PATTERN = re.compile(
    r'https://download\.marktstammdatenregister\.de/Stichtag/Gesamtdatenexport_(\d{8})_([\d.]+)\.zip')


def fetch(url, timeout=120):
    # .read() on the whole (multi-GB) body can overflow on some system
    # Python/LibreSSL builds; read in bounded chunks instead.
    for attempt in range(6):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=timeout) as response:
                chunks = []
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return b''.join(chunks)
        except (HTTPError, URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(min(2 ** (attempt + 1), 30))


def fetch_to_file(url, path, timeout=1800):
    for attempt in range(6):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=timeout) as response, \
                 path.open('wb') as out:
                h = hashlib.sha256()
                total = 0
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
                    h.update(chunk)
                    total += len(chunk)
                return total, h.hexdigest()
        except (HTTPError, URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(min(2 ** (attempt + 1), 30))


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--on-or-before', default=None,
                        help='Pick the latest Stichtag on/before this date (YYYY-MM-DD); default: today')
    args = parser.parse_args()
    cutoff = date.fromisoformat(args.on_or_before) if args.on_or_before else datetime.now(timezone.utc).date()

    page = fetch(PAGE_URL).decode('utf-8', errors='replace')
    candidates = []
    for match in STICHTAG_PATTERN.finditer(page):
        stamp, version = match.group(1), match.group(2)
        d = date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8]))
        if d <= cutoff:
            candidates.append((d, version, match.group(0)))
    if not candidates:
        raise SystemExit('Kein Stichtag-Export auf der Seite gefunden (Seitenstruktur evtl. geaendert).')
    chosen_date, chosen_version, url = max(candidates, key=lambda c: c[0])

    out_dir = ROOT / 'data/raw/mastr_stichtag' / chosen_date.isoformat()
    out_dir.mkdir(parents=True, exist_ok=False)
    print('Lade', url, flush=True)
    path = out_dir / f'Gesamtdatenexport_{chosen_date:%Y%m%d}_{chosen_version}.zip'
    total, digest = fetch_to_file(url, path)
    manifest = dict(source_page=PAGE_URL, url=url, stichtag=chosen_date.isoformat(), version=chosen_version,
                    retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                    bytes=total, sha256=digest, file=path.name)
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(out_dir)


if __name__ == '__main__':
    main()
