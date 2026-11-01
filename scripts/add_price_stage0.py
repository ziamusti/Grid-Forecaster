"""Add Day-ahead price (lag168h) as new Stage-0 feature; extend frozen v2; no training."""
import csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/stage0_v2_sunshine'
OUT = ROOT / 'data/processed/stage0_v3_price'
RAW = ROOT / 'data/raw/energycharts_price/20261027T203022Z'
FEATURE = 'price_eur_mwh_lag168h'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def load_price_series():
    # 2025 wechselt EU-weit auf 15-Minuten-Marktaufloesung, 2026 durchgehend PT15M;
    # Viertelstundenwerte werden zur vollen Stunde gemittelt, damit die Spalte mit dem
    # bestehenden Stundenraster der Merkmalstabelle kompatibel bleibt.
    buckets, sources = {}, []
    for path in sorted(RAW.glob('*.json')):
        if path.name == 'manifest.json':
            continue
        payload = json.loads(path.read_text())
        assert payload['unit'] == 'EUR / MWh'
        for entry in payload['data']:
            t = datetime.fromisoformat(entry['timestamp']).astimezone(timezone.utc)
            hour = t.replace(minute=0, second=0, microsecond=0)
            key = hour.strftime('%Y-%m-%dT%H:%M:%SZ')
            value = entry['values']['day_ahead_price']
            if value is None:
                continue
            buckets.setdefault(key, []).append(float(value))
        sources.append(dict(file=str(path.relative_to(ROOT)), sha256=sha(path), rows=len(payload['data']),
                             resolution=payload.get('resolution')))
    series = {k: sum(v) / len(v) for k, v in buckets.items()}
    return series, sources


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    series, sources = load_price_series()
    print(len(series), 'Preis-Stunden geladen', flush=True)

    schema = json.loads((BASE / 'feature_schema.json').read_text())
    assert FEATURE not in schema['features']
    schema['features'] = schema['features'] + [FEATURE]
    schema['price_features'] = [FEATURE]
    schema['price_semantics'] = (
        'Day-Ahead-Preis (EUR/MWh) zur Stunde energy_lag_time_utc = target_time_utc - 168h; '
        'kein Blick auf den zum Zielzeitpunkt noch unveroeffentlichten Day-Ahead-Preis.')

    OUT.mkdir(parents=True)
    missing_total = 0
    for path in sorted(BASE.glob('hourly_*.csv')):
        with path.open(newline='') as f, (OUT / path.name).open('w', newline='') as g:
            reader = csv.DictReader(f)
            fields = reader.fieldnames + [FEATURE]
            writer = csv.DictWriter(g, fieldnames=fields)
            writer.writeheader()
            rows = missing = 0
            for row in reader:
                price = series.get(row['energy_lag_time_utc'])
                row[FEATURE] = '' if price is None else price
                missing += price is None
                writer.writerow(row)
                rows += 1
        missing_total += missing
        print(path.name, rows, 'Zeilen,', missing, 'ohne Preis', flush=True)
        with path.open(newline='') as a, (OUT / path.name).open(newline='') as b:
            old_reader, new_reader = csv.DictReader(a), csv.DictReader(b)
            for old, new in zip(old_reader, new_reader):
                assert all(old[k] == new[k] for k in old)
                expected = series.get(old['energy_lag_time_utc'])
                assert (new[FEATURE] == '') if expected is None else abs(float(new[FEATURE]) - expected) < 1e-9
            assert next(old_reader, None) is None and next(new_reader, None) is None

    for name in ['splits.json', 'weather_metadata.json', 'mastr_monthly_reconstructed.csv',
                 'mastr_quality.json', 'smard_revision_conflicts.csv']:
        (OUT / name).write_bytes((BASE / name).read_bytes())

    original_sources = json.loads((BASE / 'source_manifest.json').read_text())
    original_sources += [dict(path=s['file'], sha256=s['sha256']) for s in sources]
    dump(OUT / 'source_manifest.json', original_sources)
    dump(OUT / 'base_version_manifest.json',
         dict(path=str(BASE.relative_to(ROOT)), hashes={p.name: sha(p) for p in BASE.iterdir() if p.is_file()}))
    dump(OUT / 'feature_schema.json', schema)
    dump(OUT / 'price_quality_report.json',
         dict(feature=FEATURE, price_hours_loaded=len(series), missing_total=missing_total, sources=sources))
    print('fertig:', OUT, flush=True)


if __name__ == '__main__':
    main()
