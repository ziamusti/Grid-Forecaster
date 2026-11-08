"""Train the pooled per-Bundesland HistGradientBoosting models: dev-folds + final.

Uses data/processed/bundesland_pooled_v1 (16 Bundeslaender stacked, one row
per (hour, Bundesland); "bundesland" is an additional categorical input
feature, same OneHotEncoder treatment as hour_local/weekday/month). Trains
two separate, independently-fitted models (CO2-intensity, Gruenanteil); no
multi-output and no total/part relationship is defined between them. Exact
same fold years as every other model in this project (splits.json, unchanged):
development folds 2018-2024, final train 2022-2024, held-out test 2025,
partial holdout 2026.
"""
import json
import platform
import sys
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundesland import BUNDESLAENDER

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/bundesland_pooled_v1'
SPLITS_SOURCE = ROOT / 'data/processed/stage0_v4_oct26/splits.json'

NUMERIC_FEATURES = [
    'station1__temperature_2m_c', 'station1__cloud_cover_pct', 'station1__wind_speed_100m_ms',
    'station1__shortwave_radiation_wm2', 'station1__sunshine_duration_preceding_hour_s',
    'station2__temperature_2m_c', 'station2__cloud_cover_pct', 'station2__wind_speed_100m_ms',
    'station2__shortwave_radiation_wm2', 'station2__sunshine_duration_preceding_hour_s',
    'daylight_hours_approx', 'pv_net_mw_reconstructed', 'wind_onshore_net_mw_reconstructed',
    'wind_offshore_net_mw_reconstructed', 'is_regional_holiday',
]
CATEGORIES = ['hour_local', 'weekday', 'month', 'bundesland']
FEATURES = NUMERIC_FEATURES + CATEGORIES
PARAMS = dict(loss='squared_error', learning_rate=.1, max_iter=100, max_leaf_nodes=31,
              max_depth=None, min_samples_leaf=20, l2_regularization=0., max_bins=255,
              early_stopping=False, random_state=42, categorical_features=None)

TARGETS = {
    'target_co2_gco2eq_kwh': dict(
        slug='bundesland_co2',
        dev_out=ROOT / 'reports/hist_gradient_boosting_bundesland_co2_v1',
        final_out=ROOT / 'reports/final_hist_gradient_boosting_bundesland_co2_2015_2026_v1'),
    'target_renewable_share_pct': dict(
        slug='bundesland_renewable_share',
        dev_out=ROOT / 'reports/hist_gradient_boosting_bundesland_renewable_share_v1',
        final_out=ROOT / 'reports/final_hist_gradient_boosting_bundesland_renewable_share_2015_2026_v1'),
}


def pipeline():
    numeric = [FEATURES.index(f) for f in NUMERIC_FEATURES]
    categorical = [FEATURES.index(f) for f in CATEGORIES]
    transform = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('calendar', OneHotEncoder(
            categories=[list(range(24)), list(range(7)), list(range(1, 13)), list(BUNDESLAENDER)],
            drop='first', sparse_output=False, handle_unknown='error'), categorical)])
    return Pipeline([('preprocess', transform), ('regression', HistGradientBoostingRegressor(**PARAMS))])


def metrics(actual, predicted):
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    errors = actual - predicted
    sse = float(np.sum(errors ** 2))
    sst = float(np.sum((actual - actual.mean()) ** 2))
    return dict(n=len(actual), mae=float(np.mean(np.abs(errors))),
                rmse=float(np.sqrt(sse / len(errors))), r2=1 - sse / sst if sst else None)


def load_years(years, target):
    cols = list(dict.fromkeys(['target_time_utc', *FEATURES, target]))
    return {y: pd.read_csv(DATA / f'hourly_{y}.csv', usecols=cols) for y in years}


def eligible(frame, target):
    rows = frame.loc[frame[target].notna()]
    x = rows[FEATURES]
    y = rows[target].to_numpy(float)
    assert np.isfinite(y).all()
    return rows, x, y


def main():
    splits = json.loads(SPLITS_SOURCE.read_text())
    folds = splits['development_folds']
    assert [f['validation_year'] for f in folds] == list(range(2018, 2025))
    for f in folds:
        assert f['train_years'] == list(range(f['validation_year'] - 3, f['validation_year']))

    for target, cfg in TARGETS.items():
        dev_out, final_out = cfg['dev_out'], cfg['final_out']
        if dev_out.exists():
            raise FileExistsError(f'{dev_out} existiert bereits; kein Ueberschreiben.')
        data = load_years(range(2015, 2025), target)
        dev_out.mkdir(parents=True)
        results = []
        started = time.monotonic()
        for fold in folds:
            year = fold['validation_year']
            train = pd.concat([data[y] for y in fold['train_years']], ignore_index=True)
            tr_rows, x_tr, y_tr = eligible(train, target)
            val_rows, x_val, y_val = eligible(data[year], target)
            with threadpool_limits(limits=1):
                model = pipeline().fit(x_tr, y_tr)
                prediction = model.predict(x_val)
            assert model.named_steps['regression'].n_iter_ == 100 and not model.named_steps['regression'].do_early_stopping_
            stats = metrics(y_val, prediction)
            results.append(dict(validation_year=year, train_n=len(tr_rows), **stats))
            pred_out = val_rows[['target_time_utc', 'bundesland']].copy()
            pred_out['actual'] = y_val
            pred_out[f'hist_gradient_boosting_{cfg["slug"]}'] = prediction
            pred_out.to_csv(dev_out / f'predictions_{year}.csv', index=False)
            print(target, year, stats, flush=True)
        pd.DataFrame(results).to_csv(dev_out / 'metrics.csv', index=False)
        dev_manifest = dict(params=PARAMS, folds=folds, features=FEATURES, target=target,
                             results=results, script_sha256=None,
                             versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                           numpy=np.__version__, pandas=pd.__version__),
                             duration_seconds=time.monotonic() - started,
                             data_version='bundesland_pooled_v1', pooled=True,
                             bundeslaender=list(BUNDESLAENDER), complete=True)
        (dev_out / 'run.json').write_text(json.dumps(dev_manifest, indent=2))
        print('Dev-fold complete:', dev_out)

        if final_out.exists():
            raise FileExistsError(f'{final_out} existiert bereits; kein Ueberschreiben.')
        final_train_data = load_years(splits['final_train_years'], target)
        train = pd.concat([final_train_data[y] for y in splits['final_train_years']], ignore_index=True)
        tr_rows, x_tr, y_tr = eligible(train, target)
        with threadpool_limits(limits=1):
            final_model = pipeline().fit(x_tr, y_tr)
        assert final_model.named_steps['regression'].n_iter_ == 100
        final_out.mkdir(parents=True)
        path = final_out / f'hist_gradient_boosting_{cfg["slug"]}_{target}.joblib'
        joblib.dump(dict(pipeline=final_model, features=FEATURES, target=target,
                          bundeslaender=list(BUNDESLAENDER), pooled=True,
                          training_years=splits['final_train_years'], training_n=len(tr_rows),
                          training_end='2024-12-31T23:00:00Z', purpose='final_application_model'), path)

        test_data = load_years([splits['final_test_year']], target)
        test_rows, x_test, y_test = eligible(test_data[splits['final_test_year']], target)
        with threadpool_limits(limits=1):
            test_prediction = final_model.predict(x_test)
        test_stats = metrics(y_test, test_prediction)
        print(target, splits['final_test_year'], 'held-out test:', test_stats)
        pd.DataFrame(dict(target_time_utc=test_rows.target_time_utc, bundesland=test_rows.bundesland,
                           actual=y_test, **{f'hist_gradient_boosting_{cfg["slug"]}': test_prediction})).to_csv(
            final_out / f'predictions_{splits["final_test_year"]}.csv', index=False)

        holdout_year = splits['holdout_partial_year']
        holdout_data = load_years([holdout_year], target)
        holdout_rows, x_holdout, y_holdout = eligible(holdout_data[holdout_year], target)
        with threadpool_limits(limits=1):
            holdout_prediction = final_model.predict(x_holdout)
        holdout_stats = metrics(y_holdout, holdout_prediction)
        print(target, holdout_year, 'partial holdout:', holdout_stats)
        pd.DataFrame(dict(target_time_utc=holdout_rows.target_time_utc, bundesland=holdout_rows.bundesland,
                           actual=y_holdout, **{f'hist_gradient_boosting_{cfg["slug"]}': holdout_prediction})).to_csv(
            final_out / f'predictions_{holdout_year}.csv', index=False)

        final_manifest = dict(status='complete', purpose=f'Final pooled Bundesland model for {target}',
                               params=PARAMS, training_years=splits['final_train_years'],
                               training_n=len(tr_rows), features=FEATURES,
                               test_year=splits['final_test_year'], test_metrics=test_stats,
                               holdout_year=holdout_year, holdout_metrics=holdout_stats,
                               data_version='bundesland_pooled_v1', pooled=True,
                               bundeslaender=list(BUNDESLAENDER), model_sha256=None,
                               versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                             numpy=np.__version__, pandas=pd.__version__),
                               caveats=['Gepooltes Modell: ein gemeinsames Modell fuer alle 16 Bundeslaender, '
                                        '"bundesland" als kategoriales Feature, keine 16 separaten Modelle. '
                                        'station2__* ist NaN fuer Bundeslaender mit nur einer Wetterstation '
                                        '(HistGradientBoostingRegressor unterstuetzt fehlende Werte nativ).'])
        (final_out / 'run.json').write_text(json.dumps(final_manifest, indent=2))
        print('Final model complete:', final_out)


if __name__ == '__main__':
    main()
