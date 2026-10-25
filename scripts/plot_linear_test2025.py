"""Plot saved 2025 OLS predictions only; no training or raw-data access."""
import hashlib
import json
from zoneinfo import ZoneInfo

import numpy as np
from plot_linear_results import ROOT, plt, pd, matplotlib
import matplotlib.dates as mdates


def main():
    report = ROOT/'reports/linear_regression_test2025_v1'
    out = report/'figures'
    out.mkdir(exist_ok=True)
    sources = [report/'metrics_common.csv']
    targets = [('target_co2_gco2eq_kwh', 'CO₂-Intensität', 'gCO₂eq/kWh', 'co2'),
               ('target_renewable_share_pct', 'Grünanteil', '%', 'gruenanteil')]
    sources += [report/f'predictions_2025_{t}.csv' for t, *_ in targets]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    scores = pd.read_csv(sources[0])
    tz = ZoneInfo('Europe/Berlin')
    start = pd.Timestamp('2025-01-06', tz=tz)
    end = pd.Timestamp('2025-01-13', tz=tz)
    for target, title, unit, name in targets:
        frame = pd.read_csv(report/f'predictions_2025_{target}.csv')
        frame = frame.loc[frame.common_scored == 1].copy()
        times = pd.to_datetime(frame.target_time_utc, utc=True)
        assert len(frame) == 8760 and times.is_unique and times.is_monotonic_increasing
        assert times.dt.year.eq(2025).all()
        frame['local_time'] = times.dt.tz_convert(tz)
        week = frame.loc[(frame.local_time >= start) & (frame.local_time < end)]
        assert len(week) == 168
        row = scores.loc[(scores.target == target) & (scores.method == 'linear')].iloc[0]
        y, p = frame.actual.to_numpy(), frame.linear.to_numpy()
        calculated = [np.abs(y-p).mean(), np.sqrt(((y-p)**2).mean()),
                      1-((y-p)**2).sum()/((y-y.mean())**2).sum()]
        np.testing.assert_allclose(calculated, row[['mae','rmse','r2']].to_numpy(float), atol=1e-9)
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios':[1.55,1]})
        fig.suptitle(f'{title} · Lineare Regression · Testjahr 2025', fontsize=17, fontweight='bold')
        ax = axes[0]
        ax.plot(week.local_time, week.actual, color='#263746', label='Tatsächlicher Zielwert', linewidth=1.8)
        ax.plot(week.local_time, week.linear, color='#1976b9', label='Vorhersage', linewidth=1.5)
        ax.set_title('Erste vollständige Kalenderwoche: 06.–12. Januar')
        ax.set_ylabel(f'{title} ({unit})')
        ax.set_xlabel('Datum · Europe/Berlin (MEZ)')
        ax.xaxis.set_major_locator(mdates.DayLocator(tz=tz))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.', tz=tz))
        ax.legend(loc='best', frameon=False)
        ax.grid(alpha=.2)
        ax = axes[1]
        ax.scatter(y, p, s=7, alpha=.18, color='#1976b9', edgecolors='none', rasterized=True)
        lo = min(0, y.min(), p.min())
        hi = max(y.max(), p.max(), 100 if unit=='%' else 0)
        pad = (hi-lo)*.04
        ax.plot([lo-pad,hi+pad],[lo-pad,hi+pad], '--', color='#263746', label='Perfekte Vorhersage')
        ax.set_xlim(lo-pad,hi+pad)
        ax.set_ylim(lo-pad,hi+pad)
        ax.set_aspect('equal', adjustable='box')
        ax.axhline(0,color='#b45309',linewidth=.8)
        if unit=='%':
            ax.axhline(100,color='#b45309',linewidth=.8)
        ax.set_title('Alle 8.760 Teststunden')
        ax.set_xlabel(f'Tatsächlicher Zielwert ({unit})')
        ax.set_ylabel(f'Vorhersage ({unit})')
        ax.legend(loc='upper left', fontsize=8, frameon=False)
        ax.grid(alpha=.2)
        metric_unit = 'Prozentpunkte' if unit=='%' else unit
        table_ax = fig.add_axes([.24,.12,.52,.09])
        table_ax.axis('off')
        values = [[f'{v:.3f}'.replace('.',',') if i==2 else f'{v:.2f}'.replace('.',',') for i,v in enumerate(calculated)]]
        table = table_ax.table(cellText=values, colLabels=[f'MAE ({metric_unit})',f'RMSE ({metric_unit})','R²'],loc='center',cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1,1.4)
        invalid = f'{int((p<0).sum())} Vorhersagen unter 0'
        if unit=='%': invalid += f'; {int((p>100).sum())} über 100 %'
        fig.text(.5,.065, f'Training 2022–2024 · Kennzahlen für ganz 2025 · {invalid} · keine Begrenzung der Werte',ha='center',fontsize=9)
        fig.text(.5,.025,'Historisches ERA5-Wetter: rückblickender Test, kein realistischer 72-Stunden-Prognosetest.',ha='center',fontsize=9,color='#475569')
        fig.subplots_adjust(left=.07,right=.97,top=.84,bottom=.32,wspace=.3)
        for extension in ('png','pdf'):
            fig.savefig(out/f'{name}_test2025.{extension}',dpi=180)
        plt.close(fig)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    (out/'manifest.json').write_text(json.dumps(dict(source_sha256=hashes,
        script_sha256=hashlib.sha256((ROOT/'scripts/plot_linear_test2025.py').read_bytes()).hexdigest(),
        week_start=str(start),week_end_exclusive=str(end),selection='First complete Monday-Sunday week; fixed before inspecting errors',
        matplotlib=matplotlib.__version__,pandas=pd.__version__,training_performed=False),indent=2)+'\n')
    print(out)


if __name__ == '__main__':
    main()
