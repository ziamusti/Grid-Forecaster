"""Vergleich XGBoost getrennt (8 Modelle) vs. Mehrziel (1 Modell), selbst berechnetes CO2.

Nur Auswertung vorhandener Vorhersagen, kein Training. Gleiche Teststunden werden geprueft.
Ausgabe: gepoolte Metriken, Tages-Block-Bootstrap der MAE-Differenz, Diagramme.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from compare_expanding_models import BOOTSTRAP, bootstrap_mae_gap
from plot_linear_expanding import SOURCES
from train_linear_expanding import RENEWABLE_SOURCES, TEST_YEARS, metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/xgboost_separate_vs_multi_v1'
CO2, TOTAL = 'target_co2_gco2eq_kwh', 'target_renewable_share_pct'
SEPARATE, MULTI, BOTTOM_UP = 'Getrennt (8 Modelle)', 'Mehrziel (1 Modell)', 'Getrennt, Summe der 6 Quellen'
COLORS = {SEPARATE: '#2a78d6', MULTI: '#eb6834', BOTTOM_UP: '#1baf7a'}
NOTE = 'XGBoost 2.1.4; je Testjahr gelernt aus 2015 bis Vorjahr; gleiche Eingaben und Teststunden'


def load(folder):
    return pd.concat([pd.read_csv(ROOT / 'reports' / folder / f'predictions_{y}.csv').assign(test_year=y)
                      for y in TEST_YEARS], ignore_index=True)


def clean(ax):
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)


def line_plot(series, ylabel, title, filename, legend='lower right'):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for name, values in series.items():
        ax.plot(TEST_YEARS, values, color=COLORS[name], lw=2, marker='o', ms=8, label=name,
                markeredgecolor='white', markeredgewidth=2)
    ax.set_xticks(TEST_YEARS); ax.set_ylabel(ylabel)
    ax.grid(axis='y', color='#e5e5e5', lw=0.6); clean(ax)
    ax.legend(frameon=False, loc=legend)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    ax.annotate(NOTE, xy=(0.5, -0.13), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout(); fig.savefig(OUT / filename, dpi=150); plt.close(fig)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    separate, multi = load('xgboost_selfco2_separate_expanding_v1'), load('xgboost_selfco2_multi_expanding_v1')
    assert separate.target_time_utc.tolist() == multi.target_time_utc.tolist()
    separate['predicted_bottom_up'] = separate[[f'predicted_{t}' for t in RENEWABLE_SOURCES]].sum(axis=1)
    OUT.mkdir(parents=True)

    def r2_per_year(frame, target, column=None):
        column = column or f'predicted_{target}'
        return [metrics(frame.loc[frame.test_year == y, f'actual_{target}'].to_numpy(),
                        frame.loc[frame.test_year == y, column].to_numpy())['r2'] for y in TEST_YEARS]

    line_plot({SEPARATE: r2_per_year(separate, CO2), MULTI: r2_per_year(multi, CO2)}, 'R²',
              'CO₂-Intensität (selbst berechnet): R² je Testjahr', 'co2_r2_per_year.png')
    line_plot({SEPARATE: r2_per_year(separate, TOTAL), BOTTOM_UP: r2_per_year(separate, TOTAL, 'predicted_bottom_up'),
               MULTI: r2_per_year(multi, TOTAL)}, 'R²', 'Grünanteil: R² je Testjahr', 'renewable_share_r2_per_year.png', legend='lower left')

    rows, rng = [], np.random.default_rng(42)
    days = pd.to_datetime(separate.target_time_utc, utc=True).dt.date
    for target in [CO2, TOTAL, *RENEWABLE_SOURCES]:
        actual = separate[f'actual_{target}'].to_numpy()
        err_s = separate[f'predicted_{target}'].to_numpy() - actual
        err_m = multi[f'predicted_{target}'].to_numpy() - actual
        gap, low, high = bootstrap_mae_gap(err_s, err_m, days, rng)
        rows.append(dict(target=target, **{f'{k}_separate': v for k, v in metrics(actual, actual + err_s).items()},
                         **{f'{k}_multi': v for k, v in metrics(actual, actual + err_m).items()},
                         mae_separate_minus_multi=gap, ci95_low=low, ci95_high=high))
    actual = separate[f'actual_{TOTAL}'].to_numpy()
    gap, low, high = bootstrap_mae_gap(separate.predicted_bottom_up.to_numpy() - actual,
                                       separate[f'predicted_{TOTAL}'].to_numpy() - actual, days, rng)
    rows.append(dict(target='bottom_up_minus_direct_separate', mae_separate_minus_multi=gap, ci95_low=low, ci95_high=high,
                     **{f'{k}_separate': v for k, v in metrics(actual, separate.predicted_bottom_up.to_numpy()).items()}))
    table = pd.DataFrame(rows)
    table.to_csv(OUT / 'metrics_pooled_and_bootstrap.csv', index=False)

    labels = list(SOURCES.values())
    r2 = {SEPARATE: [table.loc[table.target == t, 'r2_separate'].item() for t in SOURCES],
          MULTI: [table.loc[table.target == t, 'r2_multi'].item() for t in SOURCES]}
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for offset, name in [(-0.19, SEPARATE), (0.19, MULTI)]:
        bars = ax.barh(y + offset, r2[name], 0.36, color=COLORS[name], label=name, edgecolor='white', linewidth=2)
        for bar, value in zip(bars, r2[name]):
            ax.annotate(f'{value:.3f}', (value, bar.get_y() + bar.get_height() / 2), xytext=(4, 0),
                        textcoords='offset points', va='center', fontsize=8.5)
    ax.set_yticks(y); ax.set_yticklabels(labels); ax.invert_yaxis(); ax.set_xlim(0, 1.08); ax.set_xlabel('R² (alle Teststunden 2018-2026)')
    ax.grid(axis='x', color='#e5e5e5', lw=0.6); clean(ax); ax.legend(frameon=False, loc='lower right')
    ax.set_title('Erneuerbare Quellen: R² getrennt vs. Mehrziel', fontsize=12, fontweight='bold', pad=12)
    ax.annotate(NOTE, xy=(0.5, -0.16), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout(); fig.savefig(OUT / 'sources_r2_pooled.png', dpi=150); plt.close(fig)

    (OUT / 'run.json').write_text(json.dumps(dict(
        inputs=['reports/xgboost_selfco2_separate_expanding_v1', 'reports/xgboost_selfco2_multi_expanding_v1'],
        test_hours=len(separate), bootstrap=dict(resamples=BOOTSTRAP, block='UTC day', seed=42, interval='95% percentile'),
        note='Nur Auswertung vorhandener Vorhersagen, kein Training.'), indent=2))
    print(table.round(3).to_string())
    for path in sorted(OUT.glob('*.png')):
        print(path)


if __name__ == '__main__':
    main()
