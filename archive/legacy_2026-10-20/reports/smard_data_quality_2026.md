# SMARD-Datenqualitätsbericht

## Umfang

- Untersuchungszeitraum: 2026-01-01 bis 2026-12-31
- Zusammengeführte Stunden: 6.983
- Erster UTC-Zeitstempel: 2025-12-31T23:00:00+00:00
- Letzter UTC-Zeitstempel: 2026-10-18T21:00:00+00:00
- Lücken in der stündlichen UTC-Zeitachse: 0
- Nur in Erzeugungsdaten vorhandene Stunden: 0
- Nur in Verbrauchsdaten vorhandene Stunden: 0
- Widersprüchliche Erzeugungs-Duplikate: 0
- Widersprüchliche Verbrauchs-Duplikate: 0

## Verwendete Rohdateien

### Erzeugung

- `Realisierte_Erzeugung_2026_latest.csv`

### Stromverbrauch

- `Realisierter_Stromverbrauch_2026_latest.csv`

## Fehlende Werte

| Spalte | Fehlende Werte |
|---|---:|
| `biomass_mwh` | 48 |
| `hydro_mwh` | 1 |
| `wind_offshore_mwh` | 1 |
| `wind_onshore_mwh` | 1 |
| `solar_mwh` | 1 |
| `other_renewables_mwh` | 1 |
| `nuclear_mwh` | 0 |
| `lignite_mwh` | 1 |
| `hard_coal_mwh` | 1 |
| `natural_gas_mwh` | 1 |
| `pumped_storage_generation_mwh` | 1 |
| `other_conventional_mwh` | 1 |
| `grid_load_mwh` | 1 |
| `grid_load_including_pumped_storage_mwh` | 1 |
| `pumped_storage_consumption_mwh` | 1 |
| `residual_load_mwh` | 1 |
| `renewable_generation_mwh` | 48 |
| `total_generation_mwh` | 48 |
| `renewable_share_of_generation_pct` | 48 |

Die fehlenden Zielwerte reichen von `2026-10-17T00:00:00` bis `2026-10-18T23:00:00` (lokale Zeit).

## Zielvariable

Die Zielvariable ist die Summe aus Biomasse, Wasserkraft, Wind Offshore, Wind Onshore, Photovoltaik und sonstigen Erneuerbaren geteilt durch die gesamte Stromerzeugung.

- Kleinster berechenbarer Anteil: 15.775511 %
- Größter berechenbarer Anteil: 93.547104 %
- Stunden über 100 %: 0

Die Zielvariable beschreibt den erneuerbaren Anteil an der gesamten in Deutschland erfassten Stromerzeugung.

## Hinweise

- Lokale Zeitstempel wurden mit der Zeitzone `Europe/Berlin` in eindeutige UTC-Zeitstempel umgerechnet.
- Beide Stunden bei der Zeitumstellung im Herbst bleiben erhalten.
- Rohdateien wurden nicht verändert oder gelöscht.
- Dateien mit `Kopie` sowie das unvollständige Jahr 2026 wurden nicht verarbeitet.
