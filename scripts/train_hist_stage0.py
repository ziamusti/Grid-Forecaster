"""Fixed HistGradientBoosting experiment on exactly the OLS comparison data."""
import copy
import json
import platform
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
from train_linear_stage0 import sha
from train_mean_baseline import TARGETS, metrics

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/stage0_v2_sunshine'
REFERENCE=ROOT/'reports/linear_regression_v1'
OUT=ROOT/'reports/hist_gradient_boosting_v1'
PARAMS=dict(loss='squared_error',learning_rate=.1,max_iter=100,max_leaf_nodes=31,
            max_depth=None,min_samples_leaf=20,l2_regularization=0.,max_bins=255,
            early_stopping=False,random_state=42,categorical_features=None)


def estimator():
    return HistGradientBoostingRegressor(**PARAMS)


def main(xgb=False, test_2025=False, test_2026=False):
    assert not (test_2025 and test_2026)
    test_year=2026 if test_2026 else 2025 if test_2025 else None
    experiment = 'xgboost' if xgb else 'hist_gradient_boosting'
    OUT=ROOT/'reports'/(experiment+(f'_test{test_year}_v1' if test_year else '_v1'))
    REFERENCE=ROOT/'reports'/(f'linear_regression_test{test_year}_v1' if test_year else 'linear_regression_v1')
    method_name='xgboost' if xgb else 'hist_gradient_boosting'
    methods=[method_name,'linear','mean','week']
    params=PARAMS
    make_estimator=estimator
    if xgb:
        from xgboost import XGBRegressor
        params=dict(objective='reg:squarederror',n_estimators=100,learning_rate=.1,
                    max_depth=6,min_child_weight=1,subsample=1.,colsample_bytree=1.,
                    reg_alpha=0.,reg_lambda=1.,tree_method='hist',max_bin=255,
                    random_state=42,n_jobs=1,early_stopping_rounds=None)
        make_estimator=lambda: XGBRegressor(**params)
    if OUT.exists():
        raise FileExistsError('Never overwrite a completed or partial experiment')
    reference=json.loads((REFERENCE/'run.json').read_text())
    folds=reference['folds']
    assert [f['validation_year'] for f in folds]==([test_year] if test_year else list(range(2018,2025)))
    if test_year:
        previous_run=json.loads((ROOT/'reports'/f'{experiment}_v1/run.json').read_text())
        assert params==previous_run['params']
        assert reference['features']==previous_run['features']
        assert reference['transformed_features']==previous_run['transformed_features']
    for f in folds:
        assert f['train_years']==list(range(f['validation_year']-3,f['validation_year']))
    hashes=dict(reference['source_sha256'])
    assert not any((not test_2026 and '2026.csv' in p) or (not test_year and '2025.csv' in p) for p in hashes)
    for p,h in hashes.items():
        assert sha(ROOT/p)==h
    features=reference['features']
    cols=list(dict.fromkeys(['target_time_utc',*features,*TARGETS,*TARGETS.values()]))
    data={y:pd.read_csv(DATA/f'hourly_{y}.csv',usecols=cols) for y in (range(test_year-3,test_year+1) if test_year else range(2015,2025))}
    OUT.mkdir(parents=True)
    results=[]
    diagnostics=[]
    pooled={(t,m):([],[]) for t in TARGETS for m in methods}
    start=time.monotonic()
    for fold in folds:
        year=fold['validation_year']
        train=pd.concat([data[y] for y in fold['train_years']],ignore_index=True)
        for target,flag in TARGETS.items():
            tr=train.loc[train[flag]==1]
            val=data[year].loc[data[year][flag]==1]
            modelpath=REFERENCE/f'model_{year}_{target}.joblib'
            predpath=REFERENCE/f'predictions_{year}_{target}.csv'
            hashes[str(modelpath.relative_to(ROOT))]=sha(modelpath)
            hashes[str(predpath.relative_to(ROOT))]=sha(predpath)
            bundle=joblib.load(modelpath)
            assert bundle['fold']==fold and bundle['features']==features and bundle['target']==target
            transformer=copy.deepcopy(bundle['pipeline']['preprocess'])
            x=tr[features].to_numpy(float)
            xv=val[features].to_numpy(float)
            y=tr[target].to_numpy(float)
            assert np.isfinite(x).all() and np.isfinite(xv).all() and np.isfinite(y).all()
            # Independently confirm reused scaler was fitted on these training rows only.
            numeric=[i for i,f in enumerate(features) if f not in ('hour_local','weekday','month')]
            np.testing.assert_allclose(transformer.named_transformers_['numeric'].mean_,x[:,numeric].mean(axis=0),rtol=1e-10,atol=1e-8)
            assert transformer.get_feature_names_out(features).tolist()==reference['transformed_features']
            baseline=pd.read_csv(predpath)
            assert baseline.target_time_utc.tolist()==val.target_time_utc.tolist()
            np.testing.assert_allclose(baseline.actual.to_numpy(),val[target].to_numpy(),rtol=1e-12,atol=1e-9)
            with threadpool_limits(limits=1):
                learner=make_estimator().fit(transformer.transform(x),y)
                model=Pipeline([('preprocess',transformer),('regression',learner)])
                prediction=model.predict(xv)
            if xgb:
                assert learner.get_booster().num_boosted_rounds()==100
            else:
                assert learner.n_iter_==100 and not learner.do_early_stopping_
            assert np.isfinite(prediction).all()
            baseline[method_name]=prediction
            common=baseline.loc[baseline.common_scored==1]
            for method in methods:
                actual=common.actual.tolist()
                predicted=common[method].tolist()
                stats=metrics(actual,predicted)
                results.append(dict(validation_year=year,target=target,method=method,train_n=len(tr) if method!='week' else 0,**stats))
                pooled[target,method][0].extend(actual)
                pooled[target,method][1].extend(predicted)
            baseline.to_csv(OUT/f'predictions_{year}_{target}.csv',index=False)
            dest=OUT/f'model_{year}_{target}.joblib'
            joblib.dump(dict(pipeline=model,features=features,target=target,fold=fold),dest)
            with threadpool_limits(limits=1):
                np.testing.assert_allclose(joblib.load(dest)['pipeline'].predict(xv),prediction,rtol=1e-12,atol=1e-10)
            diagnostics.append(dict(year=year,target=target,train_n=len(tr),eligible_n=len(val),common_n=len(common),
                missing_week=len(val)-len(common),below_zero=int((prediction<0).sum()),
                above_100=int((prediction>100).sum()) if target.endswith('pct') else None,
                minimum=float(prediction.min()),maximum=float(prediction.max())))
            print(year,target,method_name,'MAE model/linear:',results[-4]['mae'],results[-3]['mae'],flush=True)
    pd.DataFrame(results).to_csv(OUT/'metrics_common.csv',index=False)
    summary=[dict(target=t,method=m,**metrics(a,p)) for (t,m),(a,p) in pooled.items()]
    pd.DataFrame(summary).to_csv(OUT/'metrics_pooled.csv',index=False)
    # Compare all unchanged reference scores, not only the pooled summary.
    previous=pd.read_csv(REFERENCE/'metrics_common.csv')
    for row in results:
        if row['method']==method_name: continue
        old=previous.loc[(previous.validation_year==row['validation_year'])&(previous.target==row['target'])&(previous.method==row['method'])].iloc[0]
        for field in ('n','mae','rmse','r2'):
            assert abs(old[field]-row[field])<1e-8
    for p,h in hashes.items(): assert sha(ROOT/p)==h
    manifest=dict(params=params,folds=folds,features=features,transformed_features=reference['transformed_features'],
        source_sha256=hashes,script_sha256=sha(Path(__file__)),pooled=summary,diagnostics=diagnostics,
        versions=dict(python=platform.python_version(),sklearn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__),
        duration_seconds=time.monotonic()-start,complete=True,
        policy='Fixed parameters before evaluation; exact OLS train-fitted preprocessing reused; no tuning or clipping',
        caveats=['Retrospective ERA5/revised targets/MaStR net proxy; not operational 72h test',
                 '2026 partial-year retrospective test' if test_2026 else '2025 held-out retrospective test; 2026 not read' if test_2025 else '2025/2026 not read'])
    if xgb:
        import xgboost
        manifest['versions']['xgboost']=xgboost.__version__
    (OUT/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--xgboost',action='store_true')
    parser.add_argument('--test-2025',action='store_true')
    parser.add_argument('--test-2026',action='store_true')
    args=parser.parse_args()
    main(xgb=args.xgboost,test_2025=args.test_2025,test_2026=args.test_2026)
