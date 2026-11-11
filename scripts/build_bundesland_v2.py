"""Build the Bundesland training table v2 (no training).

Per (hour, Bundesland), from the raw Energy-Charts weekly generation files:
- targets: CO2 (UBA factors, same as compute_bundesland_targets.py) and the
  shares of five renewable sources (wind onshore, solar, biomass, hydro =
  run-of-river + reservoir, other = geothermal); renewable share = their sum.
  Wind offshore is not assigned to any Bundesland by Energy-Charts.
- stage-2 inputs: the Bundesland's own generation per technology 336 h
  (14 days) earlier (Energy-Charts publishes per-state data ~6 days late, so
  168 h would not be available live), and national inputs 168 h earlier
  (12 SMARD technologies, grid load, day-ahead price) from stage0_v6.
Stage-1 inputs (weather, capacity, calendar, Bundesland) are copied unchanged
from bundesland_pooled_v1.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bundesland import BUNDESLAND_SUFFIX
from compute_bundesland_targets import FACTORS, RENEWABLE
from train_bundesland_stage0 import CATEGORIES, NUMERIC_FEATURES

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/energycharts_bundesland'
BASE = ROOT / 'data/processed/bundesland_pooled_v1'
OLD_TARGETS = ROOT / 'data/processed/bundesland_targets'
NATIONAL = ROOT / 'data/processed/stage0_v6_renewable_breakdown'
OUT = ROOT / 'data/processed/bundesland_pooled_v2'
TECHS = list(FACTORS)
SOURCES = {'wind_onshore': ['wind_onshore'], 'solar': ['solar'], 'biomass': ['biomass'],
           'hydro': ['hydro_run-of-river', 'hydro_water_reservoir'], 'other_renewables': ['geothermal']}
NATIONAL_LAGS = ['biomass_mwh_lag168h', 'hydro_mwh_lag168h', 'wind_offshore_mwh_lag168h',
                 'wind_onshore_mwh_lag168h', 'solar_mwh_lag168h', 'other_renewables_mwh_lag168h',
                 'nuclear_mwh_lag168h', 'lignite_mwh_lag168h', 'hard_coal_mwh_lag168h', 'gas_mwh_lag168h',
                 'pumped_storage_mwh_lag168h', 'other_conventional_mwh_lag168h', 'grid_load_mwh_lag168h',
                 'price_eur_mwh_lag168h']
STATE_LAGS = [f'state_{t}_mw_lag336h' for t in TECHS]
STAGE1 = NUMERIC_FEATURES + CATEGORIES
STAGE2 = STAGE1 + NATIONAL_LAGS + STATE_LAGS
TARGETS = ['target_co2_gco2eq_kwh', *[f'target_{s}_share_pct' for s in SOURCES], 'target_renewable_share_pct']
assert set(sum(SOURCES.values(), [])) == set(RENEWABLE)


def load_generation(paths=None):
    # Long table: one row per (hour, Bundesland), one column per technology (MW).
    land_of = {v: k for k, v in BUNDESLAND_SUFFIX.items()}
    parts = []
    for path in sorted(paths if paths is not None else RAW.glob('20*/week_*.json')):
        data = json.loads(path.read_text())
        times = pd.to_datetime(data[0]['xAxisValues'], unit='ms', utc=True)
        by_id = {d['id']: d for d in data}
        for suffix, land in land_of.items():
            frame = pd.DataFrame({'target_time_utc': times, 'bundesland': land})
            present = False
            for tech in TECHS:
                series = by_id.get(f'{tech}_{suffix}')
                # A technology missing for a state means no such plants there (0);
                # a missing value inside an existing series stays NaN.
                values = series.get('data', []) if series else []
                column = np.zeros(len(times)) if series is None else np.full(len(times), np.nan)
                for i, v in enumerate(values[:len(times)]):
                    if v is not None:
                        column[i] = v
                present |= series is not None
                frame[tech] = column
            if present:
                parts.append(frame)
    generation = pd.concat(parts, ignore_index=True)
    # Consecutive weekly files can overlap by one hour; keep the later file.
    generation = generation.drop_duplicates(['target_time_utc', 'bundesland'], keep='last')
    return generation.set_index(['target_time_utc', 'bundesland']).sort_index()


def targets_from(generation):
    total = generation[TECHS].sum(axis=1, min_count=len(TECHS))
    valid = total > 0
    out = pd.DataFrame(index=generation.index)
    out['target_co2_gco2eq_kwh'] = (generation[TECHS] * pd.Series(FACTORS)).sum(axis=1, min_count=len(TECHS)) / total
    for source, techs in SOURCES.items():
        out[f'target_{source}_share_pct'] = 100 * generation[techs].sum(axis=1, min_count=len(techs)) / total
    out['target_renewable_share_pct'] = out[[f'target_{s}_share_pct' for s in SOURCES]].sum(axis=1, min_count=len(SOURCES))
    return out.where(valid)


def main():
    if OUT.exists():
        raise FileExistsError(f'{OUT} existiert bereits; kein Ueberschreiben.')
    generation = load_generation()
    targets = targets_from(generation)
    lagged = generation[TECHS].copy()
    lagged.index = lagged.index.set_levels(lagged.index.levels[0] + pd.Timedelta(hours=336), level=0)
    lagged.columns = STATE_LAGS
    OUT.mkdir(parents=True)
    report = {}
    for year in range(2015, 2027):
        base = pd.read_csv(BASE / f'hourly_{year}.csv').drop(columns=['target_co2_gco2eq_kwh', 'target_renewable_share_pct'])
        base['target_time_utc'] = pd.to_datetime(base.target_time_utc, utc=True)
        national = pd.read_csv(NATIONAL / f'hourly_{year}.csv', usecols=['target_time_utc', *NATIONAL_LAGS])
        national['target_time_utc'] = pd.to_datetime(national.target_time_utc, utc=True)
        frame = (base.merge(national, on='target_time_utc', how='left', validate='many_to_one')
                 .join(lagged, on=['target_time_utc', 'bundesland'])
                 .join(targets, on=['target_time_utc', 'bundesland']))
        assert len(frame) == len(base)
        # Consistency check against the targets the old Bundesland model used.
        old = pd.read_csv(OLD_TARGETS / f'{year}.csv')
        old['target_time_utc'] = pd.to_datetime(old.target_time_utc, utc=True)
        check = frame.merge(old, on=['target_time_utc', 'bundesland'], suffixes=('', '_old')).dropna(
            subset=['target_co2_gco2eq_kwh', 'target_co2_gco2eq_kwh_old'])
        report[year] = dict(rows=len(frame), rows_with_all_targets=int(frame[TARGETS].notna().all(axis=1).sum()),
                            rows_with_stage2_inputs=int(frame[NATIONAL_LAGS + STATE_LAGS].notna().all(axis=1).sum()),
                            max_abs_diff_co2_vs_old=float((check.target_co2_gco2eq_kwh - check.target_co2_gco2eq_kwh_old).abs().max()),
                            max_abs_diff_renewable_vs_old=float((check.target_renewable_share_pct - check.target_renewable_share_pct_old).abs().max()))
        frame['target_time_utc'] = frame.target_time_utc.dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        frame.to_csv(OUT / f'hourly_{year}.csv', index=False)
        print(year, report[year], flush=True)
    (OUT / 'feature_schema.json').write_text(json.dumps(dict(
        stage1=STAGE1, stage2=STAGE2, categories=CATEGORIES, targets=TARGETS, sources=SOURCES,
        renewable_share='sum of the five source shares', national_lags='168 h (stage0_v6)',
        state_lags='336 h, Energy-Charts per-state generation (MW)', report=report), indent=2, ensure_ascii=False))
    print(OUT)


if __name__ == '__main__':
    main()
