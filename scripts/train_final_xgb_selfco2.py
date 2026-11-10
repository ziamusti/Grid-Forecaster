"""Final XGBoost main model for live use: separate models, self-computed CO2.

Same setup as the separate variant of train_xgb_selfco2_expanding.py (8
targets, 137 inputs, same rows, preprocessing, fixed parameters, targets
standardized with training mean/std), fitted once on all available years
2015 to 2026-10-26. No test year: the expanding-window evaluation already
measured this setup; this model is only for genuinely unseen future hours.
"""
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from train_hist_expanding import XGB_PARAMS
from train_linear_expanding import FIRST_YEAR, PRICE_FEATURE, pipeline
from train_xgb_selfco2_expanding import FEATURES_DATA, TARGETS, load_year

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/final_xgboost_selfco2_2015_20261026_v1'
LAST_YEAR = 2026


def main():
    if OUT.exists():
        raise FileExistsError(f'{OUT} existiert bereits; kein Ueberschreiben.')
    schema = json.loads((FEATURES_DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f != 'is_weekend']
    assert len(features) == 137 and PRICE_FEATURE in features
    train = pd.concat([load_year(y, features)[0] for y in range(FIRST_YEAR, LAST_YEAR + 1)], ignore_index=True)
    training_end = pd.to_datetime(train.target_time_utc, utc=True).max()
    x = train[features].to_numpy(float)
    y = train[TARGETS].to_numpy(float)
    mean, std = y.mean(axis=0), y.std(axis=0)

    started = time.monotonic()
    pipelines = {}
    with threadpool_limits(limits=1):
        for k, target in enumerate(TARGETS):
            model = Pipeline([('preprocess', pipeline(features).named_steps['preprocess']),
                              ('regression', XGBRegressor(**XGB_PARAMS))])
            model.fit(x, (y[:, k] - mean[k]) / std[k])
            assert model.named_steps['regression'].get_booster().num_boosted_rounds() == 100
            pipelines[target] = model
            print(target, 'fertig', flush=True)

    OUT.mkdir(parents=True)
    bundle = dict(pipelines=pipelines, target_mean=dict(zip(TARGETS, mean.tolist())),
                  target_std=dict(zip(TARGETS, std.tolist())), features=features, targets=TARGETS,
                  training_end=training_end.isoformat())
    joblib.dump(bundle, OUT / 'xgboost_selfco2_separate.joblib')
    # Reload and check the saved file predicts the same as the in-memory models.
    loaded = joblib.load(OUT / 'xgboost_selfco2_separate.joblib')
    with threadpool_limits(limits=1):
        for target in TARGETS:
            np.testing.assert_allclose(loaded['pipelines'][target].predict(x[:500]),
                                       pipelines[target].predict(x[:500]), rtol=1e-6, atol=1e-6)
    manifest = dict(method='xgboost separate (one model per target), fixed parameters, no tuning',
                    data=dict(features_and_renewable_targets='stage0_v6_renewable_breakdown',
                              co2_target='stage0_v5_selfco2 (self-computed, SMARD + UBA factors)'),
                    train_years=f'{FIRST_YEAR}-{LAST_YEAR}', train_n=len(train), training_end=training_end.isoformat(),
                    params=XGB_PARAMS, target_scaling='standardized with training mean/std, transformed back',
                    renewable_share_output='sum of the six predicted sources (more accurate in the expanding-window test)',
                    features=features, targets=TARGETS, threads=1,
                    versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                  xgboost=xgboost.__version__, numpy=np.__version__, pandas=pd.__version__),
                    duration_seconds=time.monotonic() - started, complete=True)
    (OUT / 'run.json').write_text(json.dumps(manifest, indent=2))
    print('n=', len(train), 'Trainingsende', training_end)
    print(OUT)


if __name__ == '__main__':
    main()
