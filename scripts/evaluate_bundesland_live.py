"""Evaluate Bundesland predictions after the training end against Energy-Charts; no training.

- Predictions: a predictions.csv (e.g. the archived-forecast backtest) or, by
  default, what the dashboard shows (dashboard_logic.load_bundesland_predictions).
- Truth: fresh download of the Energy-Charts weekly per-state files for the
  period (own folder, the training raw files stay untouched), converted with the
  same UBA factors and source grouping as the model target
  (build_bundesland_v2.targets_from). Energy-Charts per-state generation is a
  Fraunhofer ISE model estimate, published about six days late.
- Metrics, all states pooled and per state: MAE, mean deviation (model - truth)
  for CO2 and renewable share; Ampel hit rate (dashboard thresholds); best
  3-hour window per state and UTC day (hit, extra CO2 versus the true best).
- Reference: expanding-window test of stage 2 (2018-2026), MAE pooled over all
  test years weighted by hours, from metrics.csv.
Writes into --out and never overwrites.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_bundesland_v2 import load_generation, targets_from
from evaluate_live_main_model import WINDOW_HOURS, window_check

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dashboard_logic import category, load_bundesland_predictions, read_bundesland_model_file  # noqa: E402

UTC = timezone.utc
BASE = 'https://www.energy-charts.info/charts/power/data/de_bl'
TEST_METRICS = ROOT / 'reports/xgboost_bundesland_stage2_expanding_v1/metrics.csv'
CO2, TOTAL = 'target_co2_gco2eq_kwh', 'target_renewable_share_pct'


def fetch_weeks(start, end, folder):
    folder.mkdir(parents=True)
    days = pd.date_range(start - timedelta(days=1), end + timedelta(days=1), freq='D')
    weeks = sorted({(d.isocalendar()[0], d.isocalendar()[1]) for d in days})
    paths = []
    for year, week in weeks:
        url = f'{BASE}/week_{year}_{week:02d}.json'
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Grid-Forecaster/1.0'}), timeout=60) as response:
                body = response.read()
        except HTTPError as error:
            if error.code == 404:  # week not published yet
                print('noch nicht veroeffentlicht:', url, flush=True)
                continue
            raise
        path = folder / f'week_{year}_{week:02d}.json'
        path.write_bytes(body)
        paths.append(path)
        time.sleep(0.2)
    (folder / 'manifest.json').write_text(json.dumps(dict(
        retrieved_at_utc=datetime.now(UTC).isoformat(), endpoint=BASE, weeks=[p.name for p in paths],
        note='Fraunhofer ISE per-state generation estimate; recent weeks can still change'), indent=2))
    return paths


def test_reference():
    m = pd.read_csv(TEST_METRICS)
    m = m[m.target.isin([CO2, TOTAL])]
    ref = m.groupby(['bundesland', 'target']).apply(lambda g: np.average(g.mae, weights=g.n)).unstack()
    return ref.rename(columns={CO2: 'test_mae_co2', TOTAL: 'test_mae_renewable'})


def summary(g):
    ec, er = g.predicted_co2 - g.actual_co2, g.predicted_renewable - g.actual_renewable
    return pd.Series(dict(hours=len(g), mae_co2=ec.abs().mean(), bias_co2=ec.mean(),
                          mae_renewable=er.abs().mean(), bias_renewable=er.mean(),
                          ampel=(g.predicted_renewable.map(lambda v: category(v)[0])
                                 == g.actual_renewable.map(lambda v: category(v)[0])).mean()))


def plot_states(table, path, title):
    t = table.drop(index='alle').sort_values('mae_co2')
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.5), sharey=True)
    y = np.arange(len(t))
    for ax, (live, test, unit, name) in zip(axes, [('mae_co2', 'test_mae_co2', 'gCO₂/kWh', 'CO₂-Intensität'),
                                                   ('mae_renewable', 'test_mae_renewable', 'Prozentpunkte', 'Grünanteil')]):
        ax.barh(y + 0.2, t[live], 0.4, color='#16846a', label='Mein Modell − Energy-Charts (MAE)')
        ax.barh(y - 0.2, t[test], 0.4, color='#b5b5b5', label='Test 2018–2026 (MAE)')
        for yy, v in zip(y, t[live]):
            ax.text(v, yy + 0.2, f' {v:.1f}'.replace('.', ','), va='center', fontsize=8)
        ax.set_title(f'{name} – alle Länder: MAE {table.loc["alle", live]:.1f} (Test {table.loc["alle", test]:.1f})'
                     .replace('.', ','), loc='left', fontweight='bold', fontsize=10)
        ax.set_xlabel(unit); ax.grid(axis='x', alpha=0.3); ax.spines[['top', 'right']].set_visible(False)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=8, frameon=False)
    axes[0].set_yticks(y, t.index, fontsize=9)
    fig.suptitle(title, fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-11-12')
    parser.add_argument('--end', default='2026-12-11', help='last UTC day (inclusive)')
    parser.add_argument('--predictions', type=Path, default=None)
    parser.add_argument('--label', default='Live')
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    end = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=UTC) + timedelta(days=1)
    out = args.out or ROOT / f'reports/live_evaluation_bundesland_{start:%Y%m%d}_{end - timedelta(days=1):%Y%m%d}'
    if out.exists():
        raise FileExistsError(f'{out} existiert bereits; kein Ueberschreiben.')
    out.mkdir(parents=True)

    pred = read_bundesland_model_file(args.predictions) if args.predictions else load_bundesland_predictions(ROOT)
    pred = pred[(pred.time_utc >= start) & (pred.time_utc < end)]
    pred = pred[['time_utc', 'bundesland', 'predicted_co2', 'predicted_renewable']]
    truth = targets_from(load_generation(fetch_weeks(start, end, out / 'energycharts')))
    truth = truth[[CO2, TOTAL]].rename(columns={CO2: 'actual_co2', TOTAL: 'actual_renewable'}).reset_index()
    truth = truth.rename(columns={'target_time_utc': 'time_utc'})
    data = pred.merge(truth, on=['time_utc', 'bundesland'], how='inner').dropna(subset=['actual_co2', 'actual_renewable'])
    if data.empty:
        raise SystemExit('Keine Stunden mit Vorhersage und Energy-Charts-Wert.')
    data.to_csv(out / 'hourly.csv', index=False)

    table = pd.concat([summary(data).rename('alle').to_frame().T,
                       data.groupby('bundesland').apply(summary)])
    table = table.join(test_reference(), how='left')
    windows = pd.concat([window_check(g.reset_index(drop=True)).assign(bundesland=land)
                         for land, g in data.groupby('bundesland')], ignore_index=True)
    windows.to_csv(out / 'best_window_per_state_day.csv', index=False)
    table.loc['alle', 'window_hit'] = windows.hit.mean() if len(windows) else np.nan
    table.loc['alle', 'window_extra_co2'] = windows.extra_co2.mean() if len(windows) else np.nan
    for land, g in windows.groupby('bundesland'):
        table.loc[land, 'window_hit'] = g.hit.mean(); table.loc[land, 'window_extra_co2'] = g.extra_co2.mean()
    table.round(3).to_csv(out / 'metrics_per_state.csv', index_label='bundesland')
    (out / 'run.json').write_text(json.dumps(dict(
        label=args.label, predictions_file=str(args.predictions) if args.predictions else 'dashboard',
        period_utc=[start.isoformat(), end.isoformat()], rows_evaluated=len(data),
        hours_evaluated=int(data.time_utc.nunique()), last_hour=data.time_utc.max().isoformat(),
        window_hours=WINDOW_HOURS, window_days=len(windows),
        truth='Energy-Charts per-state generation (fresh download), UBA factors as model target',
        test_reference=str(TEST_METRICS.relative_to(ROOT))), indent=2))
    plot_states(table, out / 'fehler_pro_land.png',
                f'{args.label}: Bundesland-Modell {start:%d.%m.} bis {data.time_utc.max():%d.%m.%Y %H:%M} UTC '
                f'({data.time_utc.nunique()} Stunden × 16 Länder), Maßstab Energy-Charts')
    pd.set_option('display.width', 200)
    print(table.round(2).to_string())
    print(out)


if __name__ == '__main__':
    main()
