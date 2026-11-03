"""Hourly predicted vs. actual CO2 and renewable share, 2026-09-30..2026-10-02."""
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ACTUALS = ROOT / 'reports/actuals_20260930_02_v1/actuals.csv'
CO2_PRED = ROOT / 'reports/hist_prediction_price_20260930_02_v1/predictions.csv'
RENEWABLE_PRED = ROOT / 'reports/hist_prediction_20260930_02_v1/predictions.csv'
OUT_DIR = ROOT / 'reports/comparison_20260930_02_v1'
ACTUAL_COLOR = '#2a78d6'
PRED_COLOR = '#eb6834'


def metrics(actual, predicted):
    error = predicted - actual
    mae = float(error.abs().mean())
    rmse = float((error**2).mean() ** 0.5)
    bias = float(error.mean())
    r2 = float(1 - (error**2).sum() / ((actual - actual.mean())**2).sum())
    return mae, rmse, bias, r2


def plot(times, actual, predicted, title, ylabel, out_path, color_actual=ACTUAL_COLOR, color_pred=PRED_COLOR):
    if out_path.exists():
        raise SystemExit(f'{out_path} existiert bereits; kein Ueberschreiben.')
    mae, rmse, bias, r2 = metrics(actual, predicted)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(times, actual, color=color_actual, linewidth=2, marker='o', markersize=3, label='Ist')
    ax.plot(times, predicted, color=color_pred, linewidth=2, marker='o', markersize=3, label='Vorhersage')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.18, linestyle='--')
    ax.legend(loc='upper right', frameon=False)
    ax.set_title(f'{title}\nMAE {mae:.1f} · RMSE {rmse:.1f} · R² {r2:.3f} · Bias {bias:+.1f}', fontsize=11)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(out_path)
    return dict(mae=mae, rmse=rmse, bias=bias, r2=r2, n=len(actual))


def main():
    actuals = pd.read_csv(ACTUALS, parse_dates=['target_time_utc'])
    co2 = pd.read_csv(CO2_PRED, parse_dates=['target_time_utc'])
    renewable = pd.read_csv(RENEWABLE_PRED, parse_dates=['target_time_utc'])

    co2_merged = actuals.merge(co2, on='target_time_utc', validate='one_to_one')
    renewable_merged = actuals.merge(renewable, on='target_time_utc', validate='one_to_one')
    assert len(co2_merged) == 72 and len(renewable_merged) == 72

    co2_metrics = plot(co2_merged.target_time_utc, co2_merged.actual_co2_gco2eq_kwh,
                       co2_merged.predicted_co2_gco2eq_kwh,
                       'CO₂-Vorhersage vs. Istwert, 30.09.–02.10.2026 (Preis-Modell, stundenweise)',
                       'gCO₂eq/kWh', OUT_DIR / 'co2_hourly.png')
    renewable_metrics = plot(renewable_merged.target_time_utc, renewable_merged.actual_renewable_share_pct,
                             renewable_merged.predicted_renewable_share_pct,
                             'Grünanteil-Vorhersage vs. Istwert, 30.09.–02.10.2026 (Modell ohne Preis, stundenweise)',
                             'Grünanteil (%)', OUT_DIR / 'renewable_hourly.png')

    (OUT_DIR / 'hourly_plot_metrics.json').write_text(json.dumps(
        dict(co2=co2_metrics, renewable=renewable_metrics), indent=2))
    print(json.dumps(dict(co2=co2_metrics, renewable=renewable_metrics), indent=2))


if __name__ == '__main__':
    main()
