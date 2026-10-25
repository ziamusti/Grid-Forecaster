"""Fit final fixed HGB/XGB models using the final OLS train-only transformer."""
import copy
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from train_hist_stage0 import PARAMS, estimator
from train_linear_stage0 import sha
from train_mean_baseline import TARGETS

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/stage0_v2_sunshine'
LINEAR=ROOT/'reports/final_linear_2015_2026_v1'


def main(xgb=False):
    method='xgboost' if xgb else 'hist_gradient_boosting'
    out=ROOT/'reports'/f'final_{method}_2015_2026_v1'
    if out.exists():
        raise FileExistsError('Final experiment already exists; never overwrite it')
    linear_run=json.loads((LINEAR/'run.json').read_text())
    development=json.loads((ROOT/'reports'/f'{method}_v1/run.json').read_text())
    features=linear_run['features']
    assert features==development['features']
    params=PARAMS
    make_estimator=estimator
    if xgb:
        from xgboost import XGBRegressor
        params=dict(objective='reg:squarederror',n_estimators=100,learning_rate=.1,
                    max_depth=6,min_child_weight=1,subsample=1.,colsample_bytree=1.,
                    reg_alpha=0.,reg_lambda=1.,tree_method='hist',max_bin=255,
                    random_state=42,n_jobs=1,early_stopping_rounds=None)
        make_estimator=lambda:XGBRegressor(**params)
    assert params==development['params']
    columns=list(dict.fromkeys(['target_time_utc',*features,*TARGETS,*TARGETS.values()]))
    paths=[DATA/f'hourly_{year}.csv' for year in range(2015,2027)]
    hashes={str(path.relative_to(ROOT)):sha(path) for path in paths}
    data=pd.concat([pd.read_csv(path,usecols=columns) for path in paths],ignore_index=True)
    times=pd.to_datetime(data.target_time_utc,utc=True)
    expected=pd.date_range('2015-01-01','2026-09-23T23:00:00',freq='h',tz='UTC')
    assert pd.DatetimeIndex(times).equals(expected)
    out.mkdir(parents=True)
    records=[]
    started=time.monotonic()
    for target,flag in TARGETS.items():
        training=data.loc[data[flag]==1]
        x=training[features].to_numpy(float)
        y=training[target].to_numpy(float)
        assert np.isfinite(x).all() and np.isfinite(y).all()
        linear_bundle=joblib.load(LINEAR/f'linear_{target}.joblib')
        assert linear_bundle['training_n']==len(training)
        transformer=copy.deepcopy(linear_bundle['pipeline']['preprocess'])
        assert transformer.get_feature_names_out(features).tolist()==linear_run['transformed_features']
        numeric=[i for i,f in enumerate(features) if f not in ('hour_local','weekday','month')]
        np.testing.assert_allclose(transformer.named_transformers_['numeric'].mean_,x[:,numeric].mean(axis=0),rtol=1e-10,atol=1e-8)
        with threadpool_limits(limits=1):
            learner=make_estimator().fit(transformer.transform(x),y)
        if xgb:
            assert learner.get_booster().num_boosted_rounds()==100
        else:
            assert learner.n_iter_==100 and not learner.do_early_stopping_
        model=Pipeline([('preprocess',transformer),('regression',learner)])
        path=out/f'{method}_{target}.joblib'
        bundle=dict(pipeline=model,features=features,target=target,training_n=len(training),
                    training_start=str(times.iloc[0]),training_end=str(times.iloc[-1]),purpose='final_application_model')
        joblib.dump(bundle,path)
        loaded=joblib.load(path)
        with threadpool_limits(limits=1):
            a=model.predict(x[:100]); b=loaded['pipeline'].predict(x[:100])
        assert np.isfinite(a).all()
        np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-10)
        records.append(dict(target=target,training_n=len(training),model_sha256=sha(path)))
        print(target,len(training),flush=True)
    for rel,digest in hashes.items():assert sha(ROOT/rel)==digest
    manifest=dict(status='complete',purpose='Final application models; no internal test score',method=method,
        params=params,training_start='2015-01-01T00:00:00Z',training_end='2026-09-23T23:00:00Z',
        available_hours=len(data),features=features,transformed_features=linear_run['transformed_features'],
        models=records,source_sha256=hashes,script_sha256=sha(Path(__file__)),
        versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__),
        duration_seconds=time.monotonic()-started,
        policy='All eligible available rows; fixed prior parameters; final OLS train-fitted preprocessing; no clipping',
        evaluation_reference=['development validation 2018-2024','held-out 2025','partial-year 2026'],
        caveats=['No unused holdout remains after final refit','Retrospective ERA5/revised targets/MaStR net proxy'])
    if xgb:
        import xgboost
        manifest['versions']['xgboost']=xgboost.__version__
    (out/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--xgboost',action='store_true')
    main(xgb=parser.parse_args().xgboost)
