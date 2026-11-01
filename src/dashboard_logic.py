"""Pure helpers for the historical Stage-0 Streamlit dashboard."""
from pathlib import Path
import pandas as pd


METHOD = 'hist_gradient_boosting'


def prediction_paths(root: Path, year: int, target: str, price: bool) -> Path:
    base = 'hist_gradient_boosting_price' if price else 'hist_gradient_boosting'
    folder = f'{base}_v1' if year <= 2024 else f'{base}_test{year}_v1'
    return root/'reports'/folder/f'predictions_{year}_{target}.csv'


def load_predictions(root: Path) -> pd.DataFrame:
    # CO2 comes from the price-feature model (same procedure, +Day-ahead price
    # at lag168h); renewable share stays on the original model (unchanged, no
    # price feature was added there).
    pieces=[]
    for year in range(2018,2027):
        co2=pd.read_csv(prediction_paths(root,year,'target_co2_gco2eq_kwh',price=True),
                         usecols=['target_time_utc','actual',METHOD,'common_scored'])
        co2=co2.loc[co2.common_scored==1,['target_time_utc','actual',METHOD]]
        co2=co2.rename(columns={'actual':'actual_co2',METHOD:'predicted_co2'})
        renewable=pd.read_csv(prediction_paths(root,year,'target_renewable_share_pct',price=False),
                               usecols=['target_time_utc','actual',METHOD,'common_scored'])
        renewable=renewable.loc[renewable.common_scored==1,['target_time_utc','actual',METHOD]]
        renewable=renewable.rename(columns={'actual':'actual_renewable',METHOD:'predicted_renewable'})
        pieces.append(co2.merge(renewable,on='target_time_utc',validate='one_to_one'))
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
    result['time_utc']=pd.to_datetime(result.pop('target_time_utc'),utc=True)
    result=result.sort_values('time_utc').reset_index(drop=True)
    assert result.time_utc.is_unique
    assert result[['time_utc','predicted_co2','predicted_renewable']].notna().all().all()
    return result


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
