"""Fresh SMARD raw download for an arbitrary continuous UTC hour range."""
import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from prepare_stage0 import local_to_utc

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.smard.de/nip-download-manager/nip/download/market-data'
UTC = timezone.utc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='UTC start (YYYY-MM-DD)')
    parser.add_argument('--end-exclusive', required=True, help='UTC end exclusive (YYYY-MM-DD)')
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    end = datetime.strptime(args.end_exclusive, '%Y-%m-%d').replace(tzinfo=UTC)
    hours = int((end - start).total_seconds() / 3600)
    now = datetime.now(UTC)
    output = ROOT / 'data/raw/smard_range' / now.strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True, exist_ok=False)
    datasets = {
        'generation': [1004066, 1001226, 1001225, 1004067, 1004068, 1001228,
                       1001224, 1001223, 1004069, 1004071, 1004070, 1001227],
        'load': [5000410, 5005140, 5004387, 5004359],
    }
    manifest = dict(retrieved_at_utc=now.isoformat(), endpoint=URL,
                    start_utc=start.isoformat(), end_exclusive_utc=end.isoformat(),
                    note='Fresh revised snapshot, not historical publication state', files=[])
    for name, modules in datasets.items():
        payload = {'request_form': [dict(moduleIds=modules, region='DE', resolution='hour',
                    format='CSV', timestamp_from=int(start.timestamp()*1000),
                    timestamp_to=int(end.timestamp()*1000), type='discrete', language='de')]}
        request = Request(URL, data=json.dumps(payload).encode(), method='POST',
                          headers={'Content-Type': 'application/json', 'User-Agent': 'Grid-Forecaster/1.0'})
        with urlopen(request, timeout=300) as response:
            body = response.read()
        path = output / (name + '.csv')
        path.write_bytes(body)
        rows = list(csv.DictReader(io.StringIO(body.decode('utf-8-sig')), delimiter=';'))
        occurrences = defaultdict(int)
        selected = []
        for row in rows:
            stamp = local_to_utc(row['Datum von'], occurrences)
            if start <= stamp < end:
                selected.append((stamp, row))
        columns = [c for c in rows[0] if '[MWh]' in c]
        if name == 'load':
            columns = [c for c in columns if c.startswith('Netzlast [MWh]')]
        missing = {c: sum(r[c].strip() in ('', '-') for _, r in selected) for c in columns}
        stamps = [t for t, _ in selected]
        assert len(stamps) == len(set(stamps)) == hours, (name, len(stamps), hours)
        assert len(columns) == (12 if name == 'generation' else 1), columns
        manifest['files'].append(dict(file=path.name, sha256=hashlib.sha256(body).hexdigest(),
            request=payload, returned_rows=len(rows), selected_hours=len(selected),
            first_utc=min(stamps).isoformat(), last_utc=max(stamps).isoformat(), missing=missing))
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(name, hours, 'hours checked, missing:', missing, flush=True)
    print(output, flush=True)


if __name__ == '__main__':
    main()
