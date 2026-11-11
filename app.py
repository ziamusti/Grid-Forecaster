"""Historical Stage-0 result explorer. Run: streamlit run app.py"""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard_logic import add_scores,best_window,category,load_bundesland_predictions,load_predictions

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Grid Forecaster',page_icon='🌱',layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.6rem;max-width:1280px}
.hero{padding:1.5rem 1.8rem;border-radius:18px;
background:linear-gradient(120deg,#12372a,#1d6b4d);color:white;margin-bottom:1.1rem;
box-shadow:0 6px 18px rgba(18,55,42,.18)}
.hero h1{margin:0;font-size:2.1rem;letter-spacing:-.02em}
.hero p{margin:.35rem 0 0;color:#d9fbe8;font-size:1.02rem}
.status{padding:.9rem 1.1rem;border-radius:12px;color:white;font-weight:700;font-size:1.05rem;
display:flex;align-items:center;gap:.5rem;margin-bottom:.9rem;box-shadow:0 2px 8px rgba(0,0,0,.08)}
[data-testid="stMetric"]{background:var(--background-color,#f5f8f6);border:1px solid rgba(120,140,130,.25);
padding:1rem;border-radius:14px}
[data-testid="stMetricLabel"]{font-weight:600;opacity:.85}
hr{margin:1.4rem 0 1.1rem}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🌱 Grid Forecaster</h1>'
            '<p>Historische Analyse der CO₂-Intensität und des Grünanteils in Deutschland</p></div>',
            unsafe_allow_html=True)

@st.cache_data(show_spinner=False,ttl=60)
def data(source_version='xgboost-main-model-v1'):
    return load_predictions(ROOT)

@st.cache_data(show_spinner=False,ttl=60)
def bundesland_data():
    return load_bundesland_predictions(ROOT)

try:
    frame=data()
except FileNotFoundError as error:
    st.error(f'Eine benötigte Vorhersagedatei fehlt: {error.filename}')
    st.stop()

minimum=frame.time_utc.dt.date.min(); maximum=frame.time_utc.dt.date.max()
with st.sidebar:
    st.subheader('Einstellungen')
    selected=st.date_input('Datum auswählen',value=maximum,min_value=minimum,max_value=maximum,format='DD.MM.YYYY')
    duration=st.slider('Jobdauer in Stunden',1,6,3,help='Länge des gesuchten emissionsarmen Zeitfensters.')
    st.divider()
    st.caption('Ampel-Skala')
    st.markdown('🟢 Grün ≥ 60 % Grünanteil  \n🟡 Gelb 40–<60 %  \n🔴 Rot < 40 %')
    st.divider()
    if selected >= pd.Timestamp('2026-10-27').date():
        st.caption('Ab 27.10.2026: Hauptmodell (XGBoost, Trainingsende 26.10.2026) mit echter Wettervorhersage '
                   '(27.10.–04.11.2026: nachträglich mit echtem ERA5-Wetter). Alle Zeiten in UTC.')
    else:
        st.caption('2018–26.10.2026: Hauptmodell (XGBoost) im Test, jedes Jahr nur aus 2015 bis zum Vorjahr '
                   'gelernt, mit historischem ERA5-Wetter. Alle Zeiten in UTC.')

day=frame.loc[frame.time_utc.dt.date==selected].copy().reset_index(drop=True)
if day.empty:
    st.warning('Für dieses Datum liegen keine vollständigen historischen Modellwerte vor.')
    st.stop()
day=add_scores(day)
best=best_window(day,duration)
ICONS={'Grün':'🟢','Gelb':'🟡','Rot':'🔴'}
label,color=category(best['average_renewable'])
icon=ICONS[label]
trend=day.predicted_co2.iloc[-1]-day.predicted_co2.iloc[0]
trend_icon,trend_text=('📉','wird grüner') if trend < -5 else ('📈','wird emissionsreicher') if trend > 5 else ('➡️','bleibt etwa stabil')

weekday=selected.strftime('%A, %d.%m.%Y')
st.markdown(f'#### {weekday}')
st.markdown(f'<div class="status" style="background:{color}">{icon} {label}: Bestes Zeitfenster '
            f'{best["start"]:%H:%M}–{best["end_exclusive"]:%H:%M} UTC · {trend_icon} Tagestrend {trend_text}</div>',
            unsafe_allow_html=True)
c1,c2,c3,c4=st.columns(4)
c1.metric('Beste Startzeit',f'{best["start"]:%H:%M} UTC')
c2.metric('Ø CO₂ im Fenster',f'{best["average_co2"]:.0f} gCO₂/kWh')
c3.metric('Ø Grünanteil',f'{best["average_renewable"]:.1f} %')
c4.metric('Kennzahl −2 bis +2',f'{best["score"]:+.1f}',help='+2 bedeutet innerhalb dieses Tages besonders emissionsarm; −2 besonders emissionsreich.')

st.divider()

COLORS={'CO₂-Intensität':'#263746','Grünanteil':'#16846a'}
color_scale=alt.Scale(domain=list(COLORS),range=list(COLORS.values()))
legend=alt.Legend(title=None,orient='top',direction='horizontal',labelFontSize=13)

chart_df=day[['time_utc','predicted_co2','predicted_renewable']].copy()
chart_df['hour']=chart_df.time_utc.dt.hour
co2_df=chart_df.assign(reihe='CO₂-Intensität')
renew_df=chart_df.assign(reihe='Grünanteil')
# end_exclusive.hour would be 0 for a window ending at midnight, so use start+duration.
start=best['start'].hour;end=start+duration

nearest=alt.selection_point(nearest=True,on='pointerover',fields=['hour'],empty=False)
window_rect=alt.Chart(pd.DataFrame({'start':[start],'end':[end]})).mark_rect(
    color='#8fd3ac',opacity=.3).encode(x='start:Q',x2='end:Q')
window_top=float(day.predicted_co2.max())
window_label=alt.Chart(pd.DataFrame({'mid':[(start+end)/2],'predicted_co2':[window_top]})).mark_text(
    align='center',baseline='top',dy=4,fontSize=11,color='#2f6b48',fontWeight='bold'
    ).encode(x='mid:Q',y=alt.Y('predicted_co2:Q',scale=alt.Scale(zero=False),axis=None),
             text=alt.value('Bestes Zeitfenster'))
co2_line=alt.Chart(co2_df).mark_line(strokeWidth=2.2).encode(
    x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,25,2))),scale=alt.Scale(domain=[0,24])),
    y=alt.Y('predicted_co2:Q',title='gCO₂/kWh',scale=alt.Scale(zero=False),
            axis=alt.Axis(orient='left',titleColor='#263746',labelColor='#263746')),
    color=alt.Color('reihe:N',scale=color_scale,legend=legend))
renew_line=alt.Chart(renew_df).mark_line(strokeWidth=2.2).encode(
    x='hour:Q',y=alt.Y('predicted_renewable:Q',title='Grünanteil (%)',scale=alt.Scale(domain=[0,100]),
            axis=alt.Axis(orient='right',titleColor='#16846a',labelColor='#16846a')),
    color=alt.Color('reihe:N',scale=color_scale,legend=legend))
selectors=alt.Chart(chart_df).mark_point().encode(x='hour:Q',opacity=alt.value(0),tooltip=alt.value(None)
    ).add_params(nearest)
rule=alt.Chart(chart_df).mark_rule(color='gray').encode(
    x='hour:Q',opacity=alt.condition(nearest,alt.value(.4),alt.value(0)))
co2_points=co2_line.mark_point(size=70).encode(
    opacity=alt.condition(nearest,alt.value(1),alt.value(0)))
renew_points=renew_line.mark_point(size=70).encode(
    opacity=alt.condition(nearest,alt.value(1),alt.value(0)))
co2_text=co2_line.mark_text(align='left',dx=10,dy=-10,fontSize=13,fontWeight='bold',color='#263746').encode(
    text=alt.condition(nearest,alt.Text('predicted_co2:Q',format='.0f'),alt.value('')))
renew_text=renew_line.mark_text(align='left',dx=10,dy=10,fontSize=13,fontWeight='bold',color='#16846a').encode(
    text=alt.condition(nearest,alt.Text('predicted_renewable:Q',format='.0f'),alt.value('')))
chart=alt.layer(window_rect,window_label,co2_line,renew_line,selectors,rule,co2_points,renew_points,co2_text,renew_text
    ).resolve_scale(y='independent',color='shared').properties(height=440)
st.altair_chart(chart,use_container_width=True)
st.caption('🟩 Grün hinterlegt: bestes Zeitfenster für die gewählte Jobdauer · Zahlen beim Überfahren mit der Maus.')

with st.expander('Stündliche Werte anzeigen'):
    table=day[['time_utc','predicted_co2','predicted_renewable','co2_change','score']].copy()
    table['Ampel']=table.predicted_renewable.map(lambda value:ICONS[category(value)[0]])
    table['time_utc']=table.time_utc.dt.strftime('%H:%M')
    table.columns=['Zeit (UTC)','CO₂ (gCO₂/kWh)','Grünanteil (%)','Δ CO₂','Kennzahl','Ampel']
    st.dataframe(table,hide_index=True,width='stretch',column_config={
        'CO₂ (gCO₂/kWh)':st.column_config.NumberColumn(format='%.0f'),
        'Grünanteil (%)':st.column_config.ProgressColumn(format='%.0f %%',min_value=0,max_value=100),
        'Δ CO₂':st.column_config.NumberColumn(format='%+.1f'),
        'Kennzahl':st.column_config.NumberColumn(format='%+d'),
        'Ampel':st.column_config.TextColumn(width='small'),
    })

st.divider()
BREAKDOWN_COLS=['predicted_wind_onshore','predicted_wind_offshore','predicted_solar',
                'predicted_biomass','predicted_hydro','predicted_other_renewables']
if day[BREAKDOWN_COLS].notna().all().all():
    st.markdown('#### Grünanteil nach Energiequelle')
    order=['Wind Onshore','Wind Offshore','Solar','Biomasse','Sonstiges']
    source_colors={'Wind Onshore':'#2a78d6','Wind Offshore':'#eb6834','Solar':'#1baf7a',
                   'Biomasse':'#eda100','Sonstiges':'#e87ba4'}
    breakdown=day[['time_utc']].copy()
    breakdown['hour']=breakdown.time_utc.dt.hour
    breakdown['Wind Onshore']=day.predicted_wind_onshore
    breakdown['Wind Offshore']=day.predicted_wind_offshore
    breakdown['Solar']=day.predicted_solar
    breakdown['Biomasse']=day.predicted_biomass
    breakdown['Sonstiges']=day.predicted_hydro+day.predicted_other_renewables
    long=breakdown.melt(id_vars='hour',value_vars=order,var_name='Quelle',value_name='Anteil')
    rank={name:i for i,name in enumerate(order)}
    long['rank']=long.Quelle.map(rank)
    breakdown_chart=alt.Chart(long).mark_area().encode(
        x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,24,2))),scale=alt.Scale(domain=[0,23])),
        y=alt.Y('Anteil:Q',title='Anteil an der Erzeugung (%)',stack='zero'),
        order=alt.Order('rank:Q',sort='ascending'),
        color=alt.Color('Quelle:N',sort=order,
            scale=alt.Scale(domain=order,range=[source_colors[k] for k in order]),
            legend=alt.Legend(title=None,orient='top',direction='horizontal',labelFontSize=12))
        ).properties(height=380)
    st.altair_chart(breakdown_chart,use_container_width=True)
    st.caption('Der Grünanteil ist die Summe dieser sechs Quellen-Vorhersagen. Wasserkraft und Sonstige '
               'Erneuerbare sind zu "Sonstiges" zusammengefasst — sie sind am schwersten vorherzusagen.')
else:
    st.info('Für dieses Datum liegt keine Aufschlüsselung nach Energiequelle vor.')

st.divider()
st.markdown('#### Bundesland-Vorhersage')
bl_frame=bundesland_data()
if bl_frame is None or bl_frame.empty:
    st.info('Noch keine Bundesland-Vorhersage verfügbar.')
else:
    states=sorted(bl_frame.bundesland.unique())
    chosen_state=st.selectbox('Bundesland',states,index=states.index('Berlin') if 'Berlin' in states else 0)
    bl_day=bl_frame.loc[(bl_frame.bundesland==chosen_state)&(bl_frame.time_utc.dt.date==selected)].copy()
    if bl_day.empty:
        st.info(f'Für {selected:%d.%m.%Y} liegt keine Vorhersage für {chosen_state} vor.')
    else:
        bl_day['hour']=bl_day.time_utc.dt.hour
        bl_co2_df=bl_day.assign(reihe='CO₂-Intensität')
        bl_renew_df=bl_day.assign(reihe='Grünanteil')
        bl_nearest=alt.selection_point(nearest=True,on='pointerover',fields=['hour'],empty=False)
        bl_co2_line=alt.Chart(bl_co2_df).mark_line(strokeWidth=2.2).encode(
            x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,24,2))),scale=alt.Scale(domain=[0,23])),
            y=alt.Y('predicted_co2:Q',title='gCO₂/kWh',scale=alt.Scale(zero=False),
                    axis=alt.Axis(orient='left',titleColor='#263746',labelColor='#263746')),
            color=alt.Color('reihe:N',scale=color_scale,legend=legend))
        bl_renew_line=alt.Chart(bl_renew_df).mark_line(strokeWidth=2.2).encode(
            x='hour:Q',y=alt.Y('predicted_renewable:Q',title='Grünanteil (%)',scale=alt.Scale(domain=[0,100]),
                    axis=alt.Axis(orient='right',titleColor='#16846a',labelColor='#16846a')),
            color=alt.Color('reihe:N',scale=color_scale,legend=legend))
        bl_selectors=alt.Chart(bl_day).mark_point().encode(x='hour:Q',opacity=alt.value(0),tooltip=alt.value(None)
            ).add_params(bl_nearest)
        bl_rule=alt.Chart(bl_day).mark_rule(color='gray').encode(
            x='hour:Q',opacity=alt.condition(bl_nearest,alt.value(.4),alt.value(0)))
        bl_co2_points=bl_co2_line.mark_point(size=70).encode(opacity=alt.condition(bl_nearest,alt.value(1),alt.value(0)))
        bl_renew_points=bl_renew_line.mark_point(size=70).encode(opacity=alt.condition(bl_nearest,alt.value(1),alt.value(0)))
        bl_co2_text=bl_co2_line.mark_text(align='left',dx=10,dy=-10,fontSize=13,fontWeight='bold',color='#263746').encode(
            text=alt.condition(bl_nearest,alt.Text('predicted_co2:Q',format='.0f'),alt.value('')))
        bl_renew_text=bl_renew_line.mark_text(align='left',dx=10,dy=10,fontSize=13,fontWeight='bold',color='#16846a').encode(
            text=alt.condition(bl_nearest,alt.Text('predicted_renewable:Q',format='.0f'),alt.value('')))
        bl_chart=alt.layer(bl_co2_line,bl_renew_line,bl_selectors,bl_rule,bl_co2_points,bl_renew_points,bl_co2_text,bl_renew_text
            ).resolve_scale(y='independent',color='shared').properties(height=360)
        st.altair_chart(bl_chart,use_container_width=True)
        BL_SOURCES=['predicted_wind_onshore','predicted_solar','predicted_biomass','predicted_hydro','predicted_other_renewables']
        if set(BL_SOURCES) <= set(bl_day.columns) and bl_day[BL_SOURCES].notna().all().all():
            bl_order=['Wind Onshore','Solar','Biomasse','Sonstiges']
            bl_colors={'Wind Onshore':'#2a78d6','Solar':'#1baf7a','Biomasse':'#eda100','Sonstiges':'#e87ba4'}
            bl_breakdown=pd.DataFrame({'hour':bl_day.hour.to_numpy(),'Wind Onshore':bl_day.predicted_wind_onshore.to_numpy(),
                                       'Solar':bl_day.predicted_solar.to_numpy(),'Biomasse':bl_day.predicted_biomass.to_numpy(),
                                       'Sonstiges':(bl_day.predicted_hydro+bl_day.predicted_other_renewables).to_numpy()})
            bl_long=bl_breakdown.melt(id_vars='hour',value_vars=bl_order,var_name='Quelle',value_name='Anteil')
            bl_long['rank']=bl_long.Quelle.map({name:i for i,name in enumerate(bl_order)})
            st.altair_chart(alt.Chart(bl_long).mark_area().encode(
                x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,24,2))),scale=alt.Scale(domain=[0,23])),
                y=alt.Y('Anteil:Q',title=f'Grünanteil nach Quelle, {chosen_state} (%)',stack='zero'),
                order=alt.Order('rank:Q',sort='ascending'),
                color=alt.Color('Quelle:N',sort=bl_order,scale=alt.Scale(domain=bl_order,range=[bl_colors[k] for k in bl_order]),
                                legend=alt.Legend(title=None,orient='top',direction='horizontal',labelFontSize=12))
                ).properties(height=300),use_container_width=True)
            st.caption('Wasserkraft und Geothermie sind zu "Sonstiges" zusammengefasst. Wind auf See ist keinem '
                       'Bundesland zugeordnet und fehlt daher in der Länderansicht.')
        st.caption('Bundesland-Modell: XGBoost, ein gemeinsames Modell für alle 16 Länder, mit Wetter, '
                   'installierter Leistung, Kalender, deutschlandweiten Energiedaten von vor 7 Tagen und der '
                   'Erzeugung im Land von vor 14 Tagen. Am unsichersten für Berlin, Bremen und Mecklenburg-Vorpommern.')

st.caption('Nationale Werte: Hauptmodell XGBoost (getrennte Modelle), CO₂ selbst berechnet aus SMARD-Erzeugung und UBA-Emissionsfaktoren (direkte Emissionen), Grünanteil als Summe der sechs Quellen. Bundesland-Werte: XGBoost-Bundesland-Modell, Grünanteil als Summe von fünf Quellen. Ampel: Grün ≥60 %, Gelb 40–<60 %, Rot <40 %.')
