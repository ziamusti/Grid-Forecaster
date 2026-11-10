"""HistGradientBoosting (or XGBoost with --xgboost), national model, expanding
training window from 2015.

Same scheme, rows, 137 inputs and preprocessing as train_linear_expanding.py,
but only the two main targets (CO2 from Electricity Maps, renewable share).
Each step fits a new model from scratch on all years from 2015 up to the year
before the test year (2015-2017 -> 2018, ..., 2015-2025 -> 2026); no trees
are carried over between steps. Fixed parameters as in the earlier HistGB
runs, no tuning, no early stopping. XGBoost uses the fixed parameters of the
earlier XGBoost comparison runs.
"""
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from train_linear_expanding import DATA, FIRST_YEAR, PRICE_FEATURE, TEST_YEARS, metrics, pipeline

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'reports/linear_regression_expanding_v1'
TARGETS = ['target_co2_gco2eq_kwh', 'target_renewable_share_pct']
PARAMS = dict(loss='squared_error', learning_rate=.1, max_iter=100, max_leaf_nodes=31,
              max_depth=None, min_samples_leaf=20, l2_regularization=0., max_bins=255,
              early_stopping=False, random_state=42, categorical_features=None)
XGB_PARAMS = dict(objective='reg:squarederror', n_estimators=100, learning_rate=.1,
                  max_depth=6, min_child_weight=1, subsample=1., colsample_bytree=1.,
                  reg_alpha=0., reg_lambda=1., tree_method='hist', max_bin=255,
                  random_state=42, n_jobs=1, early_stopping_rounds=None)


def model(features, xgb=False):
    # Same preprocessing as the linear run, only the estimator differs.
    preprocess = pipeline(features).named_steps['preprocess']
    if xgb:
        from xgboost import XGBRegressor
        estimator = XGBRegressor(**XGB_PARAMS)
    else:
        estimator = HistGradientBoostingRegressor(**PARAMS)
    return Pipeline([('preprocess', preprocess), ('regression', estimator)])


def main(xgb=False):
    OUT = ROOT / 'reports' / ('xgboost_expanding_v1' if xgb else 'hist_gradient_boosting_expanding_v1')
    if OUT.exists():
        raise FileExistsError(f'{OUT} existiert bereits; kein Ueberschreiben.')
    reference = json.loads((REFERENCE / 'run.json').read_text())
    features = reference['features']
    schema_targets = reference['targets']
    assert len(features) == 137 and PRICE_FEATURE in features and set(TARGETS) <= set(schema_targets)

    data = {}
    for year in range(FIRST_YEAR, 2027):
        frame = pd.read_csv(DATA / f'hourly_{year}.csv', usecols=['target_time_utc', 'eligible_both', *features, *schema_targets])
        # Identical row filter as the linear run (all 8 targets present), so both use the same hours.
        mask = ((frame.eligible_both == 1) & frame[PRICE_FEATURE].notna()
                & frame[schema_targets].notna().all(axis=1) & frame[features].notna().all(axis=1))
        data[year] = frame.loc[mask].reset_index(drop=True)
        assert int((~mask).sum()) == reference['excluded_rows_per_year'][str(year)]

    OUT.mkdir(parents=True)
    started = time.monotonic()
    results, steps = [], []
    for test_year in TEST_YEARS:
        train_years = list(range(FIRST_YEAR, test_year))
        train = pd.concat([data[y] for y in train_years], ignore_index=True)
        test = data[test_year]
        linear = pd.read_csv(REFERENCE / f'predictions_{test_year}.csv')
        assert linear.target_time_utc.tolist() == test.target_time_utc.tolist()
        x_train, x_test = train[features].to_numpy(float), test[features].to_numpy(float)
        predictions = test[['target_time_utc']].copy()
        for target in TARGETS:
            actual = test[target].to_numpy(float)
            np.testing.assert_allclose(linear[f'actual_{target}'].to_numpy(), actual, rtol=1e-12, atol=1e-9)
            with threadpool_limits(limits=1):
                fitted = model(features, xgb).fit(x_train, train[target].to_numpy(float))
                predicted = fitted.predict(x_test)
            learner = fitted.named_steps['regression']
            if xgb:
                assert learner.get_booster().num_boosted_rounds() == 100
            else:
                assert learner.n_iter_ == 100 and not learner.do_early_stopping_
            assert np.isfinite(predicted).all()
            predictions[f'actual_{target}'] = actual
            predictions[f'predicted_{target}'] = predicted
            results.append(dict(test_year=test_year, target=target, train_years=f'{train_years[0]}-{train_years[-1]}',
                                train_n=len(train), **metrics(actual, predicted)))
            print(test_year, target, 'gelernt aus', f'{train_years[0]}-{train_years[-1]}', 'n=', len(train),
                  'R2=', round(results[-1]['r2'], 3), 'MAE=', round(results[-1]['mae'], 2), flush=True)
        steps.append(dict(test_year=test_year, train_years=train_years, train_n=len(train), test_n=len(test)))
        predictions.to_csv(OUT / f'predictions_{test_year}.csv', index=False)

    table = pd.DataFrame(results)
    table.to_csv(OUT / 'metrics.csv', index=False)
    manifest = dict(method=('xgboost' if xgb else 'hist_gradient_boosting') + ' (fixed parameters, no tuning, no early stopping)',
                    scheme='expanding window from 2015, new model from scratch on all prior years per step, tested on the following year',
                    data_version='stage0_v6_renewable_breakdown', co2_target='Electricity Maps',
                    rows='identical to reports/linear_regression_expanding_v1 (checked per test year)',
                    params=XGB_PARAMS if xgb else PARAMS, features=features, targets=TARGETS, steps=steps,
                    preprocessing='StandardScaler (numeric) + OneHotEncoder drop=first (hour_local, weekday, month), fit on training years only',
                    threads=1, versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                             numpy=np.__version__, pandas=pd.__version__,
                                             **({'xgboost': __import__('xgboost').__version__} if xgb else {})),
                    duration_seconds=time.monotonic() - started, complete=True)
    (OUT / 'run.json').write_text(json.dumps(manifest, indent=2))
    print(table.pivot(index='test_year', columns='target', values='r2').round(3).to_string())
    print(OUT)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--xgboost', action='store_true')
    main(xgb=parser.parse_args().xgboost)
