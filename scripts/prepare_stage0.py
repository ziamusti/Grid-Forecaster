"""Raw-only retrospective data preparation; no estimator fitting or training.

Standard library only. Annual tables retain missing values and quality flags.
2026 MaStR/SMARD snapshots are NOT point-in-time historical releases.
"""
import argparse
import bisect
import calendar
import csv
import hashlib
import json
import math
import platform
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'archive/legacy_2026-10-20/data/raw'
CO2 = ROOT / 'data/raw/electricitymaps/full_DE_20261020T2100Z'
UTC = timezone.utc
BERLIN = ZoneInfo('Europe/Berlin')
TECH = {'Biomasse': 'biomass', 'Wasserkraft': 'hydro',
        'Wind Offshore': 'wind_offshore', 'Wind Onshore': 'wind_onshore',
        'Photovoltaik': 'solar', 'Sonstige Erneuerbare': 'other_renewables',
        'Kernenergie': 'nuclear', 'Braunkohle': 'lignite',
        'Steinkohle': 'hard_coal', 'Erdgas': 'gas',
        'Pumpspeicher': 'pumped_storage', 'Sonstige Konventionelle': 'other_conventional'}
RENEWABLE = tuple(list(TECH.values())[:6])
WEATHER = {'temperature_2m (°C)': 'temperature_2m_c', 'cloud_cover (%)': 'cloud_cover_pct',
           'wind_speed_100m (m/s)': 'wind_speed_100m_ms',
           'shortwave_radiation (W/m²)': 'shortwave_radiation_wm2'}


def iso(t):
    return t.isoformat().replace('+00:00', 'Z')


def number(text, german=False):
    if text is None or text.strip() in ('', '-', 'NaN', 'nan', 'null'):
        return None
    if german:
        text = text.replace('.', '').replace(',', '.')
    value = float(text)
    if not math.isfinite(value):
        return None
    return value


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def source(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=digest(path))


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def local_to_utc(text, occurrences):
    local = datetime.strptime(text, '%d.%m.%Y %H:%M')
    a = local.replace(tzinfo=BERLIN, fold=0)
    b = local.replace(tzinfo=BERLIN, fold=1)
    occurrence = occurrences[local]
    occurrences[local] += 1
    if occurrence > 1 or (occurrence and a.utcoffset() == b.utcoffset()):
        raise ValueError('Unexpected duplicate local timestamp: ' + text)
    aware = local.replace(tzinfo=BERLIN, fold=occurrence)
    result = aware.astimezone(UTC)
    if result.astimezone(BERLIN).replace(tzinfo=None) != local:
        raise ValueError('Nonexistent local timestamp: ' + text)
    return result


def renewables(row):
    # Gross category sum of reported net generation; pumping output belongs
    # to the denominator, never automatically to renewable generation.
    if any(row.get(k) is None for k in TECH.values()):
        return None
    if any(row[k] < 0 for k in TECH.values()):
        return None
    total = sum(row[k] for k in TECH.values())
    return 100 * sum(row[k] for k in RENEWABLE) / total if total > 0 else None


def smard(kind, sources):
    """Prefer named exports with greatest declared end; never infer as-of time."""
    prefix = 'Realisierte_Erzeugung' if kind == 'generation' else 'Realisierter_Stromverbrauch'
    paths = sorted((RAW / 'smard').glob(prefix + '*.csv'))
    selected = []
    excluded = []
    for p in paths:
        match = re.search(r'_(\d{12})_(\d{12})_Stunde\.csv$', p.name)
        if not match:
            excluded.append(p.name)
        else:
            selected.append((match.group(2), match.group(1), p))
    rows, origins, conflicts = {}, {}, []
    counters = Counter()
    for _, _, p in sorted(selected):
        sources.append(source(p))
        seen = Counter()
        with p.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            required = TECH if kind == 'generation' else {'Netzlast': 'grid_load'}
            mapping = {name: next(k for k in reader.fieldnames
                                  if k.startswith(name + ' [MWh]')) for name in required}
            for raw in reader:
                t = local_to_utc(raw['Datum von'], seen)
                row = {required[name]: number(raw[col], german=True) for name, col in mapping.items()}
                row['nuclear_zero_rule'] = 0
                if kind == 'generation' and t.astimezone(BERLIN).date() >= date(2023, 4, 16) and row['nuclear'] is None:
                    row['nuclear'] = 0.0
                    row['nuclear_zero_rule'] = 1
                if t in rows:
                    counters['overlap_rows'] += 1
                    if rows[t] != row:
                        conflicts.append(dict(timestamp_utc=iso(t), previous_file=origins[t],
                                              chosen_file=p.name,
                                              changed_fields='|'.join(k for k in row if row[k] != rows[t].get(k))))
                rows[t], origins[t] = row, p.name
    counters['conflicting_replacements'] = len(conflicts)
    counters['unique_hours'] = len(rows)
    counters['nuclear_zero_rule_rows'] = sum(r['nuclear_zero_rule'] for r in rows.values())
    return rows, origins, dict(counters), conflicts, excluded


def load_co2(sources):
    rows = {}
    for p in sorted(CO2.glob('*.json')):
        if p.name == 'manifest.json':
            continue
        sources.append(source(p))
        for r in json.loads(p.read_text())['data']:
            if r.get('zone', 'DE') != 'DE' or r['flowTraced'] is not False or r['emissionFactorType'] != 'lifecycle':
                raise ValueError('Unexpected CO2 basis')
            t = datetime.fromisoformat(r['datetime'].replace('Z', '+00:00'))
            if t in rows:
                raise ValueError('Duplicate CO2 hour')
            rows[t] = r
    return rows


def load_weather(sources):
    tables, metadata = {}, {}
    for p in sorted((RAW / 'weather').glob('*.csv')):
        station = re.sub(r'_(2015_2025|2026)\.csv$', '', p.name)
        if station == p.name:
            raise ValueError('Unrecognized weather file')
        sources.append(source(p))
        table = tables.setdefault(station, {})
        with p.open(encoding='utf-8', newline='') as f:
            meta = next(csv.DictReader(f))
            if int(meta['utc_offset_seconds']) != 0:
                raise ValueError('Weather must be UTC')
            metadata.setdefault(station, meta)
            f.readline()
            for row in csv.DictReader(f):
                t = datetime.fromisoformat(row['time']).replace(tzinfo=UTC)
                if t in table:
                    raise ValueError('Duplicate weather timestamp')
                table[t] = tuple(number(row[k]) for k in WEATHER)
    if len(tables) != 23:
        raise ValueError('Expected 23 stations')
    return tables, metadata


def easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    n = h + l - 7 * m + 114
    return date(year, n // 31, n % 31 + 1)


def holidays(year):
    e = easter(year)
    result = {date(year, m, d) for m, d in [(1, 1), (5, 1), (10, 3), (12, 25), (12, 26)]}
    result.update(e + timedelta(days=x) for x in [-2, 1, 39, 50])
    if year == 2017:
        result.add(date(year, 10, 31))
    return result


def daylight(day, latitude=51.1657):
    # Geometric approximation, no atmosphere/terrain; explicitly a proxy.
    n = day.timetuple().tm_yday
    decl = math.radians(23.44 * math.sin(2 * math.pi * (284 + n) / 365.2425))
    angle = max(-1, min(1, -math.tan(math.radians(latitude)) * math.tan(decl)))
    return round(24 * math.acos(angle) / math.pi, 6)


def capacity_reference(t):
    # Use the month start preceding even the earliest 72-h forecast origin.
    # Strict date boundary excludes commissioning on/after that date.
    origin = (t - timedelta(hours=72)).astimezone(BERLIN)
    return date(origin.year, origin.month, 1)


def fold_spec():
    folds = [dict(train_years=list(range(y - 3, y)), validation_year=y)
             for y in range(2018, 2025)]
    return dict(year_basis='UTC target timestamp', development_folds=folds,
                final_train_years=[2022, 2023, 2024], final_test_year=2025,
                holdout_partial_year=2026, fit_preprocessors_on_train_only=True,
                note='No scaler/imputer/model fitted. 2025 must not inform selection.')


def xml_records(z, name, tag):
    with z.open(name) as f:
        iterator = ET.iterparse(f, events=('start', 'end'))
        _, root = next(iterator)
        for event, element in iterator:
            if event == 'end' and element.tag == tag:
                yield {c.tag: c.text for c in element}
                root.clear()


def mastr(output, sources):
    """Reconstruction from snapshot, never claimed to be as-issued history."""
    path = RAW / 'mastr/Gesamtdatenexport_20261020_26.2.zip'
    print('MaStR: Hash und XML-Streaming, kein Entpacken', flush=True)
    sources.append(source(path))
    events = {k: defaultdict(float) for k in ['pv', 'wind_onshore', 'wind_offshore']}
    counts = Counter()
    excluded_mw = Counter()
    seen = set()
    snapshot = date(2026, 10, 20)
    with zipfile.ZipFile(path) as z:
        catalog = {r['Id']: r['Wert'] for r in xml_records(z, 'Katalogwerte.xml', 'Katalogwert')}
        assert catalog['84'] == 'Deutschland' and catalog['35'] == 'In Betrieb'
        assert catalog['888'] == 'Windenergie an Land' and catalog['889'] == 'Windenergie auf See'
        files = sorted(n for n in z.namelist() if n.startswith('EinheitenSolar_') or n == 'EinheitenWind.xml')
        for name in files:
            solar = name.startswith('EinheitenSolar_')
            for r in xml_records(z, name, 'EinheitSolar' if solar else 'EinheitWind'):
                counts['all_units'] += 1
                category = 'pv' if solar else {'888': 'wind_onshore', '889': 'wind_offshore'}.get(r.get('WindAnLandOderAufSee'))
                power = number(r.get('Nettonennleistung'))
                reason = None
                unit = r.get('EinheitMastrNummer')
                if not unit or unit in seen:
                    raise ValueError('Missing or duplicate MaStR unit ID')
                seen.add(unit)
                if r.get('Land') != '84': reason = 'not_germany'
                elif r.get('EinheitSystemstatus') not in ('472', '484'): reason = 'inactive_or_incomplete_system_status'
                elif r.get('EinheitBetriebsstatus') == '31': reason = 'planned'
                elif r.get('EinheitBetriebsstatus') not in ('35', '37', '38'): reason = 'unknown_operating_status'
                elif category is None: reason = 'unknown_wind_type'
                elif power is None or power <= 0: reason = 'missing_or_nonpositive_net_capacity'
                start, stop = None, None
                if reason is None:
                    try:
                        start = date.fromisoformat(r.get('Inbetriebnahmedatum') or '')
                        stop = date.fromisoformat(r['DatumEndgueltigeStilllegung']) if r.get('DatumEndgueltigeStilllegung') else None
                    except ValueError:
                        reason = 'missing_or_invalid_date'
                if reason is None:
                    # Conservative screening thresholds, not inferred true dates.
                    lower = date(1954, 1, 1) if solar else date(1901, 1, 1)
                    if start < lower or start > snapshot: reason = 'commissioning_outside_screening_bounds'
                    elif stop and (stop < start or stop > snapshot): reason = 'invalid_retirement_date'
                    elif r.get('EinheitBetriebsstatus') == '38' and not stop: reason = 'retired_without_date'
                    elif r.get('EinheitBetriebsstatus') == '35' and stop: reason = 'operating_but_retired_date'
                if reason:
                    counts['excluded_' + reason] += 1
                    if power is not None and power > 0:
                        excluded_mw[reason] += power / 1000
                    continue
                counts['included_' + category] += 1
                if r.get('EinheitBetriebsstatus') == '37': counts['temporary_shutdown_counted_as_installed'] += 1
                if start.year < 1980: counts['included_pre1980_' + category] += 1
                events[category][start] += power / 1000
                if stop: events[category][stop] -= power / 1000
            print('MaStR:', name, 'Einheiten:', counts['all_units'], flush=True)
    series = {}
    for year in range(2014, 2027):
        for month in range(1, 13):
            boundary = date(year, month, 1)
            if boundary > snapshot: continue
            series[boundary] = {k: round(sum(v for d, v in events[k].items() if d < boundary), 6) for k in events}
    write_csv(output / 'mastr_monthly_reconstructed.csv',
              ['reference_date_exclusive', 'pv_net_mw', 'wind_onshore_net_mw', 'wind_offshore_net_mw', 'basis'],
              [dict(reference_date_exclusive=str(d), **{k + '_net_mw': v for k, v in row.items()},
                    basis='reconstructed_from_2026_snapshot_NOT_as_of') for d, row in sorted(series.items())])
    report = dict(counts=counts, excluded_net_mw=excluded_mw, power_field='Nettonennleistung kW / 1000',
                  status='retrospective_proxy_not_historically_available',
                  limitations=['survivorship and deleted units', 'historical capacity changes unavailable',
                               'temporary shutdowns do not remove installed capacity',
                               'dates before screening thresholds excluded; no dates guessed',
                               'registration dates do not reconstruct pre-2019 publication history'])
    write_json(output / 'mastr_quality.json', report)
    return series, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / 'data/processed').resolve()):
        raise SystemExit('Output must be inside data/processed')
    output.mkdir(parents=True, exist_ok=False)
    sources = []
    write_json(output / 'RUNNING.json', {'started_utc': iso(datetime.now(UTC)), 'script_sha256': digest(Path(__file__))})
    print('SMARD aus Rohdateien', flush=True)
    gen, gen_sources, gen_quality, gen_conflicts, gen_excluded = smard('generation', sources)
    load, load_sources, load_quality, load_conflicts, load_excluded = smard('load', sources)
    write_csv(output / 'smard_revision_conflicts.csv', ['timestamp_utc', 'previous_file', 'chosen_file', 'changed_fields'], gen_conflicts + load_conflicts)
    print('CO2 und Wetter aus Rohdateien', flush=True)
    co2 = load_co2(sources)
    weather, weather_meta = load_weather(sources)
    capacities, capacity_quality = mastr(output, sources)
    stations = sorted(weather)
    calendar_features = ['hour_local', 'weekday', 'month', 'is_weekend', 'is_national_holiday', 'daylight_hours_approx']
    weather_features = [s + '__' + v for s in stations for v in WEATHER.values()]
    capacity_features = ['pv_net_mw_reconstructed', 'wind_onshore_net_mw_reconstructed', 'wind_offshore_net_mw_reconstructed']
    energy_features = [k + '_mwh_lag168h' for k in TECH.values()] + ['grid_load_mwh_lag168h']
    features = calendar_features + weather_features + capacity_features + energy_features
    targets = ['target_co2_gco2eq_kwh', 'target_renewable_share_pct']
    meta_cols = ['target_time_utc', 'target_time_berlin', 'energy_lag_time_utc', 'capacity_reference_date',
                 'co2_is_estimated', 'co2_estimation_method', 'co2_updated_at',
                 'co2_lag168h_baseline_only', 'renewable_share_lag168h_baseline_only',
                 'generation_source', 'energy_lag_generation_source', 'energy_lag_load_source',
                 'target_nuclear_zero_rule', 'lag_nuclear_zero_rule',
                 'features_complete', 'eligible_co2_nonestimated', 'eligible_renewable', 'eligible_both']
    common = set(co2).intersection(gen, load, *(table.keys() for table in weather.values()))
    common = sorted(t for t in common if t >= datetime(2015, 1, 1, tzinfo=UTC))
    yearly = defaultdict(Counter)
    missing = Counter()
    files, writers = {}, {}
    holiday_sets = {y: holidays(y) for y in range(2014, 2028)}
    try:
        for t in common:
            year = t.year
            if year not in writers:
                f = (output / f'hourly_{year}.csv').open('w', newline='', encoding='utf-8')
                files[year] = f
                writers[year] = csv.DictWriter(f, fieldnames=meta_cols + features + targets)
                writers[year].writeheader()
            lag = t - timedelta(hours=168)
            local = t.astimezone(BERLIN)
            ref = capacity_reference(t)
            cr = capacities.get(ref, {})
            row = dict(target_time_utc=iso(t), target_time_berlin=local.isoformat(),
                       energy_lag_time_utc=iso(lag), capacity_reference_date=str(ref),
                       hour_local=local.hour, weekday=local.weekday(), month=local.month,
                       is_weekend=int(local.weekday() >= 5),
                       is_national_holiday=int(local.date() in holiday_sets[local.year]),
                       daylight_hours_approx=daylight(local.date()),
                       target_co2_gco2eq_kwh=co2[t].get('carbonIntensity'),
                       target_renewable_share_pct=renewables(gen[t]),
                       co2_is_estimated=int(co2[t].get('isEstimated', True)),
                       co2_estimation_method=co2[t].get('estimationMethod'),
                       co2_updated_at=co2[t].get('updatedAt'),
                       co2_lag168h_baseline_only=co2.get(lag, {}).get('carbonIntensity'),
                       renewable_share_lag168h_baseline_only=renewables(gen.get(lag, {})),
                       generation_source=gen_sources[t],
                       energy_lag_generation_source=gen_sources.get(lag), energy_lag_load_source=load_sources.get(lag),
                       target_nuclear_zero_rule=gen[t]['nuclear_zero_rule'],
                       lag_nuclear_zero_rule=gen.get(lag, {}).get('nuclear_zero_rule'))
            for station in stations:
                row.update({station + '__' + k: v for k, v in zip(WEATHER.values(), weather[station][t])})
            row.update({k + '_net_mw_reconstructed': cr.get(k) for k in ('pv', 'wind_onshore', 'wind_offshore')})
            row.update({k + '_mwh_lag168h': gen.get(lag, {}).get(k) for k in TECH.values()})
            row['grid_load_mwh_lag168h'] = load.get(lag, {}).get('grid_load')
            for k in features + targets:
                if row[k] is None: missing[k] += 1
            row['features_complete'] = int(all(row[k] is not None for k in features))
            row['eligible_co2_nonestimated'] = int(row['features_complete'] and row[targets[0]] is not None and not row['co2_is_estimated'])
            row['eligible_renewable'] = int(row['features_complete'] and row[targets[1]] is not None)
            row['eligible_both'] = int(row['eligible_co2_nonestimated'] and row['eligible_renewable'])
            writers[year].writerow(row)
            yearly[year]['rows'] += 1
            for k in ['features_complete', 'eligible_co2_nonestimated', 'eligible_renewable', 'eligible_both', 'co2_is_estimated']:
                yearly[year][k] += row[k]
    finally:
        for f in files.values(): f.close()
    write_json(output / 'feature_schema.json', dict(features=features, targets=targets, metadata_not_features=meta_cols,
        weather_features=weather_features, calendar_features=calendar_features,
        capacity_features=capacity_features, energy_features=energy_features,
        warning='Use explicit feature allowlist; targets, quality flags, source names and baselines are NOT inputs.'))
    write_json(output / 'splits.json', fold_spec())
    write_json(output / 'weather_metadata.json', weather_meta)
    write_json(output / 'source_manifest.json', sources)
    summary = dict(status='complete_retrospective_preparation_NOT_operational_backtest',
                   python=platform.python_version(), start_utc=iso(common[0]), end_utc=iso(common[-1]),
                   yearly=yearly, missing_values=missing, smard_generation=gen_quality, smard_load=load_quality,
                   excluded_smard_files=gen_excluded + load_excluded,
                   mastr=capacity_quality, preprocessing_fitted=False, trained_models=0,
                   source_count=len(sources), feature_count=len(features), script_sha256=digest(Path(__file__)),
                   limitations=['ERA5 future weather not available at forecast origin',
                                'SMARD revised snapshots; historical publication times unverified',
                                'MaStR reconstructed from 2026, not point-in-time history',
                                '2026 incomplete and reserved',
                                '2015-2025 old project already evaluated some years: new holdout not historically pristine'])
    write_json(output / 'quality_report.json', summary)
    write_json(output / 'COMPLETE.json', {'completed_utc': iso(datetime.now(UTC)), 'rows': len(common)})
    print(json.dumps({'output': str(output), 'yearly': yearly, 'features': len(features)}, indent=2), flush=True)


if __name__ == '__main__':
    main()
