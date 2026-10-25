"""Read-only paginated MaStR list download; never fits models or sums capacity."""
import argparse
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.marktstammdatenregister.de/Services/Public/1_2/Modelle'
URL = 'https://www.marktstammdatenregister.de/MaStRApi/Api.svc/Soap11/Anlage'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages-per-type', type=int, default=1)
    args = parser.parse_args()
    values = {}
    for line in (ROOT / '.env').read_text().splitlines():
        k, sep, v = line.partition('=')
        if sep:
            values[k.strip()] = v.strip().strip('\"\'')
    out = ROOT / 'data/raw/mastr_api' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(started_utc=datetime.now(timezone.utc).isoformat(), endpoint=URL,
                    complete=False, note='Lists lack net capacity and commissioning/retirement details', pages=[])
    for technology in ('Wind', 'SolareStrahlungsenergie'):
        start = 1
        for page in range(args.pages_per_type):
            envelope = ET.Element('{http://schemas.xmlsoap.org/soap/envelope/}Envelope')
            body = ET.SubElement(envelope, '{http://schemas.xmlsoap.org/soap/envelope/}Body')
            op = ET.SubElement(body, '{'+BASE+'/Anlage}GetGefilterteListeStromErzeugerRequest')
            for key, val in [('apiKey', values['MASTR_API_KEY']),
                             ('marktakteurMastrNummer', values['MASTR_MARKTAKTEUR_NUMMER']),
                             ('startAb', str(start)), ('limit', '200'), ('energietraeger', technology)]:
                ET.SubElement(op, '{'+BASE+'}'+key).text = val
            request = Request(URL, data=ET.tostring(envelope), headers={
                'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': 'GetGefilterteListeStromErzeuger'})
            try:
                with urlopen(request, timeout=90) as response:
                    data = response.read()
            except HTTPError as exc:
                error = ET.fromstring(exc.read())
                message = next((e.text for e in error.iter() if e.tag.endswith('faultstring')), 'HTTP error')
                raise SystemExit(str(exc.code) + ': ' + message.replace(values['MASTR_API_KEY'], '[REDACTED]'))
            assert values['MASTR_API_KEY'].encode() not in data
            path = out / f'{technology}_{start:09d}.xml'
            path.write_bytes(data)
            root = ET.fromstring(data)
            entries = [e for e in root.iter() if e.tag.split('}')[-1] == 'Einheiten']
            code = next(e.text for e in root.iter() if e.tag.split('}')[-1] == 'Ergebniscode')
            manifest['pages'].append(dict(file=path.name, technology=technology, start=start,
                rows=len(entries), result=code, sha256=hashlib.sha256(data).hexdigest()))
            (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            print(technology, start, len(entries), code, flush=True)
            if code == 'OK' or code == 'Ok':
                break
            if code != 'OkWeitereDatenVorhanden' or not entries:
                raise SystemExit('Unexpected response; raw data retained')
            start += len(entries)
            time.sleep(0.3)
    print('Raw output:', out, flush=True)


if __name__ == '__main__':
    main()
