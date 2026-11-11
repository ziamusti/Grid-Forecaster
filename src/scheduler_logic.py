"""Best start time for a flexible job (carbon-aware scheduling demonstrator).

Shared by scripts/carbon_scheduler.py (terminal) and the dashboard section
"Job planen". The idea follows bluehands Carbon-Aware-Computing
`CalculateBestExecutionTime(location, earliest start, finished by, duration)`.
"""
from __future__ import annotations

import pandas as pd


def best_execution_time(forecast: pd.DataFrame, earliest, finished_by, duration_hours: int) -> dict | None:
    """Best start hour in [earliest, finished_by - duration] by lowest mean predicted CO2.

    forecast: indexed by hourly UTC time, columns predicted_co2 and predicted_renewable.
    Only start hours whose whole job lies inside the forecast count. Returns None if
    there is no such start hour. 'immediate' is the first allowed start, 'random_co2'
    the mean over all allowed starts (expected value of a random start).
    """
    first = pd.Timestamp(earliest).ceil('h')
    last = pd.Timestamp(finished_by) - pd.Timedelta(hours=duration_hours)
    candidates = []
    start = first
    while start <= last:
        hours = pd.date_range(start, periods=duration_hours, freq='h')
        if hours.isin(forecast.index).all():
            window = forecast.loc[hours]
            candidates.append(dict(start=start, co2=float(window.predicted_co2.mean()),
                                   renewable=float(window.predicted_renewable.mean())))
        start += pd.Timedelta(hours=1)
    if not candidates:
        return None
    table = pd.DataFrame(candidates)
    best = table.loc[table.co2.idxmin()]
    return dict(start=best.start, end=best.start + pd.Timedelta(hours=duration_hours), co2=float(best.co2),
                renewable=float(best.renewable), immediate=table.iloc[0].to_dict(), random_co2=float(table.co2.mean()),
                starts=len(table), candidates=table)


def saving_percent(best_co2: float, reference_co2: float) -> float:
    """Relative saving of the best start against a reference start (in %)."""
    return 100 * (1 - best_co2 / reference_co2) if reference_co2 > 0 else float('nan')
