"""Evaluate the final price model (trained through 2026-06-30) on 2026-07-01..2026-09-23.

This period is held out from that model's training. Inputs and actual CO2
targets (Electricity Maps, already used as training targets for earlier
years) both already exist in data/processed/stage0_v3_price/hourly_2026.csv;
no new download needed.
"""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/stage0_v3_price'
MODEL = ROOT / 'reports/final_hist_gradient_boosting_price_2015_20260630_v1/hist_gradient_boosting_target_co2_gco2eq_kwh.joblib'
OUT = ROOT / 'reports/price_model_eval_20260701_0923_v1'


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    bundle = joblib.load(MODEL)
    model = bundle['pipeline']
    features = bundle['features']
    assert bundle['target'] == 'target_co2_gco2eq_kwh'
    assert bundle['training_end'] == '2026-06-30 23:00:00+00:00'

    df = pd.read_csv(DATA / 'hourly_2026.csv')
    mask = (df.target_time_utc >= '2026-07-01') & (df.target_time_utc < '2026-09-24')
    sub = df.loc[mask].copy().reset_index(drop=True)
    assert len(sub) == 2040
    assert sub.eligible_co2_nonestimated.eq(1).all()
    assert sub.co2_is_estimated.eq(0).all()
    assert sub.target_co2_gco2eq_kwh.notna().all()

    x = sub[features].to_numpy(float)
    assert np.isfinite(x).all()
    pred = model.predict(x)
    assert np.isfinite(pred).all()
    actual = sub.target_co2_gco2eq_kwh.to_numpy(float)

    error = pred - actual
    mae = float(np.abs(error).mean())
    rmse = float(np.sqrt((error ** 2).mean()))
    bias = float(error.mean())
    r2 = float(1 - (error ** 2).sum() / ((actual - actual.mean()) ** 2).sum())

    OUT.mkdir(parents=True)
    result = pd.DataFrame(dict(target_time_utc=sub.target_time_utc.values,
                               actual_co2_gco2eq_kwh=actual, predicted_co2_gco2eq_kwh=pred, error=error))
    result.to_csv(OUT / 'predictions_vs_actual.csv', index=False)

    manifest = dict(
        period_start_utc='2026-07-01T00:00:00Z', period_end_exclusive_utc='2026-09-24T00:00:00Z',
        hours=len(sub), held_out=True,
        training_end_of_model='2026-06-30T23:00:00Z',
        metrics=dict(mae=mae, rmse=rmse, bias=bias, r2=r2,
                     actual_mean=float(actual.mean()), predicted_mean=float(pred.mean())),
        model_path=str(MODEL.relative_to(ROOT)),
        source_table=str((DATA / 'hourly_2026.csv').relative_to(ROOT)),
        actual_source='Electricity Maps lifecycle CO2, already present in the prepared table (same source as all other years targets); no new API pull for this evaluation',
        caveats=['Retrospective ERA5 weather for this period, not an as-issued forecast',
                 'Day-ahead price feature uses lag168h',
                 'Single 2040-hour window, not a full year; not directly comparable in magnitude to the pooled yearly test metrics'])
    (OUT / 'run.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
