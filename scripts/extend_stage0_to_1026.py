"""Extend the price-feature Stage-0 table with 2026-09-24..2026-10-26 (new rows, no training).

Reuses the row schema of data/processed/stage0_v3_price exactly (137 features
+ meta + 2 targets + price feature). New raw data: SMARD generation/load
(data/raw/smard_range), ERA5 weather at target time (data/raw/weather_range_*),
Electricity Maps CO2 (data/raw/electricitymaps_range), Day-ahead price
(already-downloaded data/raw/energycharts_price), MaStR capacity reconstruction
(reused unchanged, already covers October 2026).
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from prepare_stage0 import (TECH, WEATHER, RENEWABLE, renewables, local_to_utc,
                             capacity_reference, daylight, holidays, number, iso, BERLIN)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/stage0_v3_price'
OUT = ROOT / 'data/processed/stage0_v4_oct26'
SMARD_DIR = ROOT / 'data/raw/smard_range/20261101T171602Z'
WEATHER_DIR = ROOT / 'data/raw/weather_range_20260924_20261026_era5'
CO2_DIR = ROOT / 'data/raw/electricitymaps_range/20261101T172727Z'
PRICE_RAW = ROOT / 'data/raw/energycharts_price/20261027T203022Z'
CAPACITY_PATH = BASE / 'mastr_monthly_reconstructed.csv'
UTC = timezone.utc
PRICE_FEATURE = 'price_eur_mwh_lag168h'
TARGET_START = datetime(2026, 9, 24, tzinfo=UTC)
TARGET_END_EXCLUSIVE = datetime(2026, 10, 27, tzinfo=UTC)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def load_smard():
    rows = {}
    seen = defaultdict(int)
    with (SMARD_DIR / 'generation.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        mapping = {name: next(k for k in reader.fieldnames if k.startswith(name + ' [MWh]')) for name in TECH}
        for raw in reader:
            t = local_to_utc(raw['Datum von'], seen)
            row = {TECH[name]: number(raw[col], german=True) for name, col in mapping.items()}
            row['nuclear_zero_rule'] = 0
            if t.astimezone(BERLIN).date() >= date(2023, 4, 16) and row['nuclear'] is None:
                row['nuclear'] = 0.0
                row['nuclear_zero_rule'] = 1
            rows[t] = row
    load_rows = {}
    seen = defaultdict(int)
    with (SMARD_DIR / 'load.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        col = next(k for k in reader.fieldnames if k.startswith('Netzlast [MWh]'))
        for raw in reader:
            t = local_to_utc(raw['Datum von'], seen)
            load_rows[t] = {'grid_load': number(raw[col], german=True)}
    return rows, load_rows


def load_co2():
    rows = {}
    for p in sorted(CO2_DIR.glob('*.json')):
        if p.name == 'manifest.json':
            continue
        for r in json.loads(p.read_text())['data']:
            if r.get('zone', 'DE') != 'DE' or r['flowTraced'] is not False or r['emissionFactorType'] != 'lifecycle':
                raise ValueError('Unexpected CO2 basis')
            t = datetime.fromisoformat(r['datetime'].replace('Z', '+00:00'))
            if t in rows:
                raise ValueError('Duplicate CO2 hour')
            rows[t] = r
    return rows


def load_weather():
    manifest = json.loads((WEATHER_DIR / 'manifest.json').read_text())
    stations = sorted(manifest['stations'])
    assert len(stations) == 23 and manifest['complete']
    weather = {}
    for station in stations:
        d = json.loads((WEATHER_DIR / (station + '.json')).read_text())['hourly']
        weather[station] = {t: {k: d[k][i] for k in d if k != 'time'} for i, t in enumerate(d['time'])}
    return weather, stations


def load_price_series():
    buckets = {}
    for path in sorted(PRICE_RAW.glob('*.json')):
        if path.name == 'manifest.json':
            continue
        payload = json.loads(path.read_text())
        assert payload['unit'] == 'EUR / MWh'
        for entry in payload['data']:
            t = datetime.fromisoformat(entry['timestamp']).astimezone(UTC)
            hour = t.replace(minute=0, second=0, microsecond=0)
            value = entry['values']['day_ahead_price']
            if value is None:
                continue
            buckets.setdefault(hour, []).append(float(value))
    return {k: sum(v) / len(v) for k, v in buckets.items()}


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    gen, load = load_smard()
    co2 = load_co2()
    weather, stations = load_weather()
    price_series = load_price_series()
    with CAPACITY_PATH.open() as f:
        capacity = {date.fromisoformat(r['reference_date_exclusive']): r for r in csv.DictReader(f)}

    schema = json.loads((BASE / 'feature_schema.json').read_text())
    features = schema['features']
    assert len(features) == 138 and PRICE_FEATURE in features  # includes is_weekend; model features (137) exclude it
    targets = schema['targets']
    weather_features = schema['weather_features']
    calendar_features = schema['calendar_features']
    capacity_features = schema['capacity_features']
    energy_features = schema['energy_features']
    meta_cols = ['target_time_utc', 'target_time_berlin', 'energy_lag_time_utc', 'capacity_reference_date',
                 'co2_is_estimated', 'co2_estimation_method', 'co2_updated_at',
                 'co2_lag168h_baseline_only', 'renewable_share_lag168h_baseline_only',
                 'generation_source', 'energy_lag_generation_source', 'energy_lag_load_source',
                 'target_nuclear_zero_rule', 'lag_nuclear_zero_rule',
                 'features_complete', 'eligible_co2_nonestimated', 'eligible_renewable', 'eligible_both']
    holiday_sets = {y: holidays(y) for y in (2026,)}

    times = [TARGET_START + timedelta(hours=i) for i in range(int((TARGET_END_EXCLUSIVE - TARGET_START).total_seconds() / 3600))]
    assert len(times) == 792
    missing = Counter()
    rows = []
    gen_source_name = 'data/raw/smard_range/20261101T171602Z/generation.csv'
    load_source_name = 'data/raw/smard_range/20261101T171602Z/load.csv'
    for t in times:
        lag = t - timedelta(hours=168)
        local = t.astimezone(BERLIN)
        ref = capacity_reference(t)
        cr = capacity.get(ref, {})
        co2_row = co2.get(t, {})
        row = dict(target_time_utc=iso(t), target_time_berlin=local.isoformat(),
                   energy_lag_time_utc=iso(lag), capacity_reference_date=str(ref),
                   hour_local=local.hour, weekday=local.weekday(), month=local.month,
                   is_weekend=int(local.weekday() >= 5),
                   is_national_holiday=int(local.date() in holiday_sets[2026]),
                   daylight_hours_approx=daylight(local.date()),
                   target_co2_gco2eq_kwh=co2_row.get('carbonIntensity'),
                   target_renewable_share_pct=renewables(gen.get(t, {})),
                   co2_is_estimated=int(co2_row.get('isEstimated', True)),
                   co2_estimation_method=co2_row.get('estimationMethod'),
                   co2_updated_at=co2_row.get('updatedAt'),
                   co2_lag168h_baseline_only=co2.get(lag, {}).get('carbonIntensity'),
                   renewable_share_lag168h_baseline_only=renewables(gen.get(lag, {})),
                   generation_source=gen_source_name,
                   energy_lag_generation_source=gen_source_name, energy_lag_load_source=load_source_name,
                   target_nuclear_zero_rule=gen.get(t, {}).get('nuclear_zero_rule'),
                   lag_nuclear_zero_rule=gen.get(lag, {}).get('nuclear_zero_rule'))
        for station in stations:
            w = weather[station][t.strftime('%Y-%m-%dT%H:%M')]
            for original, feature in WEATHER.items():
                row[station + '__' + feature] = w[original.split(' (')[0]]
            row[station + '__sunshine_duration_preceding_hour_s'] = w['sunshine_duration']
        row.update({k + '_net_mw_reconstructed': number(cr.get(k + '_net_mw')) for k in ('pv', 'wind_onshore', 'wind_offshore')})
        row.update({k + '_mwh_lag168h': gen.get(lag, {}).get(k) for k in TECH.values()})
        row['grid_load_mwh_lag168h'] = load.get(lag, {}).get('grid_load')
        row[PRICE_FEATURE] = price_series.get(lag)
        for k in list(features) + list(targets):
            if row.get(k) is None:
                missing[k] += 1
        row['features_complete'] = int(all(row[k] is not None for k in features))
        row['eligible_co2_nonestimated'] = int(row['features_complete'] and row['target_co2_gco2eq_kwh'] is not None and not row['co2_is_estimated'])
        row['eligible_renewable'] = int(row['features_complete'] and row['target_renewable_share_pct'] is not None)
        row['eligible_both'] = int(row['eligible_co2_nonestimated'] and row['eligible_renewable'])
        rows.append(row)

    assert missing['price_eur_mwh_lag168h'] == 0, f"Preis fehlt fuer {missing['price_eur_mwh_lag168h']} Stunden"
    assert sum(missing.values()) == 0, dict(missing)

    OUT.mkdir(parents=True)
    for path in sorted(BASE.glob('hourly_*.csv')):
        year = int(path.stem.split('_')[1])
        with path.open(newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            old_rows = list(reader)
        assert set(fieldnames) == set(meta_cols) | set(features) | set(targets), 'Spaltenabgleich fehlgeschlagen'
        extra = [r for r in rows if int(r['target_time_utc'][:4]) == year] if year == 2026 else []
        with (OUT / path.name).open('w', newline='') as g:
            writer = csv.DictWriter(g, fieldnames=fieldnames)
            writer.writeheader()
            for r in old_rows:
                writer.writerow(r)
            for r in extra:
                writer.writerow(r)
        print(path.name, len(old_rows), '+', len(extra), '=', len(old_rows) + len(extra), flush=True)

    for name in ['feature_schema.json', 'splits.json', 'weather_metadata.json',
                 'mastr_monthly_reconstructed.csv', 'mastr_quality.json', 'smard_revision_conflicts.csv',
                 'price_quality_report.json']:
        src = BASE / name
        if src.exists():
            (OUT / name).write_bytes(src.read_bytes())

    sources = json.loads((BASE / 'source_manifest.json').read_text())
    sources += [
        dict(path=str((SMARD_DIR / 'generation.csv').relative_to(ROOT)), sha256=sha(SMARD_DIR / 'generation.csv')),
        dict(path=str((SMARD_DIR / 'load.csv').relative_to(ROOT)), sha256=sha(SMARD_DIR / 'load.csv')),
        dict(path=str((CO2_DIR / 'manifest.json').relative_to(ROOT)), sha256=sha(CO2_DIR / 'manifest.json')),
        dict(path=str((WEATHER_DIR / 'manifest.json').relative_to(ROOT)), sha256=sha(WEATHER_DIR / 'manifest.json')),
    ]
    (OUT / 'source_manifest.json').write_text(json.dumps(sources, indent=2))
    (OUT / 'extension_report.json').write_text(json.dumps(dict(
        extended_period_start_utc=iso(TARGET_START), extended_period_end_exclusive_utc=iso(TARGET_END_EXCLUSIVE),
        hours_added=len(times), missing_values=dict(missing),
        smard_source=str(SMARD_DIR.relative_to(ROOT)), weather_source=str(WEATHER_DIR.relative_to(ROOT)),
        co2_source=str(CO2_DIR.relative_to(ROOT)), price_source=str(PRICE_RAW.relative_to(ROOT)),
        base_version=str(BASE.relative_to(ROOT))), indent=2))
    print('fertig:', OUT, flush=True)


if __name__ == '__main__':
    main()
