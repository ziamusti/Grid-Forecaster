"""Independent einsum prediction/metric audit; no fitting, no holdout files."""
import csv
import json
import hashlib
from pathlib import Path
import joblib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/linear_regression_v1'
DATA=ROOT/'data/processed/stage0_v2_sunshine'


def main():
    run=json.loads((OUT/'run.json').read_text())
    summary=list(csv.DictReader((OUT/'metrics_common.csv').open()))
    results=[]
    for year in range(2018,2025):
        with (DATA/f'hourly_{year}.csv').open() as f:
            source={r['target_time_utc']:r for r in csv.DictReader(f)}
        for target in ('target_co2_gco2eq_kwh','target_renewable_share_pct'):
            bundle=joblib.load(OUT/f'model_{year}_{target}.joblib')
            model=bundle['pipeline']
            rows=list(csv.DictReader((OUT/f'predictions_{year}_{target}.csv').open()))
            x=np.array([[float(source[r['target_time_utc']][f]) for f in bundle['features']] for r in rows])
            transformed=model['preprocess'].transform(x)
            alternative=np.einsum('ij,j->i',transformed,model['regression'].coef_,optimize=False)+model['regression'].intercept_
            saved=np.array([float(r['linear']) for r in rows])
            delta=float(np.max(np.abs(alternative-saved)))
            assert np.isfinite(alternative).all() and delta<1e-7
            # Original mean-baseline scores must reproduce the prior experiment.
            prior=list(csv.DictReader((ROOT/f'reports/mean_baseline_v1/predictions_{year}.csv').open()))
            means={r['target_time_utc']:float(r['prediction']) for r in prior if r['target']==target and r['scored']=='1'}
            assert set(means)=={r['target_time_utc'] for r in rows}
            assert all(abs(means[r['target_time_utc']]-float(r['mean']))<1e-8 for r in rows)
            common=[r for r in rows if r['common_scored']=='1']
            y=np.array([float(r['actual']) for r in common])
            for method in ('linear','mean','week'):
                p=np.array([float(r[method]) for r in common])
                expected=next(r for r in summary if r['validation_year']==str(year) and r['target']==target and r['method']==method)
                calculated=dict(mae=np.mean(np.abs(y-p)),rmse=np.sqrt(np.mean((y-p)**2)),r2=1-np.sum((y-p)**2)/np.sum((y-y.mean())**2))
                assert len(y)==int(expected['n'])
                assert all(abs(float(expected[k])-v)<1e-8 for k,v in calculated.items())
            results.append(dict(year=year,target=target,max_prediction_difference=delta,n=len(rows)))
    for filename, expected in run['source_sha256'].items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==expected
    (OUT/'verification.json').write_text(json.dumps(dict(passed=True,models=results,
        note='matmul warnings observed during original run; finite results independently reproduced by unoptimized einsum'),indent=2)+'\n')
    print('Verified 14 models, 42 metric rows, previous mean predictions and source hashes.')
    print('Maximum independent prediction difference:',max(r['max_prediction_difference'] for r in results))


if __name__=='__main__':
    main()
