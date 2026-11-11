"""Bundesland main-model prediction (XGBoost stage 2) for an existing Bundesland forecast folder.

Reuses inputs.csv of predict_bundesland_forecast.py / predict_bundesland_backtest.py
(stage-1 inputs: weather, capacity, calendar, Bundesland) and adds the stage-2 inputs:
- national values 168 h earlier from the national forecast folder's inputs.csv
  (12 SMARD technologies, grid load, day-ahead price),
- the Bundesland's own generation 336 h earlier from Energy-Charts weekly files
  (data/raw/energycharts_bundesland, see download_energycharts_bundesland.py).
Writes into predictions.csv in place: CO2 (self-computed), the five source shares
(cut off at 0) and the renewable share as their sum; earlier HistGradientBoosting
values are kept under hist_gradient_boosting_* names.
"""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from build_bundesland_v2 import NATIONAL_LAGS, RAW, STATE_LAGS, TECHS, load_generation

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'reports/final_xgboost_bundesland_2015_20261026_v1/xgboost_bundesland_stage2.joblib'
SOURCES = ['wind_onshore', 'solar', 'biomass', 'hydro', 'other_renewables']
MARKER = 'predicted_wind_onshore_share_pct'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundesland-dir', type=Path, required=True)
    parser.add_argument('--national-dir', type=Path, required=True)
    args = parser.parse_args()
    inputs = pd.read_csv(args.bundesland_dir / 'inputs.csv')
    predictions = pd.read_csv(args.bundesland_dir / 'predictions.csv')
    if MARKER in predictions.columns:
        raise SystemExit('XGBoost-Bundesland-Modell wurde fuer diesen Ordner schon angewendet; kein Ueberschreiben.')
    assert inputs[['target_time_utc', 'bundesland']].equals(predictions[['target_time_utc', 'bundesland']])
    times = pd.to_datetime(inputs.target_time_utc, utc=True)

    national = pd.read_csv(args.national_dir / 'inputs.csv', usecols=['target_time_utc', *NATIONAL_LAGS])
    national['target_time_utc'] = pd.to_datetime(national.target_time_utc, utc=True)
    frame = inputs.assign(target_time_utc=times).merge(national, on='target_time_utc', how='left', validate='many_to_one')

    lag_times = times - pd.Timedelta(hours=336)
    weeks = {(t.isocalendar()[0], t.isocalendar()[1]) for t in lag_times}
    paths = [RAW / str(y) / f'week_{y}_{w:02d}.json' for y, w in sorted(weeks)]
    missing = [str(p) for p in paths if not p.exists()]
    assert not missing, f'Energy-Charts-Wochendateien fehlen: {missing}'
    generation = load_generation(paths)[TECHS]
    generation.columns = STATE_LAGS
    lagged = generation.reindex(pd.MultiIndex.from_arrays([lag_times, inputs.bundesland]))
    frame[STATE_LAGS] = lagged.to_numpy()

    bundle = joblib.load(MODEL)
    assert pd.Timestamp(bundle['training_end']) < times.min()
    required = [f for f in bundle['features'] if f not in bundle['categories'] and not f.startswith('station2__')]
    missing_inputs = frame[required].isna().sum()
    assert not missing_inputs.any(), f'Fehlende Eingaben: {missing_inputs[missing_inputs > 0].to_dict()}'
    x = frame[bundle['features']]
    values = {t: bundle['pipelines'][t].predict(x) * bundle['target_std'][t] + bundle['target_mean'][t]
              for t in bundle['targets']}

    for old in ['predicted_co2_gco2eq_kwh', 'predicted_renewable_share_pct']:
        if old in predictions.columns:
            predictions = predictions.rename(columns={old: old.replace('predicted_', 'hist_gradient_boosting_')})
    predictions['predicted_co2_gco2eq_kwh'] = values['target_co2_gco2eq_kwh']
    for source in SOURCES:
        predictions[f'predicted_{source}_share_pct'] = np.clip(values[f'target_{source}_share_pct'], 0, None)
    predictions['predicted_renewable_share_pct'] = predictions[[f'predicted_{s}_share_pct' for s in SOURCES]].sum(axis=1)
    assert predictions.filter(like='predicted_').notna().all().all()
    predictions.to_csv(args.bundesland_dir / 'predictions.csv', index=False)

    manifest_path = args.bundesland_dir / 'run.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['main_model_xgboost_bundesland'] = dict(
        model=str(MODEL.relative_to(ROOT)), model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        model_training_end=bundle['training_end'], national_inputs=str(args.national_dir),
        state_generation_weeks=[p.name for p in paths],
        renewable_share='sum of the five predicted sources (cut off at 0)',
        previous_hist_gradient_boosting_columns_kept=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(predictions.groupby('bundesland')[['predicted_co2_gco2eq_kwh', 'predicted_renewable_share_pct']].mean().round(1).to_string())


if __name__ == '__main__':
    main()
