"""XGBoost, national model, self-computed CO2, expanding training window from 2015.

Eight targets per hour: CO2 (self-computed from SMARD + UBA factors, from
stage0_v5_selfco2), renewable share and its six sources (from
stage0_v6_renewable_breakdown). Both tables are built from stage0_v4_oct26
and share the 137 inputs; hours are checked to be identical.

Two variants on identical rows, inputs, preprocessing and scheme
(2015-2017 -> 2018, ..., 2015-2025 -> 2026, new model from scratch per step):
- separate: one XGBoost model per target (8 models per step)
- --multi:  one XGBoost model for all 8 targets (multi_strategy='multi_output_tree')
Targets are standardized with training-year mean/std before fitting and
transformed back afterwards (needed for the multi-output loss, where CO2
would otherwise dominate; applied to both variants for identical handling).
"""
import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from train_hist_expanding import XGB_PARAMS
from train_linear_expanding import FIRST_YEAR, PRICE_FEATURE, RENEWABLE_SOURCES, TEST_YEARS, metrics, pipeline

ROOT = Path(__file__).resolve().parents[1]
FEATURES_DATA = ROOT / 'data/processed/stage0_v6_renewable_breakdown'
CO2_DATA = ROOT / 'data/processed/stage0_v5_selfco2'
CO2 = 'target_co2_gco2eq_kwh'
TOTAL = 'target_renewable_share_pct'
TARGETS = [CO2, TOTAL, *RENEWABLE_SOURCES]


def load_year(year, features):
    frame = pd.read_csv(FEATURES_DATA / f'hourly_{year}.csv',
                        usecols=['target_time_utc', *features, TOTAL, *RENEWABLE_SOURCES])
    co2 = pd.read_csv(CO2_DATA / f'hourly_{year}.csv',
                      usecols=['target_time_utc', 'eligible_both', 'co2_estimation_method', CO2])
    assert frame.target_time_utc.tolist() == co2.target_time_utc.tolist()
    assert (co2.co2_estimation_method == 'self_computed_smard_uba_v1').all()
    frame[CO2] = co2[CO2].to_numpy()
    frame['eligible_both'] = co2.eligible_both.to_numpy()
    mask = ((frame.eligible_both == 1) & frame[PRICE_FEATURE].notna()
            & frame[TARGETS].notna().all(axis=1) & frame[features].notna().all(axis=1))
    rows = frame.loc[mask].reset_index(drop=True)
    assert np.isfinite(rows[features].to_numpy(float)).all() and np.isfinite(rows[TARGETS].to_numpy(float)).all()
    return rows, int((~mask).sum())


def fit_predict(features, x_train, y_train, x_test, multi):
    mean, std = y_train.mean(axis=0), y_train.std(axis=0)
    z_train = (y_train - mean) / std
    preprocess = pipeline(features).named_steps['preprocess']
    with threadpool_limits(limits=1):
        if multi:
            model = Pipeline([('preprocess', preprocess),
                              ('regression', XGBRegressor(**XGB_PARAMS, multi_strategy='multi_output_tree'))])
            model.fit(x_train, z_train)
            assert model.named_steps['regression'].get_booster().num_boosted_rounds() == 100
            z_test = model.predict(x_test)
        else:
            columns = []
            for k in range(y_train.shape[1]):
                model = Pipeline([('preprocess', pipeline(features).named_steps['preprocess']),
                                  ('regression', XGBRegressor(**XGB_PARAMS))])
                model.fit(x_train, z_train[:, k])
                assert model.named_steps['regression'].get_booster().num_boosted_rounds() == 100
                columns.append(model.predict(x_test))
            z_test = np.column_stack(columns)
    return z_test * std + mean


def main(multi=False):
    variant = 'multi' if multi else 'separate'
    out = ROOT / f'reports/xgboost_selfco2_{variant}_expanding_v1'
    if out.exists():
        raise FileExistsError(f'{out} existiert bereits; kein Ueberschreiben.')
    schema = json.loads((FEATURES_DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f != 'is_weekend']
    assert len(features) == 137 and PRICE_FEATURE in features

    data, excluded = {}, {}
    for year in range(FIRST_YEAR, 2027):
        data[year], excluded[year] = load_year(year, features)

    out.mkdir(parents=True)
    started = time.monotonic()
    results, steps = [], []
    for test_year in TEST_YEARS:
        train_years = list(range(FIRST_YEAR, test_year))
        train = pd.concat([data[y] for y in train_years], ignore_index=True)
        test = data[test_year]
        predicted = fit_predict(features, train[features].to_numpy(float), train[TARGETS].to_numpy(float),
                                test[features].to_numpy(float), multi)
        assert predicted.shape == (len(test), len(TARGETS)) and np.isfinite(predicted).all()
        predictions = test[['target_time_utc']].copy()
        for k, target in enumerate(TARGETS):
            actual = test[target].to_numpy(float)
            predictions[f'actual_{target}'] = actual
            predictions[f'predicted_{target}'] = predicted[:, k]
            results.append(dict(test_year=test_year, target=target, train_years=f'{train_years[0]}-{train_years[-1]}',
                                train_n=len(train), **metrics(actual, predicted[:, k])))
        # Bottom-up: renewable share as the sum of the six predicted sources.
        bottom_up = predictions[[f'predicted_{t}' for t in RENEWABLE_SOURCES]].sum(axis=1).to_numpy()
        results.append(dict(test_year=test_year, target='renewable_share_bottom_up_sum_of_sources',
                            train_years=f'{train_years[0]}-{train_years[-1]}', train_n=len(train),
                            **metrics(test[TOTAL].to_numpy(float), bottom_up)))
        gap = np.abs(bottom_up - predictions[f'predicted_{TOTAL}'].to_numpy())
        steps.append(dict(test_year=test_year, train_years=train_years, train_n=len(train), test_n=len(test),
                          mean_abs_gap_sum_of_sources_vs_total=float(gap.mean()),
                          max_abs_gap_sum_of_sources_vs_total=float(gap.max())))
        predictions.to_csv(out / f'predictions_{test_year}.csv', index=False)
        r2 = {r['target']: r['r2'] for r in results if r['test_year'] == test_year}
        print(test_year, variant, 'gelernt aus', f'{train_years[0]}-{train_years[-1]}', 'n=', len(train),
              'R2 CO2', round(r2[CO2], 3), 'R2 Gruen', round(r2[TOTAL], 3),
              'Luecke Quellen-Summe vs. Gesamt (Mittel)', round(float(gap.mean()), 3), flush=True)

    table = pd.DataFrame(results)
    table.to_csv(out / 'metrics.csv', index=False)
    manifest = dict(method=f'xgboost {variant} (fixed parameters, no tuning, no early stopping)',
                    multi_strategy='multi_output_tree' if multi else 'one model per target',
                    scheme='expanding window from 2015, new model from scratch on all prior years per step, tested on the following year',
                    data=dict(features_and_renewable_targets='stage0_v6_renewable_breakdown',
                              co2_target='stage0_v5_selfco2 (self-computed, SMARD + UBA factors)'),
                    params=XGB_PARAMS, target_scaling='standardized with training-year mean/std, transformed back',
                    features=features, targets=TARGETS, steps=steps, excluded_rows_per_year=excluded,
                    preprocessing='StandardScaler (numeric) + OneHotEncoder drop=first (hour_local, weekday, month), fit on training years only',
                    threads=1, versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                             xgboost=xgboost.__version__, numpy=np.__version__, pandas=pd.__version__),
                    duration_seconds=time.monotonic() - started, complete=True)
    (out / 'run.json').write_text(json.dumps(manifest, indent=2))
    pd.set_option('display.width', 220)
    print(table.pivot(index='test_year', columns='target', values='r2').round(3).to_string())
    print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--multi', action='store_true')
    main(multi=parser.parse_args().multi)
