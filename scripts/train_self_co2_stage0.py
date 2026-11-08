"""Train the self-computed-CO2 HistGradientBoosting model: dev-folds + final model.

Self-contained (does not reuse another run's fitted scaler) replacement for
the Electricity-Maps-trained CO2 model, using data/processed/stage0_v5_selfco2
(same 137 input features + price lag168h as the production price model;
only target_co2_gco2eq_kwh differs, now self-computed from SMARD + UBA
factors instead of Electricity Maps). Exact same fold years as
splits.json (unchanged, carried over from the base version): development
folds 2018-2024, final train 2022-2024, held-out test 2025, partial
holdout 2026. Renewable-share target is NOT retrained here; that model is
unaffected by the CO2 licensing issue.
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
DATA = ROOT / 'data/processed/stage0_v5_selfco2'
DEV_OUT = ROOT / 'reports/hist_gradient_boosting_self_co2_v1'
FINAL_OUT = ROOT / 'reports/final_hist_gradient_boosting_self_co2_2015_20261026_v1'
TARGET = 'target_co2_gco2eq_kwh'
FLAG = 'eligible_co2_nonestimated'
PRICE_FEATURE = 'price_eur_mwh_lag168h'
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
    cols = list(dict.fromkeys(['target_time_utc', *features, TARGET, FLAG]))
    return {y: pd.read_csv(DATA / f'hourly_{y}.csv', usecols=cols) for y in years}


def eligible(frame, features):
    mask = (frame[FLAG] == 1) & frame[PRICE_FEATURE].notna()
    rows = frame.loc[mask]
    x = rows[features].to_numpy(float)
    y = rows[TARGET].to_numpy(float)
    assert np.isfinite(x).all() and np.isfinite(y).all()
    return rows, x, y


def main():
    schema = json.loads((DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f != 'is_weekend']
    assert len(features) == 137 and PRICE_FEATURE in features
    splits = json.loads((DATA / 'splits.json').read_text())
    folds = splits['development_folds']
    assert [f['validation_year'] for f in folds] == list(range(2018, 2025))
    for f in folds:
        assert f['train_years'] == list(range(f['validation_year'] - 3, f['validation_year']))

    if DEV_OUT.exists():
        raise FileExistsError('Dev-fold experiment already exists; never overwrite')
    data = load_years(features, range(2015, 2025))
    DEV_OUT.mkdir(parents=True)
    results = []
    started = time.monotonic()
    for fold in folds:
        year = fold['validation_year']
        train = pd.concat([data[y] for y in fold['train_years']], ignore_index=True)
        tr_rows, x_tr, y_tr = eligible(train, features)
        val_rows, x_val, y_val = eligible(data[year], features)
        with threadpool_limits(limits=1):
            model = pipeline(features).fit(x_tr, y_tr)
            prediction = model.predict(x_val)
        assert model.named_steps['regression'].n_iter_ == 100 and not model.named_steps['regression'].do_early_stopping_
        stats = metrics(y_val, prediction)
        results.append(dict(validation_year=year, train_n=len(tr_rows), **stats))
        pred_out = val_rows[['target_time_utc']].copy()
        pred_out['actual'] = y_val
        pred_out['hist_gradient_boosting_self_co2'] = prediction
        pred_out.to_csv(DEV_OUT / f'predictions_{year}.csv', index=False)
        print(year, stats, flush=True)
    pd.DataFrame(results).to_csv(DEV_OUT / 'metrics.csv', index=False)
    dev_manifest = dict(params=PARAMS, folds=folds, features=features, target=TARGET,
                         results=results, script_sha256=None,
                         versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                       numpy=np.__version__, pandas=pd.__version__),
                         duration_seconds=time.monotonic() - started,
                         data_version='stage0_v5_selfco2', complete=True)
    (DEV_OUT / 'run.json').write_text(json.dumps(dev_manifest, indent=2))
    print('Dev-fold complete:', DEV_OUT)

    if FINAL_OUT.exists():
        raise FileExistsError('Final experiment already exists; never overwrite')
    final_train_data = load_years(features, splits['final_train_years'])
    train = pd.concat([final_train_data[y] for y in splits['final_train_years']], ignore_index=True)
    tr_rows, x_tr, y_tr = eligible(train, features)
    with threadpool_limits(limits=1):
        final_model = pipeline(features).fit(x_tr, y_tr)
    assert final_model.named_steps['regression'].n_iter_ == 100
    FINAL_OUT.mkdir(parents=True)
    path = FINAL_OUT / 'hist_gradient_boosting_self_co2_target_co2_gco2eq_kwh.joblib'
    joblib.dump(dict(pipeline=final_model, features=features, target=TARGET,
                      training_years=splits['final_train_years'], training_n=len(tr_rows),
                      training_end='2024-12-31T23:00:00Z', purpose='final_application_model'), path)

    test_data = load_years(features, [splits['final_test_year']])
    test_rows, x_test, y_test = eligible(test_data[splits['final_test_year']], features)
    with threadpool_limits(limits=1):
        test_prediction = final_model.predict(x_test)
    test_stats = metrics(y_test, test_prediction)
    print(splits['final_test_year'], 'held-out test:', test_stats)
    pd.DataFrame(dict(target_time_utc=test_rows.target_time_utc, actual=y_test,
                       hist_gradient_boosting_self_co2=test_prediction)).to_csv(
        FINAL_OUT / f'predictions_{splits["final_test_year"]}.csv', index=False)

    holdout_year = splits['holdout_partial_year']
    holdout_data = load_years(features, [holdout_year])
    holdout_rows, x_holdout, y_holdout = eligible(holdout_data[holdout_year], features)
    with threadpool_limits(limits=1):
        holdout_prediction = final_model.predict(x_holdout)
    holdout_stats = metrics(y_holdout, holdout_prediction)
    print(holdout_year, 'partial holdout:', holdout_stats)
    pd.DataFrame(dict(target_time_utc=holdout_rows.target_time_utc, actual=y_holdout,
                       hist_gradient_boosting_self_co2=holdout_prediction)).to_csv(
        FINAL_OUT / f'predictions_{holdout_year}.csv', index=False)

    final_manifest = dict(status='complete', purpose='Final self-computed-CO2 application model',
                           params=PARAMS, training_years=splits['final_train_years'],
                           training_n=len(tr_rows), features=features,
                           test_year=splits['final_test_year'], test_metrics=test_stats,
                           holdout_year=holdout_year, holdout_metrics=holdout_stats,
                           data_version='stage0_v5_selfco2', model_sha256=None,
                           versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                         numpy=np.__version__, pandas=pd.__version__),
                           caveats=['Self-computed production-based CO2 target (SMARD + UBA factors), '
                                    'not directly comparable to the Electricity-Maps-trained model, '
                                    'which is consumption-based with cross-border flow tracing'])
    (FINAL_OUT / 'run.json').write_text(json.dumps(final_manifest, indent=2))
    print('Final model complete:', FINAL_OUT)


if __name__ == '__main__':
    main()
