"""Scatter: Vorhersage vs. Ist-Wert, alle Stunden eines Jahres (Testjahr 2025), ein Bundesland."""
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
POINT_COLOR = '#2a78d6'
LINE_COLOR = '#263746'


def load(bundesland):
    co2 = pd.read_csv(ROOT / 'reports/final_hist_gradient_boosting_bundesland_co2_2015_2026_v1/predictions_2025.csv')
    ren = pd.read_csv(ROOT / 'reports/final_hist_gradient_boosting_bundesland_renewable_share_2015_2026_v1/predictions_2025.csv')
    co2 = co2[co2.bundesland == bundesland]
    ren = ren[ren.bundesland == bundesland]
    return co2, ren


def metrics(actual, predicted):
    errors = actual - predicted
    sse = (errors ** 2).sum()
    sst = ((actual - actual.mean()) ** 2).sum()
    return dict(mae=errors.abs().mean(), rmse=(errors ** 2).mean() ** .5, r2=1 - sse / sst)


def plot(actual, predicted, title, axis_label, filename, out):
    stats = metrics(actual, predicted)
    lo = min(actual.min(), predicted.min())
    hi = max(actual.max(), predicted.max())
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.scatter(actual, predicted, s=10, alpha=.25, color=POINT_COLOR, edgecolors='none')
    ax.plot([lo, hi], [lo, hi], color=LINE_COLOR, linewidth=1.5, linestyle='--', label='Perfekte Vorhersage')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.set_xlabel(f'Ist-Wert ({axis_label})')
    ax.set_ylabel(f'Vorhersage ({axis_label})')
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    ax.legend(frameon=False, loc='upper left')
    ax.text(.97, .03, f'MAE {stats["mae"]:.1f}\nRMSE {stats["rmse"]:.1f}\nR² {stats["r2"]:.3f}',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='#cccccc'))
    fig.tight_layout()
    fig.savefig(out / filename, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundesland', default='Bayern')
    args = parser.parse_args()
    slug = args.bundesland.lower().replace('-', '_').replace('ü', 'ue')
    out = ROOT / f'reports/bundesland_scatter2025_{slug}_v1'
    if out.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    out.mkdir(parents=True)

    co2, ren = load(args.bundesland)
    plot(co2.actual, co2.hist_gradient_boosting_bundesland_co2,
         f'{args.bundesland}, ganzes Jahr 2025 (8760 Stunden): CO₂-Intensität',
         'gCO₂eq/kWh', 'co2.png', out)
    plot(ren.actual, ren.hist_gradient_boosting_bundesland_renewable_share,
         f'{args.bundesland}, ganzes Jahr 2025 (8760 Stunden): Grünanteil',
         '%', 'renewable_share.png', out)
    print(out / 'co2.png')
    print(out / 'renewable_share.png')


if __name__ == '__main__':
    main()
