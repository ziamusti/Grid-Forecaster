"""Plot Lineare Regression (national, wachsender Trainingszeitraum ab 2015): Metriken je Testjahr,
R² der sechs Quellen, Jahresverlauf und Streudiagramm fuer ein Testjahr."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'reports/linear_regression_expanding_v1'
OUT = ROOT / 'reports/linear_regression_expanding_plots_v1'
COLOR = '#2a78d6'
ACTUAL = '#1f1f1f'
EXAMPLE_YEAR = 2025
NOTE = 'Je Testjahr gelernt aus 2015 bis Vorjahr (z. B. 2018: 2015-2017; 2026: 2015-2025, Daten bis 26.10.2026)'

TARGETS = {
    'target_co2_gco2eq_kwh': dict(slug='co2', label='CO₂-Intensität', unit='gCO₂eq/kWh'),
    'target_renewable_share_pct': dict(slug='renewable_share', label='Grünanteil', unit='%'),
}
SOURCES = {
    'target_solar_share_pct': 'Solar',
    'target_wind_onshore_share_pct': 'Wind an Land',
    'target_wind_offshore_share_pct': 'Wind auf See',
    'target_biomass_share_pct': 'Biomasse',
    'target_hydro_share_pct': 'Wasserkraft',
    'target_other_renewables_share_pct': 'Sonstige Erneuerbare',
}


def clean(ax):
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)


def plot_metric(table, target, key, cfg):
    rows = table[table.target == target].sort_values('test_year')
    vals = rows[key].to_numpy()
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    bars = ax.bar(x, vals, 0.6, color=COLOR)
    clean(ax); ax.spines['left'].set_visible(False)
    ax.set_yticks([])
    ax.set_xticks(x); ax.set_xticklabels(rows.test_year.astype(str), fontsize=9)
    name = {'mae': 'MAE', 'rmse': 'RMSE', 'r2': 'R²'}[key]
    unit = '' if key == 'r2' else f' ({cfg["unit"]})'
    ax.set_title(f'Lineare Regression – {cfg["label"]}: {name}{unit} je Testjahr', fontsize=12, fontweight='bold', pad=14)
    ax.set_ylim(min(0, vals.min() * 1.2), max(vals) * 1.18)
    for bar, value in zip(bars, vals):
        ax.annotate(f'{value:.3f}' if key == 'r2' else f'{value:.1f}', (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 4), textcoords='offset points', ha='center', fontsize=9.5)
    ax.annotate(NOTE, xy=(0.5, -0.1), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout(rect=(0, .03, 1, .93))
    fig.savefig(OUT / f'{cfg["slug"]}_{key}.png', dpi=150)
    plt.close(fig)


def plot_sources(table):
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5), sharey=True)
    low = -0.5
    for ax, (target, label) in zip(axes.flat, SOURCES.items()):
        rows = table[table.target == target].sort_values('test_year')
        ax.bar(rows.test_year.astype(str), rows.r2.clip(lower=low), 0.6, color=COLOR)
        for i, value in enumerate(rows.r2):
            if value < low:  # Balken abgeschnitten, echter Wert als Beschriftung
                ax.annotate(f'{value:.1f}', (i, low), xytext=(0, 3), textcoords='offset points',
                            ha='center', fontsize=8, color='#ffffff', fontweight='bold')
        ax.axhline(0, color='#999999', lw=0.8)
        ax.set_ylim(low, 1.05); ax.set_title(label, fontsize=11)
        ax.tick_params(axis='x', labelsize=7.5, rotation=45); ax.grid(axis='y', color='#e5e5e5', lw=0.6)
        clean(ax)
    for ax in axes[:, 0]:
        ax.set_ylabel('R²')
    fig.suptitle('Lineare Regression – R² der erneuerbaren Quellen je Testjahr', fontsize=13, fontweight='bold')
    fig.text(0.5, 0.01, NOTE, ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout(rect=(0, .03, 1, .95))
    fig.savefig(OUT / 'sources_r2.png', dpi=150)
    plt.close(fig)


def plot_year(pred, target, cfg):
    frame = pred[['target_time_utc', f'actual_{target}', f'predicted_{target}']].copy()
    frame['day'] = pd.to_datetime(frame.target_time_utc, utc=True).dt.tz_convert('Europe/Berlin').dt.date
    daily = frame.groupby('day').mean(numeric_only=True)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(daily.index, daily[f'actual_{target}'], color=ACTUAL, lw=1.6, label='Echter Wert')
    ax.plot(daily.index, daily[f'predicted_{target}'], color=COLOR, lw=1.6, label='Vorhersage')
    ax.set_ylabel(cfg['unit']); ax.grid(axis='y', color='#e5e5e5', lw=0.6); clean(ax)
    ax.legend(frameon=False, loc='upper right')
    ax.set_title(f'Lineare Regression – {cfg["label"]} {EXAMPLE_YEAR}: Tagesmittel echt vs. vorhergesagt '
                 f'(gelernt aus 2015-{EXAMPLE_YEAR - 1})', fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT / f'{cfg["slug"]}_year{EXAMPLE_YEAR}.png', dpi=150)
    plt.close(fig)


def plot_scatter(pred, target, cfg, row):
    actual, predicted = pred[f'actual_{target}'], pred[f'predicted_{target}']
    lo, hi = min(actual.min(), predicted.min()), max(actual.max(), predicted.max())
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.scatter(actual, predicted, s=4, alpha=0.25, color=COLOR, linewidths=0)
    ax.plot([lo, hi], [lo, hi], color=ACTUAL, lw=1, ls='--', label='Perfekte Vorhersage')
    ax.set_xlabel(f'Echter Wert ({cfg["unit"]})'); ax.set_ylabel(f'Vorhersage ({cfg["unit"]})')
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect('equal'); clean(ax)
    ax.legend(frameon=False, loc='upper left')
    ax.set_title(f'{cfg["label"]} {EXAMPLE_YEAR}, stündlich (n={int(row.n)})\n'
                 f'R² = {row.r2:.3f}, MAE = {row.mae:.1f} {cfg["unit"]}', fontsize=11, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT / f'{cfg["slug"]}_scatter{EXAMPLE_YEAR}.png', dpi=150)
    plt.close(fig)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    OUT.mkdir(parents=True)
    table = pd.read_csv(RUN / 'metrics.csv')
    pred = pd.read_csv(RUN / f'predictions_{EXAMPLE_YEAR}.csv')
    for target, cfg in TARGETS.items():
        for key in ('r2', 'mae', 'rmse'):
            plot_metric(table, target, key, cfg)
        plot_year(pred, target, cfg)
        row = table[(table.target == target) & (table.test_year == EXAMPLE_YEAR)].iloc[0]
        plot_scatter(pred, target, cfg, row)
    plot_sources(table)
    for path in sorted(OUT.glob('*.png')):
        print(path)


if __name__ == '__main__':
    main()
