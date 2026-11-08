"""Download a real Open-Meteo weather FORECAST (not ERA5) for an unseen future UTC block.

First genuine operational-style weather input in this project: for dates in
the actual future, ERA5 (retrospective reanalysis) does not exist yet, so the
Forecast API is the only correct source, not a compromise.
"""
import ast
import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VARIABLES = {'temperature_2m': '°C', 'cloud_cover': '%', 'wind_speed_100m': 'm/s',
             'shortwave_radiation': 'W/m²', 'sunshine_duration': 's'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-start', required=True, help='First forecast day, UTC (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=3)
    args = parser.parse_args()
    start = datetime.strptime(args.target_start, '%Y-%m-%d')
    hours = args.days * 24
    now = datetime.now(timezone.utc)
    forecast_days = (start.date() - now.date()).days + args.days + 1
    assert 0 < forecast_days <= 16, forecast_days
    OUT = ROOT / f'data/raw/weather_forecast_{start:%Y%m%d}_{args.days}d'
    tree = ast.parse((ROOT / 'archive/legacy_2026-10-20/src/download_weather_2026.py').read_text())
    locations = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'LOCATIONS' for t in n.targets))
    metadata = json.loads((ROOT / 'data/live_capacity/weather_metadata.json').read_text())
    assert len(locations) == 23
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = dict(start_utc=start.strftime('%Y-%m-%dT00:00:00Z'), hours=hours,
                    source='Open-Meteo Forecast API', retrospective=False, operational=True,
                    retrieved_at_utc=now.isoformat(), forecast_days_requested=forecast_days,
                    complete=False, stations={})
    expected = [(start + timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(hours)]
    for station, (lat, lon, sea) in sorted(locations.items()):
        params = dict(latitude=lat, longitude=lon, hourly=','.join(VARIABLES), forecast_days=forecast_days,
                      timezone='GMT', wind_speed_unit='ms', cell_selection='sea' if sea else 'land')
        url = 'https://api.open-meteo.com/v1/forecast?' + urlencode(params)
        for attempt in range(5):
            try:
                with urlopen(url, timeout=60) as response:
                    body = response.read()
                data = json.loads(body)
                if data.get('error'):
                    raise ValueError(data.get('reason'))
                break
            except (HTTPError, URLError, TimeoutError):
                if attempt == 4:
                    raise
                time.sleep(min(2 ** (attempt+1), 20))
        path = OUT / (station + '.json')
        path.write_bytes(body)
        assert data['utc_offset_seconds'] == 0
        times = data['hourly']['time']
        start_idx = times.index(expected[0])
        sliced = {k: v[start_idx:start_idx+hours] for k, v in data['hourly'].items()}
        assert sliced['time'] == expected, (station, sliced['time'][:3], expected[:3])
        for field, unit in VARIABLES.items():
            assert data['hourly_units'][field] == unit, (station, field)
            values = sliced[field]
            assert len(values) == hours and all(v is not None and math.isfinite(v) for v in values), \
                (station, field, sum(v is None for v in values))
        assert all(0 <= v <= 3600 for v in sliced['sunshine_duration'])
        assert all(0 <= v <= 100 for v in sliced['cloud_cover'])
        # Forecast API resolves to a finer model grid than the ERA5 archive grid used for
        # metadata (e.g. 52.512604 vs 52.5); loose tolerance catches a wrong station only.
        assert abs(data['latitude']-float(metadata[station]['latitude'])) < .3
        assert abs(data['longitude']-float(metadata[station]['longitude'])) < .3
        manifest['stations'][station] = dict(file=path.name, url=url, hours=hours,
            sha256=hashlib.sha256(body).hexdigest(), checked_at_utc=datetime.now(timezone.utc).isoformat(),
            latitude=data['latitude'], longitude=data['longitude'],
            generationtime_ms=data.get('generationtime_ms'))
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        print(station, hours, 'Stunden, 5 Variablen geprueft (Forecast)', flush=True)
        time.sleep(.3)
    manifest['complete'] = len(manifest['stations']) == 23
    manifest['values_checked'] = 23 * hours * 5
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print('COMPLETE:', OUT, flush=True)


if __name__ == '__main__':
    main()
