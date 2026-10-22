"""Download ERA5 sunshine, validate, extend frozen Stage-0 v1; no training."""
import ast
import csv
import hashlib
import json
import math
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/stage0_v1_2026-10-22'
OUT = ROOT / 'data/processed/stage0_v2_sunshine'
RAW = ROOT / 'data/raw/open_meteo_sunshine_era5'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def request(url, path):
    if path.exists(): return json.loads(path.read_text())
    for attempt in range(5):
        try:
            with urlopen(url, timeout=50) as r: body = r.read()
            obj = json.loads(body)
            if isinstance(obj, dict) and obj.get('error'): raise ValueError(obj)
            path.write_bytes(body)
            return obj
        except HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(str(e.code) + ': ' + e.read().decode()[:400]) from None
        except (URLError, TimeoutError): pass
        time.sleep(min(2 ** (attempt + 1), 30))
    raise RuntimeError('Download fehlgeschlagen; vorhandene Rohdateien bleiben erhalten.')


def validate(d, start, end):
    assert d['utc_offset_seconds'] == 0
    assert d['hourly_units']['sunshine_duration'] == 's'
    times, values = d['hourly']['time'], d['hourly']['sunshine_duration']
    a = datetime.fromisoformat(start)
    b = datetime.fromisoformat(end) + timedelta(days=1)
    assert len(times) == len(values) == int((b-a).total_seconds()/3600)
    for i, (t, v) in enumerate(zip(times, values)):
        assert datetime.fromisoformat(t) == a + timedelta(hours=i)
        assert v is not None and math.isfinite(v) and 0 <= v <= 3600
    return dict(zip(times, values))


def main():
    if OUT.exists(): raise SystemExit('Ausgabe existiert bereits; kein Überschreiben.')
    tree = ast.parse((ROOT / 'archive/legacy_2026-10-20/src/download_weather_2026.py').read_text())
    locations = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'LOCATIONS' for t in n.targets))
    assert len(locations) == 23
    metadata = json.loads((BASE / 'weather_metadata.json').read_text())
    baseline_hashes = {p.name: sha(p) for p in BASE.iterdir() if p.is_file()}
    RAW.mkdir(parents=True, exist_ok=True)
    manifest, sunshine = [], {}
    for station, (lat, lon, sea) in sorted(locations.items()):
        series = {}
        for year in range(2015, 2027):
            start = f'{year}-01-01'
            end = f'{year}-12-31' if year < 2026 else '2026-09-23'
            params = dict(latitude=lat, longitude=lon, start_date=start, end_date=end,
                          hourly='sunshine_duration', models='era5', timezone='GMT',
                          cell_selection='sea' if sea else 'land')
            url = 'https://archive-api.open-meteo.com/v1/archive?' + urlencode(params)
            path = RAW / f'{station}_{year}.json'
            cached = path.exists()
            d = request(url, path)
            series.update(validate(d, start, end))
            assert abs(d['latitude'] - float(metadata[station]['latitude'])) < 0.001
            assert abs(d['longitude'] - float(metadata[station]['longitude'])) < 0.001
            item = dict(file=path.name, sha256=sha(path), url=url, hours=len(d['hourly']['time']),
                        checked_at_utc=datetime.now(timezone.utc).isoformat(), cached=cached)
            manifest.append(item)
            dump(RAW / 'manifest.json', manifest)
            if not cached: time.sleep(0.3)
        sunshine[station] = series
        print(station, len(series), 'Stunden geprüft', flush=True)
    OUT.mkdir()
    schema = json.loads((BASE / 'feature_schema.json').read_text())
    new_features = [s + '__sunshine_duration_preceding_hour_s' for s in sorted(locations)]
    schema['features'] += new_features
    schema['weather_features'] += new_features
    schema['sunshine_features'] = new_features
    schema['sunshine_semantics'] = 'Seconds in [t-1h,t), native API endpoint timestamp t; derived ERA5, not station measurement.'
    report = dict(rows=0, sunshine_values=0, null_values=0, out_of_range=0,
                  original_columns_unchanged=True, units='s', features=len(schema['features']),
                  interval='preceding hour ending at target timestamp; no shift',
                  forecast_availability='full_archive_not_verified; separate Berlin single-run probe documented in docs/stufe0_sonnenscheindauer.md',
                  inherited_limitations=json.loads((BASE / 'quality_report.json').read_text())['limitations'])
    for path in sorted(BASE.glob('hourly_*.csv')):
        with path.open(newline='') as f, (OUT / path.name).open('w', newline='') as g:
            reader = csv.DictReader(f)
            fields = reader.fieldnames + new_features
            writer = csv.DictWriter(g, fieldnames=fields); writer.writeheader()
            for row in reader:
                key = datetime.fromisoformat(row['target_time_utc'].replace('Z', '+00:00')).strftime('%Y-%m-%dT%H:%M')
                for station, feature in zip(sorted(locations), new_features): row[feature] = sunshine[station][key]
                writer.writerow(row)
                report['rows'] += 1; report['sunshine_values'] += len(new_features)
        # Independent full reread verifies extension, not only writing logic.
        with path.open(newline='') as a, (OUT/path.name).open(newline='') as b:
            old, new = csv.DictReader(a), csv.DictReader(b)
            n = 0
            for x, y in zip(old, new):
                assert all(x[k] == y[k] for k in x)
                assert all(0 <= float(y[k]) <= 3600 for k in new_features)
                n += 1
            assert next(old, None) is None and next(new, None) is None
        print(path.name, n, 'Zeilen ergänzt und geprüft', flush=True)
    for name in ['splits.json', 'weather_metadata.json', 'mastr_monthly_reconstructed.csv', 'mastr_quality.json', 'smard_revision_conflicts.csv']:
        shutil.copyfile(BASE/name, OUT/name)
    original_sources = json.loads((BASE/'source_manifest.json').read_text())
    original_sources += [dict(path=str((RAW/i['file']).relative_to(ROOT)), sha256=i['sha256'],
                              bytes=(RAW/i['file']).stat().st_size) for i in manifest]
    dump(OUT/'source_manifest.json', original_sources)
    dump(OUT/'base_version_manifest.json', dict(path=str(BASE.relative_to(ROOT)), hashes=baseline_hashes))
    dump(OUT/'feature_schema.json', schema)
    dump(OUT/'quality_report_base.json', json.loads((BASE/'quality_report.json').read_text()))
    for name, h in baseline_hashes.items(): assert sha(BASE/name) == h
    for item in manifest: assert sha(RAW/item['file']) == item['sha256']
    dump(OUT/'sunshine_quality_report.json', report)
    dump(OUT/'COMPLETE.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(), **report))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__': main()
