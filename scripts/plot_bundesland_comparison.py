"""Plot HistGradientBoosting metrics: nationales Modell vs. gepooltes Bundesland-Modell."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/bundesland_comparison_v1'

NATIONAL_COLOR = '#2a78d6'
BUNDESLAND_COLOR = '#eb6834'


def national_devfold(target):
    row = next(r for r in json.loads((ROOT / 'reports/hist_gradient_boosting_v1/run.json').read_text())['pooled']
               if r['target'] == target and r['method'] == 'hist_gradient_boosting')
    return dict(mae=row['mae'], rmse=row['rmse'], r2=row['r2'])


def national_year(target, test_year):
    row = next(r for r in json.loads((ROOT / f'reports/hist_gradient_boosting_test{test_year}_v1/run.json').read_text())['pooled']
               if r['target'] == target and r['method'] == 'hist_gradient_boosting')
    return dict(mae=row['mae'], rmse=row['rmse'], r2=row['r2'])


def pooled_metrics(frame, target_col='actual'):
    pred_col = [c for c in frame.columns if c.startswith('hist_gradient_boosting_bundesland')][0]
    err = frame[target_col] - frame[pred_col]
    sse = (err ** 2).sum()
    sst = ((frame[target_col] - frame[target_col].mean()) ** 2).sum()
    return dict(mae=err.abs().mean(), rmse=(err ** 2).mean() ** .5, r2=1 - sse / sst)


def bundesland_devfold(slug):
    frames = [pd.read_csv(ROOT / f'reports/hist_gradient_boosting_bundesland_{slug}_v1/predictions_{y}.csv')
              for y in range(2018, 2025)]
    return pooled_metrics(pd.concat(frames, ignore_index=True))


def bundesland_year(slug, year):
    frame = pd.read_csv(ROOT / f'reports/final_hist_gradient_boosting_bundesland_{slug}_2015_2026_v1/predictions_{year}.csv')
    return pooled_metrics(frame)


def plot_metric(key, title, filename, periods, suptitle):
    labels = [p[0] for p in periods]
    old_vals = [p[1][key] for p in periods]
    new_vals = [p[2][key] for p in periods]
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    fig.suptitle(suptitle, fontsize=10.5, fontweight='bold', y=0.98)
    bars_old = ax.bar(x - width/2, old_vals, width, color=NATIONAL_COLOR, label='National')
    bars_new = ax.bar(x + width/2, new_vals, width, color=BUNDESLAND_COLOR, label='Bundesland (gepoolt)')
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
    OUT.mkdir(parents=True)

    co2_periods = [
        ('Dev-Fold\n2018-2024', national_devfold('target_co2_gco2eq_kwh'), bundesland_devfold('co2')),
        ('Test 2025', national_year('target_co2_gco2eq_kwh', 2025), bundesland_year('co2', 2025)),
        ('Holdout 2026', national_year('target_co2_gco2eq_kwh', 2026), bundesland_year('co2', 2026)),
    ]
    plot_metric('mae', 'MAE (gCO₂eq/kWh)', 'co2_mae.png', co2_periods,
                'CO₂-Modell: national vs. gepooltes Bundesland-Modell')
    plot_metric('rmse', 'RMSE (gCO₂eq/kWh)', 'co2_rmse.png', co2_periods,
                'CO₂-Modell: national vs. gepooltes Bundesland-Modell')
    plot_metric('r2', 'R²', 'co2_r2.png', co2_periods,
                'CO₂-Modell: national vs. gepooltes Bundesland-Modell')

    ren_periods = [
        ('Dev-Fold\n2018-2024', national_devfold('target_renewable_share_pct'), bundesland_devfold('renewable_share')),
        ('Test 2025', national_year('target_renewable_share_pct', 2025), bundesland_year('renewable_share', 2025)),
        ('Holdout 2026', national_year('target_renewable_share_pct', 2026), bundesland_year('renewable_share', 2026)),
    ]
    plot_metric('mae', 'MAE (Prozentpunkte)', 'renewable_mae.png', ren_periods,
                 'Grünanteil-Modell: national vs. gepooltes Bundesland-Modell')
    plot_metric('rmse', 'RMSE (Prozentpunkte)', 'renewable_rmse.png', ren_periods,
                 'Grünanteil-Modell: national vs. gepooltes Bundesland-Modell')
    plot_metric('r2', 'R²', 'renewable_r2.png', ren_periods,
                 'Grünanteil-Modell: national vs. gepooltes Bundesland-Modell')

    values = {
        'co2': {label.replace('\n', ' '): dict(national=old, bundesland=new) for label, old, new in co2_periods},
        'renewable_share': {label.replace('\n', ' '): dict(national=old, bundesland=new) for label, old, new in ren_periods},
    }
    (OUT / 'values.json').write_text(json.dumps(values, indent=2))
    for name in ('co2_mae', 'co2_rmse', 'co2_r2', 'renewable_mae', 'renewable_rmse', 'renewable_r2'):
        print(OUT / f'{name}.png')


if __name__ == '__main__':
    main()
