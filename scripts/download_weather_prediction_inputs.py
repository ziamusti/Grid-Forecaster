"""Download fresh ERA5 raw weather for the unseen UTC block; no training."""
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
    parser.add_argument('--target-start', default='2026-09-24', help='First prediction day, UTC (YYYY-MM-DD)')
    args = parser.parse_args()
    start = datetime.strptime(args.target_start, '%Y-%m-%d')
    end = start + timedelta(days=3)
    last = end - timedelta(days=1)
    OUT = ROOT / f'data/raw/weather_prediction_{start:%Y%m%d}_{last:%Y%m%d}_era5'
    # Read coordinate configuration only, never old weather observations.
    tree = ast.parse((ROOT / 'archive/legacy_2026-10-20/src/download_weather_2026.py').read_text())
    locations = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'LOCATIONS' for t in n.targets))
    metadata = json.loads((ROOT / 'data/processed/stage0_v2_sunshine/weather_metadata.json').read_text())
    assert len(locations) == 23
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else dict(
        start_utc=start.strftime('%Y-%m-%dT00:00:00Z'), end_exclusive_utc=end.strftime('%Y-%m-%dT00:00:00Z'),
        source='Open-Meteo Archive API', model='era5', retrospective=True, complete=False, stations={})
    assert manifest['start_utc'] == start.strftime('%Y-%m-%dT00:00:00Z')
    assert manifest['end_exclusive_utc'] == end.strftime('%Y-%m-%dT00:00:00Z')
    expected = [(start + timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(72)]
    for station, (lat, lon, sea) in sorted(locations.items()):
        params = dict(latitude=lat, longitude=lon, start_date=start.strftime('%Y-%m-%d'), end_date=last.strftime('%Y-%m-%d'),
                      hourly=','.join(VARIABLES), models='era5', timezone='GMT', wind_speed_unit='ms',
                      cell_selection='sea' if sea else 'land')
        url = 'https://archive-api.open-meteo.com/v1/archive?' + urlencode(params)
        path = OUT / (station + '.json')
        if not path.exists():
            for attempt in range(5):
                try:
                    with urlopen(url, timeout=60) as response:
                        body = response.read()
                    data = json.loads(body)
                    if data.get('error'):
                        raise ValueError(data.get('reason'))
                    path.write_bytes(body)
                    break
                except (HTTPError, URLError, TimeoutError):
                    if attempt == 4:
                        raise
                    time.sleep(min(2 ** (attempt+1), 20))
        body = path.read_bytes()
        data = json.loads(body)
        assert data['utc_offset_seconds'] == 0
        assert data['hourly']['time'] == expected, station
        for field, unit in VARIABLES.items():
            assert data['hourly_units'][field] == unit, (station, field)
            values = data['hourly'][field]
            assert len(values) == 72 and all(v is not None and math.isfinite(v) for v in values), (station, field)
        assert all(0 <= v <= 3600 for v in data['hourly']['sunshine_duration'])
        assert all(0 <= v <= 100 for v in data['hourly']['cloud_cover'])
        assert abs(data['latitude']-float(metadata[station]['latitude'])) < .001
        assert abs(data['longitude']-float(metadata[station]['longitude'])) < .001
        manifest['stations'][station] = dict(file=path.name, url=url, hours=72,
            sha256=hashlib.sha256(body).hexdigest(), checked_at_utc=datetime.now(timezone.utc).isoformat(),
            latitude=data['latitude'], longitude=data['longitude'])
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        print(station, '72 Stunden, 5 Variablen geprüft', flush=True)
        time.sleep(.3)
    manifest['complete'] = len(manifest['stations']) == 23
    manifest['values_checked'] = 23 * 72 * 5
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print('COMPLETE:', OUT, flush=True)


if __name__ == '__main__':
    main()
