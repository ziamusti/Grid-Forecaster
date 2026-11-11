"""Historical Stage-0 result explorer. Run: streamlit run app.py"""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard_logic import add_scores,best_window,category,load_bundesland_predictions,load_predictions
from src.scheduler_logic import best_execution_time,saving_percent

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Grid Forecaster',page_icon=':material/eco:',layout='wide')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--brand:#16846a;--brand-dark:#0f5c4a;--ink:#14231d;--muted:#5d6f68;--line:#e3ebe7;--soft:#eef3f0}
html,body,[class*="css"],.stMarkdown,.stMetric,button,input,select,textarea{font-family:'Inter',sans-serif}
.block-container{padding-top:3.4rem;max-width:1240px}
h4{font-weight:700;letter-spacing:-.015em;color:var(--ink);margin-top:.2rem}
/* Header */
.gf-header{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.2rem 0 1.2rem;
border-bottom:1px solid var(--line);margin-bottom:1.3rem}
.gf-brand{display:flex;align-items:center;gap:.85rem}
.gf-logo{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;flex:none;
background:linear-gradient(145deg,#1fa383,#0f5c4a);box-shadow:0 4px 12px rgba(15,92,74,.25)}
.gf-title{font-size:1.45rem;font-weight:700;letter-spacing:-.025em;color:var(--ink);line-height:1.15}
.gf-sub{font-size:.9rem;color:var(--muted);font-weight:500;margin-top:.1rem}
.gf-pill{display:inline-flex;align-items:center;gap:.45rem;padding:.4rem .8rem;border-radius:999px;font-size:.82rem;
font-weight:600;color:var(--brand-dark);background:#e7f5ef;border:1px solid #cfe9dd;white-space:nowrap}
.gf-pulse{width:.5rem;height:.5rem;border-radius:50%;background:var(--brand);box-shadow:0 0 0 3px rgba(22,132,106,.18)}
/* Tabs as a segmented control */
[data-baseweb="tab-list"]{gap:.25rem;background:var(--soft);padding:.3rem;border-radius:12px;width:fit-content;margin-bottom:.4rem}
[data-baseweb="tab"]{height:2.35rem;padding:0 1rem;border-radius:9px;background:transparent}
[data-baseweb="tab"] p{font-weight:600;color:var(--muted);font-size:.92rem}
[data-baseweb="tab"][aria-selected="true"]{background:#fff;box-shadow:0 1px 4px rgba(20,35,29,.10)}
[data-baseweb="tab"][aria-selected="true"] p,[data-baseweb="tab"][aria-selected="true"] span{color:var(--brand-dark)}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}
/* Status bar */
.status{display:flex;flex-wrap:wrap;align-items:center;gap:.7rem;padding:.8rem 1rem;border-radius:14px;margin-bottom:1rem;
font-weight:500;font-size:.98rem;color:var(--ink);background:#fff;border:1px solid var(--line);box-shadow:0 2px 10px rgba(29,43,38,.05)}
.badge{display:inline-flex;align-items:center;gap:.4rem;padding:.25rem .65rem;border-radius:999px;font-weight:700;font-size:.85rem;
color:var(--c);background:color-mix(in srgb,var(--c) 12%,white)}
.badge .dot{background:var(--c)}
.trend{display:inline-flex;align-items:center;gap:.35rem;color:var(--muted);font-weight:500;margin-left:auto}
.trend svg{flex:none}
/* Cards */
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:1rem 1.1rem;border-radius:16px;
box-shadow:0 2px 10px rgba(29,43,38,.05)}
[data-testid="stMetricLabel"] p{font-size:.76rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
[data-testid="stMetricValue"]{font-weight:700;letter-spacing:-.02em;color:var(--ink);font-size:clamp(1.3rem,2.1vw,2rem)}
[data-testid="stVegaLiteChart"],[data-testid="stArrowVegaLiteChart"]{background:#fff;border:1px solid var(--line);
border-radius:16px;box-shadow:0 2px 10px rgba(29,43,38,.05)}
[data-testid="stExpander"] details{border-radius:12px;border-color:var(--line);background:#fff}
/* Sidebar */
[data-testid="stSidebar"]{background:#f1f5f3;border-right:1px solid var(--line)}
[data-baseweb="slider"] [role="slider"]{background:var(--brand)!important;box-shadow:0 0 0 4px rgba(22,132,106,.15)!important}
[data-testid="stSliderThumbValue"]{color:var(--brand)!important}
.gf-card-title{font-weight:700;font-size:1.02rem;color:var(--ink);margin:.2rem 0 .25rem}
.gf-legend{display:flex;flex-wrap:wrap;gap:.35rem 1rem;font-size:.86rem;color:var(--muted);margin-bottom:.4rem}
.gf-legend span{display:inline-flex;align-items:center;gap:.4rem}
.gf-legend i{width:10px;height:10px;border-radius:50%;display:inline-block}
.chips{display:flex;flex-direction:column;gap:.45rem}
.chip{display:inline-flex;align-items:center;gap:.5rem;padding:.35rem .7rem;border-radius:999px;font-size:.86rem;
font-weight:600;color:var(--ink);background:#fff;border:1px solid var(--line);width:fit-content}
.dot{width:.6rem;height:.6rem;border-radius:50%;display:inline-block}
hr{margin:1.4rem 0 1rem;border-color:var(--line)}
</style>''',unsafe_allow_html=True)


LOGO=('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" '
      'stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 '
      '2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>')
TREND_SVG={'down':'<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
           'up':'<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
           'flat':'<line x1="4" y1="12" x2="20" y2="12"/><polyline points="14 6 20 12 14 18"/>'}


def trend_html(delta: float) -> str:
    kind,text=('down','Tagestrend wird grüner') if delta < -5 else ('up','Tagestrend wird emissionsreicher') if delta > 5 else ('flat','Tagestrend bleibt etwa stabil')
    return (f'<span class="trend"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{TREND_SVG[kind]}</svg>{text}</span>')


def status_html(color: str, label: str, text: str, delta: float) -> str:
    return (f'<div class="status"><span class="badge" style="--c:{color}"><span class="dot"></span>{label}</span>'
            f'<span>{text}</span>{trend_html(delta)}</div>')


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
    color_scale=alt.Scale(domain=order,range=[colors[k] for k in order])
    color=alt.Color('Quelle:N',sort=order,scale=color_scale,
                    legend=alt.Legend(title=None,orient='top',direction='horizontal',labelFontSize=12))
    # Invisible layer that owns the legend click and dims hidden entries.
    legend_layer=alt.Chart(long).mark_point(size=0,filled=True).encode(
        x=x,y='Anteil:Q',color=color,opacity=alt.condition(shown,alt.value(1),alt.value(.25))).add_params(shown)
    areas=alt.Chart(long).transform_filter(shown).mark_area(opacity=.9).encode(
        x=x,y=alt.Y('Anteil:Q',title=y_title,stack='zero'),order=alt.Order('rank:Q',sort='ascending'),color=color)
    table=wide.assign(Zeit=wide.hour.map(lambda h:f'{h:02d}:00 UTC'),Summe=wide[order].sum(axis=1),
                      lo=wide.hour-.5,hi=wide.hour+.5)
    table['Kopf']=table.Zeit.map(lambda z:f'Stunde {z}')
    table['Fuss']=table.Summe.map(lambda v:f'Summe: {v:.1f} %'.replace('.',','))
    long['Zeile']=[f'{q}: {v:.1f} %'.replace('.',',') for q,v in zip(long.Quelle,long.Anteil)]
    targets=alt.Chart(table).mark_rect(color='#000',opacity=.001,clip=True).encode(
        x='lo:Q',x2='hi:Q',tooltip=alt.value(None)).add_params(hover)
    rule=alt.Chart(table).mark_rule(color='#1d2b26',strokeWidth=1.2).encode(
        x='hour:Q',opacity=alt.condition(hover,alt.value(.5),alt.value(0)))
    # Markers on top of each visible layer at the hovered hour.
    markers=alt.Chart(long).transform_filter(shown).transform_stack(
        stack='Anteil',groupby=['hour'],sort=[alt.SortField('rank')],as_=['y0','y1']).transform_filter(hover
        ).mark_point(filled=True,size=70,stroke='white',strokeWidth=2,opacity=1).encode(
        x='hour:Q',y='y1:Q',color=alt.Color('Quelle:N',sort=order,scale=color_scale,legend=None))
    # Own hover box like energy-charts.info: time, coloured dot + value per source, sum.
    # It sits right of the cursor and flips to the left in the second half of the day.
    box_w,top,row=232,10,22
    box_h=40+len(order)*row+36
    left=f"datum.hour <= 13 ? scale('x', datum.hour) + 16 : scale('x', datum.hour) - 16 - {box_w}"
    px=lambda expr:{'value':{'expr':expr}}
    box=alt.Chart(table).transform_filter(hover).mark_rect(
        fill='white',stroke='#c9d8d1',strokeWidth=1,cornerRadius=10,opacity=.97).encode(
        x=px(left),x2=px(f'({left}) + {box_w}'),y=alt.value(top),y2=alt.value(top+box_h))
    head=alt.Chart(table).transform_filter(hover).mark_text(
        align='left',baseline='middle',fontSize=13,fontWeight=700,color='#14231d').encode(
        x=px(f'({left}) + 14'),y=alt.value(top+20),text='Kopf:N')
    lines=alt.Chart(table).transform_filter(hover).mark_rule(color='#e3ebe7').encode(
        x=px(f'({left}) + 14'),x2=px(f'({left}) + {box_w-14}'),y=alt.value(top+38))
    sep=alt.Chart(table).transform_filter(hover).mark_rule(color='#e3ebe7').encode(
        x=px(f'({left}) + 14'),x2=px(f'({left}) + {box_w-14}'),y=alt.value(top+box_h-32))
    dots=alt.Chart(long).transform_filter(hover).mark_point(filled=True,size=90,opacity=1).encode(
        x=px(f'({left}) + 20'),y=px(f'{top+52} + datum.rank * {row}'),
        color=alt.Color('Quelle:N',sort=order,scale=color_scale,legend=None))
    texts=alt.Chart(long).transform_filter(hover).mark_text(
        align='left',baseline='middle',fontSize=12.5,color='#1d2b26').encode(
        x=px(f'({left}) + 32'),y=px(f'{top+52} + datum.rank * {row}'),text='Zeile:N')
    foot=alt.Chart(table).transform_filter(hover).mark_text(
        align='left',baseline='middle',fontSize=12.5,fontWeight=700,color='#14231d').encode(
        x=px(f'({left}) + 14'),y=alt.value(top+box_h-16),text='Fuss:N')
    # The legend-owning layer must come first, otherwise the click is not wired.
    return alt.layer(legend_layer,areas,rule,markers,targets,box,head,lines,sep,dots,texts,foot).properties(height=height)


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
    shapes=alt.Chart(borders).mark_geoshape(stroke='white',strokeJoin='round').encode(
        color=alt.Color('Ampel:N',scale=alt.Scale(domain=list(colors),range=list(colors.values())),legend=None),
        strokeWidth=alt.condition(hover,alt.value(3.5),alt.value(1.2)),
        opacity=alt.condition(hover,alt.value(1),alt.value(.9)),
        tooltip=[alt.Tooltip('Land:N',title='Bundesland'),alt.Tooltip('Zeit:N',title='Zeit'),
                 alt.Tooltip('Gruen:Q',title='Grünanteil (%)',format='.0f'),
                 alt.Tooltip('CO2:Q',title='CO₂ (gCO₂/kWh)',format='.0f'),
                 alt.Tooltip('Quelle:N',title='Stärkste erneuerbare Quelle'),alt.Tooltip('Ampel:N',title='Ampel')]
    ).transform_lookup(lookup='properties.name',
                       from_=alt.LookupData(table,'Land',['Land','Zeit','Gruen','CO2','Quelle','Ampel'])
    ).add_params(hover)
    # Value label (renewable share in %) in the middle of each state; the city
    # states get a short name so the number is not mistaken for the state around them.
    short={'Berlin':'B','Hamburg':'HH','Bremen':'HB','Saarland':'SL'}
    labels=table.merge(state_centers(),on='Land')
    labels['Text']=[f'{short[n]} {v:.0f} %' if n in short else f'{v:.0f} %' for n,v in zip(labels.Land,labels.Gruen)]
    text_big=alt.Chart(labels[~labels.Land.isin(short)]).mark_text(fontSize=14,fontWeight=700,color='white').encode(
        longitude='lon:Q',latitude='lat:Q',text='Text:N',tooltip=alt.value(None))
    text_small=alt.Chart(labels[labels.Land.isin(short)]).mark_text(fontSize=10.5,fontWeight=700,color='#14231d',dy=-11).encode(
        longitude='lon:Q',latitude='lat:Q',text='Text:N',tooltip=alt.value(None))
    return alt.layer(shapes,text_big,text_small).project('mercator').properties(height=height)


@st.cache_data(show_spinner=False)
def state_centers() -> pd.DataFrame:
    # Area-weighted centre of the largest polygon of each state (for the map labels).
    import json
    geo=json.loads((ROOT/'data/geo/bundeslaender_naturalearth.geojson').read_text())
    rows=[]
    for feature in geo['features']:
        geom=feature['geometry']
        polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
        best=None
        for poly in polys:
            ring=poly[0];area=cx=cy=0.0
            for (x0,y0),(x1,y1) in zip(ring,ring[1:]+ring[:1]):
                c=x0*y1-x1*y0;area+=c;cx+=(x0+x1)*c;cy+=(y0+y1)*c
            if area and (best is None or abs(area)>abs(best[0])):
                best=(area,cx/(3*area),cy/(3*area))
        rows.append(dict(Land=feature['properties']['name'],lon=best[1],lat=best[2]))
    centers=pd.DataFrame(rows).set_index('Land')
    # Brandenburg's centre falls on Berlin; move its label south-east of Berlin.
    centers.loc['Brandenburg',['lon','lat']]=[13.85,51.95]
    return centers.reset_index()


def ranking_chart(rows: pd.DataFrame, height: int = 640):
    # All states sorted by renewable share for the map hour; colour = traffic light.
    table=rows[['bundesland','predicted_renewable','predicted_co2']].rename(
        columns={'bundesland':'Land','predicted_renewable':'Gruen','predicted_co2':'CO2'})
    table['Ampel']=table.Gruen.map(lambda value:category(value)[0])
    table['Wert']=table.Gruen.map(lambda v:f'{v:.0f} %')
    colors={name:category(value)[1] for name,value in [('Grün',100),('Gelb',50),('Rot',0)]}
    y=alt.Y('Land:N',sort=table.sort_values('Gruen',ascending=False).Land.tolist(),title=None,
            axis=alt.Axis(labelFontSize=12.5,labelColor='#1d2b26',labelLimit=190,ticks=False,domain=False,grid=False))
    bars=alt.Chart(table).mark_bar(cornerRadiusEnd=4,height={'band':.68}).encode(
        x=alt.X('Gruen:Q',title='Grünanteil (%)',scale=alt.Scale(domain=[0,112],nice=False),axis=alt.Axis(values=[0,40,60,100])),
        y=y,color=alt.Color('Ampel:N',scale=alt.Scale(domain=list(colors),range=list(colors.values())),legend=None),
        tooltip=[alt.Tooltip('Land:N',title='Bundesland'),alt.Tooltip('Gruen:Q',title='Grünanteil (%)',format='.0f'),
                 alt.Tooltip('CO2:Q',title='CO₂ (gCO₂/kWh)',format='.0f'),alt.Tooltip('Ampel:N',title='Ampel')])
    values=alt.Chart(table).mark_text(align='left',dx=6,fontSize=12,fontWeight=600,color='#1d2b26').encode(
        x='Gruen:Q',y=y,text='Wert:N')
    limits=alt.Chart(pd.DataFrame({'x':[40,60]})).mark_rule(color='#9fb2aa',strokeDash=[3,3]).encode(x='x:Q')
    return alt.layer(limits,bars,values).properties(height=height)


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
forecast_until=(frame.time_utc.max()+pd.Timedelta(hours=1)).tz_convert('Europe/Berlin')
st.markdown(f'<div class="gf-header"><div class="gf-brand"><div class="gf-logo">{LOGO}</div><div>'
            '<div class="gf-title">Grid Forecaster</div>'
            '<div class="gf-sub">CO₂-Intensität und Grünanteil im Stromnetz – Deutschland und Bundesländer</div></div></div>'
            f'<span class="gf-pill"><span class="gf-pulse"></span>Vorhersage bis {forecast_until:%d.%m. %H:%M}</span></div>',
            unsafe_allow_html=True)
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
    with st.expander('Datenstand',icon=':material/database:'):
        if selected >= pd.Timestamp('2026-10-27').date():
            st.caption('Ab 27.10.2026: Hauptmodell (XGBoost, Trainingsende 26.10.2026) mit echter Wettervorhersage '
                       '(27.10.–04.11.2026: nachträglich mit echtem ERA5-Wetter). Alle Zeiten in UTC.')
        else:
            st.caption('2018–26.10.2026: Hauptmodell (XGBoost) im Test, jedes Jahr nur aus 2015 bis zum Vorjahr '
                       'gelernt, mit historischem ERA5-Wetter. Alle Zeiten in UTC.')


tab_de,tab_bl,tab_job=st.tabs([':material/monitoring: Deutschland',':material/map: Bundesländer',':material/event_available: Job planen'])
with tab_de:
    day=frame.loc[frame.time_utc.dt.date==selected].copy().reset_index(drop=True)
    if day.empty:
        st.warning('Für dieses Datum liegen keine vollständigen historischen Modellwerte vor.')
        st.stop()
    day=add_scores(day)
    best=best_window(day,duration)
    label,color=category(best['average_renewable'])
    trend=day.predicted_co2.iloc[-1]-day.predicted_co2.iloc[0]

    WEEKDAYS=['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']
    weekday=f'{WEEKDAYS[selected.weekday()]}, {selected:%d.%m.%Y}'
    st.markdown(f'#### {weekday}')
    st.markdown(status_html(color,label,f'Bestes Zeitfenster <b>{best["start"]:%H:%M}–{best["end_exclusive"]:%H:%M} UTC</b>',trend),
                unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Beste Startzeit',f'{best["start"]:%H:%M} UTC')
    c2.metric('Ø CO₂ im Fenster',f'{best["average_co2"]:.0f} gCO₂/kWh')
    c3.metric('Ø Grünanteil im Fenster',f'{best["average_renewable"]:.1f} %')
    c4.metric('Kennzahl −2 bis +2',f'{best["score"]:+.1f}',help='+2 bedeutet innerhalb dieses Tages besonders emissionsarm; −2 besonders emissionsreich.')


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

    with st.expander('Stündliche Werte anzeigen',icon=':material/table_rows:'):
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
    else:
        st.info('Für dieses Datum liegt keine Aufschlüsselung nach Energiequelle vor.')

    with st.expander('Was zeigt diese Seite?',icon=':material/info:'):
        st.markdown('Grün hinterlegt: bestes Zeitfenster für die gewählte Jobdauer · Zahlen beim Überfahren mit der Maus.')
        st.markdown('Der Grünanteil ist die Summe dieser sechs Quellen-Vorhersagen. Wasserkraft und Sonstige ' 'Erneuerbare sind zu "Sonstiges" zusammengefasst. Legende anklicken blendet eine Quelle aus oder ein; ' 'Maus über das Diagramm zeigt alle Werte der Stunde.')
        st.markdown('Nationale Werte: Hauptmodell XGBoost (getrennte Modelle), CO₂ selbst berechnet aus SMARD-Erzeugung und UBA-Emissionsfaktoren (direkte Emissionen), Grünanteil als Summe der sechs Quellen. Bundesland-Werte: XGBoost-Bundesland-Modell, Grünanteil als Summe von fünf Quellen. Ampel: Grün ≥60 %, Gelb 40–<60 %, Rot <40 %.')
with tab_bl:
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
            map_col,rank_col=st.columns([3,2],gap='large')
            legend_html=''.join(f'<span><i style="background:{category(v)[1]}"></i>{t}</span>'
                                for t,v in [('Grün ≥ 60 %',100),('Gelb 40–60 %',50),('Rot < 40 %',0)])
            with map_col:
                st.markdown(f'<div class="gf-card-title">Grünanteil je Bundesland · {map_time:%d.%m.%Y, %H:00} UTC</div>'
                            f'<div class="gf-legend">{legend_html}</div>',unsafe_allow_html=True)
                st.altair_chart(bundesland_map(map_rows,height=640),use_container_width=True)
            with rank_col:
                st.markdown('<div class="gf-card-title">Rangfolge</div>'
                            '<div class="gf-legend"><span>gestrichelt: Grenzen 40 % und 60 %</span></div>',
                            unsafe_allow_html=True)
                st.altair_chart(ranking_chart(map_rows,height=640),use_container_width=True)
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
            st.markdown(status_html(bl_color,bl_label,
                        f'<b>{chosen_state}</b> · Bestes Zeitfenster <b>{bl_best["start"]:%H:%M}–{bl_best["end_exclusive"]:%H:%M} UTC</b> · '
                        f'Ø {bl_best["average_co2"]:.0f} gCO₂/kWh, {bl_best["average_renewable"]:.0f} % grün',bl_trend),
                        unsafe_allow_html=True)
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

    with st.expander('Was zeigt diese Seite?',icon=':material/info:'):
        st.markdown('Farbe = Ampel nach vorhergesagtem Grünanteil. Maus über ein Land zeigt die Werte. ' 'Landesgrenzen: Natural Earth (gemeinfrei).')
        st.markdown('Wasserkraft und Geothermie sind zu "Sonstiges" zusammengefasst. Wind auf See ist keinem ' 'Bundesland zugeordnet und fehlt daher in der Länderansicht.')
        st.markdown('Bundesland-Modell: XGBoost, ein gemeinsames Modell für alle 16 Länder, mit Wetter, ' 'installierter Leistung, Kalender, deutschlandweiten Energiedaten von vor 7 Tagen und der ' 'Erzeugung im Land von vor 14 Tagen. Am unsichersten für Berlin, Bremen und Mecklenburg-Vorpommern.')
with tab_job:
    # Demonstrator: carbon-aware scheduling of a flexible job (same logic as scripts/carbon_scheduler.py).
    st.caption('Für einen zeitlich flexiblen Job (z. B. Backup) die emissionsärmste Startzeit innerhalb der Frist. '
               'Alle Zeiten in deutscher Zeit.')
    BERLIN='Europe/Berlin'
    places=['Deutschland']+(sorted(bl_frame.bundesland.unique()) if bl_frame is not None and not bl_frame.empty else [])
    now_local=pd.Timestamp.now(tz=BERLIN).ceil('h')
    j1,j2,j3=st.columns([1,1,2])
    job_hours=j1.selectbox('Jobdauer',list(range(1,7)),index=1,format_func=lambda h:f'{h} Stunde'+('n' if h>1 else ''))
    job_place=j2.selectbox('Ort',places,key='job_place')
    job_span=j3.select_slider('Fertig spätestens nach',options=[6,12,24,48,72],value=24,
                              format_func=lambda h:f'{h} Stunden',help='Frist ab dem frühesten Start.')
    k1,k2=st.columns([1,1])
    start_date=k1.date_input('Frühester Start (Tag)',value=now_local.date(),format='DD.MM.YYYY',key='job_date')
    start_hour=k2.selectbox('Frühester Start (Uhrzeit)',list(range(24)),index=now_local.hour,format_func=lambda h:f'{h:02d}:00',key='job_hour')
    job_earliest=pd.Timestamp(start_date).tz_localize(BERLIN)+pd.Timedelta(hours=start_hour)
    job_deadline=job_earliest+pd.Timedelta(hours=job_span)
    if job_place=='Deutschland':
        job_forecast=frame[['time_utc','predicted_co2','predicted_renewable']]
    else:
        job_forecast=bl_frame.loc[bl_frame.bundesland==job_place,['time_utc','predicted_co2','predicted_renewable']]
    job_forecast=job_forecast.dropna().drop_duplicates('time_utc',keep='last').set_index('time_utc').sort_index()
    plan=best_execution_time(job_forecast,job_earliest.tz_convert('UTC'),job_deadline.tz_convert('UTC'),job_hours)
    forecast_end=(job_forecast.index.max()+pd.Timedelta(hours=1)).tz_convert(BERLIN)
    if plan is None:
        st.info(f'Für diesen Zeitraum gibt es keine Vorhersage (Vorhersage reicht bis {forecast_end:%d.%m. %H:%M}).')
    else:
        if job_deadline>forecast_end:
            st.warning(f'Die Vorhersage reicht nur bis {forecast_end:%d.%m. %H:%M}; spätere Startzeiten wurden nicht geprüft.')
        best_local=plan['start'].tz_convert(BERLIN); end_local=plan['end'].tz_convert(BERLIN)
        m1,m2,m3,m4=st.columns(4)
        m1.metric('Bester Start',f'{best_local:%d.%m. %H:%M}',help=f'Ende {end_local:%d.%m. %H:%M}')
        m2.metric('Erwartet im Fenster',f'{plan["co2"]:.0f} g · {plan["renewable"]:.0f} %',help='gCO₂/kWh · Grünanteil')
        m3.metric('Gegenüber sofort',f'−{saving_percent(plan["co2"],plan["immediate"]["co2"]):.0f} %',
                  help=f'Sofortiger Start: {plan["immediate"]["co2"]:.0f} gCO₂/kWh')
        m4.metric('Gegenüber zufällig',f'−{saving_percent(plan["co2"],plan["random_co2"]):.0f} %',
                  help=f'Mittel über alle {plan["starts"]} erlaubten Startzeiten: {plan["random_co2"]:.0f} gCO₂/kWh')
        span=job_forecast.loc[(job_forecast.index>=job_earliest.floor('h').tz_convert('UTC'))&
                              (job_forecast.index<job_deadline.tz_convert('UTC'))].reset_index()
        # Naive local times so Vega shows German time regardless of the viewer's time zone.
        span['zeit']=span.time_utc.dt.tz_convert(BERLIN).dt.tz_localize(None)
        naive=lambda t:t.tz_convert(BERLIN).tz_localize(None)
        job_hover=alt.selection_point(nearest=True,on='pointerover',fields=['zeit'],empty=False)
        job_window=alt.Chart(pd.DataFrame({'a':[naive(plan['start'])],'b':[naive(plan['end'])]})).mark_rect(
            color='#8fd3ac',opacity=.35).encode(x='a:T',x2='b:T')
        job_now=alt.Chart(pd.DataFrame({'a':[naive(plan['immediate']['start'])],'t':['sofort']})).mark_rule(
            color='#c2413b',strokeDash=[5,4],strokeWidth=1.5).encode(x='a:T')
        job_now_text=alt.Chart(pd.DataFrame({'a':[naive(plan['immediate']['start'])]})).mark_text(
            align='left',dx=5,dy=-6,baseline='bottom',fontSize=11,color='#c2413b',fontWeight='bold').encode(
            x='a:T',y=alt.value(14),text=alt.value('sofort'))
        job_best_text=alt.Chart(pd.DataFrame({'a':[naive(plan['start'])]})).mark_text(
            align='left',dx=5,baseline='top',fontSize=11,color='#2f6b48',fontWeight='bold').encode(
            x='a:T',y=alt.value(6),text=alt.value('bestes Fenster'))
        job_line=alt.Chart(span).mark_line(strokeWidth=2.2,color='#263746').encode(
            x=alt.X('zeit:T',title='Deutsche Zeit',axis=alt.Axis(format='%d.%m. %H:%M',labelAngle=0,tickCount=8)),
            y=alt.Y('predicted_co2:Q',title='gCO₂/kWh (Vorhersage)',scale=alt.Scale(zero=False)))
        job_points=job_line.mark_point(size=70,filled=True,color='#263746').encode(
            opacity=alt.condition(job_hover,alt.value(1),alt.value(0)),
            tooltip=[alt.Tooltip('zeit:T',title='Zeit',format='%d.%m. %H:%M'),
                     alt.Tooltip('predicted_co2:Q',title='CO₂ (g/kWh)',format='.0f'),
                     alt.Tooltip('predicted_renewable:Q',title='Grünanteil (%)',format='.0f')]).add_params(job_hover)
        st.altair_chart(alt.layer(job_window,job_now,job_line,job_points,job_now_text,job_best_text).properties(height=300),
                        use_container_width=True)
    with st.expander('Was zeigt diese Seite?',icon=':material/info:'):
        st.markdown('Grün hinterlegt: bestes Fenster · rote Linie: sofortiger Start. Einsparung nur laut Vorhersage, nicht gemessen. ' 'Gleiche Rechnung im Terminal: scripts/carbon_scheduler.py.')
