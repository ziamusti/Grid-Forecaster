"""Full-year hourly plots from existing OLS test predictions; no training."""
import hashlib
import json
import numpy as np
from plot_linear_results import ROOT, pd, plt


def main():
    report = ROOT/'reports/linear_regression_test2025_v1'
    out = report/'figures'
    out.mkdir(exist_ok=True)
    hashes = {}
    for target, title, unit, name in [
        ('target_co2_gco2eq_kwh','CO₂-Intensität','gCO₂eq/kWh','co2'),
        ('target_renewable_share_pct','Grünanteil','%','gruenanteil')]:
        source = report/f'predictions_2025_{target}.csv'
        hashes[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
        frame = pd.read_csv(source)
        frame = frame.loc[frame.common_scored==1].copy()
        time = pd.to_datetime(frame.target_time_utc,utc=True)
        expected = pd.date_range('2025-01-01', '2026-01-01',freq='h',inclusive='left',tz='UTC')
        assert pd.DatetimeIndex(time).equals(expected)
        assert np.isfinite(frame[['actual','linear']].to_numpy()).all()
        fig, ax = plt.subplots(figsize=(18,6))
        ax.plot(time,frame.actual,label='Tatsächlicher Zielwert',color='#263746',linewidth=.65,alpha=.85)
        ax.plot(time,frame.linear,label='Vorhersage · Lineare Regression',color='#2389d7',linewidth=.65,alpha=.7)
        ax.axhline(0,color='#b45309',linewidth=.8,linestyle='--')
        if unit=='%':
            ax.axhline(100,color='#b45309',linewidth=.8,linestyle='--')
        ticks = pd.date_range('2025-01-01',periods=12,freq='MS',tz='UTC')
        ax.set_xticks(ticks)
        ax.set_xticklabels(['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'])
        ax.set_xlim(expected[0],pd.Timestamp('2026-01-01',tz='UTC'))
        ax.set_ylabel(f'{title} ({unit})')
        ax.set_xlabel('Testjahr 2025 · Zeit in UTC')
        ax.set_title(f'{title} · Lineare Regression · Ganzes Jahr 2025',fontsize=17,fontweight='bold',pad=16)
        ax.legend(loc='upper center',bbox_to_anchor=(.5,1.01),ncol=2,framealpha=.95)
        ax.grid(alpha=.18)
        fig.text(.5,.065,'Training 2022–2024 · Alle 8.760 Stunden dargestellt · Keine Glättung oder Tagesmittel · Werte nicht begrenzt',ha='center',fontsize=10)
        fig.text(.5,.025,'Historisches ERA5-Wetter: rückblickender Test, kein realistischer 72-Stunden-Prognosetest.',ha='center',fontsize=10,color='#475569')
        fig.tight_layout(rect=(0,.12,1,1))
        for ext in ('png','pdf'):
            fig.savefig(out/f'{name}_jahresverlauf_2025.{ext}',dpi=200)
        plt.close(fig)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    (out/'jahresverlauf_manifest.json').write_text(json.dumps(dict(source_sha256=hashes,
        hours_per_target=8760,aggregation=None,timezone='UTC',training_performed=False),indent=2)+'\n')
    print(out)


if __name__=='__main__':
    main()
