"""Plot actual vs. predicted for one Bundesland/day from the held-out test set (2025)."""
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_COLOR = '#263746'
PREDICTED_COLOR = '#eb6834'


def load(bundesland, day):
    co2 = pd.read_csv(ROOT / 'reports/final_hist_gradient_boosting_bundesland_co2_2015_2026_v1/predictions_2025.csv')
    ren = pd.read_csv(ROOT / 'reports/final_hist_gradient_boosting_bundesland_renewable_share_2015_2026_v1/predictions_2025.csv')
    co2['target_time_utc'] = pd.to_datetime(co2.target_time_utc)
    ren['target_time_utc'] = pd.to_datetime(ren.target_time_utc)
    co2_day = co2[(co2.bundesland == bundesland) & (co2.target_time_utc.dt.date == day)].sort_values('target_time_utc')
    ren_day = ren[(ren.bundesland == bundesland) & (ren.target_time_utc.dt.date == day)].sort_values('target_time_utc')
    return co2_day, ren_day


def plot(hours, actual, predicted, title, ylabel, filename, out):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(hours, actual, color=ACTUAL_COLOR, linewidth=2.2, marker='o', markersize=4, label='Ist-Wert')
    ax.plot(hours, predicted, color=PREDICTED_COLOR, linewidth=2.2, marker='o', markersize=4, label='Vorhersage')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel('Stunde (UTC)')
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    ax.legend(frameon=False, loc='upper center', ncol=2, bbox_to_anchor=(.5, 1.18))
    fig.tight_layout()
    fig.savefig(out / filename, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundesland', default='Bayern')
    parser.add_argument('--day', default='2025-06-15')
    args = parser.parse_args()
    day = pd.Timestamp(args.day).date()
    out = ROOT / f'reports/bundesland_example_{args.bundesland.lower().replace("-", "_").replace("ü","ue")}_{args.day.replace("-", "")}_v1'
    if out.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    out.mkdir(parents=True)

    co2_day, ren_day = load(args.bundesland, day)
    hours = co2_day.target_time_utc.dt.hour
    plot(hours, co2_day.actual, co2_day.hist_gradient_boosting_bundesland_co2,
         f'{args.bundesland}, {args.day}: CO₂-Intensität, Ist vs. Vorhersage (Testjahr 2025)',
         'gCO₂eq/kWh', 'co2.png', out)
    plot(ren_day.target_time_utc.dt.hour, ren_day.actual, ren_day.hist_gradient_boosting_bundesland_renewable_share,
         f'{args.bundesland}, {args.day}: Grünanteil, Ist vs. Vorhersage (Testjahr 2025)',
         'Grünanteil (%)', 'renewable_share.png', out)
    print(out / 'co2.png')
    print(out / 'renewable_share.png')


if __name__ == '__main__':
    main()
