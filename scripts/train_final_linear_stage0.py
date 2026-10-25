"""Fit final OLS deployment models on all available 2015-2026 rows."""
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from threadpoolctl import threadpool_limits

from train_linear_stage0 import pipeline, sha
from train_mean_baseline import TARGETS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/processed/stage0_v2_sunshine'
OUT = ROOT/'reports/final_linear_2015_2026_v1'


def main():
    if OUT.exists():
        raise FileExistsError('Final experiment already exists; never overwrite it')
    reference = json.loads((ROOT/'reports/linear_regression_v1/run.json').read_text())
    features = reference['features']
    assert len(features)==136 and len(reference['transformed_features'])==173
    columns = list(dict.fromkeys(['target_time_utc',*features,*TARGETS,*TARGETS.values()]))
    paths = [DATA/'feature_schema.json']+[DATA/f'hourly_{year}.csv' for year in range(2015,2027)]
    hashes = {str(path.relative_to(ROOT)):sha(path) for path in paths}
    frames = [pd.read_csv(path,usecols=columns) for path in paths[1:]]
    data = pd.concat(frames,ignore_index=True)
    times = pd.to_datetime(data.target_time_utc,utc=True)
    expected = pd.date_range('2015-01-01','2026-09-23T23:00:00',freq='h',tz='UTC')
    assert pd.DatetimeIndex(times).equals(expected)
    OUT.mkdir(parents=True)
    start = time.monotonic()
    models = []
    for target, flag in TARGETS.items():
        training = data.loc[data[flag]==1]
        x = training[features].to_numpy(float)
        y = training[target].to_numpy(float)
        assert np.isfinite(x).all() and np.isfinite(y).all()
        model = pipeline(features)
        with threadpool_limits(limits=1):
            model.fit(x,y)
        names = model['preprocess'].get_feature_names_out(features).tolist()
        assert names==reference['transformed_features']
        path = OUT/f'linear_{target}.joblib'
        bundle = dict(pipeline=model,features=features,target=target,
                      training_start=str(times.iloc[0]),training_end=str(times.iloc[-1]),
                      training_n=len(training),purpose='final_application_model')
        joblib.dump(bundle,path)
        loaded = joblib.load(path)
        with threadpool_limits(limits=1):
            np.testing.assert_allclose(loaded['pipeline'].predict(x[:100]),model.predict(x[:100]),rtol=1e-12,atol=1e-10)
        models.append(dict(target=target,training_n=len(training),rank=int(model['regression'].rank_),
                           transformed_features=len(names),model_sha256=sha(path)))
        print(target,len(training),flush=True)
    for rel,digest in hashes.items():
        assert sha(ROOT/rel)==digest
    manifest = dict(status='complete',purpose='Final application models; no internal test score',
        method='LinearRegression',training_start='2015-01-01T00:00:00Z',
        training_end='2026-09-23T23:00:00Z',available_hours=len(data),
        features=features,transformed_features=reference['transformed_features'],models=models,
        source_sha256=hashes,script_sha256=sha(Path(__file__)),
        versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__),
        policy='All eligible available rows; target-specific fit; train-only scaling; no clipping; fixed prior specification',
        evaluation_reference=['development validation 2018-2024','held-out 2025','partial-year 2026'],
        caveats=['No unused holdout remains after final refit','Retrospective ERA5/revised targets/MaStR net proxy'])
    manifest['duration_seconds']=time.monotonic()-start
    (OUT/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(models,indent=2))


if __name__=='__main__':
    main()
