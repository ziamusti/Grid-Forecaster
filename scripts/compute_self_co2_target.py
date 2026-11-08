"""Replace the Electricity Maps CO2 target with a self-computed one; no training.

Electricity Maps' terms prohibit using its data to train an ML model without
written consent (see docs/bachelorarbeit_protokoll.md). This script builds a
drop-in replacement Stage-0 version where target_co2_gco2eq_kwh is computed
from the SMARD generation mix (already used elsewhere in this project,
CC BY 4.0) and official UBA per-technology emission factors, instead of
reading it from Electricity Maps. Every other column (all 137 input
features, target_renewable_share_pct, price feature, metadata) is copied
unchanged from stage0_v4_oct26 — only the CO2 target and its
estimation-status columns are replaced.

Emission factors (g CO2/kWh), researched and logged in
docs/bachelorarbeit_protokoll.md:
- lignite 1119, hard_coal 860, gas 394: UBA "Entwicklung der spezifischen
  Treibhausgas-Emissionen des deutschen Strommix 1990-2025" (Climate Change
  16/2026), Tabelle 4, 2025 (vorlaeufig).
- nuclear, hydro, solar, wind_onshore, wind_offshore, biomass,
  other_renewables: 0 (direct emissions; UNFCCC reporting convention for
  renewables, explicitly stated in the same report).
- pumped_storage: 0 (not primary generation; re-dispatch of electricity
  already accounted for at the time it was originally generated).
- other_conventional: 2000.1, self-derived (not an official single UBA
  figure) as a 4-year average (2020, 2022, 2024, 2025) of
  (energy-charts.info Oel + Muell(fossil) + Sonstige emissions, Mio t) /
  (SMARD "Sonstige Konventionelle" generation, same years).
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from prepare_stage0 import TECH, local_to_utc, smard, source, BERLIN

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/stage0_v4_oct26'
EXTENSION_SMARD_DIR = ROOT / 'data/raw/smard_range/20261101T171602Z'
UTC = timezone.utc

FACTORS = {
    'lignite': 1119.0, 'hard_coal': 860.0, 'gas': 394.0,
    'other_conventional': 2000.1,
    'nuclear': 0.0, 'hydro': 0.0, 'solar': 0.0,
    'wind_onshore': 0.0, 'wind_offshore': 0.0, 'biomass': 0.0,
    'other_renewables': 0.0, 'pumped_storage': 0.0,
}
assert set(FACTORS) == set(TECH.values())


def co2_intensity(row):
    if any(row[k] is None for k in TECH.values()):
        return None
    total = sum(row[k] for k in TECH.values())
    if total <= 0:
        return None
    return sum(row[k] * FACTORS[k] for k in TECH.values()) / total


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


def _number(text):
    text = text.strip()
    if not text or text == '-':
        return None
    return float(text.replace('.', '').replace(',', '.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/processed/stage0_v5_selfco2')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')

    sources = []
    gen, *_ = smard('generation', sources)
    extension = load_extension_smard()
    overlap = set(gen) & set(extension)
    gen.update(extension)
    print('Archiv-Stunden:', len(gen) - len(extension), 'Erweiterungs-Stunden:', len(extension),
          'Ueberschneidung (Erweiterung gewinnt):', len(overlap))

    args.output.mkdir(parents=True)
    missing_total = 0
    row_total = 0
    for path in sorted(BASE.glob('hourly_*.csv')):
        with path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        missing = 0
        for row in rows:
            t = datetime.fromisoformat(row['target_time_utc'].replace('Z', '+00:00'))
            value = co2_intensity(gen[t]) if t in gen else None
            if value is None:
                missing += 1
            row['target_co2_gco2eq_kwh'] = '' if value is None else str(round(value, 6))
            row['co2_is_estimated'] = '0'
            row['co2_estimation_method'] = 'self_computed_smard_uba_v1'
            row['co2_updated_at'] = datetime.now(UTC).isoformat()
            features_complete = row['features_complete'] == '1'
            eligible_co2 = int(features_complete and value is not None)
            row['eligible_co2_nonestimated'] = str(eligible_co2)
            row['eligible_both'] = str(int(eligible_co2 and row['eligible_renewable'] == '1'))
        missing_total += missing
        row_total += len(rows)
        with (args.output / path.name).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(path.name, 'Zeilen:', len(rows), 'ohne CO2-Wert:', missing)

    print('Gesamt:', row_total, 'Zeilen, davon ohne CO2-Wert:', missing_total)

    for name in ['feature_schema.json', 'splits.json', 'weather_metadata.json',
                 'mastr_monthly_reconstructed.csv', 'mastr_quality.json']:
        src = BASE / name
        if src.exists():
            (args.output / name).write_bytes(src.read_bytes())

    manifest = json.loads((BASE / 'source_manifest.json').read_text()) if (BASE / 'source_manifest.json').exists() else []
    manifest.extend(sources)
    (args.output / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))

    report = dict(created_utc=datetime.now(UTC).isoformat(), base=str(BASE.relative_to(ROOT)),
                  target_replaced='target_co2_gco2eq_kwh', target_source='self_computed_smard_uba_v1',
                  factors_gco2_per_kwh=FACTORS, rows_total=row_total, rows_missing_co2=missing_total,
                  note='Replaces Electricity Maps CO2 target; all other columns unchanged from base.')
    (args.output / 'self_co2_report.json').write_text(json.dumps(report, indent=2))
    print(args.output)


if __name__ == '__main__':
    main()
