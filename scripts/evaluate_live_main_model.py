"""Evaluate the live forecasts of the national main model against SMARD; no training.

For the planned live evaluation (thesis section 5.7.3), default period
12.11.2026-11.12.2026 UTC (30 days). Only genuine forecasts count: the weather
forecast must have been retrieved before the forecast day starts. In the set-up
phase this does not hold for every day (27.10.-04.11. ERA5 backtest; 05.11. and
08.11. weather retrieved during the day; 10.11. and 11.11. recomputed during or
after the day); genuine days there are only 06., 07. and 09.11.2026. From 12.11.
on the nightly GitHub Actions run forecasts the following days. The live
history keeps the newest value per hour, so a manual run during a day would
replace that day with a non-genuine forecast: check the data-repo commit times
for the period before using the result.

- Predictions: exactly what the dashboard shows (dashboard_logic.load_predictions:
  saved forecast folders + cumulative live history from grid-forecaster-data).
- Truth: fresh SMARD download (12 technologies), CO2 with the same UBA factors
  as the model target (compute_self_co2_target.FACTORS), renewable share =
  six renewable sources / total generation. Same definition as the model.
- Electricity Maps (optional, needs ELECTRICITY_MAPS_API_KEY in .env): only as
  plausibility check (lifecycle CO2, own renewable definition).
- Metrics: MAE, mean deviation (model - truth), R2 per target; Ampel hit rate
  (dashboard thresholds 40/60 % renewable); best 3-hour window per UTC day
  (dashboard rule, lowest predicted mean CO2): hit = same start hour as the
  true best window, plus the extra CO2 of the chosen window versus the true best.
Writes reports/live_evaluation_<start>_<end>/ and never overwrites.
"""
import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from compute_self_co2_target import FACTORS, _number
from prepare_stage0 import TECH, local_to_utc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dashboard_logic import add_scores, best_window, category, load_predictions, read_main_model_file  # noqa: E402

UTC = timezone.utc
SMARD_URL = 'https://www.smard.de/nip-download-manager/nip/download/market-data'
SMARD_MODULES = [1004066, 1001226, 1001225, 1004067, 1004068, 1001228,
                 1001224, 1001223, 1004069, 1004071, 1004070, 1001227]
RENEWABLE = ['biomass', 'hydro', 'wind_offshore', 'wind_onshore', 'solar', 'other_renewables']
# Expanding-window test 2018-2026, separate models (thesis Tabelle 5.9 / 5.6.3).
TEST = dict(mae_co2=40.97, mae_renewable=3.98, bias_co2=12.9)
WINDOW_HOURS = 3  # dashboard default job duration


def fetch_smard(start, end, out):
    payload = {'request_form': [dict(moduleIds=SMARD_MODULES, region='DE', resolution='hour', format='CSV',
                                     timestamp_from=int(start.timestamp() * 1000), timestamp_to=int(end.timestamp() * 1000),
                                     type='discrete', language='de')]}
    request = Request(SMARD_URL, data=json.dumps(payload).encode(), method='POST',
                      headers={'Content-Type': 'application/json', 'User-Agent': 'Grid-Forecaster/1.0'})
    with urlopen(request, timeout=300) as response:
        body = response.read()
    (out / 'smard_generation.csv').write_bytes(body)
    reader = csv.DictReader(io.StringIO(body.decode('utf-8-sig')), delimiter=';')
    mapping = {name: next(k for k in reader.fieldnames if k.startswith(name + ' [MWh]')) for name in TECH}
    seen, rows = defaultdict(int), []
    for raw in reader:
        t = local_to_utc(raw['Datum von'], seen)
        if not start <= t < end:
            continue
        gen = {TECH[name]: _number(raw[col]) for name, col in mapping.items()}
        if gen['nuclear'] is None:  # no nuclear since 16.04.2023, SMARD shows '-'
            gen['nuclear'] = 0.0
        total = None if any(v is None for v in gen.values()) else sum(gen.values())
        ok = total is not None and total > 0
        rows.append(dict(time_utc=t,
                         actual_co2=sum(gen[k] * FACTORS[k] for k in gen) / total if ok else np.nan,
                         actual_renewable=100 * sum(gen[k] for k in RENEWABLE) / total if ok else np.nan))
    return pd.DataFrame(rows)


def fetch_electricitymaps(start, end, out):
    env = {}
    for line in (ROOT / '.env').read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep:
            env[key.strip()] = value.strip().strip('"\'')
    token = env.get('ELECTRICITY_MAPS_API_KEY', '')
    if not token:
        return None
    fmt = lambda dt: dt.isoformat().replace('+00:00', 'Z')
    rows = {}
    cursor = start
    while cursor < end:
        stop = min(cursor + timedelta(days=10), end)
        for name, extra in [('carbon-intensity', dict(emissionFactorType='lifecycle')), ('power-breakdown', {})]:
            params = dict(zone='DE', temporalGranularity='hourly', flowTraced='false', start=fmt(cursor), end=fmt(stop), **extra)
            url = f'https://api.electricitymaps.com/v4/{name}/past-range?' + urlencode(params)
            try:
                with urlopen(Request(url, headers={'auth-token': token}), timeout=60) as response:
                    body = response.read().replace(token.encode(), b'[REDACTED]')
            except (HTTPError, URLError) as error:
                print('Electricity Maps nicht verfuegbar:', error, flush=True)
                return None
            (out / f'em_{name}_{cursor:%Y%m%d}.json').write_bytes(body)
            for r in json.loads(body)['data']:
                row = rows.setdefault(pd.Timestamp(r['datetime']), {})
                if name == 'carbon-intensity':
                    row.update(em_co2=r['carbonIntensity'], em_estimated=bool(r.get('isEstimated')))
                else:
                    row['em_renewable'] = r.get('renewablePercentage')
        cursor = stop
    frame = pd.DataFrame.from_dict(rows, orient='index').rename_axis('time_utc').reset_index()
    return frame


def scores(pred, true):
    err = pred - true
    return dict(mae=float(err.abs().mean()), bias=float(err.mean()),
                r2=float(1 - (err ** 2).sum() / ((true - true.mean()) ** 2).sum()))


def window_check(data):
    rows = []
    for day, g in data.groupby(data.time_utc.dt.date):
        if len(g) != 24:
            continue
        g = g.sort_values('time_utc').reset_index(drop=True)
        chosen = best_window(add_scores(g), WINDOW_HOURS)
        truth = g.actual_co2.rolling(WINDOW_HOURS).mean()
        true_end = int(truth.idxmin())
        true_start = g.time_utc.iloc[true_end - WINDOW_HOURS + 1]
        chosen_rows = g[(g.time_utc >= chosen['start']) & (g.time_utc < chosen['end_exclusive'])]
        rows.append(dict(day=str(day), chosen_start=chosen['start'].strftime('%H:%M'), true_start=true_start.strftime('%H:%M'),
                         hit=bool(chosen['start'] == true_start),
                         extra_co2=float(chosen_rows.actual_co2.mean() - truth.min())))
    return pd.DataFrame(rows)


def plot_days(data, path, title):
    data = data.assign(day=data.time_utc.dt.strftime('%d.%m.'))
    days = data.groupby('day', sort=False).apply(lambda g: pd.Series(dict(
        n=len(g), bias_co2=(g.predicted_co2 - g.actual_co2).mean(), mae_co2=(g.predicted_co2 - g.actual_co2).abs().mean(),
        bias_ren=(g.predicted_renewable - g.actual_renewable).mean(),
        mae_ren=(g.predicted_renewable - g.actual_renewable).abs().mean())))
    fig, axes = plt.subplots(2, 1, figsize=(14, 8.5), sharex=True)
    x = np.arange(len(days))
    for ax, (b, m, test, unit, name) in zip(axes, [
            ('bias_co2', 'mae_co2', TEST['mae_co2'], 'gCO₂/kWh', 'CO₂-Intensität'),
            ('bias_ren', 'mae_ren', TEST['mae_renewable'], 'Prozentpunkte', 'Grünanteil')]):
        ax.bar(x - 0.2, days[b], 0.4, color='#16846a', label='Mittlere Abweichung (Mein Modell − SMARD)')
        ax.bar(x + 0.2, days[m], 0.4, color='#e0a03a', label='MAE')
        ax.axhline(test, color='#c0392b', ls='--', lw=1.2, label=f'MAE im Test 2018–2026 ({test:.2f})'.replace('.', ','))
        ax.axhline(0, color='#444', lw=0.8)
        total = (data.predicted_co2 - data.actual_co2) if b == 'bias_co2' else (data.predicted_renewable - data.actual_renewable)
        ax.set_title(f'{name} – gesamt: MAE {total.abs().mean():.1f}, Mittel {total.mean():+.1f}'.replace('.', ','),
                     loc='left', fontweight='bold')
        ax.set_ylabel(unit); ax.grid(axis='y', alpha=0.3); ax.spines[['top', 'right']].set_visible(False)
        ax.legend(loc='upper left', fontsize=8, frameon=False, ncol=3)
        ax.set_ylim(min(0, days[b].min()) * 1.3, max(days[m].max(), test) * 1.35)
    axes[1].set_xticks(x, [f'{d}\n({int(n)})' if n < 24 else d for d, n in zip(days.index, days.n)], fontsize=8)
    fig.suptitle(title, fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-11-12', help='UTC start day')
    parser.add_argument('--end', default='2026-12-11', help='UTC end day inclusive')
    parser.add_argument('--out', type=Path, default=None, help='output folder (default reports/live_evaluation_<start>_<end>)')
    parser.add_argument('--predictions', type=Path, default=None,
                        help='predictions.csv to evaluate instead of the dashboard values (e.g. a backtest)')
    parser.add_argument('--label', default='Live', help='name of the evaluated predictions in table and figure')
    args = parser.parse_args()
    start = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=UTC)
    end = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=UTC) + timedelta(days=1)
    out = args.out or ROOT / f'reports/live_evaluation_{start:%Y%m%d}_{end - timedelta(days=1):%Y%m%d}'
    if out.exists():
        raise FileExistsError(f'{out} existiert bereits; kein Ueberschreiben.')
    out.mkdir(parents=True)

    if args.predictions:
        predictions = read_main_model_file(args.predictions)
        predictions['time_utc'] = pd.to_datetime(predictions.pop('target_time_utc'), utc=True)
    else:
        predictions = load_predictions(ROOT)
    predictions = predictions[(predictions.time_utc >= start) & (predictions.time_utc < end)]
    # Truth comes only from the fresh SMARD download below.
    predictions = predictions.drop(columns=[c for c in predictions if c.startswith('actual_')])
    actual = fetch_smard(start, end, out)
    data = predictions.merge(actual, on='time_utc', how='inner')
    expected = int((end - start).total_seconds() // 3600)
    missing_prediction = expected - len(predictions)
    data = data.dropna(subset=['actual_co2', 'actual_renewable'])
    if data.empty:
        raise SystemExit('Keine Stunden mit Vorhersage und SMARD-Wert.')

    em = fetch_electricitymaps(start, end, out)
    if em is not None:
        data = data.merge(em, on='time_utc', how='left')
    data['ampel_predicted'] = data.predicted_renewable.map(lambda v: category(v)[0])
    data['ampel_actual'] = data.actual_renewable.map(lambda v: category(v)[0])
    data.to_csv(out / 'hourly.csv', index=False)

    windows = window_check(data)
    windows.to_csv(out / 'best_window_per_day.csv', index=False)
    result = dict(
        label=args.label, predictions_file=str(args.predictions) if args.predictions else 'dashboard',
        period_utc=[start.isoformat(), end.isoformat()], hours_expected=expected, hours_with_prediction=len(predictions),
        missing_prediction_hours=missing_prediction, hours_evaluated=len(data),
        last_hour_with_smard=data.time_utc.max().isoformat(),
        co2=scores(data.predicted_co2, data.actual_co2),
        renewable=scores(data.predicted_renewable, data.actual_renewable),
        test_reference=TEST,
        ampel=dict(hit_rate=float((data.ampel_predicted == data.ampel_actual).mean()),
                   confusion=pd.crosstab(data.ampel_actual, data.ampel_predicted).to_dict()),
        best_window=dict(hours=WINDOW_HOURS, days=len(windows),
                         hit_rate=float(windows.hit.mean()) if len(windows) else None,
                         mean_extra_co2=float(windows.extra_co2.mean()) if len(windows) else None),
        truth='SMARD generation, UBA factors (same as model target), fresh download; recent days may still be revised',
    )
    if em is not None and 'em_co2' in data:
        both = data.dropna(subset=['em_co2', 'em_renewable'])
        result['electricitymaps'] = dict(
            hours=len(both), estimated_hours=int(both.em_estimated.fillna(False).sum()),
            em_minus_smard_co2=float((both.em_co2 - both.actual_co2).mean()),
            em_minus_smard_renewable=float((both.em_renewable - both.actual_renewable).mean()),
            model_vs_em_corr_co2=float(np.corrcoef(both.predicted_co2, both.em_co2)[0, 1]),
            note='lifecycle CO2 and own renewable definition: plausibility check only')
    (out / 'metrics.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    table = pd.DataFrame([
        ['MAE CO₂ (gCO₂/kWh)', TEST['mae_co2'], result['co2']['mae']],
        ['Mittlere Abweichung CO₂ (gCO₂/kWh)', TEST['bias_co2'], result['co2']['bias']],
        ['MAE Grünanteil (Prozentpunkte)', TEST['mae_renewable'], result['renewable']['mae']],
        ['Mittlere Abweichung Grünanteil (Prozentpunkte)', None, result['renewable']['bias']],
        ['R² CO₂', 0.850, result['co2']['r2']],
        ['R² Grünanteil', 0.917, result['renewable']['r2']],
        ['Ampel richtig (%)', None, 100 * result['ampel']['hit_rate']],
        [f'Bestes {WINDOW_HOURS}-h-Fenster getroffen (%)', None,
         None if result['best_window']['hit_rate'] is None else 100 * result['best_window']['hit_rate']],
        ['Mehr-CO₂ im gewählten Fenster (gCO₂/kWh)', None, result['best_window']['mean_extra_co2']],
    ], columns=['Kennzahl', 'Test 2018–2026', f'{args.label} ({len(data)} Std.)'])
    table.round(3).to_csv(out / 'tabelle_live_vs_test.csv', index=False)

    plot_days(data, out / 'fehler_pro_tag.png',
              f'{args.label}: Hauptmodell {start:%d.%m.} bis {data.time_utc.max():%d.%m.%Y %H:%M} UTC '
              f'({len(data)} Stunden), Maßstab SMARD')
    print(table.round(2).to_string(index=False))
    print(json.dumps({k: result[k] for k in ['hours_expected', 'hours_evaluated', 'missing_prediction_hours', 'last_hour_with_smard']}))
    print(out)


if __name__ == '__main__':
    main()
