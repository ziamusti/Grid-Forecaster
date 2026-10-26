"""Compare frozen 72h predictions against already-fetched provider actuals; no fitting."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / 'reports/hist_prediction_20260930_02_v1/predictions.csv'
ACTUALS = ROOT / 'reports/actuals_20260930_02_v1/actuals.csv'
OUT = ROOT / 'reports/comparison_20260930_02_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError('Comparison already exists; no overwrite')
    pred = pd.read_csv(PRED)
    actual = pd.read_csv(ACTUALS)
    assert len(pred) == len(actual) == 72
    assert list(pred.target_time_utc) == list(actual.target_time_utc)
    frame = pred[['target_time_utc', 'target_time_berlin']].copy()
    frame['predicted_co2_gco2eq_kwh'] = pred['predicted_co2_gco2eq_kwh']
    frame['actual_co2_gco2eq_kwh'] = actual['actual_co2_gco2eq_kwh']
    frame['predicted_renewable_share_pct'] = pred['predicted_renewable_share_pct']
    frame['actual_renewable_share_pct'] = actual['actual_renewable_share_pct']
    metrics = {}
    for target in ['co2_gco2eq_kwh', 'renewable_share_pct']:
        diff = frame['predicted_' + target] - frame['actual_' + target]
        frame['error_' + target] = diff
        metrics[target] = dict(mae=float(diff.abs().mean()), rmse=float(np.sqrt((diff ** 2).mean())),
            bias=float(diff.mean()), predicted_mean=float(frame['predicted_' + target].mean()),
            actual_mean=float(frame['actual_' + target].mean()))
    OUT.mkdir()
    frame.to_csv(OUT / 'comparison.csv', index=False)
    manifest = dict(hours=72, error_definition='prediction minus actual', metrics=metrics,
        sources={str(p.relative_to(ROOT)): sha(p) for p in [PRED, ACTUALS]},
        script_sha256=sha(Path(__file__)))
    (OUT / 'run.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(metrics, indent=2))
    print(frame.to_string(index=False))


if __name__ == '__main__':
    main()
