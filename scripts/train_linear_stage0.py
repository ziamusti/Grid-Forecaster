"""Separate OLS targets; development folds only; fair three-way comparison."""
import csv
import hashlib
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits
from train_mean_baseline import fit as fit_mean, key, metrics, write_csv, TARGETS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/stage0_v2_sunshine'
OUT = ROOT / 'reports/linear_regression_v1'
CATEGORIES = ['hour_local', 'weekday', 'month']


def pipeline(features):
    numeric = [i for i, f in enumerate(features) if f not in CATEGORIES]
    categorical = [features.index(f) for f in CATEGORIES]
    transform = ColumnTransformer([
        ('numeric', StandardScaler(), numeric),
        ('calendar', OneHotEncoder(categories=[list(range(24)), list(range(7)), list(range(1, 13))],
                                   drop='first', sparse_output=False, handle_unknown='error'), categorical)])
    return Pipeline([('preprocess', transform), ('regression', LinearRegression())])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(s):
    return s != '' and np.isfinite(float(s))


def main(test_2025=False):
    OUT = ROOT / 'reports' / ('linear_regression_test2025_v1' if test_2025 else 'linear_regression_v1')
    if OUT.exists():
        raise FileExistsError('Use a new version, never overwrite an experiment')
    schema = json.loads((DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f != 'is_weekend']
    assert len(features) == 136 and not set(features) & set(TARGETS)
    folds = json.loads((DATA / 'splits.json').read_text())['development_folds']
    assert [f['validation_year'] for f in folds] == list(range(2018, 2025))
    for f in folds:
        assert f['train_years'] == list(range(f['validation_year']-3, f['validation_year']))
    if test_2025:
        folds = [dict(train_years=[2022, 2023, 2024], validation_year=2025)]
    files = [DATA/'feature_schema.json', DATA/'splits.json']
    data = {}
    for year in (range(2022, 2026) if test_2025 else range(2015, 2025)):
        path = DATA/f'hourly_{year}.csv'
        files.append(path)
        with path.open() as stream:
            data[year] = list(csv.DictReader(stream))
        start = datetime.fromisoformat(f'{year}-01-01T00:00:00+00:00')
        assert len(data[year]) == (start.replace(year=year+1)-start).total_seconds()/3600
        for i, row in enumerate(data[year]):
            t = datetime.fromisoformat(row['target_time_utc'].replace('Z', '+00:00'))
            assert t == start+timedelta(hours=i)
            weekday, hour = key(row['target_time_utc'])
            assert int(row['weekday']) == weekday and int(row['hour_local']) == hour
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    by_time = {r['target_time_utc']: r for rows in data.values() for r in rows}
    OUT.mkdir(parents=True)
    summaries, checks = [], []
    pooled = {(t, m): ([], []) for t in TARGETS for m in ('linear', 'mean', 'week')}
    for fold in folds:
        year = fold['validation_year']
        train = [r for y in fold['train_years'] for r in data[y]]
        validation = data[year]
        for target, flag in TARGETS.items():
            training = [r for r in train if r[flag] == '1']
            eligible = [r for r in validation if r[flag] == '1']
            xtrain = np.asarray([[float(r[f]) for f in features] for r in training])
            ytrain = np.asarray([float(r[target]) for r in training])
            xval = np.asarray([[float(r[f]) for f in features] for r in eligible])
            assert np.isfinite(xtrain).all() and np.isfinite(xval).all() and np.isfinite(ytrain).all()
            model = pipeline(features)
            with threadpool_limits(limits=1):
                model.fit(xtrain, ytrain)
                preds = model.predict(xval)
            assert np.isfinite(preds).all()
            mean_model = fit_mean(train, target)
            entries = []
            for row, pred in zip(eligible, preds):
                t = datetime.fromisoformat(row['target_time_utc'].replace('Z', '+00:00'))
                lag = (t-timedelta(hours=168)).isoformat().replace('+00:00', 'Z')
                old = by_time.get(lag)
                week_ok = old is not None and finite(old[target])
                if target == 'target_co2_gco2eq_kwh':
                    week_ok = week_ok and old['co2_is_estimated'] == '0'
                weekly = float(old[target]) if week_ok else None
                # Assert stored lag has exactly the expected value where comparable.
                lagcol = 'co2_lag168h_baseline_only' if target == 'target_co2_gco2eq_kwh' else 'renewable_share_lag168h_baseline_only'
                if week_ok:
                    assert finite(row[lagcol]) and abs(float(row[lagcol])-weekly)<1e-8
                entries.append(dict(target_time_utc=row['target_time_utc'], actual=float(row[target]),
                                    linear=float(pred), mean=mean_model[key(row['target_time_utc'])][0],
                                    week=weekly, common_scored=int(week_ok)))
            shared = [e for e in entries if e['common_scored']]
            for method in ('linear', 'mean', 'week'):
                actual, prediction = [e['actual'] for e in shared], [e[method] for e in shared]
                stats = metrics(actual, prediction)
                summaries.append(dict(validation_year=year, target=target, method=method,
                                      train_n=len(training) if method != 'week' else 0,
                                      eligible_n=len(eligible), excluded_week=len(entries)-len(shared), **stats))
                pooled[target, method][0].extend(actual)
                pooled[target, method][1].extend(prediction)
            # Also retain linear/mean scores on original baseline eligibility mask.
            for method in ('linear', 'mean'):
                checks.append(dict(validation_year=year, target=target, method=method,
                                   **metrics([e['actual'] for e in entries], [e[method] for e in entries])))
            joblib.dump(dict(pipeline=model, features=features, target=target, fold=fold), OUT/f'model_{year}_{target}.joblib')
            names = model['preprocess'].get_feature_names_out(features).tolist()
            assert len(names) == 173
            write_csv(OUT/f'coefficients_{year}_{target}.csv',
                      [dict(feature=n, coefficient=float(c)) for n,c in zip(names,model['regression'].coef_)])
            write_csv(OUT/f'predictions_{year}_{target}.csv', entries)
            bound = (0, 100) if target == 'target_renewable_share_pct' else (0, float('inf'))
            diagnostic = dict(train_n=len(training), eligible_n=len(eligible),
                              train_rank=int(model['regression'].rank_), transformed_features=len(names),
                              intercept=float(model['regression'].intercept_),
                              below_zero=int((preds<bound[0]).sum()), above_upper=int((preds>bound[1]).sum()),
                              minimum=float(preds.min()), maximum=float(preds.max()),
                              mean_original_mask=checks[-1], train_years=fold['train_years'])
            (OUT/f'diagnostic_{year}_{target}.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
            loaded=joblib.load(OUT/f'model_{year}_{target}.joblib')['pipeline']
            assert np.allclose(loaded.predict(xval[:10]),preds[:10])
            print(year,target,'MAE linear/mean/week:',*[round(s['mae'],3) for s in summaries[-3:]],flush=True)
    write_csv(OUT/'metrics_common.csv', summaries)
    write_csv(OUT/'metrics_original_mask.csv', checks)
    for path, expected in hashes.items():
        assert sha(ROOT/path)==expected
    result = dict(features=features, transformed_features=names, folds=folds,
                  source_sha256=hashes, script_sha256=sha(Path(__file__)),
                  versions=dict(python=platform.python_version(),numpy=np.__version__,sklearn=sklearn.__version__),
                  pooled=[dict(target=t,method=m,**metrics(a,p)) for (t,m),(a,p) in pooled.items()],
                  policy='OLS unregularized; fixed calendar categories; train-only scaling; no clipping',
                  scoring='Per-target eligible mask AND finite nonestimated weekly target; weekly lag in UTC',
                  caveats=['Retrospective ERA5 and revised targets, not operational 72h backtest',
                           'PV net retained; historical MaStR proxy',
                           '2025 retrospective held-out test; 2026 never read' if test_2025 else '2025/2026 never read',
                           'No tuning; rank deficiency/collinearity can affect coefficients'],complete=True)
    (OUT/'run.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['pooled'],indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-2025', action='store_true')
    main(test_2025=parser.parse_args().test_2025)
