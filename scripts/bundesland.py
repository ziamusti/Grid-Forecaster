"""Weather-station-to-Bundesland mapping for the per-state model; no training.

Each of the 23 weather stations (prepare_stage0.py / archive legacy
LOCATIONS) is assigned to the German state its coordinates fall in. The two
offshore stations (nordsee_offshore, ostsee_offshore) belong to no state and
are intentionally excluded. All 16 Bundeslaender are covered by at least one
station; five have two (their values can be averaged where a single weather
input per state is needed).
"""

STATION_BUNDESLAND = {
    'kiel': 'Schleswig-Holstein',
    'hamburg': 'Hamburg',
    'rostock': 'Mecklenburg-Vorpommern',
    'schwerin': 'Mecklenburg-Vorpommern',
    'hannover': 'Niedersachsen',
    'berlin': 'Berlin',
    'muenster': 'Nordrhein-Westfalen',
    'koeln': 'Nordrhein-Westfalen',
    'leipzig': 'Sachsen',
    'dresden': 'Sachsen',
    'frankfurt': 'Hessen',
    'nuernberg': 'Bayern',
    'muenchen': 'Bayern',
    'stuttgart': 'Baden-Württemberg',
    'freiburg': 'Baden-Württemberg',
    'bremen': 'Bremen',
    'potsdam': 'Brandenburg',
    'magdeburg': 'Sachsen-Anhalt',
    'erfurt': 'Thüringen',
    'mainz': 'Rheinland-Pfalz',
    'saarbruecken': 'Saarland',
}
OFFSHORE_STATIONS = ('nordsee_offshore', 'ostsee_offshore')
BUNDESLAENDER = tuple(sorted(set(STATION_BUNDESLAND.values())))
assert len(BUNDESLAENDER) == 16

# energy-charts.info per-Bundesland id suffixes (see download_energycharts_bundesland.py)
BUNDESLAND_SUFFIX = {
    'Baden-Württemberg': 'bw', 'Bayern': 'by', 'Berlin': 'be', 'Brandenburg': 'bb',
    'Bremen': 'hb', 'Hamburg': 'hh', 'Hessen': 'he', 'Mecklenburg-Vorpommern': 'mv',
    'Niedersachsen': 'ni', 'Nordrhein-Westfalen': 'nw', 'Rheinland-Pfalz': 'rp',
    'Saarland': 'sl', 'Sachsen': 'sn', 'Sachsen-Anhalt': 'st', 'Schleswig-Holstein': 'sh',
    'Thüringen': 'th',
}
assert set(BUNDESLAND_SUFFIX) == set(BUNDESLAENDER)
