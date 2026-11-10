"""Linear regression, national model, expanding training window from 2015.

One model per target (8): CO2 (Electricity Maps), renewable share and its six
sources. Each step learns from 2015 up to the year before the test year and
is tested on that year: 2015-2017 -> 2018, ..., 2015-2025 -> 2026. For
ordinary least squares, refitting on all years up to t is identical to
continuing the previous fit with year t added. Same 137 inputs (incl. price
lag168h) and same rows as the later HistGradientBoosting/XGBoost runs.
Preprocessing (scaling) is fit on the training years only.
"""
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/stage0_v6_renewable_breakdown'
OUT = ROOT / 'reports/linear_regression_expanding_v1'
FIRST_YEAR = 2015
TEST_YEARS = list(range(2018, 2027))
CATEGORIES = ['hour_local', 'weekday', 'month']
PRICE_FEATURE = 'price_eur_mwh_lag168h'
RENEWABLE_SOURCES = ['target_biomass_share_pct', 'target_hydro_share_pct', 'target_wind_offshore_share_pct',
                     'target_wind_onshore_share_pct', 'target_solar_share_pct', 'target_other_renewables_share_pct']


def pipeline(features):
    numeric = [i for i, f in enumerate(features) if f not in CATEGORIES]
    categorical = [features.index(f) for f in CATEGORIES]
    transform = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('calendar', OneHotEncoder(categories=[list(range(24)), list(range(7)), list(range(1, 13))],
                                   drop='first', sparse_output=False, handle_unknown='error'), categorical)])
    return Pipeline([('preprocess', transform), ('regression', LinearRegression())])


def metrics(actual, predicted):
    errors = actual - predicted
    sse = float(np.sum(errors ** 2))
    sst = float(np.sum((actual - actual.mean()) ** 2))
    return dict(n=len(actual), mae=float(np.mean(np.abs(errors))),
                rmse=float(np.sqrt(sse / len(errors))), r2=1 - sse / sst)


def main():
    if OUT.exists():
        raise FileExistsError(f'{OUT} existiert bereits; kein Ueberschreiben.')
    schema = json.loads((DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f != 'is_weekend']
    targets = schema['targets']
    assert len(features) == 137 and PRICE_FEATURE in features and len(targets) == 8
    assert set(RENEWABLE_SOURCES) <= set(targets)

    data = {}
    excluded = {}
    for year in range(FIRST_YEAR, 2027):
        frame = pd.read_csv(DATA / f'hourly_{year}.csv', usecols=['target_time_utc', 'eligible_both', *features, *targets])
        mask = ((frame.eligible_both == 1) & frame[PRICE_FEATURE].notna()
                & frame[targets].notna().all(axis=1) & frame[features].notna().all(axis=1))
        excluded[year] = int((~mask).sum())
        rows = frame.loc[mask].reset_index(drop=True)
        assert np.isfinite(rows[features].to_numpy(float)).all() and np.isfinite(rows[targets].to_numpy(float)).all()
        data[year] = rows

    OUT.mkdir(parents=True)
    started = time.monotonic()
    results, steps = [], []
    for test_year in TEST_YEARS:
        train_years = list(range(FIRST_YEAR, test_year))
        train = pd.concat([data[y] for y in train_years], ignore_index=True)
        test = data[test_year]
        x_train, x_test = train[features].to_numpy(float), test[features].to_numpy(float)
        predictions = test[['target_time_utc']].copy()
        for target in targets:
            model = pipeline(features).fit(x_train, train[target].to_numpy(float))
            predicted = model.predict(x_test)
            actual = test[target].to_numpy(float)
            assert np.isfinite(predicted).all()
            predictions[f'actual_{target}'] = actual
            predictions[f'predicted_{target}'] = predicted
            results.append(dict(test_year=test_year, target=target, train_years=f'{train_years[0]}-{train_years[-1]}',
                                train_n=len(train), **metrics(actual, predicted)))
        source_sum = predictions[[f'predicted_{t}' for t in RENEWABLE_SOURCES]].sum(axis=1)
        max_gap = float((source_sum - predictions['predicted_target_renewable_share_pct']).abs().max())
        steps.append(dict(test_year=test_year, train_years=train_years, train_n=len(train), test_n=len(test),
                          max_abs_gap_sum_of_sources_vs_total=max_gap))
        predictions.to_csv(OUT / f'predictions_{test_year}.csv', index=False)
        print(test_year, 'gelernt aus', f'{train_years[0]}-{train_years[-1]}', 'n=', len(train),
              'Test n=', len(test), 'Luecke Quellen-Summe vs. Gesamt:', round(max_gap, 6), flush=True)

    table = pd.DataFrame(results)
    table.to_csv(OUT / 'metrics.csv', index=False)
    manifest = dict(method='linear_regression (ordinary least squares, no regularization, no clipping)',
                    scheme='expanding window from 2015, one model per target, tested on the following year',
                    data_version='stage0_v6_renewable_breakdown', co2_target='Electricity Maps',
                    features=features, targets=targets, steps=steps, excluded_rows_per_year=excluded,
                    preprocessing='StandardScaler (numeric) + OneHotEncoder drop=first (hour_local, weekday, month), fit on training years only',
                    versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                  numpy=np.__version__, pandas=pd.__version__),
                    duration_seconds=time.monotonic() - started, complete=True)
    (OUT / 'run.json').write_text(json.dumps(manifest, indent=2))
    pd.set_option('display.width', 200)
    print(table.pivot(index='test_year', columns='target', values='r2').round(3).to_string())
    print(OUT)


if __name__ == '__main__':
    main()
