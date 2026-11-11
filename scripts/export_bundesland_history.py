"""Slim, compressed copy of the Bundesland stage-2 test predictions for the dashboard (no training).

The full prediction files of xgboost_bundesland_stage2_expanding_v1 are ~36 MB per
year and stay local (.gitignore). This keeps only what the dashboard shows, rounded
to 2 decimals, as gzip CSV per test year: actual CO2 and renewable share, predicted
CO2 and the five source shares (cut off at 0); renewable share = their sum.
"""
from pathlib import Path

import pandas as pd

from train_bundesland_xgb_expanding import SOURCE_TARGETS
from train_linear_expanding import TEST_YEARS

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'reports/xgboost_bundesland_stage2_expanding_v1'
OUT = RUN / 'dashboard'


def main():
    if OUT.exists():
        raise FileExistsError(f'{OUT} existiert bereits; kein Ueberschreiben.')
    OUT.mkdir()
    for year in TEST_YEARS:
        p = pd.read_csv(RUN / f'predictions_{year}.csv')
        slim = pd.DataFrame({'target_time_utc': p.target_time_utc, 'bundesland': p.bundesland,
                             'actual_co2': p.actual_target_co2_gco2eq_kwh,
                             'actual_renewable': p.actual_target_renewable_share_pct,
                             'predicted_co2': p.predicted_target_co2_gco2eq_kwh})
        for target in SOURCE_TARGETS:
            slim['predicted_' + target.removeprefix('target_').removesuffix('_share_pct')] = p['predicted_' + target].clip(lower=0)
        slim.round(2).to_csv(OUT / f'history_{year}.csv.gz', index=False)
        print(year, len(slim), flush=True)


if __name__ == '__main__':
    main()
