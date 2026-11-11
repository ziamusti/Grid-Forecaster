"""Main-model prediction (XGBoost separate, self-computed CO2) for an existing forecast folder.

Reuses inputs.csv built by predict_price_forecast.py (or predict_price_backtest.py):
same 137 inputs (23-location weather, calendar, capacity, 168h lags incl. price).
Writes into predictions.csv in place:
- predicted_co2_gco2eq_kwh: self-computed CO2 (direct emissions, gCO2/kWh)
- predicted_<source>_share_pct for the six renewable sources, cut off at 0
  (trees can return slightly negative shares, mostly solar at night)
- predicted_renewable_share_pct: sum of the six sources (main output)
- predicted_renewable_share_direct_pct: the direct renewable-share model, for comparison
Earlier HistGradientBoosting values in that file are kept under hist_gradient_boosting_* names.
"""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'reports/final_xgboost_selfco2_2015_20261026_v1/xgboost_selfco2_separate.joblib'
SOURCES = ['biomass', 'hydro', 'wind_offshore', 'wind_onshore', 'solar', 'other_renewables']
MARKER = 'predicted_renewable_share_direct_pct'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forecast-dir', type=Path, required=True)
    args = parser.parse_args()
    forecast_dir = args.forecast_dir.resolve()
    inputs = pd.read_csv(forecast_dir / 'inputs.csv')
    predictions = pd.read_csv(forecast_dir / 'predictions.csv')
    if MARKER in predictions.columns:
        raise SystemExit('XGBoost-Hauptmodell wurde fuer diesen Ordner schon angewendet; kein Ueberschreiben.')
    assert inputs.target_time_utc.tolist() == predictions.target_time_utc.tolist()

    bundle = joblib.load(MODEL)
    assert pd.Timestamp(bundle['training_end']) < pd.Timestamp(predictions.target_time_utc.iloc[0])
    x = inputs[bundle['features']].to_numpy(float)
    assert np.isfinite(x).all()
    values = {}
    with threadpool_limits(limits=1):
        for target in bundle['targets']:
            z = bundle['pipelines'][target].predict(x)
            values[target] = z * bundle['target_std'][target] + bundle['target_mean'][target]
            assert np.isfinite(values[target]).all()

    for old in ['predicted_co2_gco2eq_kwh', 'predicted_renewable_share_pct']:
        if old in predictions.columns:
            predictions = predictions.rename(columns={old: old.replace('predicted_', 'hist_gradient_boosting_')})
    predictions['predicted_co2_gco2eq_kwh'] = values['target_co2_gco2eq_kwh']
    for source in SOURCES:
        predictions[f'predicted_{source}_share_pct'] = np.clip(values[f'target_{source}_share_pct'], 0, None)
    # Sources summing to more than 100 % are scaled down proportionally; CO2 at least 0.
    shares = predictions[[f'predicted_{s}_share_pct' for s in SOURCES]]
    shares = shares.mul((100 / shares.sum(axis=1)).clip(upper=1), axis=0)
    predictions[shares.columns] = shares
    predictions['predicted_renewable_share_pct'] = shares.sum(axis=1)
    predictions['predicted_co2_gco2eq_kwh'] = np.clip(predictions['predicted_co2_gco2eq_kwh'], 0, None)
    predictions[MARKER] = values['target_renewable_share_pct']
    predictions.to_csv(forecast_dir / 'predictions.csv', index=False)

    manifest_path = forecast_dir / 'run.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['main_model_xgboost_selfco2'] = dict(
        model=str(MODEL.relative_to(ROOT)), model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        model_training_end=bundle['training_end'],
        co2='self-computed (SMARD + UBA factors, direct emissions, gCO2/kWh)',
        renewable_share='sum of the six predicted sources; direct model kept as ' + MARKER,
        clipping='source shares cut off at 0, scaled to 100 % if their sum exceeds it; CO2 at least 0',
        previous_hist_gradient_boosting_columns_kept=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(predictions[['target_time_utc', 'predicted_co2_gco2eq_kwh', 'predicted_renewable_share_pct']].to_string(index=False))


if __name__ == '__main__':
    main()
