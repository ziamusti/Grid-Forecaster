"""Plot HistGradientBoosting CO2 metrics with vs. without price feature (2025 held-out test)."""
import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/price_feature_comparison_v1'

WITHOUT_COLOR = '#2a78d6'
WITH_COLOR = '#eb6834'


def load(path, target='target_co2_gco2eq_kwh', method='hist_gradient_boosting'):
    pooled = json.loads(path.read_text())['pooled']
    row = next(r for r in pooled if r['target'] == target and r['method'] == method)
    return row['mae'], row['rmse'], row['r2']


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    without = load(ROOT / 'reports/hist_gradient_boosting_test2025_v1/run.json')
    with_price = load(ROOT / 'reports/hist_gradient_boosting_price_test2025_v1/run.json')

    metrics = [('MAE', 'gCO₂eq/kWh', without[0], with_price[0]),
               ('RMSE', 'gCO₂eq/kWh', without[1], with_price[1]),
               ('R²', 'dimensionslos', without[2], with_price[2])]

    fig, axes = plt.subplots(1, 3, figsize=(10, 4.2))
    fig.suptitle('HistGradientBoosting – CO₂-Vorhersage, unabhängiger 2025-Test',
                 fontsize=13, fontweight='bold')
    for ax, (name, unit, v_without, v_with) in zip(axes, metrics):
        bars = ax.bar(['ohne Preis', 'mit Preis'], [v_without, v_with],
                       color=[WITHOUT_COLOR, WITH_COLOR], width=0.6)
        for spine in ('top', 'right', 'left'):
            ax.spines[spine].set_visible(False)
        ax.set_yticks([])
        ax.set_title(name, fontsize=11, fontweight='bold')
        ax.set_xlabel(unit, fontsize=8.5, color='#52514e')
        headroom = max(v_without, v_with) * 0.18 or 0.02
        ax.set_ylim(0, max(v_without, v_with) + headroom)
        for bar, value in zip(bars, (v_without, v_with)):
            ax.annotate(f'{value:.3f}' if name == 'R²' else f'{value:.2f}',
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 4), textcoords='offset points',
                        ha='center', fontsize=9.5, color='#0b0b0b')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    OUT.mkdir(parents=True)
    fig.savefig(OUT / 'co2_mae_rmse_r2.png', dpi=150)
    plt.close(fig)
    (OUT / 'values.json').write_text(json.dumps(
        dict(without=dict(mae=without[0], rmse=without[1], r2=without[2]),
             with_price=dict(mae=with_price[0], rmse=with_price[1], r2=with_price[2]),
             source=['reports/hist_gradient_boosting_test2025_v1/run.json',
                     'reports/hist_gradient_boosting_price_test2025_v1/run.json']), indent=2))
    print(OUT / 'co2_mae_rmse_r2.png')


if __name__ == '__main__':
    main()
