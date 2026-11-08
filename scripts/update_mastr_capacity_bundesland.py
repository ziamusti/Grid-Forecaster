"""Recompute installed PV/wind capacity per Bundesland from a MaStR export.

Same reconstruction logic/business rules as scripts/update_mastr_capacity.py
(screening thresholds, excluded reasons, net-capacity field), extended to
also group by the unit's Bundesland field (a catalog code directly on every
EinheitSolar/EinheitWind record). Never touches the national-only output.
"""
import argparse
import json
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundesland import BUNDESLAENDER
from prepare_stage0 import number, source, write_csv, write_json, xml_records

ROOT = Path(__file__).resolve().parents[1]


def reconstruct(zip_path: Path, snapshot: date):
    sources = [source(zip_path)]
    events = {k: defaultdict(lambda: defaultdict(float)) for k in ['pv', 'wind_onshore', 'wind_offshore']}
    counts = Counter()
    excluded_mw = Counter()
    seen = set()
    with zipfile.ZipFile(zip_path) as z:
        catalog = {r['Id']: r['Wert'] for r in xml_records(z, 'Katalogwerte.xml', 'Katalogwert')}
        assert catalog['84'] == 'Deutschland' and catalog['35'] == 'In Betrieb'
        assert catalog['888'].startswith('Wind') and catalog['888'].endswith('an Land')
        assert catalog['889'].startswith('Wind') and catalog['889'].endswith('auf See')
        bundesland_id = {code: name for code, name in catalog.items() if name in BUNDESLAENDER}
        assert set(bundesland_id.values()) == set(BUNDESLAENDER), 'Nicht alle 16 Bundeslaender im Katalog gefunden'
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
                bundesland = bundesland_id.get(r.get('Bundesland'))
                if r.get('Land') != '84': reason = 'not_germany'
                elif bundesland is None: reason = 'unknown_or_missing_bundesland'
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
                events[category][bundesland][start] += power / 1000
                if stop: events[category][bundesland][stop] -= power / 1000
            print('MaStR:', name, 'Einheiten:', counts['all_units'], flush=True)
    series = {}
    for year in range(2014, snapshot.year + 2):
        for month in range(1, 13):
            boundary = date(year, month, 1)
            if boundary > snapshot: continue
            for land in BUNDESLAENDER:
                series[boundary, land] = {k: round(sum(v for d, v in events[k][land].items() if d < boundary), 6)
                                           for k in events}
    return series, dict(counts=counts, excluded_net_mw=excluded_mw, power_field='Nettonennleistung kW / 1000',
                        status='retrospective_proxy_not_historically_available', snapshot=str(snapshot),
                        limitations=['survivorship and deleted units', 'historical capacity changes unavailable',
                                     'temporary shutdowns do not remove installed capacity',
                                     'dates before screening thresholds excluded; no dates guessed',
                                     'registration dates do not reconstruct pre-2019 publication history',
                                     'Bundesland from unit record at snapshot time, not historical address']), sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, required=True, help='Path to the downloaded Gesamtdatenexport ZIP')
    parser.add_argument('--snapshot', required=True, help='Export snapshot date (YYYY-MM-DD)')
    parser.add_argument('--output', type=Path, required=True, help='Output directory (must not exist)')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    snapshot = date.fromisoformat(args.snapshot)
    series, report, sources = reconstruct(args.zip.resolve(), snapshot)
    args.output.mkdir(parents=True)
    write_csv(args.output / 'mastr_monthly_reconstructed_bundesland.csv',
              ['reference_date_exclusive', 'bundesland', 'pv_net_mw', 'wind_onshore_net_mw', 'wind_offshore_net_mw', 'basis'],
              [dict(reference_date_exclusive=str(d), bundesland=land, **{k + '_net_mw': v for k, v in row.items()},
                    basis=f'reconstructed_from_{snapshot}_snapshot_NOT_as_of')
               for (d, land), row in sorted(series.items())])
    write_json(args.output / 'mastr_quality.json', report)
    write_json(args.output / 'source_manifest.json', sources)
    print('neueste Referenz:', max(d for d, _ in series), flush=True)
    print(args.output)


if __name__ == '__main__':
    main()
