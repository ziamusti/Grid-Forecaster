"""Add one target column per renewable source (percent share), no training.

Builds a new Stage-0 version on top of stage0_v4_oct26: every existing
column (138 input features, both existing targets, price feature,
metadata) is copied unchanged, and six new target columns are added, one
per renewable source, each defined exactly like the existing
target_renewable_share_pct but for a single source instead of their sum:

    target_<source>_share_pct = 100 * generation[source] / total_generation

for source in (biomass, hydro, wind_offshore, wind_onshore, solar,
other_renewables) - the same six that make up RENEWABLE in
prepare_stage0.py. By construction the six new columns sum to the
existing target_renewable_share_pct for every row (asserted below).
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from prepare_stage0 import TECH, RENEWABLE, local_to_utc, smard, source, BERLIN

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/stage0_v4_oct26'
EXTENSION_SMARD_DIR = ROOT / 'data/raw/smard_range/20261101T171602Z'
UTC = timezone.utc
NEW_TARGETS = [f'target_{name}_share_pct' for name in RENEWABLE]


def _number(text):
    text = text.strip()
    if not text or text == '-':
        return None
    return float(text.replace('.', '').replace(',', '.'))


def load_extension_smard():
    rows = {}
    seen = defaultdict(int)
    with (EXTENSION_SMARD_DIR / 'generation.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        mapping = {name: next(k for k in reader.fieldnames if k.startswith(name + ' [MWh]'))
                   for name in TECH}
        for raw in reader:
            t = local_to_utc(raw['Datum von'], seen)
            row = {TECH[name]: _number(raw[col]) for name, col in mapping.items()}
            if t.astimezone(BERLIN).date() >= date(2023, 4, 16) and row['nuclear'] is None:
                row['nuclear'] = 0.0
            rows[t] = row
    return rows


def shares(row):
    if any(row[k] is None for k in TECH.values()):
        return None
    total = sum(row[k] for k in TECH.values())
    if total <= 0:
        return None
    return {f'target_{name}_share_pct': 100 * row[name] / total for name in RENEWABLE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/processed/stage0_v6_renewable_breakdown')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')

    sources = []
    gen, *_ = smard('generation', sources)
    extension = load_extension_smard()
    gen.update(extension)

    args.output.mkdir(parents=True)
    row_total, missing_total, mismatch_total = 0, 0, 0
    for path in sorted(BASE.glob('hourly_*.csv')):
        with path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames + NEW_TARGETS
            rows = list(reader)
        missing = 0
        for row in rows:
            t = datetime.fromisoformat(row['target_time_utc'].replace('Z', '+00:00'))
            values = shares(gen[t]) if t in gen else None
            if values is None:
                missing += 1
                for name in NEW_TARGETS:
                    row[name] = ''
                continue
            for name, value in values.items():
                row[name] = str(round(value, 6))
            if row['eligible_renewable'] == '1':
                total_check = sum(values.values())
                existing = float(row['target_renewable_share_pct'])
                if abs(total_check - existing) > 1e-6:
                    mismatch_total += 1
        row_total += len(rows)
        missing_total += missing
        with (args.output / path.name).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(path.name, 'Zeilen:', len(rows), 'ohne Aufschlüsselung:', missing)

    print('Gesamt:', row_total, 'ohne Wert:', missing_total, 'Summenabweichung > 1e-6:', mismatch_total)
    assert mismatch_total == 0, 'Aufschlüsselung summiert sich nicht zum Gesamt-Grünanteil'

    for name in ['splits.json', 'weather_metadata.json', 'mastr_monthly_reconstructed.csv', 'mastr_quality.json']:
        src = BASE / name
        if src.exists():
            (args.output / name).write_bytes(src.read_bytes())
    schema = json.loads((BASE / 'feature_schema.json').read_text())
    schema['targets'] = schema['targets'] + NEW_TARGETS
    (args.output / 'feature_schema.json').write_text(json.dumps(schema, indent=2))

    manifest = json.loads((BASE / 'source_manifest.json').read_text()) if (BASE / 'source_manifest.json').exists() else []
    manifest.extend(sources)
    (args.output / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))

    report = dict(created_utc=datetime.now(UTC).isoformat(), base=str(BASE.relative_to(ROOT)),
                  new_targets=NEW_TARGETS, rows_total=row_total, rows_missing=missing_total,
                  note='Per-source renewable share targets; sum to existing target_renewable_share_pct.')
    (args.output / 'renewable_breakdown_report.json').write_text(json.dumps(report, indent=2))
    print(args.output)


if __name__ == '__main__':
    main()
