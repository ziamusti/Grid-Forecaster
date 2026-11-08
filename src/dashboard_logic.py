"""Pure helpers for the historical Stage-0 Streamlit dashboard."""
from __future__ import annotations
from pathlib import Path
from urllib.error import URLError
import pandas as pd


METHOD = 'hist_gradient_boosting'
LIVE_PREDICTIONS_URL = 'https://raw.githubusercontent.com/ziamusti/grid-forecaster-data/main/predictions.csv'
RENEWABLE_SOURCES = ['wind_onshore', 'wind_offshore', 'solar', 'biomass', 'hydro', 'other_renewables']
SELF_CO2_DEV = 'hist_gradient_boosting_self_co2_v1'
SELF_CO2_FINAL = 'final_hist_gradient_boosting_self_co2_2015_20261026_v1'
BREAKDOWN_DEV = 'hist_gradient_boosting_renewable_breakdown_v1'
BREAKDOWN_FINAL = 'final_hist_gradient_boosting_renewable_breakdown_2015_20261026_v1'


def prediction_paths(root: Path, year: int, target: str, price: bool) -> Path:
    base = 'hist_gradient_boosting_price' if price else 'hist_gradient_boosting'
    folder = f'{base}_v1' if year <= 2024 else f'{base}_test{year}_v1'
    return root/'reports'/folder/f'predictions_{year}_{target}.csv'


def self_co2_path(root: Path, year: int) -> Path:
    folder = SELF_CO2_DEV if year <= 2024 else SELF_CO2_FINAL
    return root/'reports'/folder/f'predictions_{year}.csv'


def breakdown_path(root: Path, source: str, year: int) -> Path:
    folder = BREAKDOWN_DEV if year <= 2024 else BREAKDOWN_FINAL
    return root/'reports'/folder/f'predictions_{source}_{year}.csv'


def load_predictions(root: Path) -> pd.DataFrame:
    # CO2 uses the self-computed target (SMARD generation mix + UBA emission
    # factors), replacing the Electricity-Maps-trained model for 2018-2026
    # (see docs/bachelorarbeit_protokoll.md for the licensing reason and the
    # methodology). Renewable share stays on the original model (unaffected
    # by that issue); the per-source breakdown is additional, computed by six
    # separate models whose predictions sum to that same total by construction.
    pieces=[]
    for year in range(2018,2027):
        co2=pd.read_csv(self_co2_path(root,year),usecols=['target_time_utc','hist_gradient_boosting_self_co2'])
        co2=co2.rename(columns={'hist_gradient_boosting_self_co2':'predicted_co2'})
        renewable=pd.read_csv(prediction_paths(root,year,'target_renewable_share_pct',price=False),
                               usecols=['target_time_utc','actual',METHOD,'common_scored'])
        renewable=renewable.loc[renewable.common_scored==1,['target_time_utc','actual',METHOD]]
        renewable=renewable.rename(columns={'actual':'actual_renewable',METHOD:'predicted_renewable'})
        piece=co2.merge(renewable,on='target_time_utc',validate='one_to_one')
        for source in RENEWABLE_SOURCES:
            path=breakdown_path(root,source,year)
            column='hist_gradient_boosting_'+source if year<=2024 else 'prediction'
            extra=pd.read_csv(path,usecols=['target_time_utc',column])
            extra=extra.rename(columns={column:'predicted_'+source})
            piece=piece.merge(extra,on='target_time_utc',how='left',validate='one_to_one')
        pieces.append(piece)
    result=pd.concat(pieces,ignore_index=True)
    extra_paths = [
        (root/'reports/hist_prediction_price_20260924_26_v1/predictions.csv',
         root/'reports/hist_prediction_20260924_26_v1/predictions.csv'),
        (root/'reports/hist_prediction_price_20260927_29_v1/predictions.csv',
         root/'reports/hist_prediction_20260927_29_v1/predictions.csv'),
        (root/'reports/hist_prediction_price_20260930_02_v1/predictions.csv',
         root/'reports/hist_prediction_20260930_02_v1/predictions.csv'),
        (root/'reports/forecast_price_20261102_1d_v1/predictions.csv', None),
    ]
    for co2_path,renewable_path in extra_paths:
        if not co2_path.exists():
            continue
        co2_extra=pd.read_csv(co2_path,usecols=['target_time_utc','predicted_co2_gco2eq_kwh'])
        co2_extra=co2_extra.rename(columns={'predicted_co2_gco2eq_kwh':'predicted_co2'})
        if renewable_path is None:
            renewable_extra=pd.read_csv(co2_path,usecols=['target_time_utc','predicted_renewable_share_pct'])
        else:
            renewable_extra=pd.read_csv(renewable_path,usecols=['target_time_utc','predicted_renewable_share_pct'])
        renewable_extra=renewable_extra.rename(columns={'predicted_renewable_share_pct':'predicted_renewable'})
        extra=co2_extra.merge(renewable_extra,on='target_time_utc',validate='one_to_one')
        if extra.isna().any().any():
            raise ValueError('Neue Vorhersagedatei enthält fehlende Werte')
        result=pd.concat([result,extra],ignore_index=True)
    live=load_live_predictions()
    if live is not None:
        result=pd.concat([result,live],ignore_index=True)
        result=result.drop_duplicates('target_time_utc',keep='last')
    result['time_utc']=pd.to_datetime(result.pop('target_time_utc'),utc=True)
    result=result.sort_values('time_utc').reset_index(drop=True)
    assert result.time_utc.is_unique
    assert result[['time_utc','predicted_co2','predicted_renewable']].notna().all().all()
    return result


def load_live_predictions() -> pd.DataFrame | None:
    # Written daily by the GitHub Actions job in the separate
    # grid-forecaster-data repo; not mirrored from GitLab, so it survives
    # pushes to this repo. None on any fetch problem, so a stale network or
    # an empty/missing file degrades to the historical data only.
    try:
        frame=pd.read_csv(LIVE_PREDICTIONS_URL,
                           usecols=['target_time_utc','predicted_co2_gco2eq_kwh','predicted_renewable_share_pct'])
    except (URLError, OSError, ValueError):
        return None
    if frame.empty:
        return None
    return frame.rename(columns={'predicted_co2_gco2eq_kwh':'predicted_co2',
                                  'predicted_renewable_share_pct':'predicted_renewable'})


def category(renewable: float) -> tuple[str,str]:
    if renewable >= 60:
        return 'Grün','#16846a'
    if renewable >= 40:
        return 'Gelb','#d69e2e'
    return 'Rot','#c2413b'


def add_scores(day: pd.DataFrame) -> pd.DataFrame:
    result=day.copy()
    percentile=result.predicted_co2.rank(method='average',pct=True)
    result['score']=pd.cut(percentile,bins=[0,.2,.4,.6,.8,1],labels=[2,1,0,-1,-2],include_lowest=True).astype(int)
    result['co2_change']=result.predicted_co2.diff()
    return result


def best_window(day: pd.DataFrame, duration: int) -> dict:
    if duration < 1 or duration > len(day):
        raise ValueError('Duration outside available day')
    rolling=day.predicted_co2.rolling(duration).mean()
    end=int(rolling.idxmin())
    positions=day.index.get_indexer([end])
    if positions[0] < duration-1:
        raise AssertionError('Invalid rolling window')
    start_pos=positions[0]-duration+1
    window=day.iloc[start_pos:positions[0]+1]
    return dict(start=window.time_utc.iloc[0],end_exclusive=window.time_utc.iloc[-1]+pd.Timedelta(hours=1),
                average_co2=float(window.predicted_co2.mean()),average_renewable=float(window.predicted_renewable.mean()),
                score=float(window.score.mean()))
