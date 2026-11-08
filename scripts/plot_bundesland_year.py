"""Plot actual vs. predicted, daily mean over the whole held-out test year (2025)."""
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_COLOR = '#263746'
PREDICTED_COLOR = '#eb6834'


def load_daily(bundesland):
    co2 = pd.read_csv(ROOT / 'reports/final_hist_gradient_boosting_bundesland_co2_2015_2026_v1/predictions_2025.csv')
    ren = pd.read_csv(ROOT / 'reports/final_hist_gradient_boosting_bundesland_renewable_share_2015_2026_v1/predictions_2025.csv')
    co2['target_time_utc'] = pd.to_datetime(co2.target_time_utc)
    ren['target_time_utc'] = pd.to_datetime(ren.target_time_utc)
    co2 = co2[co2.bundesland == bundesland].copy()
    ren = ren[ren.bundesland == bundesland].copy()
    co2['date'] = co2.target_time_utc.dt.date
    ren['date'] = ren.target_time_utc.dt.date
    co2_daily = co2.groupby('date')[['actual', 'hist_gradient_boosting_bundesland_co2']].mean().reset_index()
    ren_daily = ren.groupby('date')[['actual', 'hist_gradient_boosting_bundesland_renewable_share']].mean().reset_index()
    return co2_daily, ren_daily


def plot(dates, actual, predicted, title, ylabel, filename, out):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(dates, actual, color=ACTUAL_COLOR, linewidth=1.3, label='Ist-Wert (Tagesmittel)')
    ax.plot(dates, predicted, color=PREDICTED_COLOR, linewidth=1.3, alpha=.85, label='Vorhersage (Tagesmittel)')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    ax.legend(frameon=False, loc='upper center', ncol=2, bbox_to_anchor=(.5, 1.16))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out / filename, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundesland', default='Bayern')
    args = parser.parse_args()
    slug = args.bundesland.lower().replace('-', '_').replace('ü', 'ue')
    out = ROOT / f'reports/bundesland_year2025_{slug}_v1'
    if out.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    out.mkdir(parents=True)

    co2_daily, ren_daily = load_daily(args.bundesland)
    plot(co2_daily.date, co2_daily.actual, co2_daily.hist_gradient_boosting_bundesland_co2,
         f'{args.bundesland}, ganzes Jahr 2025: CO₂-Intensität, Ist vs. Vorhersage (Tagesmittel, Testjahr)',
         'gCO₂eq/kWh', 'co2.png', out)
    plot(ren_daily.date, ren_daily.actual, ren_daily.hist_gradient_boosting_bundesland_renewable_share,
         f'{args.bundesland}, ganzes Jahr 2025: Grünanteil, Ist vs. Vorhersage (Tagesmittel, Testjahr)',
         'Grünanteil (%)', 'renewable_share.png', out)
    print(out / 'co2.png')
    print(out / 'renewable_share.png')


if __name__ == '__main__':
    main()
