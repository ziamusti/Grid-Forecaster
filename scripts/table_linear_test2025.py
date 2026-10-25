"""Export the two annual OLS result rows without retraining."""
import hashlib
import json
from plot_linear_results import ROOT, pd, plt


def main():
    report = ROOT/'reports/linear_regression_test2025_v1'
    source = report/'metrics_common.csv'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    scores = pd.read_csv(source)
    rows = []
    for target, label, unit in [
        ('target_co2_gco2eq_kwh', 'CO₂-Intensität', 'gCO₂eq/kWh'),
        ('target_renewable_share_pct', 'Grünanteil', 'Prozentpunkte')]:
        selected = scores.loc[(scores.method=='linear') & (scores.target==target) & (scores.validation_year==2025)]
        assert len(selected)==1
        row = selected.iloc[0]
        assert row['n']==8760
        rows.append({'Modell':'Lineare Regression', 'Zielgröße':label,
                     'Testzeitraum':'Ganzes Jahr 2025', 'Stunden':int(row['n']),
                     'MAE':float(row.mae), 'RMSE':float(row.rmse), 'R²':float(row.r2),
                     'Einheit MAE/RMSE':unit, 'Trainingszeitraum':'2022–2024'})
    out = report/'figures'
    out.mkdir(exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(out/'jahrestabelle_2025.csv',index=False,sep=';',decimal=',',encoding='utf-8-sig')
    display = table.iloc[:,:7].copy()
    display['Stunden'] = display.Stunden.map(lambda n:f'{n:,}'.replace(',','.'))
    for field in ['MAE','RMSE','R²']:
        display[field] = display[field].map(lambda v: format(v,'.3f' if field=='R²' else '.2f').replace('.',','))
    fig, ax = plt.subplots(figsize=(13,3.5))
    ax.axis('off')
    fig.suptitle('Lineare Regression · Jahresergebnisse 2025',fontsize=17,fontweight='bold',y=.94)
    t = ax.table(cellText=display.values,colLabels=display.columns,cellLoc='center',
                 colWidths=[.23,.18,.22,.10,.09,.09,.09],bbox=[0,.40,1,.43])
    t.auto_set_font_size(False)
    t.set_fontsize(11)
    for (r,c),cell in t.get_celld().items():
        cell.set_edgecolor('#cbd5e1')
        if r==0:
            cell.set_facecolor('#e2e8f0')
            cell.set_text_props(weight='bold')
    fig.text(.5,.25,'MAE/RMSE: CO₂ in gCO₂eq/kWh · Grünanteil in Prozentpunkten · R² dimensionslos',ha='center',fontsize=10)
    fig.text(.5,.17,'Training: 2022–2024 · Test: vollständiges UTC-Jahr 2025 (8.760 Stunden je Ziel)',ha='center',fontsize=10)
    fig.text(.5,.09,'Historisches ERA5-Wetter · kein realistischer 72-Stunden-Prognosetest · Vorhersagen nicht begrenzt',ha='center',fontsize=10)
    fig.subplots_adjust(left=.035,right=.965,top=.85,bottom=.1)
    for ext in ['png','pdf']:
        fig.savefig(out/f'jahrestabelle_2025.{ext}',dpi=200)
    plt.close(fig)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    (out/'jahrestabelle_manifest.json').write_text(json.dumps(dict(source=str(source.relative_to(ROOT)),
        source_sha256=digest,training_performed=False,rows=2,hours_per_target=8760),indent=2)+'\n')
    print(out/'jahrestabelle_2025.pdf')


if __name__=='__main__':
    main()
