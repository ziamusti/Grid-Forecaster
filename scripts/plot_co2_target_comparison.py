"""CO2 Electricity Maps vs. selbst berechnet (XGBoost getrennt, wachsender Trainingszeitraum ab 2015).

Nur Auswertung vorhandener Vorhersagen auf den gemeinsamen Teststunden, kein Training.
Diagramme: Tagesmittel beider Zielgroessen 2025, R² je Testjahr, MAE relativ zum Mittelwert je Testjahr.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

from train_linear_expanding import TEST_YEARS, metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/co2_target_comparison_expanding_v1'
TARGET = 'target_co2_gco2eq_kwh'
RUNS = {'Electricity Maps (Lebenszyklus)': ('xgboost_expanding_v1', '#2a78d6'),
        'Selbst berechnet (SMARD + UBA)': ('xgboost_selfco2_separate_expanding_v1', '#eb6834')}
NOTE = 'XGBoost getrennt; je Testjahr gelernt aus 2015 bis Vorjahr; nur gemeinsame Teststunden'


def clean(ax):
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.grid(axis='y', color='#e5e5e5', lw=0.6)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    frames = {}
    for name, (folder, _) in RUNS.items():
        frames[name] = pd.concat([pd.read_csv(ROOT / 'reports' / folder / f'predictions_{y}.csv').assign(test_year=y)
                                  for y in TEST_YEARS], ignore_index=True)
    common = set.intersection(*(set(f.target_time_utc) for f in frames.values()))
    frames = {n: f[f.target_time_utc.isin(common)].sort_values('target_time_utc').reset_index(drop=True)
              for n, f in frames.items()}
    OUT.mkdir(parents=True)

    rows = []
    for name, frame in frames.items():
        for year in TEST_YEARS:
            part = frame[frame.test_year == year]
            stats = metrics(part[f'actual_{TARGET}'].to_numpy(), part[f'predicted_{TARGET}'].to_numpy())
            rows.append(dict(target=name, test_year=year, relative_mae_pct=100 * stats['mae'] / part[f'actual_{TARGET}'].mean(), **stats))
    table = pd.DataFrame(rows)
    table.to_csv(OUT / 'metrics_per_year.csv', index=False)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    for name, (_, color) in RUNS.items():
        part = frames[name][frames[name].test_year == 2025].copy()
        part['day'] = pd.to_datetime(part.target_time_utc, utc=True).dt.tz_convert('Europe/Berlin').dt.date
        daily = part.groupby('day')[f'actual_{TARGET}'].mean()
        ax.plot(daily.index, daily.values, color=color, lw=1.6, label=name)
    ax.set_ylabel('gCO₂eq/kWh'); clean(ax); ax.legend(frameon=False, loc='upper right')
    ax.set_title('Echte CO₂-Intensität 2025, Tagesmittel: zwei Zielgrößen', fontsize=12, fontweight='bold')
    fig.tight_layout(); fig.savefig(OUT / 'targets_daily_2025.png', dpi=150); plt.close(fig)

    for key, ylabel, title, filename in [('r2', 'R²', 'R² je Testjahr', 'r2_per_year.png'),
                                         ('relative_mae_pct', 'MAE in % des Mittelwerts', 'Relativer Fehler (MAE / Mittelwert) je Testjahr', 'relative_mae_per_year.png')]:
        fig, ax = plt.subplots(figsize=(8.5, 5))
        for name, (_, color) in RUNS.items():
            part = table[table.target == name]
            ax.plot(part.test_year, part[key], color=color, lw=2, marker='o', ms=8, label=name,
                    markeredgecolor='white', markeredgewidth=2)
        ax.set_xticks(TEST_YEARS); ax.set_ylabel(ylabel); clean(ax)
        ax.legend(frameon=False, loc='lower right' if key == 'r2' else 'upper right')
        ax.set_title(f'CO₂-Vorhersage: {title}', fontsize=12, fontweight='bold', pad=12)
        ax.annotate(NOTE, xy=(0.5, -0.13), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
        fig.tight_layout(); fig.savefig(OUT / filename, dpi=150); plt.close(fig)
    print(table.round(3).to_string())
    for path in sorted(OUT.glob('*.png')):
        print(path)


if __name__ == '__main__':
    main()
