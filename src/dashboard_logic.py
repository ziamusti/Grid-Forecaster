"""Pure helpers for the historical Stage-0 Streamlit dashboard."""
from __future__ import annotations
from pathlib import Path
from urllib.error import URLError
import pandas as pd


LIVE_PREDICTIONS_URL = 'https://raw.githubusercontent.com/ziamusti/grid-forecaster-data/main/predictions.csv'
BUNDESLAND_LIVE_URL = 'https://raw.githubusercontent.com/ziamusti/grid-forecaster-data/main/predictions_bundesland.csv'
RENEWABLE_SOURCES = ['wind_onshore', 'wind_offshore', 'solar', 'biomass', 'hydro', 'other_renewables']
# Main model: separate XGBoost models, self-computed CO2 (SMARD + UBA factors),
# renewable share = sum of the six predicted sources. History 2018-2026 comes
# from its expanding-window test (each year predicted by a model trained only
# on 2015..previous year), see docs/bachelorarbeit_protokoll.md.
MAIN_MODEL_HISTORY = 'xgboost_selfco2_separate_expanding_v1'
SOURCE_COLUMNS = {f'predicted_{s}_share_pct': f'predicted_{s}' for s in RENEWABLE_SOURCES}


def main_model_history_path(root: Path, year: int) -> Path:
    return root/'reports'/MAIN_MODEL_HISTORY/f'predictions_{year}.csv'


def read_main_model_file(path: Path | str) -> pd.DataFrame:
    # Forecast/backtest folders after predict_xgb_forecast.py and the live
    # file share these column names; sources are optional (older live files).
    frame=pd.read_csv(path)
    keep=['target_time_utc','predicted_co2_gco2eq_kwh','predicted_renewable_share_pct',
          *[c for c in SOURCE_COLUMNS if c in frame.columns]]
    frame=frame[keep].rename(columns={'predicted_co2_gco2eq_kwh':'predicted_co2',
                                      'predicted_renewable_share_pct':'predicted_renewable',**SOURCE_COLUMNS})
    if set(SOURCE_COLUMNS.values()) <= set(frame.columns):
        clip_sources(frame)
    return frame


def clip_sources(frame: pd.DataFrame) -> None:
    # Trees can return slightly negative shares (mostly solar at night); cut
    # them off at 0 and keep the renewable share equal to the sum of sources.
    columns=['predicted_'+s for s in RENEWABLE_SOURCES]
    frame[columns]=frame[columns].clip(lower=0)
    frame['predicted_renewable']=frame[columns].sum(axis=1)


def load_predictions(root: Path) -> pd.DataFrame:
    pieces=[]
    for year in range(2018,2027):
        raw=pd.read_csv(main_model_history_path(root,year))
        piece=pd.DataFrame({'target_time_utc':raw.target_time_utc,
                            'predicted_co2':raw.predicted_target_co2_gco2eq_kwh,
                            'actual_renewable':raw.actual_target_renewable_share_pct})
        for source in RENEWABLE_SOURCES:
            piece['predicted_'+source]=raw[f'predicted_target_{source}_share_pct']
        clip_sources(piece)
        pieces.append(piece)
    result=pd.concat(pieces,ignore_index=True)
    # Unseen hours after the training end (2026-10-26), predicted by the final
    # main model (predict_xgb_forecast.py). The backtest (real ERA5 history,
    # not a forecast) is listed last, so drop_duplicates(keep='first') prefers
    # the genuine operational forecasts wherever they overlap (e.g. 2026-11-02).
    extra_paths=[root/'reports/forecast_price_20261102_1d_v1/predictions.csv',
                 root/'reports/forecast_price_20261105_3d_v1/predictions.csv',
                 root/'reports/backtest_price_20261027_20261104_v1/predictions.csv']
    for path in extra_paths:
        if not path.exists():
            continue
        extra=read_main_model_file(path)
        if extra.isna().any().any():
            raise ValueError('Neue Vorhersagedatei enthält fehlende Werte')
        result=pd.concat([result,extra],ignore_index=True)
    result=result.drop_duplicates('target_time_utc',keep='first')
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
        frame=read_main_model_file(LIVE_PREDICTIONS_URL)
    except (URLError, OSError, ValueError, KeyError):
        return None
    if frame.empty:
        return None
    return frame


BUNDESLAND_CO2_DEV = 'hist_gradient_boosting_bundesland_co2_v1'
BUNDESLAND_CO2_FINAL = 'final_hist_gradient_boosting_bundesland_co2_2015_2026_v1'
BUNDESLAND_RENEWABLE_DEV = 'hist_gradient_boosting_bundesland_renewable_share_v1'
BUNDESLAND_RENEWABLE_FINAL = 'final_hist_gradient_boosting_bundesland_renewable_share_2015_2026_v1'


def bundesland_co2_path(root: Path, year: int) -> Path:
    folder = BUNDESLAND_CO2_DEV if year <= 2024 else BUNDESLAND_CO2_FINAL
    return root/'reports'/folder/f'predictions_{year}.csv'


def bundesland_renewable_path(root: Path, year: int) -> Path:
    folder = BUNDESLAND_RENEWABLE_DEV if year <= 2024 else BUNDESLAND_RENEWABLE_FINAL
    return root/'reports'/folder/f'predictions_{year}.csv'


def load_bundesland_history(root: Path) -> pd.DataFrame:
    # Pooled model (one model per target, "bundesland" as an input feature),
    # same dev-fold/final-model split and test years as every other model
    # here - see train_bundesland_stage0.py / splits.json.
    pieces=[]
    for year in range(2018,2027):
        co2=pd.read_csv(bundesland_co2_path(root,year),
                         usecols=['target_time_utc','bundesland','actual','hist_gradient_boosting_bundesland_co2'])
        co2=co2.rename(columns={'actual':'actual_co2','hist_gradient_boosting_bundesland_co2':'predicted_co2'})
        renewable=pd.read_csv(bundesland_renewable_path(root,year),
                               usecols=['target_time_utc','bundesland','actual','hist_gradient_boosting_bundesland_renewable_share'])
        renewable=renewable.rename(columns={'actual':'actual_renewable',
                                             'hist_gradient_boosting_bundesland_renewable_share':'predicted_renewable'})
        piece=co2.merge(renewable,on=['target_time_utc','bundesland'],validate='one_to_one')
        pieces.append(piece)
    result=pd.concat(pieces,ignore_index=True)
    # Backtest: real ERA5 history (not a forecast), fills the gap between the
    # historical build (ends 2026-10-26) and when the live pipeline started
    # (2026-11-10) - see predict_bundesland_backtest.py.
    backtest_path=root/'reports/backtest_bundesland_20261027_20261104_v1/predictions.csv'
    if backtest_path.exists():
        backtest=pd.read_csv(backtest_path,usecols=['target_time_utc','bundesland','actual_co2_gco2eq_kwh',
                                                      'actual_renewable_share_pct','predicted_co2_gco2eq_kwh',
                                                      'predicted_renewable_share_pct'])
        backtest=backtest.rename(columns={'actual_co2_gco2eq_kwh':'actual_co2','actual_renewable_share_pct':'actual_renewable',
                                           'predicted_co2_gco2eq_kwh':'predicted_co2','predicted_renewable_share_pct':'predicted_renewable'})
        backtest=backtest.dropna(subset=['actual_co2','actual_renewable'])
        result=pd.concat([result,backtest],ignore_index=True)
    result['time_utc']=pd.to_datetime(result.pop('target_time_utc'),utc=True)
    result=result.sort_values(['bundesland','time_utc']).drop_duplicates(['bundesland','time_utc'],keep='last').reset_index(drop=True)
    return result


def load_bundesland_predictions(root: Path) -> pd.DataFrame | None:
    # Written daily by the same GitHub Actions job as load_live_predictions(),
    # one extra column (predicted_co2_gco2eq_kwh/predicted_renewable_share_pct
    # per Bundesland). Pooled model.
    history=load_bundesland_history(root)
    try:
        live=pd.read_csv(BUNDESLAND_LIVE_URL,
                         usecols=['target_time_utc','bundesland','predicted_co2_gco2eq_kwh','predicted_renewable_share_pct'])
    except (URLError, OSError, ValueError):
        live=None
    if live is not None and not live.empty:
        live['time_utc']=pd.to_datetime(live.pop('target_time_utc'),utc=True)
        live=live.rename(columns={'predicted_co2_gco2eq_kwh':'predicted_co2',
                                   'predicted_renewable_share_pct':'predicted_renewable'})
        combined=pd.concat([history,live],ignore_index=True)
        combined=combined.sort_values(['bundesland','time_utc']).drop_duplicates(['bundesland','time_utc'],keep='last').reset_index(drop=True)
        return combined
    return history


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
