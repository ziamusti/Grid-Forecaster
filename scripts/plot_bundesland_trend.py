"""Plot gepooltes Bundesland-Modell: Metriken je Testjahr (2018-2026), kein Vergleich mit national."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/bundesland_trend_v1'
COLOR = '#2a78d6'

TARGETS = {
    'co2': dict(label='CO₂-Intensität', unit='gCO₂eq/kWh'),
    'renewable_share': dict(label='Grünanteil', unit='Prozentpunkte'),
}


def devfold_years(slug):
    frame = pd.read_csv(ROOT / f'reports/hist_gradient_boosting_bundesland_{slug}_v1/metrics.csv')
    return {int(r.validation_year): dict(mae=r.mae, rmse=r.rmse, r2=r.r2) for r in frame.itertuples()}


def final_year(slug, year):
    pred = pd.read_csv(ROOT / f'reports/final_hist_gradient_boosting_bundesland_{slug}_2015_2026_v1/predictions_{year}.csv')
    pred_col = [c for c in pred.columns if c.startswith('hist_gradient_boosting_bundesland')][0]
    err = pred.actual - pred[pred_col]
    sse = (err ** 2).sum()
    sst = ((pred.actual - pred.actual.mean()) ** 2).sum()
    return dict(mae=err.abs().mean(), rmse=(err ** 2).mean() ** .5, r2=1 - sse / sst)


def plot_metric(key, title, filename, years, values):
    labels = [str(y) for y in years]
    vals = [values[y][key] for y in years]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    bars = ax.bar(x, vals, 0.6, color=COLOR)
    for spine in ('top', 'right', 'left'):
        ax.spines[spine].set_visible(False)
    ax.set_yticks([])
    ax.set_xticks(x)
    ax.set_xticklabels([f'{l}*' if y in (2025, 2026) else l for l, y in zip(labels, years)], fontsize=9)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=14)
    headroom = max(vals) * 0.18 or 0.02
    ax.set_ylim(0, max(vals) + headroom)
    for bar in bars:
        value = bar.get_height()
        ax.annotate(f'{value:.3f}' if key == 'r2' else f'{value:.1f}',
                    (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 4), textcoords='offset points',
                    ha='center', fontsize=9.5, color='#0b0b0b')
    ax.annotate('* 2025 = finaler Test, 2026 = Holdout (anderes Modell als 2018-2024 Dev-Folds)',
                xy=(0.5, -0.1), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout(rect=(0, .03, 1, .93))
    fig.savefig(OUT / filename, dpi=150)
    plt.close(fig)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    OUT.mkdir(parents=True)
    years = list(range(2018, 2027))
    all_values = {}
    for slug, cfg in TARGETS.items():
        values = devfold_years(slug)
        values[2025] = final_year(slug, 2025)
        values[2026] = final_year(slug, 2026)
        all_values[slug] = values
        plot_metric('mae', f'{cfg["label"]}: MAE ({cfg["unit"]}) je Jahr', f'{slug}_mae.png', years, values)
        plot_metric('rmse', f'{cfg["label"]}: RMSE ({cfg["unit"]}) je Jahr', f'{slug}_rmse.png', years, values)
        plot_metric('r2', f'{cfg["label"]}: R² je Jahr', f'{slug}_r2.png', years, values)
        print(slug, 'fertig')

    (OUT / 'values.json').write_text(json.dumps(
        {slug: {str(y): v for y, v in vals.items()} for slug, vals in all_values.items()}, indent=2))
    for slug in TARGETS:
        for metric in ('mae', 'rmse', 'r2'):
            print(OUT / f'{slug}_{metric}.png')


if __name__ == '__main__':
    main()
