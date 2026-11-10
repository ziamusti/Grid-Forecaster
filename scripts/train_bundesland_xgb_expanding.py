"""XGBoost Bundesland model (pooled), expanding training window from 2015.

Six separate models per step (CO2 + five renewable sources), one model for all
16 Bundeslaender ("bundesland" one-hot encoded). Renewable share = sum of the
five predicted sources. Same scheme as the national main model: 2015-2017 ->
2018, ..., 2015-2025 -> 2026, new model from scratch per step, fixed XGBoost
parameters, targets standardized with training mean/std.
--stage 1: 19 inputs (weather, capacity, calendar, Bundesland)
--stage 2: 45 inputs (+ national 168 h lags incl. price, own-state generation 336 h earlier)
Both stages use identical rows (all targets and all stage-2 inputs present).
"""
import argparse
import json
import os
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from bundesland import BUNDESLAENDER
from train_hist_expanding import XGB_PARAMS
from train_linear_expanding import FIRST_YEAR, TEST_YEARS, metrics

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/bundesland_pooled_v2'
SOURCE_TARGETS = ['target_wind_onshore_share_pct', 'target_solar_share_pct', 'target_biomass_share_pct',
                  'target_hydro_share_pct', 'target_other_renewables_share_pct']
MODELLED = ['target_co2_gco2eq_kwh', *SOURCE_TARGETS]
TOTAL = 'target_renewable_share_pct'
# Histogram XGBoost gives the same trees for any thread count up to float
# summation order; more threads only to keep 108 fits on ~1.5M rows feasible.
PARAMS = dict(XGB_PARAMS, n_jobs=min(8, os.cpu_count() or 1))


def model(features, categories):
    numeric = [f for f in features if f not in categories]
    transform = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('calendar', OneHotEncoder(categories=[list(range(24)), list(range(7)), list(range(1, 13)), list(BUNDESLAENDER)],
                                   drop='first', sparse_output=False, handle_unknown='error'), categories)])
    return Pipeline([('preprocess', transform), ('regression', XGBRegressor(**PARAMS))])


def main(stage):
    out = ROOT / f'reports/xgboost_bundesland_stage{stage}_expanding_v1'
    if out.exists():
        raise FileExistsError(f'{out} existiert bereits; kein Ueberschreiben.')
    schema = json.loads((DATA / 'feature_schema.json').read_text())
    features, categories = schema[f'stage{stage}'], schema['categories']
    assert len(features) == {1: 19, 2: 45}[stage]
    assert schema['targets'] == [MODELLED[0], 'target_wind_onshore_share_pct', 'target_solar_share_pct',
                                 'target_biomass_share_pct', 'target_hydro_share_pct',
                                 'target_other_renewables_share_pct', TOTAL]

    data, excluded = {}, {}
    for year in range(FIRST_YEAR, 2027):
        frame = pd.read_csv(DATA / f'hourly_{year}.csv', usecols=['target_time_utc', *schema['stage2'], *schema['targets']])
        # Same rows for both stages; station2 is NaN for one-station states (XGBoost handles NaN).
        required = [f for f in schema['stage2'] if not f.startswith('station2__')]
        mask = frame[schema['targets']].notna().all(axis=1) & frame[required].notna().all(axis=1)
        excluded[year] = int((~mask).sum())
        data[year] = frame.loc[mask].reset_index(drop=True)

    out.mkdir(parents=True)
    started = time.monotonic()
    results, steps = [], []
    for test_year in TEST_YEARS:
        train_years = list(range(FIRST_YEAR, test_year))
        train = pd.concat([data[y] for y in train_years], ignore_index=True)
        test = data[test_year]
        predictions = test[['target_time_utc', 'bundesland']].copy()
        for target in MODELLED:
            y = train[target].to_numpy(float)
            mean, std = y.mean(), y.std()
            fitted = model(features, categories).fit(train[features], (y - mean) / std)
            assert fitted.named_steps['regression'].get_booster().num_boosted_rounds() == 100
            predicted = fitted.predict(test[features]) * std + mean
            assert np.isfinite(predicted).all()
            predictions[f'actual_{target}'] = test[target].to_numpy(float)
            predictions[f'predicted_{target}'] = predicted
        predictions[f'actual_{TOTAL}'] = test[TOTAL].to_numpy(float)
        predictions[f'predicted_{TOTAL}'] = predictions[[f'predicted_{t}' for t in SOURCE_TARGETS]].sum(axis=1)
        for target in [*MODELLED, TOTAL]:
            results.append(dict(test_year=test_year, bundesland='alle', target=target, train_n=len(train),
                                **metrics(predictions[f'actual_{target}'].to_numpy(), predictions[f'predicted_{target}'].to_numpy())))
            for land, part in predictions.groupby('bundesland'):
                results.append(dict(test_year=test_year, bundesland=land, target=target, train_n=len(train),
                                    **metrics(part[f'actual_{target}'].to_numpy(), part[f'predicted_{target}'].to_numpy())))
        steps.append(dict(test_year=test_year, train_years=train_years, train_n=len(train), test_n=len(test)))
        predictions.to_csv(out / f'predictions_{test_year}.csv', index=False)
        r2 = {r['target']: r['r2'] for r in results if r['test_year'] == test_year and r['bundesland'] == 'alle'}
        print(test_year, f'Stufe {stage}', 'gelernt aus', f'{train_years[0]}-{train_years[-1]}', 'n=', len(train),
              'R2 CO2', round(r2[MODELLED[0]], 3), 'R2 Gruen', round(r2[TOTAL], 3),
              f'{time.monotonic() - started:.0f}s', flush=True)

    table = pd.DataFrame(results)
    table.to_csv(out / 'metrics.csv', index=False)
    (out / 'run.json').write_text(json.dumps(dict(
        method='xgboost, pooled over 16 Bundeslaender, one model per target, fixed parameters, no tuning',
        stage=stage, scheme='expanding window from 2015, new model per step, tested on the following year',
        data='bundesland_pooled_v2', params=PARAMS, features=features, modelled_targets=MODELLED,
        renewable_share='sum of the five predicted sources', target_scaling='standardized with training mean/std',
        rows='identical for both stages (all targets and all stage-2 inputs present)',
        steps=steps, excluded_rows_per_year=excluded,
        versions=dict(python=platform.python_version(), sklearn=sklearn.__version__, xgboost=xgboost.__version__,
                      numpy=np.__version__, pandas=pd.__version__),
        duration_seconds=time.monotonic() - started, complete=True), indent=2, ensure_ascii=False))
    pooled = table[table.bundesland == 'alle'].pivot(index='test_year', columns='target', values='r2').round(3)
    pd.set_option('display.width', 220)
    print(pooled.to_string())
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=int, choices=[1, 2], required=True)
    main(parser.parse_args().stage)
