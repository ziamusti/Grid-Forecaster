# SMARD-Datenqualitätsbericht

## Umfang

- Untersuchungszeitraum: 2015-01-01 bis 2025-12-31
- Zusammengeführte Stunden: 96.432
- Erster UTC-Zeitstempel: 2014-12-31T23:00:00+00:00
- Letzter UTC-Zeitstempel: 2025-12-31T22:00:00+00:00
- Lücken in der stündlichen UTC-Zeitachse: 0
- Nur in Erzeugungsdaten vorhandene Stunden: 0
- Nur in Verbrauchsdaten vorhandene Stunden: 0
- Widersprüchliche Erzeugungs-Duplikate: 0
- Widersprüchliche Verbrauchs-Duplikate: 0

## Verwendete Rohdateien

### Erzeugung

- `Realisierte_Erzeugung_201501010000_201601020000_Stunde.csv`
- `Realisierte_Erzeugung_201601010000_201701010000_Stunde.csv`
- `Realisierte_Erzeugung_201701010000_201801020000_Stunde.csv`
- `Realisierte_Erzeugung_201801010000_201901010000_Stunde.csv`
- `Realisierte_Erzeugung_201901010000_202001020000_Stunde.csv`
- `Realisierte_Erzeugung_202001010000_202101010000_Stunde.csv`
- `Realisierte_Erzeugung_202101010000_202201020000_Stunde.csv`
- `Realisierte_Erzeugung_202201010000_202301010000_Stunde.csv`
- `Realisierte_Erzeugung_202301010000_202401020000_Stunde.csv`
- `Realisierte_Erzeugung_202401010000_202501010000_Stunde.csv`
- `Realisierte_Erzeugung_202501010000_202601010000_Stunde.csv`

### Stromverbrauch

- `Realisierter_Stromverbrauch_201501010000_201701010000_Stunde.csv`
- `Realisierter_Stromverbrauch_201701010000_201901010000_Stunde.csv`
- `Realisierter_Stromverbrauch_201901010000_202101010000_Stunde.csv`
- `Realisierter_Stromverbrauch_202101010000_202301010000_Stunde.csv`
- `Realisierter_Stromverbrauch_202301010000_202501010000_Stunde.csv`
- `Realisierter_Stromverbrauch_202501010000_202609010000_Stunde.csv`

## Fehlende Werte

| Spalte | Fehlende Werte |
|---|---:|
| `biomass_mwh` | 0 |
| `hydro_mwh` | 0 |
| `wind_offshore_mwh` | 0 |
| `wind_onshore_mwh` | 0 |
| `solar_mwh` | 0 |
| `other_renewables_mwh` | 24 |
| `nuclear_mwh` | 0 |
| `lignite_mwh` | 0 |
| `hard_coal_mwh` | 0 |
| `natural_gas_mwh` | 0 |
| `pumped_storage_generation_mwh` | 96 |
| `other_conventional_mwh` | 0 |
| `grid_load_mwh` | 0 |
| `grid_load_including_pumped_storage_mwh` | 96 |
| `pumped_storage_consumption_mwh` | 96 |
| `residual_load_mwh` | 0 |
| `renewable_generation_mwh` | 24 |
| `total_generation_mwh` | 120 |
| `renewable_share_of_generation_pct` | 120 |

Die fehlenden Zielwerte reichen von `2016-11-08T00:00:00` bis `2018-08-23T23:00:00` (lokale Zeit).

## Zielvariable

Die Zielvariable ist die Summe aus Biomasse, Wasserkraft, Wind Offshore, Wind Onshore, Photovoltaik und sonstigen Erneuerbaren geteilt durch die gesamte Stromerzeugung.

- Kleinster berechenbarer Anteil: 10.703712 %
- Größter berechenbarer Anteil: 91.067983 %
- Stunden über 100 %: 0

Die Zielvariable beschreibt den erneuerbaren Anteil an der gesamten in Deutschland erfassten Stromerzeugung.

## Hinweise

- Lokale Zeitstempel wurden mit der Zeitzone `Europe/Berlin` in eindeutige UTC-Zeitstempel umgerechnet.
- Beide Stunden bei der Zeitumstellung im Herbst bleiben erhalten.
- Rohdateien wurden nicht verändert oder gelöscht.
- Dateien mit `Kopie` sowie das unvollständige Jahr 2026 wurden nicht verarbeitet.
