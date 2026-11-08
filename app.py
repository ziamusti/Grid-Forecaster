"""Historical Stage-0 result explorer. Run: streamlit run app.py"""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard_logic import add_scores,best_window,category,load_predictions

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
def data(source_version='historical-plus-september-through-29-v2'):
    return load_predictions(ROOT)

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
    if selected >= pd.Timestamp('2026-11-05').date():
        st.divider()
        st.caption('05.–07.11.2026: 3-Tage-Vorhersage mit aktualisierter MaStR-Kapazität (Stand 05.11.2026) — echte Wettervorhersage statt historischem ERA5-Wetter (CO₂ mit Preis-Merkmal, Trainingsende 26.10.2026). Alle Zeiten in UTC.')
    elif selected >= pd.Timestamp('2026-11-02').date():
        st.divider()
        st.caption('02.11.2026: Erste echte operative Vorhersage — echte Wettervorhersage statt historischem ERA5-Wetter (CO₂ mit Preis-Merkmal, Trainingsende 26.10.2026). Alle Zeiten in UTC.')
    elif selected >= pd.Timestamp('2026-09-24').date():
        st.divider()
        st.caption('24.09.–02.10.2026: Vorhersagen des finalen HistGradientBoosting-Modells (CO₂ mit Preis-Merkmal) mit historischem ERA5-Wetter. Alle Zeiten in UTC.')

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
c2.metric('Ø CO₂ im Fenster',f'{best["average_co2"]:.0f} gCO₂eq/kWh')
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
start=best['start'].hour;end=best['end_exclusive'].hour

nearest=alt.selection_point(nearest=True,on='pointerover',fields=['hour'],empty=False)
window_rect=alt.Chart(pd.DataFrame({'start':[start],'end':[end]})).mark_rect(
    color='#8fd3ac',opacity=.3).encode(x='start:Q',x2='end:Q')
window_top=float(day.predicted_co2.max())
window_label=alt.Chart(pd.DataFrame({'mid':[(start+end)/2],'predicted_co2':[window_top]})).mark_text(
    align='center',baseline='top',dy=4,fontSize=11,color='#2f6b48',fontWeight='bold'
    ).encode(x='mid:Q',y=alt.Y('predicted_co2:Q',scale=alt.Scale(zero=False),axis=None),
             text=alt.value('Bestes Zeitfenster'))
co2_line=alt.Chart(co2_df).mark_line(strokeWidth=2.2).encode(
    x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,24,2))),scale=alt.Scale(domain=[0,23])),
    y=alt.Y('predicted_co2:Q',title='gCO₂eq/kWh',scale=alt.Scale(zero=False),
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
    table.columns=['Zeit (UTC)','CO₂ (gCO₂eq/kWh)','Grünanteil (%)','Δ CO₂','Kennzahl','Ampel']
    st.dataframe(table,hide_index=True,width='stretch',column_config={
        'CO₂ (gCO₂eq/kWh)':st.column_config.NumberColumn(format='%.0f'),
        'Grünanteil (%)':st.column_config.ProgressColumn(format='%.0f %%',min_value=0,max_value=100),
        'Δ CO₂':st.column_config.NumberColumn(format='%+.1f'),
        'Kennzahl':st.column_config.NumberColumn(format='%+d'),
        'Ampel':st.column_config.TextColumn(width='small'),
    })

st.caption('Retrospektive Untersuchung mit historischem ERA5-Wetter. Gezeigt werden zeitlich getrennte HistGradientBoosting-Vorhersagen, keine zukünftige Wetterprognose. Ampel: Grün ≥60 %, Gelb 40–<60 %, Rot <40 %.')
