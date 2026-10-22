"""Read-only verification of prepared Stage-0 tables and source hashes."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    folder = args.directory
    schema = json.loads((folder / 'feature_schema.json').read_text())
    features = schema['features']
    assert not set(features).intersection(schema['targets'] + schema['metadata_not_features'])
    assert len(features) == len(set(features)) == 114
    assert (folder / 'COMPLETE.json').exists()
    manifest = json.loads((folder / 'source_manifest.json').read_text())
    for entry in manifest:
        assert '/raw/' in entry['path'], entry['path']
        path = ROOT / entry['path']
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        assert h.hexdigest() == entry['sha256'], entry['path']
    counts = Counter()
    previous = None
    co2_history, renewable_history = {}, {}
    quality = json.loads((folder / 'quality_report.json').read_text())
    for path in sorted(folder.glob('hourly_*.csv')):
        year_counts = Counter()
        year = int(path.stem.split('_')[1])
        with path.open() as f:
            reader = csv.DictReader(f)
            assert set(reader.fieldnames) == set(features + schema['targets'] + schema['metadata_not_features'])
            for row in reader:
                t = datetime.fromisoformat(row['target_time_utc'].replace('Z', '+00:00'))
                lag = datetime.fromisoformat(row['energy_lag_time_utc'].replace('Z', '+00:00'))
                assert t.year == year
                assert t - lag == timedelta(hours=168)
                if previous is not None:
                    assert t - previous == timedelta(hours=1)
                previous = t
                earliest_origin = (t - timedelta(hours=72)).astimezone(ZoneInfo('Europe/Berlin'))
                assert date.fromisoformat(row['capacity_reference_date']) == date(earliest_origin.year, earliest_origin.month, 1)
                complete = all(row[k] != '' for k in features)
                assert int(row['features_complete']) == int(complete)
                assert int(row['eligible_co2_nonestimated']) == int(complete and row['target_co2_gco2eq_kwh'] != '' and row['co2_is_estimated'] == '0')
                assert int(row['eligible_renewable']) == int(complete and row['target_renewable_share_pct'] != '')
                assert int(row['eligible_both']) == int(row['eligible_co2_nonestimated'] == '1' and row['eligible_renewable'] == '1')
                if row['target_renewable_share_pct']:
                    assert 0 <= float(row['target_renewable_share_pct']) <= 100
                if lag in co2_history:
                    assert row['co2_lag168h_baseline_only'] == co2_history[lag]
                    assert row['renewable_share_lag168h_baseline_only'] == renewable_history[lag]
                co2_history[t] = row['target_co2_gco2eq_kwh']
                renewable_history[t] = row['target_renewable_share_pct']
                counts['rows'] += 1
                year_counts['rows'] += 1
                for k in ['features_complete', 'eligible_co2_nonestimated', 'eligible_renewable', 'eligible_both', 'co2_is_estimated']:
                    year_counts[k] += int(row[k])
                    counts[k] += int(row[k])
        assert dict(year_counts) == quality['yearly'][str(year)]
    print(json.dumps(dict(verified=True, raw_source_hashes_verified=len(manifest), counts=counts), indent=2))


if __name__ == '__main__':
    main()
