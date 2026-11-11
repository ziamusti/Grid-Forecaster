"""Historical Stage-0 result explorer. Run: streamlit run app.py"""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard_logic import add_scores,best_window,category,load_bundesland_predictions,load_predictions

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Grid Forecaster',page_icon='🌱',layout='wide')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"],.stMarkdown,.stMetric,button,input,select,textarea{font-family:'Inter',sans-serif}
.block-container{padding-top:1.4rem;max-width:1240px}
h4{font-weight:700;letter-spacing:-.01em;color:#1d2b26;margin-top:.4rem}
.hero{position:relative;overflow:hidden;padding:1.6rem 1.9rem;border-radius:20px;color:white;margin-bottom:1.3rem;
background:radial-gradient(circle at 85% -20%,rgba(255,255,255,.18),transparent 45%),linear-gradient(120deg,#0f3326,#16846a);
box-shadow:0 10px 30px rgba(15,51,38,.18)}
.hero h1{margin:0;font-size:2rem;font-weight:700;letter-spacing:-.03em}
.hero p{margin:.4rem 0 0;color:#d6f5e6;font-size:1rem;font-weight:500}
.status{display:flex;align-items:center;gap:.6rem;padding:.85rem 1.1rem;border-radius:14px;margin-bottom:1rem;
font-weight:600;font-size:1.02rem;color:#1d2b26;background:#ffffff;border:1px solid #e3ebe7;
border-left:6px solid var(--accent);box-shadow:0 2px 10px rgba(29,43,38,.05)}
[data-testid="stMetric"]{background:#ffffff;border:1px solid #e3ebe7;padding:1rem 1.1rem;border-radius:16px;
box-shadow:0 2px 10px rgba(29,43,38,.05)}
[data-testid="stMetricLabel"] p{font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#5d6f68}
[data-testid="stMetricValue"]{font-weight:700;letter-spacing:-.02em;color:#1d2b26;font-size:clamp(1.3rem,2.1vw,2rem)}
[data-testid="stVegaLiteChart"],[data-testid="stArrowVegaLiteChart"]{background:#ffffff;border:1px solid #e3ebe7;
border-radius:16px;box-shadow:0 2px 10px rgba(29,43,38,.05)}
[data-testid="stSidebar"]{background:#eef3f0;border-right:1px solid #e3ebe7}
.chips{display:flex;flex-direction:column;gap:.45rem}
.chip{display:inline-flex;align-items:center;gap:.5rem;padding:.35rem .7rem;border-radius:999px;font-size:.88rem;
font-weight:600;color:#1d2b26;background:#ffffff;border:1px solid #e3ebe7;width:fit-content}
.dot{width:.7rem;height:.7rem;border-radius:50%}
hr{margin:1.5rem 0 1.1rem;border-color:#e3ebe7}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🌱 Grid Forecaster</h1>'
            '<p>Historische Analyse der CO₂-Intensität und des Grünanteils in Deutschland</p></div>',
            unsafe_allow_html=True)


def chart_theme():
    # Same charts, calmer look: one font, light grid, no axis domain lines.
    axis=dict(labelFont='Inter',titleFont='Inter',labelColor='#5d6f68',titleColor='#5d6f68',labelFontSize=12,
              titleFontSize=12,titleFontWeight=600,gridColor='#edf2ef',domain=False,tickColor='#e3ebe7')
    # Padding inside the chart; CSS padding on the card made Vega clip the axis labels.
    return dict(padding=dict(left=14,right=14,top=12,bottom=8),autosize=dict(type='fit',contains='padding'),
                config=dict(view=dict(stroke=None),font='Inter',axis=axis,
                            legend=dict(labelFont='Inter',labelFontSize=12,labelColor='#1d2b26',symbolType='circle'),
                            title=dict(font='Inter')))


if hasattr(alt,'theme'):  # Altair >= 5.5
    alt.theme.register('grid_forecaster',enable=True)(chart_theme)
else:
    alt.themes.register('grid_forecaster',chart_theme)
    alt.themes.enable('grid_forecaster')


def sources_chart(wide: pd.DataFrame, order: list[str], colors: dict, y_title: str, height: int):
    # Stacked area of the source shares per hour. Click a legend entry to hide
    # or show that source (the others restack); hover shows a box with every
    # source and the total, like energy-charts.info.
    long=wide.melt(id_vars='hour',value_vars=order,var_name='Quelle',value_name='Anteil')
    long['rank']=long.Quelle.map({name:i for i,name in enumerate(order)})
    shown=alt.selection_point(fields=['Quelle'],bind='legend',toggle='true',value=[{'Quelle':q} for q in order])
    hover=alt.selection_point(fields=['hour'],on='pointerover',clear='pointerout',empty=False)
    x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,24,2))),scale=alt.Scale(domain=[0,23]))
    color=alt.Color('Quelle:N',sort=order,scale=alt.Scale(domain=order,range=[colors[k] for k in order]),
                    legend=alt.Legend(title=None,orient='top',direction='horizontal',labelFontSize=12))
    # Invisible layer that owns the legend click and dims hidden entries.
    legend_layer=alt.Chart(long).mark_point(size=0,filled=True).encode(
        x=x,y='Anteil:Q',color=color,opacity=alt.condition(shown,alt.value(1),alt.value(.25))).add_params(shown)
    areas=alt.Chart(long).transform_filter(shown).mark_area(opacity=.9).encode(
        x=x,y=alt.Y('Anteil:Q',title=y_title,stack='zero'),order=alt.Order('rank:Q',sort='ascending'),color=color)
    table=wide.assign(Zeit=wide.hour.map(lambda h:f'{h:02d}:00 UTC'),Summe=wide[order].sum(axis=1),
                      lo=wide.hour-.5,hi=wide.hour+.5)
    tooltip=[alt.Tooltip('Zeit:N',title='Zeit'),
             *[alt.Tooltip(field=q,type='quantitative',title=q,format='.1f') for q in order],
             alt.Tooltip('Summe:Q',title='Grünanteil gesamt',format='.1f')]
    targets=alt.Chart(table).mark_rect(color='#000',opacity=.001,clip=True).encode(
        x='lo:Q',x2='hi:Q',tooltip=tooltip).add_params(hover)
    rule=alt.Chart(table).mark_rule(color='#1d2b26',strokeWidth=1.2).encode(
        x='hour:Q',opacity=alt.condition(hover,alt.value(.5),alt.value(0)))
    # The legend-owning layer must come first, otherwise the click is not wired.
    return alt.layer(legend_layer,areas,rule,targets).properties(height=height)


@st.cache_data(show_spinner=False)
def state_borders():
    # Passed as a data: URL, because Streamlit converts inline chart data to
    # Arrow tables, which fails for nested GeoJSON geometries.
    import base64
    raw=(ROOT/'data/geo/bundeslaender_naturalearth.geojson').read_bytes()
    return 'data:application/json;base64,'+base64.b64encode(raw).decode('ascii')


def bundesland_map(rows: pd.DataFrame, height: int = 560):
    # One colour per Bundesland by traffic light of the predicted renewable
    # share; hover shows a card with time, renewable share, CO2 and the
    # strongest renewable source.
    names={'predicted_wind_onshore':'Wind an Land','predicted_solar':'Solar','predicted_biomass':'Biomasse',
           'predicted_hydro':'Wasser','predicted_other_renewables':'Sonstige'}
    table=rows[['bundesland','time_utc','predicted_co2','predicted_renewable']].copy()
    table['Ampel']=table.predicted_renewable.map(lambda value:category(value)[0])
    table['Zeit']=table.time_utc.dt.strftime('%d.%m.%Y, %H:00 UTC')
    sources=[c for c in names if c in rows.columns]
    if sources:
        strongest=rows[sources].idxmax(axis=1).map(names)
        share=rows[sources].max(axis=1)
        table['Quelle']=[f'{n} ({v:.0f} %)' if isinstance(n,str) else '–' for n,v in zip(strongest,share)]
    else:
        table['Quelle']='–'
    table=table.drop(columns='time_utc').rename(columns={'bundesland':'Land','predicted_renewable':'Gruen','predicted_co2':'CO2'})
    colors={name:category(value)[1] for name,value in [('Grün',100),('Gelb',50),('Rot',0)]}
    hover=alt.selection_point(fields=['properties.name'],on='pointerover',clear='pointerout',empty=False)
    borders=alt.UrlData(url=state_borders(),format=alt.DataFormat(property='features',type='json'))
    return alt.Chart(borders).mark_geoshape(stroke='white').encode(
        color=alt.Color('Ampel:N',scale=alt.Scale(domain=list(colors),range=list(colors.values())),
                        legend=alt.Legend(title=None,orient='top',direction='horizontal',labelFontSize=12)),
        strokeWidth=alt.condition(hover,alt.value(3),alt.value(1)),
        opacity=alt.condition(hover,alt.value(1),alt.value(.88)),
        tooltip=[alt.Tooltip('Land:N',title='Bundesland'),alt.Tooltip('Zeit:N',title='Zeit'),
                 alt.Tooltip('Gruen:Q',title='Grünanteil (%)',format='.0f'),
                 alt.Tooltip('CO2:Q',title='CO₂ (gCO₂/kWh)',format='.0f'),
                 alt.Tooltip('Quelle:N',title='Stärkste erneuerbare Quelle'),alt.Tooltip('Ampel:N',title='Ampel')]
    ).transform_lookup(lookup='properties.name',
                       from_=alt.LookupData(table,'Land',['Land','Zeit','Gruen','CO2','Quelle','Ampel'])
    ).add_params(hover).project('mercator').properties(height=height)

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
    st.markdown('<div class="chips">'
                '<span class="chip"><span class="dot" style="background:#16846a"></span>Grün ≥ 60 % Grünanteil</span>'
                '<span class="chip"><span class="dot" style="background:#d69e2e"></span>Gelb 40–<60 %</span>'
                '<span class="chip"><span class="dot" style="background:#c2413b"></span>Rot < 40 %</span></div>',
                unsafe_allow_html=True)
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

WEEKDAYS=['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']
weekday=f'{WEEKDAYS[selected.weekday()]}, {selected:%d.%m.%Y}'
st.markdown(f'#### {weekday}')
st.markdown(f'<div class="status" style="--accent:{color}">{icon} {label}: Bestes Zeitfenster '
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
    table['Ampel']=table.predicted_renewable.map(lambda value:category(value)[0])
    table['time_utc']=table.time_utc.dt.strftime('%H:%M')
    table.columns=['Zeit (UTC)','CO₂ (gCO₂/kWh)','Grünanteil (%)','Δ CO₂','Kennzahl','Ampel']
    # Ampel as a coloured label in the traffic-light colours (same as the sidebar
    # chips); the first hour has no previous hour, so Δ CO₂ shows a dash.
    AMPEL={name:category(value)[1] for name,value in [('Grün',100),('Gelb',50),('Rot',0)]}
    styled=(table.style
            .map(lambda name:f'color:{AMPEL[name]};background-color:{AMPEL[name]}1f;font-weight:600',subset=['Ampel'])
            .format({'Δ CO₂':'{:+.1f}'},na_rep='–')
            .format({'Ampel':lambda name:f'● {name}'}))
    st.dataframe(styled,hide_index=True,width='stretch',column_config={
        'CO₂ (gCO₂/kWh)':st.column_config.NumberColumn(format='%.0f'),
        'Grünanteil (%)':st.column_config.ProgressColumn(format='%.0f %%',min_value=0,max_value=100),
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
    breakdown=pd.DataFrame({'hour':day.time_utc.dt.hour.to_numpy(),'Wind Onshore':day.predicted_wind_onshore.to_numpy(),
                            'Wind Offshore':day.predicted_wind_offshore.to_numpy(),'Solar':day.predicted_solar.to_numpy(),
                            'Biomasse':day.predicted_biomass.to_numpy(),
                            'Sonstiges':(day.predicted_hydro+day.predicted_other_renewables).to_numpy()})
    st.altair_chart(sources_chart(breakdown,order,source_colors,'Anteil an der Erzeugung (%)',380),use_container_width=True)
    st.caption('Der Grünanteil ist die Summe dieser sechs Quellen-Vorhersagen. Wasserkraft und Sonstige '
               'Erneuerbare sind zu "Sonstiges" zusammengefasst. Legende anklicken blendet eine Quelle aus oder ein; '
               'Maus über das Diagramm zeigt alle Werte der Stunde.')
else:
    st.info('Für dieses Datum liegt keine Aufschlüsselung nach Energiequelle vor.')

st.divider()
st.markdown('#### Bundesland-Vorhersage')
bl_frame=bundesland_data()
if bl_frame is None or bl_frame.empty:
    st.info('Noch keine Bundesland-Vorhersage verfügbar.')
else:
    map_hour=st.slider('Stunde für die Karte (UTC)',0,23,12,help='Karte aller Bundesländer für diese Stunde des gewählten Tages.')
    map_time=pd.Timestamp(selected).tz_localize('UTC')+pd.Timedelta(hours=map_hour)
    map_rows=bl_frame.loc[bl_frame.time_utc==map_time]
    if map_rows.empty:
        st.info(f'Für {map_time:%d.%m.%Y, %H:00} UTC liegt keine Bundesland-Vorhersage vor.')
    else:
        st.altair_chart(bundesland_map(map_rows),use_container_width=True)
        st.caption('Farbe = Ampel nach vorhergesagtem Grünanteil. Maus über ein Land zeigt die Werte. '
                   'Landesgrenzen: Natural Earth (gemeinfrei).')
    states=sorted(bl_frame.bundesland.unique())
    chosen_state=st.selectbox('Bundesland',states,index=states.index('Berlin') if 'Berlin' in states else 0)
    bl_day=bl_frame.loc[(bl_frame.bundesland==chosen_state)&(bl_frame.time_utc.dt.date==selected)].copy()
    if bl_day.empty:
        st.info(f'Für {selected:%d.%m.%Y} liegt keine Vorhersage für {chosen_state} vor.')
    else:
        bl_day=add_scores(bl_day.sort_values('time_utc').reset_index(drop=True))
        bl_best=best_window(bl_day,min(duration,len(bl_day)))
        bl_label,bl_color=category(bl_best['average_renewable'])
        bl_trend=bl_day.predicted_co2.iloc[-1]-bl_day.predicted_co2.iloc[0]
        bl_trend_icon,bl_trend_text=(('📉','wird grüner') if bl_trend < -5 else ('📈','wird emissionsreicher')
                                     if bl_trend > 5 else ('➡️','bleibt etwa stabil'))
        st.markdown(f'<div class="status" style="--accent:{bl_color}">{ICONS[bl_label]} {chosen_state} – {bl_label}: '
                    f'Bestes Zeitfenster {bl_best["start"]:%H:%M}–{bl_best["end_exclusive"]:%H:%M} UTC · '
                    f'Ø {bl_best["average_co2"]:.0f} gCO₂/kWh, {bl_best["average_renewable"]:.0f} % grün · '
                    f'{bl_trend_icon} Tagestrend {bl_trend_text}</div>',unsafe_allow_html=True)
        bl_day['hour']=bl_day.time_utc.dt.hour
        # end_exclusive.hour would be 0 for a window ending at midnight, so use start+duration.
        bl_start=bl_best['start'].hour;bl_end=bl_start+min(duration,len(bl_day))
        bl_window_rect=alt.Chart(pd.DataFrame({'start':[bl_start],'end':[bl_end]})).mark_rect(
            color='#8fd3ac',opacity=.3).encode(x='start:Q',x2='end:Q')
        bl_window_label=alt.Chart(pd.DataFrame({'mid':[(bl_start+bl_end)/2],'predicted_co2':[float(bl_day.predicted_co2.max())]})).mark_text(
            align='center',baseline='top',dy=4,fontSize=11,color='#2f6b48',fontWeight='bold'
            ).encode(x='mid:Q',y=alt.Y('predicted_co2:Q',scale=alt.Scale(zero=False),axis=None),
                     text=alt.value('Bestes Zeitfenster'))
        bl_co2_df=bl_day.assign(reihe='CO₂-Intensität')
        bl_renew_df=bl_day.assign(reihe='Grünanteil')
        bl_nearest=alt.selection_point(nearest=True,on='pointerover',fields=['hour'],empty=False)
        bl_co2_line=alt.Chart(bl_co2_df).mark_line(strokeWidth=2.2).encode(
            x=alt.X('hour:Q',title='Stunde (UTC)',axis=alt.Axis(values=list(range(0,25,2))),scale=alt.Scale(domain=[0,24])),
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
        bl_chart=alt.layer(bl_window_rect,bl_window_label,bl_co2_line,bl_renew_line,bl_selectors,bl_rule,bl_co2_points,bl_renew_points,bl_co2_text,bl_renew_text
            ).resolve_scale(y='independent',color='shared').properties(height=360)
        st.altair_chart(bl_chart,use_container_width=True)
        BL_SOURCES=['predicted_wind_onshore','predicted_solar','predicted_biomass','predicted_hydro','predicted_other_renewables']
        if set(BL_SOURCES) <= set(bl_day.columns) and bl_day[BL_SOURCES].notna().all().all():
            bl_order=['Wind Onshore','Solar','Biomasse','Sonstiges']
            bl_colors={'Wind Onshore':'#2a78d6','Solar':'#1baf7a','Biomasse':'#eda100','Sonstiges':'#e87ba4'}
            bl_breakdown=pd.DataFrame({'hour':bl_day.hour.to_numpy(),'Wind Onshore':bl_day.predicted_wind_onshore.to_numpy(),
                                       'Solar':bl_day.predicted_solar.to_numpy(),'Biomasse':bl_day.predicted_biomass.to_numpy(),
                                       'Sonstiges':(bl_day.predicted_hydro+bl_day.predicted_other_renewables).to_numpy()})
            st.altair_chart(sources_chart(bl_breakdown,bl_order,bl_colors,f'Grünanteil nach Quelle, {chosen_state} (%)',300),
                            use_container_width=True)
            st.caption('Wasserkraft und Geothermie sind zu "Sonstiges" zusammengefasst. Wind auf See ist keinem '
                       'Bundesland zugeordnet und fehlt daher in der Länderansicht.')
        st.caption('Bundesland-Modell: XGBoost, ein gemeinsames Modell für alle 16 Länder, mit Wetter, '
                   'installierter Leistung, Kalender, deutschlandweiten Energiedaten von vor 7 Tagen und der '
                   'Erzeugung im Land von vor 14 Tagen. Am unsichersten für Berlin, Bremen und Mecklenburg-Vorpommern.')

st.caption('Nationale Werte: Hauptmodell XGBoost (getrennte Modelle), CO₂ selbst berechnet aus SMARD-Erzeugung und UBA-Emissionsfaktoren (direkte Emissionen), Grünanteil als Summe der sechs Quellen. Bundesland-Werte: XGBoost-Bundesland-Modell, Grünanteil als Summe von fünf Quellen. Ampel: Grün ≥60 %, Gelb 40–<60 %, Rot <40 %.')
