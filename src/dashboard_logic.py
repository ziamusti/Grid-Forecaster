"""Pure helpers for the historical Stage-0 Streamlit dashboard."""
from pathlib import Path
import pandas as pd


METHOD = 'hist_gradient_boosting'


def prediction_paths(root: Path, year: int, target: str) -> Path:
    folder = ('hist_gradient_boosting_v1' if year <= 2024 else
              f'hist_gradient_boosting_test{year}_v1')
    return root/'reports'/folder/f'predictions_{year}_{target}.csv'


def load_predictions(root: Path) -> pd.DataFrame:
    targets = {'target_co2_gco2eq_kwh':'co2',
               'target_renewable_share_pct':'renewable'}
    pieces=[]
    for year in range(2018,2027):
        merged=None
        for target,name in targets.items():
            path=prediction_paths(root,year,target)
            frame=pd.read_csv(path,usecols=['target_time_utc','actual',METHOD,'common_scored'])
            frame=frame.loc[frame.common_scored==1,['target_time_utc','actual',METHOD]]
            frame=frame.rename(columns={'actual':f'actual_{name}',METHOD:f'predicted_{name}'})
            merged=frame if merged is None else merged.merge(frame,on='target_time_utc',validate='one_to_one')
        pieces.append(merged)
    result=pd.concat(pieces,ignore_index=True)
    extra_path=root/'reports/hist_prediction_20260924_26_v1/predictions.csv'
    if extra_path.exists():
        extra=pd.read_csv(extra_path,usecols=['target_time_utc',
            'predicted_co2_gco2eq_kwh','predicted_renewable_share_pct'])
        extra=extra.rename(columns={'predicted_co2_gco2eq_kwh':'predicted_co2',
                                   'predicted_renewable_share_pct':'predicted_renewable'})
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
