"""Plot predicted vs. actual CO2 for the held-out 2026-07-01..2026-09-23 evaluation."""
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'reports/price_model_eval_20260701_0923_v1'
ACTUAL_COLOR = '#2a78d6'
PRED_COLOR = '#eb6834'


def main():
    out_path = SRC / 'predicted_vs_actual.png'
    if out_path.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    df = pd.read_csv(SRC / 'predictions_vs_actual.csv', parse_dates=['target_time_utc'])
    manifest = json.loads((SRC / 'run.json').read_text())
    daily = df.set_index('target_time_utc').resample('D').mean(numeric_only=True)

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(daily.index, daily.actual_co2_gco2eq_kwh, color=ACTUAL_COLOR, linewidth=2, label='Ist (Electricity Maps)')
    ax.plot(daily.index, daily.predicted_co2_gco2eq_kwh, color=PRED_COLOR, linewidth=2, label='Vorhersage (Preis-Modell)')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel('gCO₂eq/kWh (Tagesmittel)')
    ax.grid(alpha=.18, linestyle='--')
    ax.legend(loc='upper right', frameon=False)
    m = manifest['metrics']
    ax.set_title(f"CO₂-Vorhersage vs. Istwert, 01.07.–23.09.2026 (ungesehen)\n"
                 f"MAE {m['mae']:.1f} · RMSE {m['rmse']:.1f} · R² {m['r2']:.3f} · Bias {m['bias']:+.1f}",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(out_path)


if __name__ == '__main__':
    main()
