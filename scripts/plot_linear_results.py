"""Pandas result tables and Matplotlib charts; no training or holdout access."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', tempfile.mkdtemp(prefix='grid-mpl-'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/linear_regression_v1'
OUT = REPORT / 'figures'


def main(hist=False):
    REPORT = ROOT / 'reports' / ('hist_gradient_boosting_v1' if hist else 'linear_regression_v1')
    OUT = REPORT / 'figures'
    paths = [REPORT/'metrics_common.csv', REPORT/'run.json']
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    yearly = pd.read_csv(paths[0])
    pooled = pd.DataFrame(json.loads(paths[1].read_text())['pooled'])
    assert len(yearly) == (56 if hist else 42) and len(pooled) == (8 if hist else 6)
    OUT.mkdir(exist_ok=True)
    methods = ['linear']
    labels = ['Lineare Regression']
    colors = ['#1769aa']
    if hist:
        methods = ['hist_gradient_boosting']
        labels = ['HistGradientBoosting']
        colors = ['#16846a']
    for target, name, unit, filename in [
        ('target_co2_gco2eq_kwh', 'CO₂-Intensität', 'gCO₂eq/kWh', 'co2_ergebnisse'),
        ('target_renewable_share_pct', 'Grünanteil', 'Prozentpunkte', 'gruenanteil_ergebnisse')]:
        table = pooled.loc[pooled.target == target].set_index('method').loc[methods]
        annual = yearly.loc[yearly.target == target]
        assert annual.groupby('validation_year')['n'].nunique().eq(1).all()
        pooled.loc[pooled.target == target].set_index('method').to_csv(OUT/f'{filename}_gesamt.csv')
        annual.loc[annual.method == ('hist_gradient_boosting' if hist else 'linear')].to_csv(OUT/f'{filename}_jaehrlich.csv', index=False)
        fig, axes = plt.subplots(2, 3, figsize=(16 if hist else 14, 9 if hist else 8))
        title = 'HistGradientBoosting' if hist else 'Lineare Regression'
        fig.suptitle(f'{name} · {title}', fontsize=18, fontweight='bold')
        for col, (metric, title) in enumerate([('mae','MAE'),('rmse','RMSE'),('r2','R²')]):
            ax=axes[0,col]
            values=table[metric].to_numpy()
            short_labels = ['HistGradient\nBoosting'] if hist else labels
            bars=ax.bar(short_labels, values, color=colors, width=.65)
            ax.axhline(0, color='#64748b', linewidth=.8)
            ax.set_title(f'{title} · alle Bewertungsstunden')
            ax.set_ylabel('dimensionslos' if metric=='r2' else unit)
            ax.tick_params(axis='x', labelsize=9, rotation=12)
            ax.bar_label(bars, labels=[f'{v:.3f}'.replace('.',',') if metric=='r2' else f'{v:.2f}'.replace('.',',') for v in values],padding=5)
            ax.margins(y=.23)
            if metric != 'r2': ax.set_ylim(bottom=0)
            else: ax.set_ylim(min(0, values.min()-.15),1)
            ax=axes[1,col]
            for method,label,color in zip(methods,labels,colors):
                series=annual.loc[annual.method==method].sort_values('validation_year')
                ax.plot(series.validation_year,series[metric],marker='o',label=label,color=color)
            ax.axhline(0,color='#64748b',linewidth=.8)
            ax.set_title(f'{title} · je Validierungsjahr')
            ax.set_xlabel('Validierungsjahr (jeweils 3 Jahre Training davor)')
            ax.set_ylabel('dimensionslos' if metric=='r2' else unit)
            ax.set_xticks(range(2018,2025))
            ax.grid(axis='y',alpha=.2)
            if metric != 'r2': ax.set_ylim(bottom=0)
        handles, legend_labels=axes[1,0].get_legend_handles_labels()
        fig.legend(handles,legend_labels,loc='lower center',bbox_to_anchor=(.5,.06),ncol=len(methods),frameon=False)
        n=int(table.iloc[0]['n'])
        fig.text(.5,.028,f'2018–2024 · {n:,} gemeinsame Stunden je Verfahren · MAE/RMSE: kleiner besser; R²: größer besser'.replace(',', '.'),ha='center',fontsize=10)
        fig.text(.5,.008,'Retrospektive ERA5-Untersuchung, kein operativer 72h-Test. Gepooltes R² ist kein Mittel der Jahres-R².',ha='center',fontsize=9,color='#475569')
        fig.tight_layout(rect=(0,.11,1,.95))
        fig.savefig(OUT/f'{filename}.png',dpi=180)
        fig.savefig(OUT/f'{filename}.pdf')
        plt.close(fig)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    (OUT/'manifest.json').write_text(json.dumps(dict(source_sha256=hashes,
        pandas=pd.__version__,matplotlib=matplotlib.__version__,displayed_methods=methods,
        training_performed=False),indent=2)+'\n')
    print(OUT)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hist', action='store_true', help='Render HistGradientBoosting comparison')
    main(hist=parser.parse_args().hist)
