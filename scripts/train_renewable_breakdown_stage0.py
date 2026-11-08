"""Train one HistGradientBoosting model per renewable source: dev-folds + final model.

Six separate models (wind onshore/offshore, solar, biomass, hydro, other
renewables), same methodology and fold years as the production models
(splits.json unchanged): development folds 2018-2024, final train
2022-2024, held-out test 2025, partial holdout 2026. Uses the 136
non-price features, matching the convention of the deployed renewable-
share model (that model never had the price feature added).
"""
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/stage0_v6_renewable_breakdown'
DEV_OUT = ROOT / 'reports/hist_gradient_boosting_renewable_breakdown_v1'
FINAL_OUT = ROOT / 'reports/final_hist_gradient_boosting_renewable_breakdown_2015_20261026_v1'
PRICE_FEATURE = 'price_eur_mwh_lag168h'
SOURCES = ['biomass', 'hydro', 'wind_offshore', 'wind_onshore', 'solar', 'other_renewables']
TARGETS = [f'target_{name}_share_pct' for name in SOURCES]
FLAG = 'eligible_renewable'
CATEGORIES = ['hour_local', 'weekday', 'month']
PARAMS = dict(loss='squared_error', learning_rate=.1, max_iter=100, max_leaf_nodes=31,
              max_depth=None, min_samples_leaf=20, l2_regularization=0., max_bins=255,
              early_stopping=False, random_state=42, categorical_features=None)


def pipeline(features):
    numeric = [i for i, f in enumerate(features) if f not in CATEGORIES]
    categorical = [features.index(f) for f in CATEGORIES]
    transform = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('calendar', OneHotEncoder(categories=[list(range(24)), list(range(7)), list(range(1, 13))],
                                   drop='first', sparse_output=False, handle_unknown='error'), categorical)])
    return Pipeline([('preprocess', transform), ('regression', HistGradientBoostingRegressor(**PARAMS))])


def metrics(actual, predicted):
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    errors = actual - predicted
    sse = float(np.sum(errors ** 2))
    sst = float(np.sum((actual - actual.mean()) ** 2))
    return dict(n=len(actual), mae=float(np.mean(np.abs(errors))),
                rmse=float(np.sqrt(sse / len(errors))), r2=1 - sse / sst if sst else None)


def load_years(features, years):
    cols = list(dict.fromkeys(['target_time_utc', *features, *TARGETS, FLAG]))
    return {y: pd.read_csv(DATA / f'hourly_{y}.csv', usecols=cols) for y in years}


def eligible(frame, features, target):
    rows = frame.loc[frame[FLAG] == 1]
    x = rows[features].to_numpy(float)
    y = rows[target].to_numpy(float)
    assert np.isfinite(x).all() and np.isfinite(y).all()
    return rows, x, y


def main():
    schema = json.loads((DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f not in ('is_weekend', PRICE_FEATURE)]
    assert len(features) == 136 and PRICE_FEATURE not in features
    splits = json.loads((DATA / 'splits.json').read_text())
    folds = splits['development_folds']
    assert [f['validation_year'] for f in folds] == list(range(2018, 2025))

    if DEV_OUT.exists():
        raise FileExistsError('Dev-fold experiment already exists; never overwrite')
    data = load_years(features, range(2015, 2025))
    DEV_OUT.mkdir(parents=True)
    all_results = []
    started = time.monotonic()
    for target, source in zip(TARGETS, SOURCES):
        for fold in folds:
            year = fold['validation_year']
            train = pd.concat([data[y] for y in fold['train_years']], ignore_index=True)
            tr_rows, x_tr, y_tr = eligible(train, features, target)
            val_rows, x_val, y_val = eligible(data[year], features, target)
            with threadpool_limits(limits=1):
                model = pipeline(features).fit(x_tr, y_tr)
                prediction = model.predict(x_val)
            stats = metrics(y_val, prediction)
            all_results.append(dict(source=source, validation_year=year, train_n=len(tr_rows), **stats))
            pred_out = val_rows[['target_time_utc']].copy()
            pred_out['actual'] = y_val
            pred_out[f'hist_gradient_boosting_{source}'] = prediction
            pred_out.to_csv(DEV_OUT / f'predictions_{source}_{year}.csv', index=False)
            print(source, year, stats, flush=True)
    pd.DataFrame(all_results).to_csv(DEV_OUT / 'metrics.csv', index=False)
    (DEV_OUT / 'run.json').write_text(json.dumps(dict(
        params=PARAMS, folds=folds, features=features, targets=TARGETS, results=all_results,
        versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                      numpy=np.__version__, pandas=pd.__version__),
        duration_seconds=time.monotonic() - started, data_version='stage0_v6_renewable_breakdown',
        complete=True), indent=2))
    print('Dev-fold complete:', DEV_OUT)

    if FINAL_OUT.exists():
        raise FileExistsError('Final experiment already exists; never overwrite')
    final_train_data = load_years(features, splits['final_train_years'])
    train = pd.concat([final_train_data[y] for y in splits['final_train_years']], ignore_index=True)
    test_data = load_years(features, [splits['final_test_year']])
    holdout_year = splits['holdout_partial_year']
    holdout_data = load_years(features, [holdout_year])
    FINAL_OUT.mkdir(parents=True)
    final_records = []
    for target, source in zip(TARGETS, SOURCES):
        tr_rows, x_tr, y_tr = eligible(train, features, target)
        with threadpool_limits(limits=1):
            final_model = pipeline(features).fit(x_tr, y_tr)
        path = FINAL_OUT / f'hist_gradient_boosting_{source}.joblib'
        joblib.dump(dict(pipeline=final_model, features=features, target=target, source=source,
                          training_years=splits['final_train_years'], training_n=len(tr_rows),
                          training_end='2024-12-31T23:00:00Z', purpose='final_application_model'), path)

        test_rows, x_test, y_test = eligible(test_data[splits['final_test_year']], features, target)
        with threadpool_limits(limits=1):
            test_prediction = final_model.predict(x_test)
        test_stats = metrics(y_test, test_prediction)

        holdout_rows, x_holdout, y_holdout = eligible(holdout_data[holdout_year], features, target)
        with threadpool_limits(limits=1):
            holdout_prediction = final_model.predict(x_holdout)
        holdout_stats = metrics(y_holdout, holdout_prediction)

        pd.DataFrame(dict(target_time_utc=test_rows.target_time_utc, actual=y_test,
                           prediction=test_prediction)).to_csv(FINAL_OUT / f'predictions_{source}_2025.csv', index=False)
        pd.DataFrame(dict(target_time_utc=holdout_rows.target_time_utc, actual=y_holdout,
                           prediction=holdout_prediction)).to_csv(FINAL_OUT / f'predictions_{source}_{holdout_year}.csv', index=False)
        final_records.append(dict(source=source, training_n=len(tr_rows), test_metrics=test_stats,
                                   holdout_metrics=holdout_stats))
        print(source, 'test 2025:', test_stats, 'holdout', holdout_year, ':', holdout_stats)

    (FINAL_OUT / 'run.json').write_text(json.dumps(dict(
        status='complete', purpose='Final per-source renewable share models', params=PARAMS,
        training_years=splits['final_train_years'], features=features, targets=TARGETS,
        test_year=splits['final_test_year'], holdout_year=holdout_year, models=final_records,
        data_version='stage0_v6_renewable_breakdown',
        versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                      numpy=np.__version__, pandas=pd.__version__)), indent=2))
    print('Final models complete:', FINAL_OUT)


if __name__ == '__main__':
    main()
