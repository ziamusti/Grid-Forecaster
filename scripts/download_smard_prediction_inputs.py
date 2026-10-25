"""Fresh SMARD raw download for a 72h prediction block's 168h lags."""
import argparse
import csv
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.smard.de/nip-download-manager/nip/download/market-data'
UTC = timezone.utc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-start', default='2026-09-24', help='First prediction day, UTC (YYYY-MM-DD)')
    args = parser.parse_args()
    target_start = datetime.strptime(args.target_start, '%Y-%m-%d').replace(tzinfo=UTC)
    now = datetime.now(UTC)
    output = ROOT / 'data/raw/smard_prediction_inputs' / now.strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True, exist_ok=False)
    start = target_start - timedelta(hours=168)
    end = start + timedelta(hours=72)
    datasets = {
        'generation': [1004066, 1001226, 1001225, 1004067, 1004068, 1001228,
                       1001224, 1001223, 1004069, 1004071, 1004070, 1001227],
        'load': [5000410, 5005140, 5004387, 5004359],
    }
    manifest = dict(retrieved_at_utc=now.isoformat(), endpoint=URL,
                    target_start_utc=target_start.isoformat(),
                    target_end_exclusive_utc=(target_start + timedelta(hours=72)).isoformat(),
                    start_utc=start.isoformat(), end_exclusive_utc=end.isoformat(),
                    note='Fresh revised snapshot, not historical publication state', files=[])
    for name, modules in datasets.items():
        payload = {'request_form': [dict(moduleIds=modules, region='DE', resolution='hour',
                    format='CSV', timestamp_from=int(start.timestamp()*1000),
                    timestamp_to=int(end.timestamp()*1000), type='discrete', language='de')]}
        request = Request(URL, data=json.dumps(payload).encode(), method='POST',
                          headers={'Content-Type': 'application/json', 'User-Agent': 'Grid-Forecaster/1.0'})
        with urlopen(request, timeout=180) as response:
            body = response.read()
        path = output / (name + '.csv')
        path.write_bytes(body)
        rows = list(csv.DictReader(io.StringIO(body.decode('utf-8-sig')), delimiter=';'))
        selected = []
        for row in rows:
            stamp = datetime.strptime(row['Datum von'], '%d.%m.%Y %H:%M').replace(
                tzinfo=ZoneInfo('Europe/Berlin')).astimezone(UTC)
            if start <= stamp < end:
                selected.append((stamp, row))
        columns = [c for c in rows[0] if '[MWh]' in c]
        if name == 'load':
            columns = [c for c in columns if c.startswith('Netzlast [MWh]')]
        missing = {c: sum(r[c].strip() in ('', '-') for _, r in selected) for c in columns}
        stamps = [t for t, _ in selected]
        assert len(stamps) == len(set(stamps)) == 72, (name, len(stamps))
        assert len(columns) == (12 if name == 'generation' else 1), columns
        manifest['files'].append(dict(file=path.name, sha256=hashlib.sha256(body).hexdigest(),
            request=payload, returned_rows=len(rows), selected_hours=len(selected),
            first_utc=min(stamps).isoformat(), last_utc=max(stamps).isoformat(), missing=missing))
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(name, '72 hours checked', missing, flush=True)
    print(output, flush=True)


if __name__ == '__main__':
    main()
