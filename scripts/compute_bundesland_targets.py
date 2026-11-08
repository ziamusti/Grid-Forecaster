"""Compute CO2-intensity and renewable-share targets per Bundesland; no training.

Reads the already-downloaded per-Bundesland weekly generation JSON files
(data/raw/energycharts_bundesland) and, for every (hour, Bundesland) pair,
computes:

    target_co2_gco2eq_kwh = sum(generation[tech] * factor[tech]) / total
    target_renewable_share_pct = 100 * sum(generation[tech] for tech in RENEWABLE) / total

using the same UBA-based factors as the national self-computed CO2 model,
plus the two additionally derived factors (Oel, Muell) logged in
docs/bachelorarbeit_protokoll.md. Output: one CSV per year, long format
(one row per hour per Bundesland).
"""
import csv
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundesland import BUNDESLAND_SUFFIX

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/energycharts_bundesland'
OUT = ROOT / 'data/processed/bundesland_targets'
UTC = timezone.utc

FACTORS = {
    'fossil_brown_coal_lignite': 1119.0, 'fossil_hard_coal': 860.0, 'fossil_gas': 394.0,
    'fossil_oil': 1971.0, 'waste': 850.9,
    'biomass': 0.0, 'geothermal': 0.0, 'hydro_run-of-river': 0.0,
    'hydro_water_reservoir': 0.0, 'hydro_pumped_storage': 0.0, 'solar': 0.0, 'wind_onshore': 0.0,
}
RENEWABLE = ('biomass', 'geothermal', 'hydro_run-of-river', 'hydro_water_reservoir', 'solar', 'wind_onshore')
SUFFIX_TO_LAND = {v: k for k, v in BUNDESLAND_SUFFIX.items()}


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    OUT.mkdir(parents=True)
    for year_dir in sorted(RAW.glob('20*')):
        year = year_dir.name
        rows = []
        for path in sorted(year_dir.glob(f'week_{year}_*.json')):
            data = json.loads(path.read_text())
            by_id = {d['id']: d for d in data}
            times = data[0]['xAxisValues']
            n = len(times)
            # accumulate per (index, land) -> {tech: value}
            per_land = {land: [dict() for _ in range(n)] for land in SUFFIX_TO_LAND.values()}
            for tech in FACTORS:
                for suffix, land in SUFFIX_TO_LAND.items():
                    series = by_id.get(f'{tech}_{suffix}')
                    if series is None:
                        continue
                    values = series.get('data', [])
                    for i, v in enumerate(values[:n]):
                        if v is not None:
                            per_land[land][i][tech] = v
            for i, ms in enumerate(times):
                t = datetime.fromtimestamp(ms / 1000, tz=UTC)
                for land, hours in per_land.items():
                    gen = hours[i]
                    if not gen:
                        continue
                    total = sum(gen.values())
                    if total <= 0:
                        continue
                    co2 = sum(gen.get(k, 0.0) * f for k, f in FACTORS.items()) / total
                    renewable = 100 * sum(gen.get(k, 0.0) for k in RENEWABLE) / total
                    rows.append((t.isoformat().replace('+00:00', 'Z'), land, round(co2, 6), round(renewable, 6)))
        rows.sort(key=lambda r: (r[0], r[1]))
        with (OUT / f'{year}.csv').open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['target_time_utc', 'bundesland', 'target_co2_gco2eq_kwh', 'target_renewable_share_pct'])
            writer.writerows(rows)
        print(year, 'Zeilen:', len(rows), flush=True)
    print(OUT)


if __name__ == '__main__':
    main()
