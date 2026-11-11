"""Carbon-aware scheduler (demonstrator): best start time for a flexible job; no training.

Given a job duration and a deadline, the scheduler reads the current forecast
of the Grid Forecaster (the same live files the dashboard shows: national main
model or one Bundesland) and picks the start hour whose job hours have the
lowest mean predicted CO2 intensity. The interface follows the idea of
bluehands Carbon-Aware-Computing `CalculateBestExecutionTime(location,
earliest start, finished by, duration)`.

For comparison it also reports the predicted CO2 for starting immediately and
the mean over all allowed start hours (= expected value of a random start).
Every decision is appended to a log, so it can later be checked against the
actual SMARD values. With --ausfuehren the scheduler waits until the chosen
start and then runs the given command (the computer has to stay on).

Example:
  python carbon_scheduler.py --dauer 2 --fertig-bis "2026-11-13 18:00"
  python carbon_scheduler.py --dauer 2 --bundesland Bayern --ausfuehren "rsync -a ~/Dokumente /Volumes/Backup"
"""
import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dashboard_logic import (BUNDESLAND_LIVE_URL, LIVE_PREDICTIONS_URL, read_bundesland_model_file,  # noqa: E402
                             read_main_model_file)
from scheduler_logic import best_execution_time, saving_percent  # noqa: E402

UTC = timezone.utc
BERLIN = ZoneInfo('Europe/Berlin')
LOG = ROOT / 'reports/scheduler/entscheidungen.csv'
LOG_FIELDS = ['entschieden_utc', 'ort', 'dauer_h', 'fruehester_start_utc', 'fertig_bis_utc', 'bester_start_utc',
              'erwartet_co2', 'erwartet_gruen', 'sofort_co2', 'zufall_co2', 'moegliche_starts', 'vorhersage_bis_utc',
              'quelle', 'ausgefuehrt', 'befehl', 'rueckgabecode']


def load_forecast(bundesland=None, path=None):
    """Hourly forecast with columns time_utc, predicted_co2, predicted_renewable."""
    if bundesland:
        frame = read_bundesland_model_file(path or BUNDESLAND_LIVE_URL)
        if bundesland not in set(frame.bundesland):
            raise SystemExit(f'Unbekanntes Bundesland: {bundesland}. Moeglich: {", ".join(sorted(set(frame.bundesland)))}')
        frame = frame[frame.bundesland == bundesland]
    else:
        frame = read_main_model_file(path or LIVE_PREDICTIONS_URL)
        frame['time_utc'] = pd.to_datetime(frame.pop('target_time_utc'), utc=True)
    frame = frame[['time_utc', 'predicted_co2', 'predicted_renewable']].dropna()
    return frame.drop_duplicates('time_utc', keep='last').sort_values('time_utc').set_index('time_utc')


def local(t):
    return pd.Timestamp(t).tz_convert(BERLIN).strftime('%d.%m. %H:%M')


def parse_local(text):
    return pd.Timestamp(datetime.strptime(text, '%Y-%m-%d %H:%M').replace(tzinfo=BERLIN)).tz_convert(UTC)


def write_log(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dauer', type=int, required=True, help='Jobdauer in ganzen Stunden')
    parser.add_argument('--fertig-bis', help='Spaetestes Ende, deutsche Zeit "JJJJ-MM-TT HH:MM" (Standard: in 24 Stunden)')
    parser.add_argument('--fruehester-start', help='Fruehester Start, deutsche Zeit (Standard: jetzt)')
    parser.add_argument('--bundesland', help='z. B. Bayern; ohne Angabe Deutschland gesamt')
    parser.add_argument('--vorhersage', type=Path, help='eigene predictions.csv statt der Live-Vorhersage')
    parser.add_argument('--ausfuehren', help='Befehl, der zur besten Zeit gestartet wird')
    parser.add_argument('--log', type=Path, default=LOG, help=f'Entscheidungsliste (Standard: {LOG.relative_to(ROOT)})')
    args = parser.parse_args()
    if args.dauer < 1:
        raise SystemExit('Die Jobdauer muss mindestens 1 Stunde sein.')

    now = pd.Timestamp.now(tz=UTC)
    earliest = parse_local(args.fruehester_start) if args.fruehester_start else now
    finished_by = parse_local(args.fertig_bis) if args.fertig_bis else earliest + pd.Timedelta(hours=24)
    if finished_by - earliest < pd.Timedelta(hours=args.dauer):
        raise SystemExit('Zwischen fruehestem Start und Frist ist weniger Zeit als die Jobdauer.')

    place = args.bundesland or 'Deutschland'
    forecast = load_forecast(args.bundesland, args.vorhersage)
    horizon = forecast.index.max() + pd.Timedelta(hours=1)
    result = best_execution_time(forecast, earliest, finished_by, args.dauer)
    print(f'Job: {args.dauer} Stunde(n), {place}, frühestens {local(earliest)}, fertig bis {local(finished_by)} (deutsche Zeit)')
    if result is None:
        raise SystemExit(f'Keine Vorhersage für diesen Zeitraum (Vorhersage reicht bis {local(horizon)}).')
    if finished_by > horizon:
        print(f'Hinweis: Die Vorhersage reicht nur bis {local(horizon)}; spätere Startzeiten wurden nicht geprüft.')

    immediate = result['immediate']
    saving_now = saving_percent(result['co2'], immediate['co2'])
    saving_random = saving_percent(result['co2'], result['random_co2'])
    print(f'Bester Start:      {local(result["start"])} bis {local(result["end"])}  '
          f'({result["start"]:%H:%M} UTC)')
    print(f'Erwartet:          {result["co2"]:.0f} gCO₂/kWh · {result["renewable"]:.0f} % grün')
    print(f'Sofort starten:    {immediate["co2"]:.0f} gCO₂/kWh ab {local(immediate["start"])} '
          f'→ bester Start spart laut Vorhersage {saving_now:.0f} %')
    print(f'Zufällig starten:  {result["random_co2"]:.0f} gCO₂/kWh im Mittel über {result["starts"]} mögliche Starts '
          f'→ bester Start spart laut Vorhersage {saving_random:.0f} %')

    row = dict(entschieden_utc=now.isoformat(), ort=place, dauer_h=args.dauer, fruehester_start_utc=earliest.isoformat(),
               fertig_bis_utc=finished_by.isoformat(), bester_start_utc=result['start'].isoformat(),
               erwartet_co2=round(result['co2'], 1), erwartet_gruen=round(result['renewable'], 1),
               sofort_co2=round(immediate['co2'], 1), zufall_co2=round(result['random_co2'], 1),
               moegliche_starts=result['starts'], vorhersage_bis_utc=horizon.isoformat(),
               quelle=str(args.vorhersage) if args.vorhersage else 'live (grid-forecaster-data)',
               ausgefuehrt=False, befehl=args.ausfuehren or '', rueckgabecode='')
    if args.ausfuehren:
        wait = (result['start'] - pd.Timestamp.now(tz=UTC)).total_seconds()
        if wait > 0:
            print(f'Warte {wait / 3600:.1f} Stunden bis {local(result["start"])} ...', flush=True)
            time.sleep(wait)
        print(f'Starte: {args.ausfuehren}', flush=True)
        completed = subprocess.run(args.ausfuehren, shell=True)
        row.update(ausgefuehrt=True, rueckgabecode=completed.returncode)
        print(f'Fertig, Rückgabecode {completed.returncode}')
    write_log(args.log, row)
    print(f'Entscheidung gespeichert: {args.log}')


if __name__ == '__main__':
    main()
