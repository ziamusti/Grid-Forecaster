"""Scatter plot predicted vs. actual CO2 for the held-out 2026-07-01..2026-09-23 evaluation."""
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'reports/price_model_eval_20260701_0923_v1'
POINT_COLOR = '#2a78d6'
LINE_COLOR = '#52514e'


def main():
    out_path = SRC / 'predicted_vs_actual_scatter.png'
    if out_path.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    df = pd.read_csv(SRC / 'predictions_vs_actual.csv')
    manifest = json.loads((SRC / 'run.json').read_text())
    m = manifest['metrics']

    lo = min(df.actual_co2_gco2eq_kwh.min(), df.predicted_co2_gco2eq_kwh.min())
    hi = max(df.actual_co2_gco2eq_kwh.max(), df.predicted_co2_gco2eq_kwh.max())
    pad = (hi - lo) * 0.04

    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color=LINE_COLOR, linewidth=1.3,
            linestyle='--', zorder=1, label='Ideal (Vorhersage = Istwert)')
    ax.scatter(df.actual_co2_gco2eq_kwh, df.predicted_co2_gco2eq_kwh,
               s=10, color=POINT_COLOR, alpha=.35, linewidths=0, zorder=2, label=f'Stunden (n={len(df)})')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_aspect('equal')
    ax.set_xlabel('Istwert (Electricity Maps), gCO₂eq/kWh')
    ax.set_ylabel('Vorhersage (Preis-Modell), gCO₂eq/kWh')
    ax.grid(alpha=.18, linestyle='--')
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.set_title('CO₂-Vorhersage vs. Istwert, stundenweise\n'
                 f"01.07.–23.09.2026, ungesehener retrospektiver Holdout-Test (n={len(df)})\n"
                 f"MAE {m['mae']:.1f} · RMSE {m['rmse']:.1f} · R² {m['r2']:.3f} · Bias {m['bias']:+.1f}\n"
                 "Modell trainiert bis 2026-06-30 · retrospektives ERA5-Wetter, kein operativer Test",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(out_path)


if __name__ == '__main__':
    main()
