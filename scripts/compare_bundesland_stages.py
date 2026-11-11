"""Vergleich Bundesland-Modell Stufe 1 (19 Eingaben) vs. Stufe 2 (45 Eingaben), XGBoost.

Nur Auswertung vorhandener Ergebnisse, kein Training. Gepoolte Metriken und
Bootstrap aus den (lokalen) Vorhersagedateien, je Jahr und je Land aus metrics.csv.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from compare_expanding_models import BOOTSTRAP, bootstrap_mae_gap
from train_bundesland_stage0 import metrics
from train_linear_expanding import TEST_YEARS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/bundesland_stage_comparison_v1'
RUNS = {'Stufe 1 (19 Eingaben)': ('xgboost_bundesland_stage1_expanding_v1', '#2a78d6'),
        'Stufe 2 (45 Eingaben)': ('xgboost_bundesland_stage2_expanding_v1', '#eb6834')}
CO2, TOTAL = 'target_co2_gco2eq_kwh', 'target_renewable_share_pct'
SOURCES = {'target_wind_onshore_share_pct': 'Wind an Land', 'target_solar_share_pct': 'Solar',
           'target_biomass_share_pct': 'Biomasse', 'target_hydro_share_pct': 'Wasser',
           'target_other_renewables_share_pct': 'Sonstige (Geothermie)'}
NOTE = 'XGBoost, ein Modell für alle 16 Länder; je Testjahr gelernt aus 2015 bis Vorjahr; gleiche Teststunden'
LOW = -0.5


def clean(ax):
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)


def main():
    if OUT.exists():
        raise SystemExit('Ausgabe existiert bereits; kein Ueberschreiben.')
    tables = {name: pd.read_csv(ROOT / 'reports' / folder / 'metrics.csv') for name, (folder, _) in RUNS.items()}
    OUT.mkdir(parents=True)

    for target, label, filename in [(CO2, 'CO₂-Intensität (selbst berechnet)', 'co2_r2_per_year.png'),
                                    (TOTAL, 'Grünanteil (Summe der Quellen)', 'renewable_share_r2_per_year.png')]:
        fig, ax = plt.subplots(figsize=(8.5, 5))
        for name, (_, color) in RUNS.items():
            rows = tables[name].query('bundesland == "alle" and target == @target').sort_values('test_year')
            ax.plot(rows.test_year, rows.r2, color=color, lw=2, marker='o', ms=8, label=name,
                    markeredgecolor='white', markeredgewidth=2)
        ax.set_xticks(TEST_YEARS); ax.set_ylabel('R² (alle Länder)'); ax.grid(axis='y', color='#e5e5e5', lw=0.6); clean(ax)
        ax.legend(frameon=False, loc='lower left')
        ax.set_title(f'Bundesländer – {label}: R² je Testjahr', fontsize=12, fontweight='bold', pad=12)
        ax.annotate(NOTE, xy=(0.5, -0.13), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
        fig.tight_layout(); fig.savefig(OUT / filename, dpi=150); plt.close(fig)

    frames = {name: pd.concat([pd.read_csv(ROOT / 'reports' / folder / f'predictions_{y}.csv') for y in TEST_YEARS],
                              ignore_index=True) for name, (folder, _) in RUNS.items()}
    first, second = frames.values()
    assert first[['target_time_utc', 'bundesland']].equals(second[['target_time_utc', 'bundesland']])
    blocks = first.target_time_utc.str[:10] + first.bundesland
    rng, rows = np.random.default_rng(42), []
    for target in [CO2, TOTAL, *SOURCES]:
        actual = first[f'actual_{target}'].to_numpy()
        errors = {name: f[f'predicted_{target}'].to_numpy() - actual for name, f in frames.items()}
        gap, low, high = bootstrap_mae_gap(*reversed(list(errors.values())), blocks, rng)
        row = dict(target=target, mae_stage2_minus_stage1=gap, ci95_low=low, ci95_high=high)
        for i, (name, err) in enumerate(errors.items(), start=1):
            row.update({f'{k}_stage{i}': v for k, v in metrics(actual, actual + err).items()})
        rows.append(row)
    pooled = pd.DataFrame(rows)
    pooled.to_csv(OUT / 'metrics_pooled_and_bootstrap.csv', index=False)

    y = np.arange(len(SOURCES))
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for offset, (i, (name, (_, color))) in zip((-0.19, 0.19), enumerate(RUNS.items(), start=1)):
        values = [pooled.loc[pooled.target == t, f'r2_stage{i}'].item() for t in SOURCES]
        bars = ax.barh(y + offset, values, 0.36, color=color, label=name, edgecolor='white', linewidth=2)
        for bar, value in zip(bars, values):
            ax.annotate(f'{value:.3f}', (value, bar.get_y() + bar.get_height() / 2), xytext=(4, 0),
                        textcoords='offset points', va='center', fontsize=8.5)
    ax.set_yticks(y); ax.set_yticklabels(SOURCES.values()); ax.invert_yaxis(); ax.set_xlim(0, 1.08)
    ax.set_xlabel('R² (alle Länder und Teststunden 2018-2026)'); ax.grid(axis='x', color='#e5e5e5', lw=0.6); clean(ax)
    ax.legend(frameon=False, loc='lower right')
    ax.set_title('Bundesländer – erneuerbare Quellen: R² Stufe 1 vs. Stufe 2', fontsize=12, fontweight='bold', pad=12)
    ax.annotate(NOTE, xy=(0.5, -0.17), xycoords='axes fraction', ha='center', fontsize=7.5, color='#555555')
    fig.tight_layout(); fig.savefig(OUT / 'sources_r2_pooled.png', dpi=150); plt.close(fig)

    for target, label, filename in [(CO2, 'CO₂-Intensität', 'states_co2_r2_2025.png'),
                                    (TOTAL, 'Grünanteil', 'states_renewable_share_r2_2025.png')]:
        lands = sorted(tables['Stufe 1 (19 Eingaben)'].query('bundesland != "alle"').bundesland.unique())
        yy = np.arange(len(lands))
        fig, ax = plt.subplots(figsize=(8.5, 7.5))
        for offset, (name, (_, color)) in zip((-0.19, 0.19), RUNS.items()):
            part = tables[name].query('test_year == 2025 and target == @target').set_index('bundesland')
            values = part.loc[lands, 'r2'].to_numpy()
            bars = ax.barh(yy + offset, np.clip(values, LOW, None), 0.36, color=color, label=name, edgecolor='white', linewidth=2)
            for bar, value in zip(bars, values):
                x = max(value, LOW)
                ax.annotate(f'{value:.2f}', (x, bar.get_y() + bar.get_height() / 2), xytext=(4, 0),
                            textcoords='offset points', va='center', fontsize=8)
        ax.axvline(0, color='#999999', lw=0.8)
        ax.set_yticks(yy); ax.set_yticklabels(lands); ax.invert_yaxis(); ax.set_xlim(LOW, 1.1)
        ax.set_xlabel('R² im Testjahr 2025 (gelernt aus 2015-2024)\nAchse bei −0,5 abgeschnitten, Zahl = echter Wert')
        ax.grid(axis='x', color='#e5e5e5', lw=0.6); clean(ax); ax.legend(frameon=False, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2)
        ax.set_title(f'{label} je Bundesland 2025: R² Stufe 1 vs. Stufe 2', fontsize=12, fontweight='bold', pad=30)
        fig.tight_layout(); fig.savefig(OUT / filename, dpi=150); plt.close(fig)

    (OUT / 'run.json').write_text(json.dumps(dict(
        inputs=[f'reports/{f}' for f, _ in RUNS.values()], test_rows=len(first),
        bootstrap=dict(resamples=BOOTSTRAP, block='UTC day per Bundesland', seed=42, interval='95% percentile'),
        note='Nur Auswertung vorhandener Ergebnisse, kein Training.'), indent=2, ensure_ascii=False))
    print(pooled.round(3).to_string())
    for path in sorted(OUT.glob('*.png')):
        print(path)


if __name__ == '__main__':
    main()
