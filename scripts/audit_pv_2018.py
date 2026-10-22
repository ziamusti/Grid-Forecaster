"""Diagnostic only: stream solar register, leave all model data untouched."""
import csv
import json
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from prepare_stage0 import xml_records, number, digest

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / 'archive/legacy_2026-10-20/data/raw/mastr/Gesamtdatenexport_20261020_26.2.zip'
BASE = ROOT / 'data/processed/stage0_v2_sunshine/mastr_monthly_reconstructed.csv'
OUT = ROOT / 'reports/mastr_smard_capacity_2026-10-22/pv_2018_diagnostic.json'


def main():
    before = digest(BASE)
    counts, net, gross = Counter(), Counter(), Counter()
    boundary = date(2018, 1, 1)
    snapshot = date(2026, 10, 20)

    def add(group, n, g):
        counts[group] += 1
        net[group] += (n or 0) / 1000
        gross[group] += (g or 0) / 1000
        if g is None:
            counts[group + '_gross_missing'] += 1

    with zipfile.ZipFile(ZIP) as z:
        for filename in sorted(n for n in z.namelist() if n.startswith('EinheitenSolar_')):
            for r in xml_records(z, filename, 'EinheitSolar'):
                n, g = number(r.get('Nettonennleistung')), number(r.get('Bruttoleistung'))
                counts['all_solar'] += 1
                reason = None
                if r.get('Land') != '84': reason = 'not_germany'
                elif r.get('EinheitSystemstatus') not in ('472', '484'): reason = 'inactive_system'
                elif r.get('EinheitBetriebsstatus') == '31': reason = 'planned'
                elif r.get('EinheitBetriebsstatus') not in ('35', '37', '38'): reason = 'unknown_status'
                elif n is None or n <= 0: reason = 'missing_nonpositive_net'
                start = stop = None
                try:
                    start = date.fromisoformat(r.get('Inbetriebnahmedatum') or '')
                    stop = date.fromisoformat(r['DatumEndgueltigeStilllegung']) if r.get('DatumEndgueltigeStilllegung') else None
                except ValueError:
                    if reason is None: reason = 'invalid_date'
                if reason is None:
                    if start < date(1954, 1, 1) or start > snapshot: reason = 'implausible_start'
                    elif stop and (stop < start or stop > snapshot): reason = 'invalid_retirement'
                    elif r.get('EinheitBetriebsstatus') == '38' and not stop: reason = 'retired_without_date'
                    elif r.get('EinheitBetriebsstatus') == '35' and stop: reason = 'operating_with_retirement'
                if reason:
                    add('excluded_' + reason, n, g)
                    if start and start < boundary and r.get('Land') == '84':
                        add('excluded_pre2018_' + reason, n, g)
                    continue
                if start < boundary:
                    add('commissioned_before_2018', n, g)
                    if stop and stop < boundary:
                        add('retired_before_2018', n, g)
                    else:
                        add('active_at_boundary', n, g)
                        add('net_below_1mw' if n < 1000 else 'net_atleast_1mw', n, g)
                        add('current_status_' + r['EinheitBetriebsstatus'], n, g)
                        if g is not None and n > g: add('net_above_gross', n, g)
                if start == boundary: add('commissioned_on_jan1', n, g)
                if stop == boundary and start <= boundary: add('retired_on_jan1', n, g)
            print(filename, counts['all_solar'], flush=True)
    with BASE.open() as f:
        old = next(float(r['pv_net_mw']) for r in csv.DictReader(f)
                   if r['reference_date_exclusive'] == '2018-01-01')
    assert abs(net['active_at_boundary'] - old) < 0.00001
    assert digest(BASE) == before
    smard = json.loads((ROOT / 'data/raw/smard_capacity_audit_2026-10-22/188_1514761200000.json').read_text())['series'][0][1]
    result = dict(reference='strictly before 2018-01-01', input=str(ZIP),
                  zip_sha256=digest(ZIP), base_sha256=before, smard_mw=smard,
                  counts=dict(counts), net_mw=dict(net), gross_mw=dict(gross),
                  net_delta_pct=(net['active_at_boundary']/smard-1)*100,
                  gross_delta_pct=(gross['active_at_boundary']/smard-1)*100,
                  unchanged_base=True, limitations=['Present snapshot, not historical vintage',
                      'Gross missing values summed as zero and separately counted',
                      '1MW split is unit-based, not necessarily SMARD plant aggregation',
                      'No personal unit information exported; no training or correction'])
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
