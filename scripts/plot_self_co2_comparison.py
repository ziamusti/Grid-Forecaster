"""Plot HistGradientBoosting CO2 metrics: Electricity Maps target vs. self-computed target."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/self_co2_comparison_v1'

OLD_COLOR = '#2a78d6'
NEW_COLOR = '#eb6834'


def pooled(frame):
    err = frame.actual - frame.iloc[:, -1]
    sse = (err ** 2).sum()
    sst = ((frame.actual - frame.actual.mean()) ** 2).sum()
    return dict(mae=err.abs().mean(), rmse=(err ** 2).mean() ** .5, r2=1 - sse / sst)


def old_devfold():
    row = next(r for r in json.loads((ROOT / 'reports/hist_gradient_boosting_price_v1/run.json').read_text())['pooled']
               if r['target'] == 'target_co2_gco2eq_kwh' and r['method'] == 'hist_gradient_boosting')
    return dict(mae=row['mae'], rmse=row['rmse'], r2=row['r2'])


def old_year(test_year):
    row = next(r for r in json.loads((ROOT / f'reports/hist_gradient_boosting_price_test{test_year}_v1/run.json').read_text())['pooled']
               if r['target'] == 'target_co2_gco2eq_kwh' and r['method'] == 'hist_gradient_boosting')
    return dict(mae=row['mae'], rmse=row['rmse'], r2=row['r2'])


def new_devfold():
    frames = [pd.read_csv(ROOT / f'reports/hist_gradient_boosting_self_co2_v1/predictions_{y}.csv') for y in range(2018, 2025)]
    return pooled(pd.concat(frames, ignore_index=True))


def new_year(year):
    frame = pd.read_csv(ROOT / f'reports/final_hist_gradient_boosting_self_co2_2015_20261026_v1/predictions_{year}.csv')
    return pooled(frame)


def plot_metric(key, title, filename, periods):
    labels = [p[0] for p in periods]
    old_vals = [p[1][key] for p in periods]
    new_vals = [p[2][key] for p in periods]
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    fig.suptitle('CO₂-Modell: Electricity Maps vs. selbstberechnete Zielgröße (SMARD + UBA)',
                 fontsize=10.5, fontweight='bold', y=0.98)
    bars_old = ax.bar(x - width/2, old_vals, width, color=OLD_COLOR, label='Electricity Maps')
    bars_new = ax.bar(x + width/2, new_vals, width, color=NEW_COLOR, label='Selbstberechnet')
    for spine in ('top', 'right', 'left'):
        ax.spines[spine].set_visible(False)
    ax.set_yticks([])
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=14)
    headroom = max(old_vals + new_vals) * 0.18 or 0.02
    ax.set_ylim(0, max(old_vals + new_vals) + headroom)
    for bars in (bars_old, bars_new):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(f'{value:.3f}' if key == 'r2' else f'{value:.1f}',
                        (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 4), textcoords='offset points',
                        ha='center', fontsize=9.5, color='#0b0b0b')
    fig.legend(*ax.get_legend_handles_labels(), loc='upper center', ncol=2, frameon=False,
               bbox_to_anchor=(.5, .9))
    fig.tight_layout(rect=(0, 0, 1, .84))
    fig.savefig(OUT / filename, dpi=150)
    plt.close(fig)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    periods = [('Dev-Fold\n2018-2024', old_devfold(), new_devfold()),
               ('Test 2025', old_year(2025), new_year(2025)),
               ('Holdout 2026', old_year(2026), new_year(2026))]

    OUT.mkdir(parents=True)
    plot_metric('mae', 'MAE (gCO₂eq/kWh)', 'co2_mae.png', periods)
    plot_metric('rmse', 'RMSE (gCO₂eq/kWh)', 'co2_rmse.png', periods)
    plot_metric('r2', 'R²', 'co2_r2.png', periods)

    values = {label.replace('\n', ' '): dict(electricity_maps=old, self_computed=new)
              for label, old, new in periods}
    (OUT / 'values.json').write_text(json.dumps(values, indent=2))
    print(OUT / 'co2_mae.png')
    print(OUT / 'co2_rmse.png')
    print(OUT / 'co2_r2.png')


if __name__ == '__main__':
    main()
