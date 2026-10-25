"""Historical Stage-0 result explorer. Run: streamlit run app.py"""
from pathlib import Path
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR',tempfile.mkdtemp(prefix='grid-streamlit-mpl-'))
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.dashboard_logic import add_scores,best_window,category,load_predictions

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Grid Forecaster',page_icon='🌱',layout='wide')
st.markdown('''<style>
.block-container{padding-top:2rem;max-width:1280px}.hero{padding:1.3rem 1.5rem;border-radius:18px;
background:linear-gradient(120deg,#12372a,#1d6b4d);color:white;margin-bottom:1.2rem}
.hero h1{margin:0;font-size:2.1rem}.hero p{margin:.4rem 0 0;color:#d9fbe8}
.status{padding:.85rem 1rem;border-radius:12px;color:white;font-weight:700;font-size:1.05rem}
[data-testid="stMetric"]{background:#f5f8f6;border:1px solid #dbe7df;padding:1rem;border-radius:14px}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🌱 Grid Forecaster</h1><p>Historische Analyse der CO₂-Intensität und des Grünanteils in Deutschland</p></div>',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def data():
    return load_predictions(ROOT)

try:
    frame=data()
except FileNotFoundError as error:
    st.error(f'Eine benötigte Vorhersagedatei fehlt: {error.filename}')
    st.stop()

minimum=frame.time_utc.dt.date.min(); maximum=frame.time_utc.dt.date.max()
left,right=st.columns([2,1])
with left:
    selected=st.date_input('Datum auswählen',value=maximum,min_value=minimum,max_value=maximum,format='DD.MM.YYYY')
with right:
    duration=st.slider('Jobdauer in Stunden',1,6,3)

day=frame.loc[frame.time_utc.dt.date==selected].copy().reset_index(drop=True)
if day.empty:
    st.warning('Für dieses Datum liegen keine vollständigen historischen Modellwerte vor.')
    st.stop()
day=add_scores(day)
best=best_window(day,duration)
label,color=category(best['average_renewable'])
trend=day.predicted_co2.iloc[-1]-day.predicted_co2.iloc[0]
trend_text='wird grüner' if trend < -5 else 'wird emissionsreicher' if trend > 5 else 'bleibt etwa stabil'

st.markdown(f'<div class="status" style="background:{color}">{label}: Bestes Zeitfenster {best["start"]:%H:%M}–{best["end_exclusive"]:%H:%M} UTC · Tagestrend {trend_text}</div>',unsafe_allow_html=True)
c1,c2,c3,c4=st.columns(4)
c1.metric('Beste Startzeit',f'{best["start"]:%H:%M} UTC')
c2.metric('Ø CO₂ im Fenster',f'{best["average_co2"]:.0f} gCO₂eq/kWh')
c3.metric('Ø Grünanteil',f'{best["average_renewable"]:.1f} %')
c4.metric('Kennzahl −2 bis +2',f'{best["score"]:+.1f}',help='+2 bedeutet innerhalb dieses Tages besonders emissionsarm; −2 besonders emissionsreich.')

fig,ax=plt.subplots(figsize=(13,5))
hours=day.time_utc.dt.hour
ax.plot(hours,day.predicted_co2,color='#263746',linewidth=2,label='CO₂-Intensität')
ax.set_xlabel('Stunde (UTC)');ax.set_ylabel('gCO₂eq/kWh',color='#263746');ax.set_xticks(range(0,24,2));ax.grid(alpha=.2)
ax2=ax.twinx();ax2.plot(hours,day.predicted_renewable,color='#16846a',linewidth=2,label='Grünanteil');ax2.set_ylabel('Grünanteil (%)',color='#16846a');ax2.set_ylim(0,100)
start=best['start'].hour;end=best['end_exclusive'].hour
window_patch=ax.axvspan(start,end,color='#8fd3ac',alpha=.28,label='Bestes Zeitfenster')
handles=[*ax.get_lines(),*ax2.get_lines(),window_patch]
ax.legend(handles,[h.get_label() for h in handles],loc='upper center',ncol=3,frameon=False)
st.pyplot(fig,width='stretch')
plt.close(fig)

with st.expander('Stündliche Werte anzeigen'):
    table=day[['time_utc','predicted_co2','predicted_renewable','co2_change','score']].copy()
    table['Ampel']=table.predicted_renewable.map(lambda value:category(value)[0])
    table.columns=['Zeit (UTC)','CO₂-Prognose','Grünanteil (%)','CO₂-Änderung','Kennzahl','Ampel']
    st.dataframe(table,hide_index=True,width='stretch')

st.caption('Retrospektive Untersuchung mit historischem ERA5-Wetter. Gezeigt werden zeitlich getrennte HistGradientBoosting-Vorhersagen, keine zukünftige Wetterprognose. Ampel: Grün ≥60 %, Gelb 40–<60 %, Rot <40 %.')
