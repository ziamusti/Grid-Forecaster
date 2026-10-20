# Neues Deutschland-Modell – Kurzüberblick

Status: geplant, noch nicht trainiert oder in die App eingebaut.

## Ziel und Änderung

Wir prognostizieren weiterhin den erneuerbaren Anteil an Deutschlands
Stromerzeugung für die nächsten 72 Stunden.

- **Bisher:** Vier Wettermittelwerte aus 21 Landstandorten und ein
  Offshore-Windmittelwert aus zwei Punkten.
- **Neu:** Wetterwerte je Region als eigene Modellspalten, ergänzt um die
  dort installierte Wind- und Solarleistung. Regionen und Wetterpunkte werden
  vor der Datenaufbereitung festgelegt; die vier Regelzonen sind eine Option.
- **Unverändert:** XGBoost, Stromwerte von 168 Stunden vorher,
  Kalendermerkmale und der deutschlandweite Grünanteil als Trainingsziel.

## Benötigte Daten

| Daten | Zweck | Quelle / Stand |
|---|---|---|
| Stündliche Temperatur, Wind, Sonnenstrahlung und Bewölkung je Standort | Regionale Wettersituation abbilden | Open-Meteo; grundsätzlich vorhanden, Abdeckung prüfen |
| Anlagenstandort, Wind-/Solarleistung, Inbetriebnahme, Stilllegung und Status | Regionalen Anlagenbestand abbilden | MaStR; zusätzlich beschaffen |
| Stündliche Erzeugung Deutschlands je Energieträger | Echten Grünanteil als Trainingsziel berechnen | SMARD; grundsätzlich vorhanden |
| Vergangene Erzeugung und Netzlast | Strommerkmale von 168 Stunden vorher bilden | SMARD |
| Stunde, Wochentag, Monat, Feiertage und Tageslichtdauer | Zeitliche Muster abbilden | Selbst berechnen |
| Archivierte Wetterprognosen mit Ausgabezeitpunkt | Training und Tests an reale Vorhersagebedingungen annähern | Verfügbarkeit und Zeitraum prüfen |

## Vorgehen

1. Im MaStR den aktuellen Gesamtdatenexport und die Exportbeschreibung
   herunterladen. Wind- und Solareinheiten daraus auslesen.
2. Anlagen und Wetterpunkte Regionen zuordnen. Historische Anlagenbestände
   möglichst aus Inbetriebnahme und Stilllegung rekonstruieren. Der aktuelle
   Export ist keine vollständige Historie; Lücken und Leistungsänderungen prüfen.
3. Pro Stunde eine Trainingszeile erstellen: regionale Wetterwerte,
   zeitlich passende Anlagenleistungen, verfügbare Strom-Lags und Kalender.
   Der echte deutschlandweite Grünanteil derselben Stunde ist die Zielspalte.
4. XGBoost separat neu trainieren. Ältere Daten zum Training verwenden,
   spätere zur Modellauswahl und einen unbenutzten Zeitraum zum Abschlusstest.
   Nur Informationen verwenden, die zum jeweiligen Prognosezeitpunkt
   verfügbar waren; Veröffentlichungsverzögerungen berücksichtigen.
5. Neues und bisheriges Modell auf identischen Teststunden vergleichen:
   MAE in Prozentpunkten, RMSE und Fehler für 1–24, 25–48 und 49–72 Stunden.
6. Nur bei nachgewiesener Verbesserung das neue Modell in die App übernehmen.
   Im Betrieb dieselben Spalten mit Wetterprognosen und verfügbaren
   Anlagen-, Strom- und Kalenderdaten füllen.

## Empfehlung

Regionale Wetterdaten plus Anlagenleistung sind unser bevorzugter nächster
Versuch. Mehr Daten garantieren keine höhere Genauigkeit; entscheidend ist
der unabhängige Vergleich. Das bisherige Modell bleibt als Referenz erhalten.
