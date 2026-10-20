"""Deutschland-Rohdaten abrufen; keine Aufbereitung und kein Training."""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    values = {}
    for line in (ROOT / '.env').read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep:
            values[key.strip()] = value.strip().strip('\"\'')
    token = values.get('ELECTRICITY_MAPS_API_KEY', '')
    if not token or token == 'YOUR_API_KEY':
        raise SystemExit('API-Schlüssel fehlt in .env.')
    run = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'data/raw/electricitymaps' / run
    # API erlaubt direkte Faktoren nicht mit flowTraced=false.
    # Deshalb deutsche Erzeugung mit Lebenszyklus-Faktoren (gCO2eq/kWh).
    common = {'zone': 'DE', 'temporalGranularity': 'hourly',
              'flowTraced': 'false', 'emissionFactorType': 'lifecycle'}
    queries = [
        ('latest', {}),
        ('history', {}),
        ('past-range', {'start': '2022-01-01T00:00:00Z',
                        'end': '2022-01-02T00:00:00Z'}),
    ]
    manifest = []
    for endpoint, extra in queries:
        url = 'https://api.electricitymaps.com/v4/carbon-intensity/' + endpoint
        url += '?' + urlencode({**common, **extra})
        request = Request(url, headers={'auth-token': token, 'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=45) as response:
                status, body = response.status, response.read()
        except HTTPError as error:
            status, body = error.code, error.read()
        except URLError:
            raise SystemExit('Netzwerkverbindung fehlgeschlagen; keine Zugangsdaten ausgegeben.')
        # Auch Fehlermeldungen speichern, aber niemals den Schlüssel.
        body = body.replace(token.encode(), b'[REDACTED]')
        output.mkdir(parents=True, exist_ok=True)
        filename = endpoint + ('.json' if status == 200 else '_error.json')
        (output / filename).write_bytes(body)
        item = {'endpoint': endpoint, 'url': url, 'http_status': status,
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(), 'file': filename}
        try:
            data = json.loads(body)
        except ValueError:
            data = {}
        if status == 200:
            rows = data.get('history', data.get('data', [data]))
            item['rows'] = len(rows)
            times = sorted(r['datetime'] for r in rows if 'datetime' in r)
            item['first'] = times[0] if times else None
            item['last'] = times[-1] if times else None
        else:
            item['message'] = data.get('error', data.get('message', 'API-Anfrage abgelehnt'))
        manifest.append(item)
        (output / 'manifest.json').write_text(json.dumps({
            'zone': 'DE', 'basis': 'production', 'emissionFactorType': 'lifecycle',
            'note': 'Raw provider responses, including estimation flags; no training data.',
            'requests': manifest,
        }, indent=2), encoding='utf-8')
        print(json.dumps(item, ensure_ascii=False))
        if status in (401, 429):
            break
    print('Rohdatenordner:', output)


if __name__ == '__main__':
    main()
