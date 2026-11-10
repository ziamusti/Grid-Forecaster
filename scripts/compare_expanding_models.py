"""Vergleich Lineare Regression, HistGradientBoosting, XGBoost (national, wachsender Trainingszeitraum ab 2015).

Liest nur die fertigen Vorhersagen (kein Training). Gleiche Testzeilen werden geprueft.
Ausgabe: Tabellen je Testjahr, gepoolte Metriken 2018-2026, Siege, Tages-Block-Bootstrap
der MAE-Differenz, Diagramme R2 je Testjahr.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from train_linear_expanding import TEST_YEARS, metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/model_comparison_expanding_v1'
METHODS = {'Lineare Regression': ('linear_regression_expanding_v1', '#2a78d6'),
           'HistGradientBoosting': ('hist_gradient_boosting_expanding_v1', '#eb6834'),
           'XGBoost': ('xgboost_expanding_v1', '#1baf7a')}
TARGETS = {'target_co2_gco2eq_kwh': dict(slug='co2', label='CO₂-Intensität', unit='gCO₂eq/kWh'),
           'target_renewable_share_pct': dict(slug='renewable_share', label='Grünanteil', unit='%-Punkte')}
BOOTSTRAP = 2000


def load():
    frames = {}
    for method, (folder, _) in METHODS.items():
        parts = []
        for year in TEST_YEARS:
            p = pd.read_csv(ROOT / 'reports' / folder / f'predictions_{year}.csv')
            p['test_year'] = year
            parts.append(p)
        frames[method] = pd.concat(parts, ignore_index=True)
    base = frames['Lineare Regression']
    for method, frame in frames.items():
        assert frame.target_time_utc.tolist() == base.target_time_utc.tolist(), method
        for target in TARGETS:
            np.testing.assert_allclose(frame[f'actual_{target}'], base[f'actual_{target}'], rtol=1e-12, atol=1e-9)
    return frames


def bootstrap_mae_gap(err_a, err_b, days, rng):
    # Resample whole days, so that hours of one day stay together (errors within a day are correlated).
    gap = pd.Series(np.abs(err_a) - np.abs(err_b)).groupby(days.to_numpy())
    sums, counts = gap.sum().to_numpy(), gap.count().to_numpy()
    picks = rng.integers(0, len(sums), size=(BOOTSTRAP, len(sums)))
    values = sums[picks].sum(axis=1) / counts[picks].sum(axis=1)
    return float(np.mean(np.abs(err_a)) - np.mean(np.abs(err_b))), float(np.quantile(values, .025)), float(np.quantile(values, .975))


def plot_r2(yearly, target, cfg):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for method, (_, color) in METHODS.items():
        rows = yearly[(yearly.target == target) & (yearly.method == method)].sort_values('test_year')
        ax.plot(rows.test_year, rows.r2, color=color, lw=2, marker='o', ms=8, label=method,
                markeredgecolor='white', markeredgewidth=2)
    ax.set_xticks(TEST_YEARS)
    ax.set_ylabel('R²')
    ax.grid(axis='y', color='#e5e5e5', lw=0.6)
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, loc='lower right')
    ax.set_title(f'{cfg["label"]}: R² je Testjahr, drei Verfahren', fontsize=12, fontweight='bold', pad=12)
    ax.annotate('Je Testjahr gelernt aus 2015 bis Vorjahr; gleiche Eingaben und Teststunden für alle Verfahren',
                xy=(0.5, -0.13), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout()
    fig.savefig(OUT / f'{cfg["slug"]}_r2_comparison.png', dpi=150)
    plt.close(fig)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    frames = load()
    OUT.mkdir(parents=True)
    yearly, pooled, wins, gaps = [], [], [], []
    rng = np.random.default_rng(42)
    days = pd.to_datetime(frames['Lineare Regression'].target_time_utc, utc=True).dt.date
    for target in TARGETS:
        for method, frame in frames.items():
            for year in TEST_YEARS:
                rows = frame[frame.test_year == year]
                yearly.append(dict(target=target, method=method, test_year=year,
                                   **metrics(rows[f'actual_{target}'].to_numpy(), rows[f'predicted_{target}'].to_numpy())))
            pooled.append(dict(target=target, method=method,
                               **metrics(frame[f'actual_{target}'].to_numpy(), frame[f'predicted_{target}'].to_numpy()),
                               bias=float((frame[f'predicted_{target}'] - frame[f'actual_{target}']).mean())))
        table = pd.DataFrame([r for r in yearly if r['target'] == target])
        for year in TEST_YEARS:
            best = table[table.test_year == year].sort_values('mae').iloc[0]
            wins.append(dict(target=target, test_year=year, best_mae=best.method))
        errors = {m: (f[f'predicted_{target}'] - f[f'actual_{target}']).to_numpy() for m, f in frames.items()}
        for a, b in [('HistGradientBoosting', 'XGBoost'), ('HistGradientBoosting', 'Lineare Regression'),
                     ('XGBoost', 'Lineare Regression')]:
            gap, low, high = bootstrap_mae_gap(errors[a], errors[b], days, rng)
            gaps.append(dict(target=target, a=a, b=b, mae_a_minus_b=gap, ci95_low=low, ci95_high=high))
    yearly, pooled, wins, gaps = map(pd.DataFrame, (yearly, pooled, wins, gaps))
    yearly.to_csv(OUT / 'metrics_per_year.csv', index=False)
    pooled.to_csv(OUT / 'metrics_pooled_2018_2026.csv', index=False)
    wins.to_csv(OUT / 'best_per_year_by_mae.csv', index=False)
    gaps.to_csv(OUT / 'mae_gap_bootstrap.csv', index=False)
    for target, cfg in TARGETS.items():
        plot_r2(yearly, target, cfg)
    (OUT / 'run.json').write_text(json.dumps(dict(
        inputs={m: f'reports/{f}' for m, (f, _) in METHODS.items()}, test_years=TEST_YEARS,
        bootstrap=dict(resamples=BOOTSTRAP, block='UTC day', seed=42, interval='95% percentile'),
        note='Nur Auswertung vorhandener Vorhersagen, kein Training.'), indent=2))
    pd.set_option('display.width', 200)
    print(yearly.pivot_table(index='test_year', columns=['target', 'method'], values='r2').round(3).to_string())
    print(pooled.round(3).to_string())
    print(wins.groupby(['target', 'best_mae']).size().to_string())
    print(gaps.round(2).to_string())


if __name__ == '__main__':
    main()
