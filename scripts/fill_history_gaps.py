"""Dashboard-only predictions for hours the expanding-window tests skipped.

The tests only score hours with all inputs and targets present, so the dashboard
history has gaps (e.g. national 2018 where SMARD lag inputs are missing, all
Bundeslaender 27.-31.08.2026 where Energy-Charts has no generation). For each
test year with skipped hours, the step model is refitted exactly as in the test
(same training rows 2015..year-1, same parameters) and predicts the skipped
hours; missing inputs stay empty (XGBoost handles NaN). Not used for any metric.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import train_bundesland_xgb_expanding as bl
import train_xgb_selfco2_expanding as nat
from train_linear_expanding import FIRST_YEAR, PRICE_FEATURE, TEST_YEARS

ROOT = Path(__file__).resolve().parents[1]
NAT_OUT = ROOT / 'reports/xgboost_selfco2_separate_expanding_v1/gap_fill.csv'
BL_OUT = ROOT / 'reports/xgboost_bundesland_stage2_expanding_v1/dashboard/gap_fill.csv.gz'


def national():
    schema = json.loads((nat.FEATURES_DATA / 'feature_schema.json').read_text())
    features = [f for f in schema['features'] if f != 'is_weekend']
    data = {y: nat.load_year(y, features)[0] for y in range(FIRST_YEAR, 2027)}
    parts = []
    for year in TEST_YEARS:
        frame = pd.read_csv(nat.FEATURES_DATA / f'hourly_{year}.csv', usecols=['target_time_utc', *features])
        skipped = frame[~frame.target_time_utc.isin(data[year].target_time_utc)].reset_index(drop=True)
        # Calendar columns must be present for the one-hot encoding.
        skipped = skipped.dropna(subset=['hour_local', 'weekday', 'month'])
        if skipped.empty:
            continue
        train = pd.concat([data[y] for y in range(FIRST_YEAR, year)], ignore_index=True)
        predicted = nat.fit_predict(features, train[features].to_numpy(float), train[nat.TARGETS].to_numpy(float),
                                    skipped[features].to_numpy(float), multi=False)
        out = skipped[['target_time_utc']].copy()
        for k, target in enumerate(nat.TARGETS):
            out[f'predicted_{target}'] = predicted[:, k]
        out['test_year'] = year
        parts.append(out)
        print('national', year, 'Luecken-Stunden:', len(out), flush=True)
    pd.concat(parts, ignore_index=True).to_csv(NAT_OUT, index=False)


def bundesland():
    schema = json.loads((bl.DATA / 'feature_schema.json').read_text())
    features, categories = schema['stage2'], schema['categories']
    required = [f for f in features if not f.startswith('station2__')]
    data, raw = {}, {}
    for year in range(FIRST_YEAR, 2027):
        frame = pd.read_csv(bl.DATA / f'hourly_{year}.csv', usecols=['target_time_utc', *features, *schema['targets']])
        mask = frame[schema['targets']].notna().all(axis=1) & frame[required].notna().all(axis=1)
        data[year], raw[year] = frame.loc[mask].reset_index(drop=True), frame.loc[~mask].reset_index(drop=True)
    parts = []
    for year in TEST_YEARS:
        skipped = raw[year]
        if skipped.empty:
            continue
        train = pd.concat([data[y] for y in range(FIRST_YEAR, year)], ignore_index=True)
        out = skipped[['target_time_utc', 'bundesland']].copy()
        for target in bl.MODELLED:
            y = train[target].to_numpy(float)
            mean, std = y.mean(), y.std()
            fitted = bl.model(features, categories).fit(train[features], (y - mean) / std)
            out[f'predicted_{target}'] = fitted.predict(skipped[features]) * std + mean
        out['test_year'] = year
        parts.append(out)
        print('bundesland', year, 'Luecken-Zeilen:', len(out), flush=True)
    filled = pd.concat(parts, ignore_index=True)
    slim = pd.DataFrame({'target_time_utc': filled.target_time_utc, 'bundesland': filled.bundesland,
                         'predicted_co2': filled.predicted_target_co2_gco2eq_kwh})
    for target in bl.SOURCE_TARGETS:
        slim['predicted_' + target.removeprefix('target_').removesuffix('_share_pct')] = filled['predicted_' + target]
    slim['actual_co2'] = np.nan
    slim['actual_renewable'] = np.nan
    slim.round(2).to_csv(BL_OUT, index=False)


def main():
    for path in (NAT_OUT, BL_OUT):
        if path.exists():
            raise FileExistsError(f'{path} existiert bereits; kein Ueberschreiben.')
    national()
    bundesland()


if __name__ == '__main__':
    main()
