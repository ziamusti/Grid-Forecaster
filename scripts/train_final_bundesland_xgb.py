"""Final Bundesland model for live use: XGBoost stage 2 (45 inputs), pooled.

Same setup as train_bundesland_xgb_expanding.py --stage 2 (six separate models:
CO2 + five renewable sources, same rows, preprocessing, parameters, target
standardization), fitted once on all years 2015 to 2026-10-26. No test year:
the expanding-window evaluation already measured this setup.
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

from train_bundesland_xgb_expanding import DATA, MODELLED, PARAMS, model
from train_linear_expanding import FIRST_YEAR

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/final_xgboost_bundesland_2015_20261026_v1'


def main():
    if OUT.exists():
        raise FileExistsError(f'{OUT} existiert bereits; kein Ueberschreiben.')
    schema = json.loads((DATA / 'feature_schema.json').read_text())
    features, categories = schema['stage2'], schema['categories']
    required = [f for f in features if not f.startswith('station2__')]
    parts = []
    for year in range(FIRST_YEAR, 2027):
        frame = pd.read_csv(DATA / f'hourly_{year}.csv', usecols=['target_time_utc', *features, *schema['targets']])
        parts.append(frame.loc[frame[schema['targets']].notna().all(axis=1) & frame[required].notna().all(axis=1)])
    train = pd.concat(parts, ignore_index=True)
    training_end = pd.to_datetime(train.target_time_utc, utc=True).max()

    started = time.monotonic()
    pipelines, mean, std = {}, {}, {}
    for target in MODELLED:
        y = train[target].to_numpy(float)
        mean[target], std[target] = float(y.mean()), float(y.std())
        pipelines[target] = model(features, categories).fit(train[features], (y - mean[target]) / std[target])
        assert pipelines[target].named_steps['regression'].get_booster().num_boosted_rounds() == 100
        print(target, 'fertig', flush=True)

    OUT.mkdir(parents=True)
    bundle = dict(pipelines=pipelines, target_mean=mean, target_std=std, features=features,
                  categories=categories, targets=MODELLED, training_end=training_end.isoformat())
    joblib.dump(bundle, OUT / 'xgboost_bundesland_stage2.joblib')
    loaded = joblib.load(OUT / 'xgboost_bundesland_stage2.joblib')
    sample = train[features].iloc[:2000]
    for target in MODELLED:
        np.testing.assert_allclose(loaded['pipelines'][target].predict(sample), pipelines[target].predict(sample),
                                   rtol=1e-6, atol=1e-6)
    (OUT / 'run.json').write_text(json.dumps(dict(
        method='xgboost stage 2, pooled over 16 Bundeslaender, one model per target, fixed parameters',
        data='bundesland_pooled_v2', train_years=f'{FIRST_YEAR}-2026', train_n=len(train),
        training_end=training_end.isoformat(), params=PARAMS, features=features, modelled_targets=MODELLED,
        renewable_share='sum of the five predicted sources', target_scaling='standardized with training mean/std',
        versions=dict(python=platform.python_version(), sklearn=sklearn.__version__, xgboost=xgboost.__version__,
                      numpy=np.__version__, pandas=pd.__version__),
        duration_seconds=time.monotonic() - started, complete=True), indent=2, ensure_ascii=False))
    print('n=', len(train), 'Trainingsende', training_end)
    print(OUT)


if __name__ == '__main__':
    main()
