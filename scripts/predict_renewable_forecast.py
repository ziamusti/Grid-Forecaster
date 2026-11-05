"""Add renewable-share prediction (old, non-price model) to an existing price-CO2 forecast.

Reuses the already-built inputs.csv from predict_price_forecast.py (same 23-
location weather forecast, same SMARD/capacity inputs) and runs it through the
old final model (reports/final_hist_gradient_boosting_2015_2026_v1, 136
features, no price, training end 2026-09-23) for target_renewable_share_pct.
That training end is also before the forecast day, so this is genuinely
unseen for this model too.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
OLD_MODEL_DIR = ROOT / 'reports/final_hist_gradient_boosting_2015_2026_v1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forecast-dir', type=Path, required=True)
    args = parser.parse_args()
    forecast_dir = args.forecast_dir.resolve()
    inputs = pd.read_csv(forecast_dir / 'inputs.csv')
    predictions = pd.read_csv(forecast_dir / 'predictions.csv')

    run = json.loads((OLD_MODEL_DIR / 'run.json').read_text())
    features = run['features']
    assert len(features) == 136 and 'price_eur_mwh_lag168h' not in features
    bundle = joblib.load(OLD_MODEL_DIR / 'hist_gradient_boosting_target_renewable_share_pct.joblib')
    assert bundle['features'] == features
    assert pd.Timestamp(bundle['training_end']) < pd.Timestamp(predictions.target_time_utc.iloc[0])

    x = inputs[features].to_numpy(float)
    assert np.isfinite(x).all()
    with threadpool_limits(limits=1):
        pred = bundle['pipeline'].predict(x)
    assert np.isfinite(pred).all()

    predictions['predicted_renewable_share_pct'] = pred
    predictions.to_csv(forecast_dir / 'predictions.csv', index=False)

    manifest_path = forecast_dir / 'run.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['renewable_share_added'] = dict(
        model=str((OLD_MODEL_DIR / 'hist_gradient_boosting_target_renewable_share_pct.joblib').relative_to(ROOT)),
        model_training_end=bundle['training_end'],
        note='Old non-price model; this forecast day is unseen for it too (training end 2026-09-23)')
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(predictions[['target_time_utc', 'predicted_renewable_share_pct']].to_string(index=False))


if __name__ == '__main__':
    main()
