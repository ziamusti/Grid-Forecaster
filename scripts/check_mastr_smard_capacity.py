"""Read-only capacity audit; downloads references, never modifies model inputs."""
import csv
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/smard_capacity_audit_2026-10-22'
OUT = ROOT / 'reports/mastr_smard_capacity_2026-10-22'
INPUT = ROOT / 'data/processed/stage0_v2_sunshine/mastr_monthly_reconstructed.csv'
SERIES = {'pv': (188, 'Photovoltaik'), 'wind_onshore': (186, 'Wind Onshore'),
          'wind_offshore': (4076, 'Wind Offshore')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []

    def get(path, name):
        url = 'https://www.smard.de' + path
        dest = RAW / name
        cached = dest.exists()
        if cached:
            content = dest.read_bytes()
        else:
            for attempt in range(4):
                try:
                    with urlopen(url, timeout=45) as response:
                        content = response.read()
                    break
                except OSError:
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
            json.loads(content)
            dest.write_bytes(content)
        manifest.append(dict(url=url, file=str(dest.relative_to(ROOT)),
                             sha256=sha(content), reused_cache=cached,
                             checked_at_utc=datetime.now(timezone.utc).isoformat()))
        return json.loads(content)

    config = get('/app/chart_configuration/market_data_configuration.json', 'configuration.json')
    translations = get('/app/assets/translations/lang-de.json', 'translations_de.json')
    description = translations['MM-Beschreibung.Installierte Erzeugungsleistung']
    category = next(s for m in config['main'] for s in m['sub'] if s['id'] == 3)
    modules = {m['data_id']: m for group in category['module'].values() for m in group}
    original = INPUT.read_bytes()
    with INPUT.open() as f:
        capacities = {r['reference_date_exclusive']: r for r in csv.DictReader(f)}
    rows = []
    for tech, (series_id, label) in SERIES.items():
        module = modules[series_id]
        assert module['name'] == 'MM-Bausteine.' + label
        assert module['unit'] == 'VD-Einheit.MW'
        assert module['source_resolution'] == 'year' and 'DE' in module['region']
        index = get('/app/chart_data/%s/DE/index_year.json' % series_id, '%s_index.json' % series_id)
        seen = set()
        for stamp in index['timestamps']:
            year = datetime.fromtimestamp(stamp / 1000, ZoneInfo('Europe/Berlin')).year
            if not 2015 <= year <= 2026:
                continue
            data = get('/app/chart_data/{0}/DE/{0}_DE_year_{1}.json'.format(series_id, stamp),
                       '%s_%s.json' % (series_id, stamp))
            for ts, value in data['series']:
                date = datetime.fromtimestamp(ts / 1000, ZoneInfo('Europe/Berlin'))
                if not 2015 <= date.year <= 2026:
                    continue
                assert (date.month, date.day, date.hour, date.minute) == (1, 1, 0, 0)
                assert ts not in seen
                seen.add(ts)
                ref = date.date().isoformat()
                actual = float(capacities[ref][tech + '_net_mw'])
                valid = value is not None and math.isfinite(value) and value > 0
                # 2025+ year-label match is NOT a verified identical reference date.
                confirmed_date = date.year <= 2024
                delta = actual - value if valid and confirmed_date else None
                rows.append(dict(year=date.year, technology=tech, smard_series_id=series_id,
                    smard_year_label_berlin=ref, mastr_reference_date_exclusive=ref,
                    smard_mw=value, mastr_mw=actual,
                    difference_mw=round(delta, 6) if delta is not None else '',
                    difference_pct=round(100 * delta / value, 4) if delta is not None else '',
                    date_status='jan1_documented' if confirmed_date else 'reference_date_unconfirmed',
                    scope_status='not_identical_SMARD_description_min_1MW_MaStR_all_sizes'))
    rows.sort(key=lambda r: (r['year'], r['technology']))
    assert len(rows) == 36, 'Expected three annual series for 2015–2026; inspect missing years'
    assert INPUT.read_bytes() == original, 'Input must remain unchanged'
    with (OUT / 'comparison.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = dict(smard_description=description, input_file=str(INPUT.relative_to(ROOT)),
                  input_sha256=sha(original), rows=len(rows),
                  arithmetic_rows=sum(r['difference_pct'] != '' for r in rows),
                  caveats=['Not an independent validation: SMARD uses MaStR from 2025',
                           'SMARD description says minimum 1MW; cannot assume same population',
                           'MaStR strict-before Jan1 vs SMARD Jan1 may differ for Jan1 events',
                           'Snapshot reconstruction is not historical publication vintage',
                           'No automatic correction or acceptance threshold; no training'],
                  sources=manifest)
    (OUT / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for r in rows:
        print(r['year'], r['technology'], 'SMARD', r['smard_mw'], 'MaStR', r['mastr_mw'],
              'delta%', r['difference_pct'], r['date_status'])
    print('Saved:', OUT, '\nInput unchanged; no model trained.')


if __name__ == '__main__':
    main()
