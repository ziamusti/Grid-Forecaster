# Bachelorarbeit – Arbeits- und Entscheidungsprotokoll

## 26.10.2026 – Problem und Ursachenhypothesen kompakt formuliert

- **Beratung:** Beobachtetes Problem am 27.09.: CO2 in 19/24 Stunden
  unterschätzt, Bias -20,31 gCO2eq/kWh, MAE 24,61; EE-MAE 2,86
  Prozentpunkte. Keine allgemeine Gütebehauptung aus einem Tag und kein
  direkter Vergleich verschieden dimensionierter MAEs.
- **Hypothesen:** 168h-Lags bilden geänderten Kraftwerkseinsatz/Verbrauch
  möglicherweise unzureichend ab; gleicher EE-Anteil lässt verschiedene
  fossile Mischungen zu; separate Zielmodelle sichern keine Konsistenz;
  unterschiedliche Zielquellen/-definitionen können zusätzlich beitragen.
  Architekturmerkmale sind keine bewiesenen Fehlerursachen.
- **Abgrenzung:** Kein Übertragungsfehler in bisherigen Eingabeprüfungen
  gefunden. Historisches ERA5 eingesetzt: Fehler einer damals ausgegebenen
  Wetterprognose ist für diese Auswertung keine belegte Erklärung.
- **Empfehlung:** Vor Änderungen aktuelle Ist-Erzeugung mit Vorwochenmix
  an auffälligen Stunden vergleichen, anschließend gezielte Varianten auf
  unabhängigen Zeiträumen prüfen. Kein Training oder neue Diagnose ausgeführt.

## 26.10.2026 – Unterschiedliche Fehler von CO2 und Grünanteil eingeordnet

- **Prüfung:** Zielberechnung, getrennte finale HGB-Inferenz und gespeicherte
  Tagesmetriken erneut gelesen. Offizielle Electricity-Maps-Methodik und
  Emissionsfaktor-Dokumentation nachgeschlagen:
  `https://www.electricitymaps.com/data/methodology` und
  `https://app.electricitymaps.com/docs/concepts/emission-factors`.
- **Befunde:** EE ist SMARD-Anteil, CO2 separates Electricity-Maps-Lifecycle-
  Produktionsziel. Zwei getrennte Modelle erzwingen keine gemeinsame
  physikalische Konsistenz. Die absoluten MAEs 24,61 gCO2eq/kWh und
  2,86 Prozentpunkte sind wegen verschiedener Einheiten nicht direkt vergleichbar.
- **Mögliche Erklärungen, nicht kausal nachgewiesen:** Gleicher EE-Anteil
  lässt unterschiedliche fossile Zusammensetzung und damit Emissionsintensität
  zu. Zielwetter beschreibt Wind/Sonne, aber nicht vollständig den zukünftigen
  Kraftwerkseinsatz; Erzeugungs-/Lastinformationen liegen im Modell als
  Vorwochenwerte vor. Anbieterdefinitionen, Faktoren und Revisionen können
  zusätzlich Unterschiede beitragen. CO2 wird nicht aus vorhergesagtem EE
  berechnet. Früherer Median-Lagtest belegt Sensitivität, keine Fehlerursache.
- **Empfehlung:** Vor Modelländerung Istmix an Stunden mit großem CO2- und
  kleinem EE-Fehler untersuchen; Vorwochenvergleich und Fehler über weitere
  Zeiträume auswerten. Auch das ergibt zunächst Zusammenhänge, keine
  gesicherte Kausalität. Keine neue Auswertung/Modelländerung/Trainings.

## 25.10.2026 – Automatische Modellberechnung und manueller Start erklärt

- **Beratung:** Die Vorhersagen 24.–29.09.2026 wurden von den gespeicherten
  finalen HistGradientBoosting-Pipelines mittels `predict` berechnet, nicht
  von Hand festgelegt. Das Skript wurde manuell gestartet; es ordnete die
  Eingaben zu, lud die beiden Modelle und speicherte deren Ausgaben.
- Je ein Modell liefert CO2 und Grünanteil. Keine erneute Anpassung auf
  die Zieltage; historische ERA5-Eingaben machen dies zur rückblickenden
  Vorhersageprüfung. Dashboard zeigt gespeicherte Ausgaben und berechnet
  daraus Zeitfenster/Mittelwerte. Keine neuen Berechnungen oder Codeänderungen.

## 25.10.2026 – Verbrauchseingabe präzisiert

- **Beratung:** Verbrauchsseite ist als SMARD-Netzlast im Modell enthalten,
  Merkmal `grid_load_mwh_lag168h`. Je Zielstunde wird die Netzlast genau
  168 Stunden vorher verwendet. Netzlast nicht pauschal mit sämtlichem
  Endenergie-/Stromverbrauch einschließlich Eigenverbrauch gleichsetzen.
  Keine zusätzliche aktuelle oder künftige Istlast als Modelleingabe behauptet.
  Keine Daten- oder Codeänderung und kein Training ausgeführt.

## 25.10.2026 – Tatsächlich verwendete Quellen und Zeiträume geprüft

- **Ausgeführt:** Finales HGB-Trainingsmanifest, V2-Quellen-/Qualitätsberichte,
  MaStR-Monatsdatei, Merkmalsnamen und erste zulässige 2015-Zeile gelesen.
  Keine Downloads, Datenaufbereitung oder Trainings ausgeführt.
- **Ergebnis:** Gemeinsame vorbereitete Stunden 01.01.2015 00 UTC bis
  23.09.2026 23 UTC, 102.816 Zeilen. Finaler Fit laut Manifest CO2 102.311,
  EE 102.409 zulässige Zeilen. Erste zulässige Zielstunde beider Modelle
  07.01.2015 23 UTC; frühe Stunden wegen fehlender 168h-Lags ausgeschlossen.
- **Eingaben:** 115 Wettermerkmale (23 Punkte × fünf Variablen), 13
  SMARD-Lags (zwölf Erzeugungsarten und Netzlast), drei installierte
  Leistungen und fünf Kalendermerkmale, zusammen 136. Ziel CO2 aus
  Electricity Maps, Ziel EE-Anteil aus SMARD; gemeinsame Nutzung 2015–2026
  bis zur genannten Trainingsgrenze, nicht vollständiges Jahr 2026.
- **MaStR-Abgrenzung:** Quelle laut Manifest ist der Gesamtdatenexport
  `Gesamtdatenexport_20261020_26.2.zip` aus archivierten Rohdaten. Monatliche
  Reihe 01.01.2014–01.10.2026 ist rückblickend rekonstruiert und kein
  seit 2014 gespeichertes Registerarchiv. Für Trainingszeitpunkte gilt die
  bestehende Monatsreferenzregel. Historische Datenstände nicht nachgewiesen.
- **Neue Prüfung:** 24.–29.09.2026 wurden anschließend separat prognostiziert;
  ihre Ziele nicht zum Fit verwendet. Neue Wetter-/SMARD-Eingaben frisch
  heruntergeladen; September-Kapazität aus vorhandener Monatsreihe verwendet.

## 25.10.2026 – Bezugsquelle tatsächlicher Stromerzeugung erläutert

- **Beratung/Prüfung:** Offizielle SMARD-Downloadseite
  `https://www.smard.de/home/downloadcenter/download-marktdaten/` geöffnet.
  Verweis für Deutschland, realisierte Stromerzeugung, Stundenauflösung und
  CSV gegeben. Projekt verwendet nationale Erzeugung je Energieträger in MWh,
  nicht Messwerte jeder einzelnen MaStR-Anlage.
- Bereits vorhandenes Downloadskript als automatischen Bezugsweg benannt;
  kein erneuter Download, keine Modelländerung oder Trainings ausgeführt.

## 25.10.2026 – Anlagenzahl, Leistung und Strommenge unterschieden

- **Beratung:** MaStR beschreibt einzelne Anlagen; im bestehenden Modell
  werden die aufsummierten installierten Leistungen von PV, Onshore und
  Offshore verwendet, nicht deren Anzahl als zusätzliches Merkmal.
  MW bezeichnet Leistung, MWh die über einen Zeitraum erzeugte Energie.
- **Didaktisches Beispiel, keine Projektdaten:** Zehn Windanlagen à 5 MW
  ergeben 50 MW installierte Leistung. Eine Stunde tatsächlich konstant
  50 MW entspricht 50 MWh; tatsächliche Erzeugung hängt u.a. von Wind,
  Verfügbarkeit und Abregelung ab und ist nicht durch Nennleistung garantiert.
  Keine Daten- oder Codeänderung, kein Training ausgeführt.

## 25.10.2026 – Aufgaben von MaStR und Electricity Maps erneut erläutert

- **Beratung:** MaStR-Anlagenstammdaten dienen im bestehenden Modell zur
  Rekonstruktion dreier nationaler Monatswerte: installierte PV-, Onshore-
  und Offshore-Nettoleistung in MW. Diese Summen sind abgeleitete Eingaben,
  keine stündliche Erzeugung und keine fertigen Prognosen des Registers.
- Electricity Maps liefert hier den erzeugungsbezogenen Lebenszyklus-CO2-Wert
  Deutschlands in gCO2eq/kWh als Trainingsziel und nachträglichen Vergleichswert.
  Künftige tatsächliche CO2-Werte sind keine Eingabe der finalen HGB-Inferenz.
  Grünanteilsziel stammt im Projekt aus SMARD-Erzeugung, nicht Electricity Maps.
- **Prüfung:** Verwendungsstellen im Inferenz- und Vergleichsskript gelesen.
  Keine Aussage über den vollständigen aktuellen Produktumfang der Anbieter,
  keine Downloads, Trainings oder Codeänderungen vorgenommen.

## 25.10.2026 – Prüfung während der Modellentwicklung erklärt

- **Ausgeführt:** `train_hist_stage0.py`, Verweise auf Validierungsfolds und
  finales HGB-Manifest gelesen. Entwicklung verwendet drei Trainingsjahre
  und das jeweils folgende Validierungsjahr (2018–2024); Vergleichsmethoden
  umfassen lineare Regression, Mittelwert und Vorwochenwert. HGB läuft mit
  100 Iterationen und `early_stopping=False`. Finale Anwendung trainiert
  2015 bis 23.09.2026, laut Manifest ohne eigenen internen Testscore.
- **Beratung:** Trainingsfehler beschreibt Anpassung an bekannte Beispiele;
  spätere, beim Fit unbekannte Validierungsdaten prüfen Übertragbarkeit.
  Einstellungen nur anhand der Entwicklung wählen, Abschlusstest getrennt
  halten. MAE, RMSE, Bias und Vergleich auf identischen Stunden erklären.
- **Präzisierung früherer Aussage:** Baselinevergleiche sind in der bisherigen
  Entwicklung bereits implementiert. Empfehlung zum weiteren Vergleich
  bezog sich auf die neuen September-Tage und operative Wetterprognosen.
  Die Leistung der früheren Drei-Jahres-Modelle ist kein eigenständiger
  Testnachweis für den finalen Fit über die gesamte Historie. Keine Änderung
  an Training, Parametern oder Daten ausgeführt.

## 25.10.2026 – Güte des Stundenvergleichs vom 27.09. eingeordnet

- **Beratung auf Bewertungsfrage:** Ergebnis dieses Tages als vielversprechend,
  allgemeine oder operative Güte als noch nicht belegt eingestuft. Grundlage:
  CO2-MAE 24,61 gCO2eq/kWh, EE-MAE 2,86 Prozentpunkte; CO2 in 19/24 Stunden
  unterschätzt, größte absolute CO2-Abweichung 70,29 um 21 UTC/23 MESZ.
- **Empfehlung:** Modell vorerst unverändert lassen. Gegen eine einfache
  Vorwochenprognose auf denselben Stunden und über weitere unangetastete
  Zeiträume vergleichen; für den operativen Nachweis Wetterprognosen nutzen,
  die zum jeweiligen Ausgabezeitpunkt verfügbar waren. Bereits untersuchte
  Tage nach darauf basierender Optimierung nicht als unabhängigen Test ausgeben.
- **Alternative/Grenze:** Sofortiges Nachtrainieren oder Entfernen der Lags
  allein wegen dieses Tages nicht empfohlen; Nutzen erst kontrolliert prüfen.
  Keine neuen Auswertungen, Modelländerungen oder Trainings durchgeführt.

## 25.10.2026 – Stundenvergleich 27.09.2026 beauftragt

- **Auftrag/Abgrenzung:** Alle 24 UTC-Stunden des Dashboardtags mit
  Anbieter-Istwerten vergleichen; deutsche Zeit zusätzlich ausweisen.
- **Ausgeführt:** Projektregeln, Downloadskripte, Zieldefinition und Rohdaten
  geprüft. Electricity-Maps-Datei `full_DE_20261020T2100Z/20260919T23.json`
  enthält die 24 CO2-Stunden (Abruf 20.10., erzeugungsbezogen/lifecycle).
- **Geplant:** SMARD-Erzeugung desselben Tages frisch herunterladen und roh
  speichern. EE-Anteil identisch zum Trainingsziel (sechs EE-Kategorien durch
  zwölf Erzeugungskategorien inklusive Pumpspeicher) berechnen. Eingefrorene
  Prognosen stundengenau verbinden, Fehler und Mittelwerte dokumentieren.
  Keine Modell-/Dashboardänderung; diese Auswertung ist nachträgliche Bewertung.
- **Ausgeführt:** `scripts/compare_hist_20260927.py` unter `.venv-stage0/bin/python`
  erstellt und ausgeführt. Frische SMARD-Rohantwort samt Anfrage/Abrufzeit/Hash
  in `data/raw/smard_comparison_20260927/` gespeichert. Ergebnisse in
  `reports/hist_comparison_20260927_v1/comparison.csv` und `run.json`.
- **Geprüft:** 24 eindeutige, deckungsgleiche Stunden; Electricity Maps
  durchgehend DE, Produktion (`flowTraced=false`), lifecycle, nicht als
  geschätzt gekennzeichnet. SMARD-Kernenergie 24 leere Werte nach bestehender
  Nullregel; sechs EE-Kategorien im Zähler, alle zwölf im Nenner.
  CSV erneut gelesen, Fehler und MAE nachgerechnet, Quellenhashes bestätigt;
  ursprüngliche Vorhersagedatei unverändert. `git diff --check` erfolgreich.
- **Ergebnisse:** CO2-MAE 24,6053 gCO2eq/kWh, RMSE 29,9030, Bias -20,3091;
  Tagesmittel Vorhersage 296,6075 / Anbieter-Ist 316,9167. EE-MAE 2,8556
  Prozentpunkte, RMSE 3,2565, Bias +1,7648; Tagesmittel 70,1115 / 68,3467 %.
- **Grenzen:** Revidierte Anbieterwerte und rückblickendes ERA5-Wetter,
  kein Echtzeitnachweis. Ein einzelner Tagesvergleich belegt keine allgemeine
  Modellgüte und keine Ursache. Istziele nur nach eingefrorener Inferenz gelesen.

## 25.10.2026 – Vorhersagen 27.–29.09. im Dashboard einbinden

- **Auftrag:** Bereits berechnete drei Tage im Dashboard anzeigen.
- **Ausgeführt:** Projektregeln, App, Datenlader und bestehende Dashboardtests
  gelesen. Datenlader um den expliziten Report
  `reports/hist_prediction_20260927_29_v1/predictions.csv` erweitert;
  bestehender Block bleibt enthalten. Cache-Version und Zeitraumhinweis
  auf 24.–29.09. aktualisiert. Modelle und Vorhersagedateien nicht verändert.
- **Geplant:** Bestehende Tests ausführen, neue Stunden gegen Report prüfen
  und alle drei Tage über Streamlit-AppTest auswählen; Kennzahlen und
  Stundentabelle gegen dieselben Quelldaten vergleichen.
- **Geprüft/abgeschlossen:** Beide bestehenden Dashboard-Unit-Tests bestanden.
  Alle 72 neu geladenen Stunden und beide Vorhersagespalten stimmen exakt
  mit dem Report überein; Zeitstempel eindeutig, Istspalten weiterhin leer.
  Streamlit-AppTest ohne Ausnahme: Standarddatum 29.09.2026, alle drei Tage
  einzeln auswählbar, je 24 Tabellenzeilen und vier Kennzahlen gegen
  `best_window` geprüft. Aktualisierter Zeitraumhinweis sichtbar.
  `git diff --check` erfolgreich. Kein Training oder Neuberechnen der Prognosen.

## 25.10.2026 – Vorhersagen 27.–29.09.2026 beauftragt

- **Auftrag:** 72 stündliche Vorhersagen mit den bereits geladenen Eingaben
  und unveränderten finalen HistGradientBoosting-Modellen berechnen.
- **Ausgeführt:** Regeln, Inferenzskript und Datenprotokoll gelesen. Vorhandene
  Downloader-Änderungen beibehalten. Bestehendes Inferenzskript um UTC-Startdatum
  und SMARD-Verzeichnis als Parameter erweitert; Default bleibt 24.–26.09.
  Zusätzliche Quellenhash-/Zeitraumprüfungen vor der Inferenz eingefügt.
- **Geplant:** `scripts/predict_hist_20260924_26.py --target-start 2026-09-27
  --smard-dir data/raw/smard_prediction_inputs/20261025T215146Z` unter
  `.venv-stage0/bin/python` ausführen. Ausgabe in getrenntem Reportordner,
  danach gespeicherte Ergebnisse auf Zeitraster, Vollständigkeit und
  Modell-/Quellenhashes prüfen. Kein Fit, keine Istziele der Zieltage lesen.
  Historisches ERA5 bleibt eine rückblickende Prüfung.
- **Ausgeführt:** Obigen Befehl erfolgreich ausgeführt. Reportordner
  `reports/hist_prediction_20260927_29_v1/` enthält `inputs.csv`,
  `predictions.csv` und `run.json` mit Quellen-/Modell-/Skripthashes.
  72 Stunden von 27.09. 00:00 bis 29.09. 23:00 UTC, je zwei Ausgaben.
- **Geprüft:** Gespeicherte Dateien erneut gelesen: 136 Merkmale in exakter
  Modellreihenfolge, endliche Werte, eindeutiges stündliches Raster, Lag exakt
  168h, Ortszeitdarstellung konsistent, Kapazitätsreferenz immer 01.09.
  Quellen-, Modell- und Skripthashes bestätigt. Erneutes `predict` aus den
  gespeicherten Eingaben reproduziert sämtliche Ausgaben (rtol 1e-12,
  atol 1e-10). CO2 nichtnegativ, EE im Bereich 0–100 ohne Clipping.
  `git diff --check` erfolgreich. Joblib meldete lediglich Fallback von
  physischer auf logische Kernzahl; beide Berechnungen erfolgreich.
- **Ergebnisse (Vorhersage-Tagesmittel, UTC):** 27.09.: CO2 296,608 gCO2eq/kWh,
  EE 70,111 %; 28.09.: 464,273 und 49,857 %; 29.09.: 379,722 und 60,262 %.
  Gesamtmittel CO2 380,201, EE 60,077 %. Noch kein Vergleich mit Istwerten.
  Keine Modellanpassung und keine neue Dashboardeinbindung vorgenommen.

## 25.10.2026 – Eingabedownload für 27.–29.09.2026 beauftragt

- **Auftrag:** Alle für die nächste rückblickende 72h-Vorhersage benötigten
  Eingaben laden. Wie beim vorherigen Block UTC-Tage: 27.09. 00:00 bis
  30.09. 00:00 exklusiv; deutsche Ortszeit 27.09. 02:00 bis 30.09. 02:00.
- **Ausgeführt:** Projektregeln, bisherige Downloader, Inferenzskript und
  Protokollregeln gelesen; Arbeitsbaum vor Änderungen sauber. Beide Downloader
  um `--target-start` erweitert, Standardzeitraum bleibt 24.–26.09. unverändert.
- **Entscheidung:** Frische SMARD-Erzeugung und Netzlast 20.–22.09. UTC
  (Zielzeit minus 168h) und ERA5 für 27.–29.09. an denselben 23 Punkten.
  Nur Koordinaten aus Archivskript, keine alten Beobachtungen übernehmen.
  Vorhandene September-Kapazitäten und lokale Kalenderberechnung prüfen.
- **Geplant:** Downloads ausführen, Stunden/Einheiten/Vollständigkeit/Hashes
  und Abdeckung aller 136 Modelleingaben kontrollieren. Keine Zielwerte
  der neuen Tage für diesen Auftrag laden, kein Training oder Modellwechsel.
  ERA5 und revidierte SMARD-Daten erlauben nur rückblickende Prüfung;
  archivierte Wetterprognosen wären für einen Echtzeitnachweis erforderlich.
- **Ausführung/Zwischenstand:** Beide Skripte mit `--target-start 2026-09-27`
  gestartet. Erster Start unter `.venv/bin/python` scheiterte, da dieser
  Interpreter fehlt; danach vorhandenes `.venv-stage0/bin/python` verwendet.
  SMARD erfolgreich in `data/raw/smard_prediction_inputs/20261025T215146Z/`:
  72 eindeutige Stunden pro Datei, ausschließlich Kernenergie 72-mal leer.
  Bestehende Nullregel bleibt anzuwenden, Rohdaten unverändert.
  Wetterdownload läuft mit Wiederholungen; erste Gesamtprüfung brach korrekt
  am noch falschen `complete`-Kennzeichen ab. Kein fertiges Ergebnis behauptet.
- **Abgeschlossen/geprüft:** Wetterdownload erfolgreich, 23 Dateien plus
  vollständiges Manifest in `data/raw/weather_prediction_20260927_20260929_era5/`.
  8.280 endliche Wetterwerte (23 × 72 × 5), passende Einheiten und Gitterpunkte
  durch Downloader bestätigt. Rohdateien erneut unabhängig eingelesen:
  Wetter- und SMARD-SHA256 stimmen, Zielraster und Lagzeiten eindeutig/lückenlos.
  936 SMARD-Eingabewerte einschließlich 72 dokumentierter Kernenergie-Nullwerte
  verfügbar; keine weiteren Lücken, alle Erzeugungs-/Lastwerte nichtnegativ.
- **Kapazität/Kalender:** Alle Stunden verwenden nach unveränderter Regel
  01.09.2026: PV 114.862,481874 MW, Onshore 70.821,845627 MW, Offshore
  11.298,743 MW aus bestehender Monatsdatei. Kalenderfunktionen für alle
  72 lokalen Zeitpunkte ausführbar. Kein erneuter MaStR-Abruf nötig.
- **Modellabdeckung:** Vereinigte Merkmalsnamen exakt gleich den 136 Merkmalen
  im finalen Trainingsmanifest. Trainingsende vor neuem Block; beide
  Modellhashes weiterhin identisch mit Trainingsmanifest. CLI-Hilfe und
  `git diff --check` erfolgreich. Keine Vorhersage ausgeführt, keine Istziele
  des neuen Blocks gelesen, kein Training und keine Dashboardänderung.

## 25.10.2026 – Modellfehler durch Eingabe-Sensitivität näher untersucht

- Gespeichertes CO2-HGB ohne Fit ausgewertet. Ausgangspunkt 24.09.2026
  07:00 UTC: 240,97 gegenüber Anbieter-Ist 303 gCO2eq/kWh.
- Diagnoseintervention: jeweilige Gruppe durch komponentenweise Mediane
  der vorhandenen 2026-Trainingstabelle ersetzt, andere Gruppen gleich
  gelassen. Resultat für diese Stunde: Energie-Lags 286,24; Wetter 463,71;
  Kapazitäten 238,70 gCO2eq/kWh. Median ausschließlich Diagnose, keine neue
  Prognosemethode oder zugelassene Vergleichsvariante. Ungewöhnliche gemeinsame
  Wetterkombinationen und Wechselwirkungen verhindern kausale Interpretation.
- Zusätzliche Diagnose: Nur Energie-Lagvektor der Stunde durch die 72
  verschiedenen bereits verwendeten Lagprofile ersetzt, Wetter/Kalender/
  Kapazitäten unverändert. Ausgabe 209,18–329,77. Belegt lokale Sensitivität
  auf Marktmerkmale; weder Attributionsanteile noch Garantie einer Verbesserung.
- Wettervergleich 17./24.09. 07 UTC: ungewichtetes Mittel über 23 Punkte,
  nur zur Beschreibung: Strahlung 138,83→82,35 W/m², Wind 6,38→7,98 m/s,
  Sonnenscheindauer 3280,71→2082,65 s. Kein einzelnes Wettermerkmal der
  Zielstunde außerhalb des Wertebereichs der 2026-Trainingstabelle gefunden.
- Einordnung: Vorwochenmerkmale können die niedrige Schätzung beeinflussen;
  pauschale frühere Erklärung allein durch Vorwochenmix nicht bewiesen.
  Wetter beeinflusst das Modell ebenfalls deutlich, Kapazitätsintervention
  an dieser Stelle nur gering. Keine eindeutige kausale Fehlerzerlegung aus
  diesen Beobachtungen möglich; ablationierte Modelle benötigen gesonderte
  Trainings und unabhängige Bewertung. Keine Trainings autorisiert/ausgeführt,
  keine Originaleingaben/Modelle/Vorhersagen geändert.

## 25.10.2026 – 72h-Eingaben gegen Rohdaten unabhängig nachgeprüft

- Vorhandene `inputs.csv` erneut gelesen, Zeitraster 72h, 136 Merkmale in
  exakter Modellreihenfolge, endliche Werte und Zielzeiten nach Trainingsende
  bestätigt. Quellen- und Modellhashes aus Inferenzmanifest erneut bestätigt.
- Alle 8.280 Wetterwerte gegen die fünf Rohreihen je Standort abgeglichen;
  alle 936 SMARD-Eingaben (13 Reihen × 72) gegen Roh-CSV und genaue Zielzeit
  minus 168h abgeglichen. Deutsche CSV-Zeit korrekt in UTC umgewandelt.
  Keine Abweichungen gegenüber gespeicherten Quellen gefunden.
- Kalendermerkmale und Kapazitätsreferenzregel unabhängig nachgerechnet.
  Stichtag 01.09.2026: PV netto 114.862,481874 MW, Onshore 70.821,845627 MW,
  Offshore 11.298,743 MW. Übereinstimmung mit eingefrorener Monatsdatei.
- Ergebnis: Kein Übertragungs-, Spalten- oder Zeitzonenfehler bei diesen
  Prüfungen gefunden. Dies validiert nicht die fachliche Wahrheit des MaStR-
  Proxys, Wetterrepräsentativität oder den Einfluss einzelner Merkmale.
  ERA5-Intervallsemantik wie im Training beibehalten. Kein erneutes Training.

## 25.10.2026 – SMARD-Strommix vom 17. und 24.09. verglichen

- Beide UTC-Tage frisch per SMARD-Download-Manager abgefragt. Je 24 eindeutige
  Stunden und zwölf Erzeugungsarten ausgewertet; Kernenergie-Nullregel wie
  bisher. Keine Modelländerung. Antworten im Arbeitsspeicher ausgewertet.
- 09:00 MESZ: Solar 23.682,84 → 12.380,31 MWh, Wind an Land 14.239,43 →
  24.841,85, Wind auf See 4.279,00 → 4.957,41; Braunkohle 7.584,54 →
  8.798,48, Steinkohle 4.082,33 → 4.752,63, Gas 4.332,24 → 6.390,01.
- UTC-Tagessummen Solar 285.879,80 → 197.646,77 MWh; Gas 92.895,18 →
  151.526,91; Braunkohle 204.950,35 → 224.500,49 und Steinkohle
  78.965,44 → 109.381,73. Vorwochenmix ist somit deutlich anders als Istmix.
- Dies macht die begrenzte Aussagekraft der Lags sichtbar, beweist aber
  nicht deren kausalen Anteil am Modellfehler. Wetter- und Modellbeiträge
  wurden noch nicht getrennt untersucht.

## 25.10.2026 – Eingefrorene 72h-Vorhersagen gegen Istwerte geprüft

- Auf Auftrag alle 72 vorhandenen HGB-Vorhersagen 24.–26.09.2026 UTC
  nachträglich bewertet. Electricity-Maps-Rohdaten: erzeugungsbezogene
  Lebenszykluswerte, alle 72 ohne Schätzkennzeichen. SMARD-Erzeugung für
  denselben Zeitraum frisch via Download-Manager abgerufen; EE-Ziel mit
  identischen zwölf Kategorien und Kernenergie-Nullregel berechnet.
- Ergebnis CO2: MAE 39,693 und RMSE 47,679 gCO2eq/kWh; mittlerer Fehler
  Vorhersage minus Ist -12,991. 48/72 Stunden unterschätzt. Istmittel 457,347,
  Prognosemittel 444,356. Tages-Bias 24./25./26.: -43,860/+16,652/-11,765.
- Ergebnis EE: MAE 3,786, RMSE 4,825 Prozentpunkte; Bias +1,969 Prozentpunkte.
  Tages-MAE 24./25./26.: 4,300/3,228/3,829 Prozentpunkte.
- Interpretation: 24.09. CO2 überwiegend unterschätzt; über die drei Tage
  keine durchgehend gleiche Fehlerrichtung. Fehlerursache damit nicht
  kausal erklärt. Nur drei Tage, tatsächliches ERA5-Wetter und revidierte
  Istwerte; keine Aussage zur allgemeinen operativen 72h-Genauigkeit.
- Keine Parameter, Eingaben oder Vorhersagen verändert. SMARD-Antwort im
  Arbeitsspeicher ausgewertet, keine neue Rohdatei gespeichert.

## 25.10.2026 – Vergleichszeitpunkt im Dashboard geklärt

- Vorhersagedatei für 24.09.2026 07:00 UTC (=09:00 MESZ) gezielt gelesen,
  um mit der vorausgehenden Istwert-Nachschau dieselbe Stunde zu vergleichen.
- Screenshot dagegen zeigt Mittelwerte des optimalen 3h-Fensters
  09:00–12:00 UTC (=11:00–14:00 MESZ). Diese unterscheiden sich sowohl in
  Zeitzone als auch Aggregation und sind nicht direkt mit 09:00 MESZ vergleichbar.
- Keine Modell-/Dashboardänderung; keine Gesamtgüte aus Einzelstunde ableiten.

## 25.10.2026 – Tatsächliche Werte am 24.09.2026 um 09:00 MESZ nachgeschlagen

- Uhrzeit ausdrücklich als deutsche Ortszeit interpretiert: 07:00 UTC.
  Electricity-Maps-Rohantwort `full_DE_20261020T2100Z/20260919T23.json`
  enthält 303 gCO2eq/kWh, erzeugungsbezogen (`flowTraced=false`), Lebenszyklus,
  `isEstimated=false`. Revidierter Anbieterwert, keine Modellvorhersage.
- SMARD-Erzeugung für diese Stunde frisch über offiziellen Download-Manager
  abgerufen, alle zwölf Erzeugungsarten gelesen. Kernenergie leer, gemäß
  bestehender Ausstiegsregel null. EE-Summe 47.479,53 MWh; Gesamterzeugung
  einschließlich Pumpspeicher 69.364,54 MWh; EE-Anteil 68,4492826 %.
- Nur gezielte Nachschau; keine Modelländerung und keine Kennzahlenbewertung.
  SMARD-Antwort im Arbeitsspeicher ausgewertet, nicht als neue Rohdatei gespeichert.

## 25.10.2026 – Neue September-Vorhersagen im Dashboard eingebunden

- Auf ausdrücklichen Auftrag Datenlader in `src/dashboard_logic.py` um
  `hist_prediction_20260924_26_v1/predictions.csv` erweitert. Neue Spalten auf
  Dashboard-Namen abgebildet; keine tatsächlichen Zielwerte erfunden.
  Eindeutigkeit und vollständige Vorhersagen geprüft. Historische Daten behalten.
- `app.py`: Cache-Version erneuert und Lebensdauer 60 Sekunden gesetzt;
  Erläuterung für neue September-Tage ergänzt. Kalenderobergrenze folgt den
  Daten und reicht jetzt bis 26.09.2026 UTC. Kennzahlen, Zeitfenster und
  Diagramm verwenden dieselben Berechnungen auch für die neuen Tage.
- Prüfung: beide Dashboard-Unit-Tests bestanden; je neuer Tag 24 vollständige
  Stunden und funktionierende 3h-Zeitfensterberechnung. Kein Training.

## 25.10.2026 – Fehlende neue Vorhersagen im Dashboard diagnostiziert

- `app.py` und `src/dashboard_logic.py` gelesen. Dashboard-Lader verwendet
  bestehende historische Jahres-Vorhersagedateien; der neue separate
  `hist_prediction_20260924_26_v1/predictions.csv`-Report wird nicht eingelesen.
  Datumsobergrenze wird aus den geladenen Daten abgeleitet. Neue Stunden
  fehlen deshalb im Kalender. Zusätzlich cached Streamlit den Lader.
- Nur Diagnose dokumentiert; keine App-Änderung auf die Erklärungsfrage hin.

## 25.10.2026 – HistGradientBoosting-Vorhersagen für 24.–26.09.2026 erstellt

- **Auftrag/Ausführung:** `scripts/predict_hist_20260924_26.py` implementiert
  und ausgeführt. Gespeicherte finale HGB-Pipelines für CO2 und EE-Anteil
  ausschließlich mit `predict` verwendet. Keine neue Anpassung, keine Zielwerte
  geöffnet. Modelle und deren Vorverarbeitung unverändert; Hashes gegen
  Trainingsmanifest und vor/nach Inferenz bestätigt.
- **Eingaben:** 72 UTC-Stunden, 24.09. 00:00 bis 26.09. 23:00. Frische
  ERA5-Rohantworten (23 Orte, fünf Größen), frische SMARD-Rohdaten vom
  17.–19.09. mit exakt 168-h-Zuordnung, vorhandene rekonstruierte MaStR-
  Monatswerte zum 01.09. gemäß bisheriger Referenzregel und identisch
  berechneter Kalender. 136 Merkmale in gespeicherter Modellreihenfolge.
  Leere Kernenergiewerte mit bestehender Regel nach 16.04.2023 als null
  behandelt. Stunden in Europe/Berlin zusätzlich ausgegeben; UTC-Zeitraum
  entspricht lokal 24.09. 02:00 bis 27.09. 01:00.
- **Ergebnisse:** `reports/hist_prediction_20260924_26_v1/inputs.csv`,
  `predictions.csv`, `run.json`. 72 CO2-Vorhersagen: Mittel 444,36,
  Minimum 187,25, Maximum 680,62 gCO2eq/kWh. 72 EE-Vorhersagen: Mittel
  52,68 %, Minimum 23,02 %, Maximum 83,70 %. Unbeschnittene Modellwerte.
- **Prüfung:** Ausgabe erneut eingelesen; 72 eindeutige Zielstunden, 136
  vollständige endliche Eingaben, exakte Lag-Abstände, endliche Ausgaben.
  EE-Vorhersagen innerhalb 0–100 %. Jede Zielstunde liegt nach Trainingsende
  23.09.2026 23:00 UTC. Quellen-/Modell-/Skripthashes im Run-Manifest.
- **Grenzen:** Retrospektives tatsächliches ERA5-Wetter, kein as-issued
  72h-Test. SMARD revidiert, MaStR historischer Proxy. Keine Bewertung gegen
  tatsächliche Zielwerte, deshalb keine MAE/RMSE/R2 oder Genauigkeitsbehauptung.
  Hinweis zur CPU-Kernerkennung von joblib ohne Einfluss auf erfolgreichen Lauf.

## 25.10.2026 – Wetter für 24.–26.09.2026 frisch heruntergeladen

- **Auftrag/Ausführung:** `scripts/download_weather_prediction_inputs.py`
  erstellt und ausgeführt. Open-Meteo Archive API, Modell ERA5, 24.09.2026
  00:00 bis 26.09.2026 23:00 UTC, alle 23 bisherigen Wetterpunkte.
  Aus dem Archiv ausschließlich Koordinatenkonfiguration gelesen, keine
  Wetterbeobachtungen übernommen. Keine Trainingsdaten verändert.
- **Daten:** Temperatur 2 m (°C), Bewölkung (%), Wind 100 m (m/s),
  Kurzwelleneinstrahlung (W/m²), Sonnenscheindauer der vorausgehenden Stunde
  (s). Rohantworten unter `data/raw/weather_prediction_20260924_20260926_era5/`:
  23 JSON-Dateien plus Manifest mit URLs, SHA-256, Prüfzeit und Rasterkoordinaten.
- **Prüfung/Ergebnis:** Alle 23 Orte mit exakt 72 fortlaufenden UTC-Stunden;
  insgesamt 8.280 endliche, nicht fehlende Wetterwerte. Einheiten bestätigt,
  Bewölkung 0–100 %, Sonnenscheindauer 0–3.600 s; Rasterkoordinaten stimmen
  mit der Trainingsmetadatei überein. Download erfolgreich abgeschlossen.
- **Grenze:** Tatsächlich eingetretenes Reanalyse-Wetter, keine damals
  ausgegebene Wettervorhersage. Damit nur retrospektiver Test. Noch keine
  Modellmerkmale zusammengeführt und keine Modellvorhersage erzeugt.

## 25.10.2026 – Direkte Kapazitätssummen in MaStR-API geprüft

- Produktions-WSDL frisch geladen: 132 verschiedene Operationen. Keine
  Operation für nationale Summen, Statistik oder installierte Gesamtleistung
  gefunden. Solar-/Wind-Detailoperationen und Änderungs-/Löschlisten vorhanden.
- Wind-Detailantwort enthält `WindAnLandOderSee`; Listenabruf allein liefert
  die benötigten drei nationalen Nettoleistungssummen nicht. Diese müssen aus
  vollständigen, nach einheitlichen Bestandsregeln gefilterten Details selbst
  berechnet werden. Keine neuen Anlagen geladen oder Modellmerkmale geändert.
- Quelle: https://www.marktstammdatenregister.de/MaStRAPI/wsdl/mastr.wsdl
  und importiertes `mastrbasetypes.xsd`.

## 25.10.2026 – Erste MaStR-Solar- und Wind-Rohdaten über Webdienst geladen

- **Ausgeführt:** `scripts/download_mastr_raw.py` implementiert und gestartet.
  Lesender `GetGefilterteListeStromErzeuger`-Abruf, Energieträger `Wind` und
  `SolareStrahlungsenergie`, jeweils erste Seite mit Limit 200. Rohantworten
  unverändert unter `data/raw/mastr_api/20261025T205037Z/` gespeichert;
  Manifest mit Hashes, Filter, Seitenstart und Ergebniscode. Schlüssel nicht
  gespeichert. Kein Training, keine Kapazitätsberechnung.
- **Ergebnis:** Je 200 Einheiten, beide `OkWeitereDatenVorhanden`.
  Dies ist ausdrücklich ein unvollständiger Listenabruf, kein Gesamtexport.
- **Wesentliche Grenze:** Offizielle XSD-Antwort `Einheit` enthält
  Bruttoleistung und Standortübersicht, aber keine für die bisherige
  Modellaufbereitung benötigte Nettoleistung und vollständige Betriebsdaten.
  Dafür wären Einzelabrufe notwendig. Bei mehreren Millionen Solar-Einheiten
  überschreitet ein vollständiger Detailabruf das dokumentierte Tageskontingent
  von 100.000 Aufrufen deutlich. Vollständigkeit nicht behauptet.
- **Empfehlung korrigiert:** Webdienst für Änderungen geeignet, vollständiger
  neuer Ausgangsbestand besser als offizieller ZIP-Gesamtexport. Ein vollständiger
  Erstabruf per Webdienst ist für diesen Zweck nicht praktikabel. Nutzer muss
  diesen Umfang vor einem mehrtägigen API-Detailabruf kennen. Keine Umgehung
  des Downloadportals implementiert. Alle weiteren Seiten und Detaildaten offen.

## 25.10.2026 – MaStR-Leseberechtigung nach Zuordnung bestätigt

- Nutzer hat API-Benutzer im Portal dem eigenen Marktakteur als lesenden
  Vertreter zugeordnet. Danach `GetListeAlleEinheiten`, Limit 1, erneut
  ausgeführt: HTTP 200, `OkWeitereDatenVorhanden`, ein Einheiten-Element.
- Anlagen-Lesezugriff damit bestätigt. Antwort nur zur Berechtigungsprüfung
  ausgewertet; noch kein vollständiger Solar-/Winddownload und keine
  neue Kapazitätssumme erstellt. Schlüssel nicht ausgegeben.

## 25.10.2026 – Anlagenabruf mit eingetragener Marktakteursnummer geprüft

- `.env` enthält Schlüssel und Marktakteursnummer. Lesender SOAP-Aufruf
  `GetListeAlleEinheiten`, Limit 1, mit beiden Angaben ausgeführt.
- Ergebnis HTTP 400, `FalscherMarktakteur`: Marktakteur ist nicht gültig
  oder kann mit diesen Zugangsdaten nicht verwendet werden. Keine Einheiten
  erhalten. Schlüssel nicht ausgegeben. Zuordnung, Rollen und Freigabestatus
  müssen im Portal geprüft werden; genaue Ursache bisher nicht bestimmt.

## 25.10.2026 – Beauftragter MaStR-Anlagenabruf durch fehlende Zuordnung gestoppt

- **Ausgeführt:** Offizielles XSD für `GetListeAlleEinheiten` geprüft und
  lesenden Abruf mit Limit 1 am SOAP-1.1-Anlage-Endpunkt versucht. Schlüssel
  lokal aus `.env` gelesen, nicht ausgegeben. Keine Anlagendaten erhalten.
- **Ergebnis:** HTTP 400, `marktakteurMastrNummer fehlt`. In `.env` liegt
  keine `MASTR_MARKTAKTEUR_NUMMER` vor. Authentifizierung war im vorherigen
  Uhrzeittest erfolgreich, reicht für Anlagenabrufe allein jedoch nicht aus.
- **Offen:** Tatsächliche Marktakteursnummer und Zuordnung des API-Benutzers
  zu diesem Marktakteur erforderlich. Keine Nummer erfunden und keine fremde
  Zuordnung verwendet. Registrierung oder Änderung der Marktakteursrolle
  wurde nicht vorgenommen. Vollständiger Download bleibt unerledigt.

## 25.10.2026 – MaStR-Authentifizierung erfolgreich getestet

- **Ausgeführt:** Offizielle WSDL und importierte XSD-Schemata geprüft;
  `GetLokaleUhrzeitMitAuthentifizierung` per SOAP 1.1 an den Common-Endpunkt
  gesendet. Schlüssel ausschließlich aus `.env` gelesen und nicht ausgegeben.
- **Korrektur:** Das Request-Element gehört zum Namensraum `Modelle/Common`,
  der geerbte Parameter `apiKey` dagegen zu `Modelle`. Frühere Versuche mit
  falschem Parameter-Namensraum lieferten HTTP 403, `apiKey fehlt`.
- **Geprüftes Ergebnis:** Korrigierter Aufruf liefert HTTP 200 und
  `Ergebniscode OK`. Der eingetragene Schlüssel wird akzeptiert.
- **Grenzen:** Keine Anlagendaten geladen. Marktakteurszuordnung und Rechte
  für Einheitenabrufe sind durch diesen Uhrzeit-Anmeldungstest nicht geprüft.
- **Quellen:** `https://www.marktstammdatenregister.de/MaStRAPI/wsdl/mastr.wsdl`
  und `https://www.marktstammdatenregister.de/MaStRAPI/xsd/mastrbasetypes.xsd`.

## 25.10.2026 – Eingetragenen MaStR-Schlüssel lokal geprüft

- `.env` ohne Ausgabe des Geheimnisses auf genau einen gesetzten
  `MASTR_API_KEY` und Leerzeichen geprüft. Git-Ignorierung erneut kontrolliert.
- Dies prüft nur die lokale Konfiguration; Authentifizierung und
  Abrufberechtigungen beim MaStR sind damit noch nicht bestätigt.

## 25.10.2026 – MaStR-Zugangskonfiguration vorbereitet

- Auf Auftrag `MASTR_API_KEY` als leeren Eintrag in der bestehenden `.env`
  ergänzt. Bestehende Einträge erhalten. `.env` wird von Git ignoriert.
- Schlüssel aus Screenshot nicht übertragen: zuverlässige Zeichenübernahme
  nicht gewährleistet. Nutzer muss den Schlüssel direkt lokal einfügen.
  Kein authentifizierter Abruf durchgeführt, keine Zugangsdaten dokumentiert.

## 25.10.2026 – SMARD-Lag-Rohdaten frisch heruntergeladen

- **Status:** auf Auftrag ausgeführt; kein Training und keine Modellvorhersage.
- **Durchführung:** Neues Skript `scripts/download_smard_prediction_inputs.py`,
  nach den Request-Parametern des alten Download-Skripts. Direkter POST an
  `https://www.smard.de/nip-download-manager/nip/download/market-data`;
  Deutschland, CSV, stündlich, 17.09.2026 00:00 bis 20.09.2026 00:00 UTC exklusiv.
- **Ausgabe:** `data/raw/smard_prediction_inputs/20261025T200051Z/` mit
  unveränderten `generation.csv`, `load.csv` und `manifest.json` (Requests,
  Abrufzeit, SHA-256 und Prüfungen). Keine Archivdaten übernommen.
- **Prüfung:** Jeweils 72 eindeutige Stunden vom 17.09. 00:00 bis 19.09.
  23:00 UTC. Zwölf Erzeugungsreihen und exakt `Netzlast [MWh]` geprüft;
  zusätzliche gelieferte Lastspalten werden nicht als Modellmerkmale ausgewählt.
  Keine fehlenden benötigten Werte außer 72 leeren Kernenergiewerten.
  Diese bleiben in den Rohdateien unverändert; bei späterer Merkmalsbildung
  gilt die vorhandene dokumentierte Nullregel nach dem deutschen Atomausstieg.
- **Versuche:** Erster Netzwerkzugriff in Sandbox scheiterte an DNS, danach
  genehmigter Abruf. Ein erster Abruf stoppte bei der Prüfung, weil SMARD
  zusätzlich `Netzlast inkl. Pumpspeicher` liefert. Auswahl auf exakten
  Spaltenpräfix korrigiert; erneuter Abruf vollständig erfolgreich.
  Frühere unvollständige Abrufordner bleiben nachvollziehbar erhalten.
- **Grenze:** Heute abgerufener revidierter Datenstand, keine Bestätigung der
  am historischen Prognosestart veröffentlichten Werte. Rohdaten werden erst
  später den Zielstunden 24.–26.09.2026 UTC über `t - 168 h` zugeordnet.

## Vereinbarung vom 21.10.2026

Wir dokumentieren den Projektneustart von Anfang an begleitend. Jeder ausgeführte
Arbeitsschritt und jede wesentliche Entscheidung erhält einen nachvollziehbaren
Eintrag. Diese Dokumentation ist die Grundlage für die spätere Bachelorarbeit,
nicht bereits deren fertiger Text.

Der Nutzer setzt das neue Modell selbst um. Ohne ausdrücklichen Auftrag werden
keine Trainingsdaten aufbereitet, keine Trainingspipeline implementiert und
keine Modelle trainiert. Das alte Projekt bleibt im Archiv.

## Was wir dokumentieren

- Ziel und Fragestellung jedes Schritts.
- Verwendete Daten: Quelle, Zeitraum, Einheit, räumlicher Bezug, Lizenz,
  Abrufdatum und Qualitätsprobleme. Keine API-Keys oder anderen Geheimnisse.
- Entscheidungen mit Begründung, Alternativen, Vorteilen und Grenzen.
- Tatsächlich ausgeführte Befehle oder Skripte, relevante Parameter,
  Softwareversionen und Speicherorte für reproduzierbare Ergebnisse.
- Datenprüfungen, fehlende Werte, Zeitzonen und gegebenenfalls Änderungen.
- Modellwahl und Referenzmodelle: Warum wird welches Modell untersucht?
- Trainings-, Validierungs- und Testzeiträume sowie Maßnahmen gegen Data Leakage.
- Nur zum jeweiligen Vorhersagezeitpunkt verfügbare Informationen verwenden;
  Veröffentlichungsverzögerungen und Ausgabezeitpunkte von Prognosen beachten.
- Aufbereitung und Parameterauswahl nicht mit dem Abschlusstest abstimmen.
- Vergleich auf identischen Teststunden, Kennzahlen, Einschränkungen und Fehler.
- Fehlgeschlagene Versuche und Korrekturen ebenfalls festhalten.

Geplante Schritte sind keine erledigten Arbeiten. Eine Methode wird nur dann als
besser bezeichnet, wenn ein geeigneter unabhängiger Vergleich das belegt.
Nachträglich rekonstruierte Angaben werden ausdrücklich als solche markiert.

## Ausgangspunkt – aus dem bisherigen Gespräch, noch kein neues Experiment

- Geplantes Ziel: stündliche CO₂-Intensität Deutschlands für die nächsten
  72 Stunden prognostizieren.
- Die bisher heruntergeladenen Electricity-Maps-Daten beziehen sich auf
  Stromerzeugung und Lebenszyklus-Emissionen in gCO₂eq/kWh. Diese Definition ist
  von direktem CO₂ und verbrauchsbezogener Intensität zu unterscheiden.
- Gewünschter historischer Datenbeginn: 2015.
- Wetter- und SMARD-Dateien liegen im alten Archiv; ihre Vollständigkeit ist
  vor Verwendung zu prüfen.
- Ursprünglich sollte MaStR zunächst entfallen. Diese Planung wurde am
  22.10.2026 ersetzt: nationale monatliche Anlagenleistungen gehören bereits
  zu Stufe 0; siehe Planänderung unten.
- Das neue Modell ist noch nicht trainiert. Konkrete Trainings- und Testgrenzen
  werden vor Experimenten anhand der Datenverfügbarkeit festgelegt.

## Vorlage für weitere Einträge

## 25.10.2026 – Historisches Streamlit-Frontend beauftragt

- **Auftrag:** Datumsauswahl und Darstellung von Strommix/CO₂, Ampel,
  Trend, Kennzahl −2…+2 sowie bestem verschiebbarem Zeitfenster.
- **Datenentscheidung:** Keine erfundenen Zukunftswerte. Das Frontend nutzt
  die bereits gespeicherten, jeweils zeitlich getrennten HGB-Vorhersagen von
  2018 bis 23.09.2026 (Entwicklungsfolds, Test 2025, Teiltest 2026).
  Tatsächliche Zielwerte werden nicht als Eingabe der Empfehlung verwendet.
- **Regeln:** Ampel anhand prognostiziertem EE-Anteil: Grün ≥60 %, Gelb
  40–<60 %, Rot <40 %. Kennzahl +2…−2 ist der tagesinterne CO₂-Rang in fünf
  gleich großen Bereichen; keine universelle Emissionsklasse. Bestes Fenster
  minimiert den Mittelwert der prognostizierten CO₂-Intensität für 1–6 Stunden.
- **Umsetzung:** Neues `app.py`, reine Logik in `src/dashboard_logic.py`, Tests
  in `tests/test_dashboard_logic.py`; Streamlit 1.50.0 ergänzt. Historische
  ERA5-Abgrenzung sichtbar im Frontend. Ausführung/Prüfung folgt.
- **Abgeschlossen:** Streamlit 1.50.0 in `.venv-stage0` installiert. App lädt
  76.266 eindeutige historische Vorhersagestunden von 01.01.2018 bis
  23.09.2026. Standarddatum ist der letzte verfügbare Tag, nicht das heutige
  Datum. Für den 23.09.2026/3 h ergibt der Logiktest 10:00–13:00 UTC,
  Ø 231,64 gCO₂eq/kWh, Ø 75,27 % EE und Score +2,0.
- **Prüfung:** 26 Unit-Tests bestanden, darunter Ampelgrenzen und bekanntes
  Minimum eines Testfensters. Streamlit-Server nach Sandbox-Freigabe auf Port
  8502 gestartet; Health-Endpunkt antwortete `ok`, danach sauber beendet.
  Streamlit `AppTest` bestätigt Datum, Slider, vier Kennzahlen, Diagrammcode
  und Datentabelle ohne App-Ausnahme. Veraltete Breitenparameter korrigiert;
  `git diff --check` bestanden.
- **Grenzen:** Oberfläche ist ein historischer Ergebnisexplorer und verwendet
  gespeicherte Out-of-sample-HGB-Vorhersagen, nicht die finalen Refit-Modelle
  zur Zukunftsprognose. Grün/Gelb/Rot und −2…+2 sind explizite UI-Regeln,
  nicht gelernte Zielgrößen. Keine Dateien oder Modelle im Archiv geändert.

## 25.10.2026 – Finales XGBoost-Refit 2015–2026 beauftragt

- **Auftrag/Plan:** Nach OLS und HGB nun XGBoost getrennt für CO₂/EE auf allen
  geeigneten Daten 01.01.2015–23.09.2026. Ausführung über das vorbereitete
  `train_final_boosting_stage0.py --xgboost`; separater Ergebnisordner.
- **Festgelegte Konfiguration:** 100 Bäume, Tiefe 6, Lernrate 0,1,
  `tree_method=hist`, `max_bin=255`, L2=1, Seed 42, ein Thread, kein Early
  Stopping. Automatischer Abgleich mit dem bewerteten Entwicklungsmanifest;
  finale OLS-Trainingsvorverarbeitung pro Ziel, kein Tuning/Clipping.
- **Einordnung:** Finales Anwendungsrefit ohne neue interne Qualitätskennzahlen.
  Die zeitlich getrennten Tests bleiben Qualitätsbeleg. Status vor Ausführung.
- **Abgeschlossen:** Zwei finale XGBoost-Modelle erfolgreich trainiert:
  CO₂ mit 102.311, EE mit 102.409 geeigneten Stunden auf dem gemeinsamen
  verfügbaren Raster von 102.816 Stunden. 136 Roh-/173 transformierte Merkmale,
  je 100 Bäume; XGBoost 2.1.4.
- **Prüfung:** 24 Unit-Tests bestanden. Beide Joblib-Dateien erneut geladen;
  Ziel, Zeitraum, Trainingsumfang, Merkmalszahlen, Baumanzahl und ein Thread
  geprüft. Parameter stimmen exakt mit dem zuvor bewerteten XGB-Verfahren
  überein. Modell- und alle Quellhashes stimmen, Prüfprediktionen nach Reload
  identisch und endlich; `git diff --check` bestanden. Daten unverändert.
- **Ergebnisort:** `reports/final_xgboost_2015_2026_v1/` mit zwei von Git
  ausgeschlossenen Joblib-Modellen und `run.json`. Keine Trainingskennzahlen
  als Qualitätsbehauptung; frühere zeitlich getrennte Tests bleiben maßgeblich.
- **Stand:** Finale Refits für OLS, HGB und XGB sind nun vollständig. HGB bleibt
  aufgrund der unabhängigen Tests der bevorzugte Kandidat; die drei finalen
  Refits wurden nicht erneut auf unbekannten Daten verglichen. Kein Commit/Push.

## 25.10.2026 – Finales HGB-Refit 2015–2026 beauftragt

- **Auftrag:** Nach finaler OLS nun ausschließlich HistGradientBoosting,
  getrennt für CO₂/EE, auf allen geeigneten Daten 01.01.2015–23.09.2026.
  XGBoost noch nicht final trainieren.
- **Umsetzung:** Neues `train_final_boosting_stage0.py`, das später separat
  auch XGB unterstützt. Für HGB gelten unverändert 100 Iterationen, Lernrate
  0,1, maximal 31 Blätter, mindestens 20 Zeilen je Blatt, kein Early Stopping,
  Seed 42. Exakte finale OLS-Trainingsvorverarbeitung pro Ziel wird übernommen;
  Mittelwerte und 173 transformierte Merkmale werden erneut geprüft.
- **Einordnung:** Finales Anwendungsmodell, keine neue Bewertung auf seinen
  Trainingsdaten. Qualitätsbeleg bleibt die zeitlich getrennte Validierung
  2018–2024 sowie die Tests 2025 und Teiljahr 2026. Kein Clipping.
- **Status:** Implementiert; Ausführung und Prüfung folgen.
- **Abgeschlossen:** Zwei finale HGB-Modelle erfolgreich trainiert. Verfügbares
  Raster 102.816 Stunden; CO₂ 102.311 und EE 102.409 geeignete Trainingszeilen.
  Je Ziel 136 Roh-/173 transformierte Merkmale, 100 vollständige Iterationen,
  kein Early Stopping. Ein CPU-Erkennungshinweis der Umgebung hatte keinen
  Einfluss auf den erfolgreichen Ein-Thread-Lauf.
- **Prüfung:** 24 Unit-Tests bestanden. Joblib-Modelle erneut geladen;
  Ziel, Zeitraum, Trainingsumfang, Merkmalszahlen, Parameter, Iterationen und
  Early-Stopping-Status geprüft. Parameter stimmen exakt mit dem zuvor
  bewerteten HGB-Verfahren überein. Modell- und alle Eingabehashes stimmen;
  gespeicherte Prüfprediktionen nach Reload identisch und endlich.
  `git diff --check` bestanden; Eingabedaten unverändert.
- **Ergebnisort:** `reports/final_hist_gradient_boosting_2015_2026_v1/` mit
  zwei ignorierten Joblib-Dateien und versionierbarem `run.json`. Keine
  Trainingskennzahlen als Qualitätsaussage; maßgeblich bleiben frühere Tests.
- **Offen:** Nur das finale XGBoost-Refit fehlt noch. Kein Commit/Push.

## 25.10.2026 – Finales OLS-Refit 2015–2026 beauftragt

- **Entscheidung/Auftrag:** Finale Modelle schrittweise erstellen; zuerst nur
  lineare Regression, HGB und XGB erst nach separatem Auftrag. Je ein Modell
  für CO₂ und EE auf allen geeigneten verfügbaren Zeilen von 01.01.2015 bis
  23.09.2026. Bestehende Validierungs-/Testergebnisse bleiben unverändert.
- **Umsetzung:** Neues `scripts/train_final_linear_stage0.py`; Ausgabe getrennt
  unter `reports/final_linear_2015_2026_v1`. Gleiche 136 Rohmerkmale,
  173 transformierte Merkmale und festgelegte OLS-Pipeline. Skalierung wird
  ausschließlich aus dem finalen Trainingsbestand bestimmt, kein Clipping.
- **Einordnung:** Das Refit ist für die spätere Anwendung, nicht ein weiterer
  Modellvergleich. Weil auch 2025 und der verfügbare Teil 2026 einfließen,
  bleibt danach kein unbenutzter Holdout für dieses konkrete Modell. Seine
  Qualitätsaussage stammt aus den zuvor zeitlich getrennten Tests.
- **Status:** Implementiert; Ausführung und Prüfung folgen.
- **Abgeschlossen:** `train_final_linear_stage0.py` erfolgreich. Gemeinsames
  verfügbares Stundenraster: 102.816 Stunden vom 01.01.2015 00:00 bis
  23.09.2026 23:00 UTC. Zielbezogen geeignete Trainingszeilen: CO₂ 102.311,
  EE 102.409. Beide Modelle haben Rang 173 bei 173 transformierten Merkmalen.
- **Prüfung:** 24 bestehende Unit-Tests bestanden. Beide Joblib-Dateien erneut
  geladen; Zeitraum, Ziel, 136 Eingabemerkmale, 173 transformierte Merkmale,
  Rang und Trainingsumfang geprüft. Modell- und sämtliche Quellhashes stimmen;
  `git diff --check` bestanden. Wie bei früherer OLS-Auswertung traten interne
  Matmul-Warnungen auf, gespeicherte Prüfprediktionen waren endlich und wurden
  nach Reload reproduziert. Keine Roh-/aufbereiteten Daten verändert.
- **Ergebnisort:** `reports/final_linear_2015_2026_v1/`; zwei Joblib-Modelle
  (von Git ausgeschlossen) und `run.json` mit Datenzeitraum, Versionen,
  Richtlinie und Prüfsummen. Keine MAE/RMSE/R² für das Refit berechnet, da
  dieselben Stunden vollständig zum Fit gehören; dafür gelten die bereits
  dokumentierten zeitlich getrennten Testresultate.
- **Offen:** Finale HGB- und XGB-Modelle sind noch nicht erstellt. Sie werden
  nur nacheinander nach weiterem Auftrag trainiert. Kein Commit/Push.

## 25.10.2026 – XGBoost-Aktualitätstest 2026 beauftragt

- **Auftrag/Plan:** XGBoost getrennt für CO₂ und EE; Training 2023–2025,
  Test 01.01.–23.09.2026 auf denselben Stunden wie OLS/HGB.
  Bestehendes Skript `train_hist_stage0.py --xgboost --test-2026` verwenden.
  Unveränderte Entwicklungsparameter/Features automatisch prüfen, keine
  Optimierung auf Testdaten, Vorverarbeitung nur aus Trainingsdaten, kein Clipping.
- **Ausgaben:** Separater Ordner `reports/xgboost_test2026_v1`; Modell- und
  Vorhersagedateien von Git ausgeschlossen. Vorherige Ergebnisse erhalten.
- **Grenzen:** Retrospektives ERA5/revidierte Daten/MaStR-Nettoleistungsproxy;
  kein operativer 72h-Test und kein vollständiges Testjahr 2026.
  Training und unabhängige Ergebnisprüfung folgen.

## 25.10.2026 – XGBoost-Aktualitätstest 2026 abgeschlossen und geprüft

- **Status:** Lauf war beim letzten Mal bereits durchgelaufen; Dokumentation
  und Prüfung waren wegen einer Nutzungslimit-Unterbrechung noch offen und
  wurden jetzt nachgeholt. Kein erneutes Training nötig, keine Dateien geändert.
- **Ergebnis (`reports/xgboost_test2026_v1/run.json`, `metrics_common.csv`):**
  Training 2023–2025 (26.280 CO₂-/26.304 EE-Zeilen), Test 01.01.–23.09.2026,
  je 6.384 Stunden, identische Stunden wie OLS und HGB.
  CO₂ MAE 39,5326, RMSE 50,0190 gCO₂eq/kWh, R² 0,90335.
  EE MAE 4,07769, RMSE 5,29431 Prozentpunkte, R² 0,92560.
- **Vergleich auf denselben 6.384 Stunden (`metrics_common.csv`, Pooled-Verfahren):**
  | Verfahren | CO₂ MAE | CO₂ R² | EE MAE | EE R² |
  |---|---|---|---|---|
  | HistGradientBoosting | 38,8932 | 0,9048 | 3,8966 | 0,9327 |
  | XGBoost | 39,5326 | 0,9033 | 4,0777 | 0,9256 |
  | Lineare Regression | 56,0141 | 0,8092 | 5,8830 | 0,8567 |
  | Mittelwert-Baseline | 115,3197 | 0,2916 | 13,7497 | 0,3182 |
  Auf diesem Teilzeitraum 2026 bleibt HistGradientBoosting knapp vor XGBoost;
  beide deutlich vor der linearen Regression und der Baseline.
- **Prüfung:** `diagnostics` im `run.json` zeigt `complete: true`, keine
  negativen CO₂-Werte, keine EE-Werte über 100 % (CO₂-Spanne 80,46–695,58,
  EE-Spanne 17,52–93,02 %). `source_sha256`/`script_sha256` vorhanden und
  verweisen auf unveränderte Eingabedateien. Alle 24 bestehenden Unit-Tests
  (`.venv-stage0/bin/python3 -m unittest discover -s tests`) bestanden.
  Parameter/Features entsprechen dem gespeicherten Entwicklungsmanifest,
  kein Tuning und kein Clipping auf den Testdaten.
- **Grenzen:** Retrospektives ERA5, revidierte Zielwerte, rekonstruierter
  MaStR-Nettoleistungsproxy; kein operativer 72h-Test; 2026 nur bis 23.09.
  erfasst, nicht als vollständiges Jahr auszuweisen. Unterschiede zwischen
  HGB und XGBoost auf dieser einen Stichprobe nicht signifikanzgeprüft.
- **Offen:** `.gitignore`-Erweiterung und `run.json`/Metrikdateien aus diesem
  Lauf sind noch nicht committet (nur `reports/xgboost_test2026_v1/*.joblib`
  und `predictions_*.csv` bleiben laut `.gitignore` ausgeschlossen).

## 25.10.2026 – As-issued-72h-Test aus dem Arbeitsplan entfernt

- **Entscheidung des Nutzers:** In Stufe 0 wird ausschließlich mit historischen
  ERA5-Wetterdaten weitergearbeitet. Archivierte Wettervorhersagen und ein
  ausgabezeitpunktgenauer 72-Stunden-Backtest werden nicht umgesetzt.
- **Folge:** Als nächstes werden die Merkmalsgruppen zur Forschungsfrage auf
  denselben retrospektiven Zeitfenstern verglichen. Regionale Modelle folgen
  erst danach. Bestehende Hinweise „kein operativer 72h-Test“ bleiben als
  wissenschaftliche Abgrenzung erhalten und sind kein offener Arbeitsschritt.
- **Formulierung:** Ergebnisse werden als retrospektive Schätzung bei bekanntem
  historischen Wetter bezeichnet, nicht als nachgewiesene 72h-Einsatzgüte.

## 25.10.2026 – HGB-Aktualitätstest 2026 beauftragt

- **Abgeschlossen:** `train_hist_stage0.py --test-2026` erfolgreich; zwei
  Modelle, 26.280 CO₂-/26.304 EE-Trainingszeilen, je 6.384 Teststunden.
  CO₂ MAE 38,89315, RMSE 49,63933 gCO₂eq/kWh, R² 0,904808.
  EE MAE 3,89662, RMSE 5,03454 Prozentpunkte, R² 0,932724.
- **Prüfung:** 24 Tests bestanden. Modell-Reload reproduziert sämtliche
  Vorhersagen, Quellhashes unverändert, Parameter/Features identisch und
  train-only Skalierung bestätigt. Separater pandas/NumPy-Check bestätigt
  alle OLS-Referenzspalten, exakt 6.384 aufeinanderfolgende Teststunden und
  unabhängig berechnete Kennzahlen. `git diff --check` bestanden.
- **Ergebnisgrenzen:** Keine negativen Vorhersagen, kein EE über 100 %;
  CO₂-Spanne 69,16–692,86, EE 18,14–93,62 %. HGB genauer als OLS auf
  diesen Stunden, noch kein XGB-Vergleich 2026 und kein Signifikanznachweis.
  CPU-Erkennungswarnung wie zuvor ohne Abbruch, ein Rechenthread.
  Keine anderen Verfahren trainiert, keine alten Ergebnisse überschrieben.

- **Plan/Umsetzung:** Nur HGB für CO₂/EE, Training 2023–2025, verfügbarer
  Testabschnitt 01.01.–23.09.2026. Skript um `--test-2026` erweitert,
  getrennte Ausgaben in `reports/hist_gradient_boosting_test2026_v1`.
  Parameter/Features werden unverändert gegen Entwicklungsmanifest geprüft;
  Vorverarbeitung nur aus passenden OLS-Trainingsdaten übernommen und geprüft.
  Exakt gleiche Bewertungsmaske, kein Tuning/Clipping. Andere Verfahren nicht
  neu trainieren. Ergebnisprüfung folgt nach Ausführung.
- **Grenzen:** Historisches ERA5, revidierte Zielwerte, rekonstruierter
  MaStR-Bestand; kein operativer 72h-Test. Teiljahr nicht als Ganzjahr ausweisen.

## 25.10.2026 – OLS-Aktualitätstest 2026

- **Abgeschlossen:** `train_linear_stage0.py --test-2026` und
  `verify_linear_stage0.py --test-2026` erfolgreich. Zwei Modelle, je
  6.384 Teststunden. Training: 26.280 geeignete CO₂-/26.304 EE-Stunden.
  CO₂ MAE 56,01406, RMSE 70,27760 gCO₂eq/kWh, R² 0,809198;
  EE MAE 5,88297, RMSE 7,34670 Prozentpunkte, R² 0,856739.
- **Prüfung:** 24 Tests bestanden; Quellhashes unverändert, zwei Modelle und
  sechs Kennzahlenzeilen unabhängig nachgerechnet. Wie früher matmul-Warnungen,
  aber alle Werte endlich und einsum-Nachrechnung stimmt auf maximal 3,69e-13
  überein. Rang 173 je Modell. `git diff --check` erfolgreich.
- **Grenzen:** Ohne Clipping 115 negative CO₂-Prognosen (Minimum −228,17),
  99 EE-Prognosen über 100 % (Maximum 126,25). Diese Schwäche unbeschränkter
  OLS ist dokumentiert, nicht nachträglich anhand des Tests korrigiert.
  Ergebnisse in `reports/linear_regression_test2026_v1`; alte Experimente
  unverändert. HGB/XGB für 2026 noch nicht trainiert. Kein Commit/Push.

- **Auftrag/Plan:** Nach Zustimmung zunächst nur OLS für beide Ziele:
  Training 2023–2025, Test auf verfügbarem 2026-Abschnitt, feste Einstellungen.
- **Vorprüfung:** Vorhandene V2-Datei 2026 enthält 6.384 Stunden vom
  01.01.2026 00:00 bis 23.09.2026 23:00 UTC. Beide Eignungsflags durchgehend
  gesetzt. Kein Nachladen, keine Ergänzung/Imputation fehlender späterer Monate.
- **Umsetzung:** Trainings-/Prüfskript um `--test-2026` ergänzt; nur für diesen
  Test ein Teiljahr erlaubt, stündliche lückenlose Zeitachse weiterhin geprüft.
  Getrennter Ergebnisordner; gleiche 136 Rohmerkmale/173 transformierte Spalten,
  Skalierung ausschließlich auf Training. Baselines als Referenzen unverändert.
- **Grenzen:** Retrospektives ERA5, revidierte Daten, MaStR-Nettoleistungsproxy,
  keine operative 72h-Prognose. Teiljahr nicht direkt mit Ganzjahr vergleichen.
  Training/Ergebnisprüfung stehen zum Zeitpunkt dieses Eintrags noch aus.

## 25.10.2026 – XGBoost-Test 2025 beauftragt

- **Abgeschlossen/geprüft:** Zwei Modelle trainiert; 26.280 CO₂- bzw. 26.304
  EE-Trainingsstunden, je 8.760 Teststunden. 24 Tests bestanden. Parameter und
  Features identisch zur Entwicklung, Skalierung nur aus Training bestätigt,
  unveränderte Quellhashes; gespeicherte Modelle erneut geladen und sämtliche
  Vorhersagen reproduziert. Keine Begrenzung der Vorhersagen.
- **Ergebnisse XGBoost:** CO₂ MAE 46,58959, RMSE 58,82175 gCO₂eq/kWh,
  R² 0,870600; EE MAE 5,06435, RMSE 6,42617 Prozentpunkte, R² 0,893477.
  Keine negativen CO₂-/EE-Werte oder EE-Werte über 100 % in diesem Test.
- **Vergleich:** Separates Vergleichsskript erfolgreich; identische Zeitstempel
  und Zielwerte aller drei Verfahren, Kennzahlen unabhängig aus gespeicherten
  CSV nachgerechnet. Float32-CSV-Toleranz wie zuvor rtol=1e-7, atol=1e-8.
  HGB hat 2025 bei beiden Zielen niedrigeren MAE/RMSE und höheres R² als XGB
  und OLS. Dies bestätigt die bisherige Rangfolge, nicht statistische Signifikanz
  oder generelle Optimalität. Keine Anpassung anhand des Abschlusstests.
- **Dateien:** XGB-Jahreskurven PNG/PDF im neuen Ergebnisordner;
  `reports/model_comparison_test2025_v1/` enthält Vergleichsdiagramme je Ziel
  (nur OLS/HGB/XGB) und `metrics_verified.csv`. Alle Läufe erfolgreich,
  `git diff --check` bestanden. 2026 unberührt, keine Commits/Pushes.
- **Einordnung:** Historisches ERA5 und revidierte Daten; kein operativer
  72h-Prognosetest. Jahreskurven zeigen alle Stunden ohne Glättung.

- **Plan/Umsetzung:** XGBoost getrennt für CO₂/EE mit 2022–2024 trainieren,
  2025 retrospektiv testen. `train_hist_stage0.py --xgboost --test-2025`.
  Einstellungen automatisch gegen Entwicklungsmanifest vergleichen: 100 Bäume,
  Tiefe 6, Lernrate 0,1, hist/max_bin 255, L2=1, Seed 42, kein Early Stopping.
  Gleiche Features, reine Trainingsskalierung und OLS-Bewertungsmasken;
  keine Optimierung nach Testwerten. 2026 ausgeschlossen.
- **Ausgabeplan:** Separater Ordner `reports/xgboost_test2025_v1`, Jahreskurven
  mit `plot_linear_year2025.py --xgboost`; Vergleich aller drei Verfahren mit
  `compare_stage0_models.py --test-2025`, nach unabhängiger Kennzahlenprüfung
  und identischen Teststunden. Kein Überschreiben früherer Experimente.

## 25.10.2026 – HGB-Test 2025 gestartet

- **Abgeschlossen:** `scripts/train_hist_stage0.py --test-2025` erfolgreich;
  zwei Modelle mit identischen Parametern/Features zum Entwicklungsdurchlauf.
  CO₂ 26.280, EE 26.304 Trainingszeilen; je 8.760 Teststunden.
- **Ergebnisse 2025:** CO₂ MAE 46,36665, RMSE 58,11031 gCO₂eq/kWh,
  R² 0,873711. EE MAE 4,84049, RMSE 6,13890 Prozentpunkte, R² 0,902788.
  Beide Ziele hier genauer als OLS; kein Signifikanz-/Optimalitätsnachweis.
- **Prüfungen:** 24 bestehende Tests bestanden. Modelle neu geladen und alle
  Vorhersagen reproduziert; Quellhashes unverändert, train-only Skalierung
  geprüft. Separater pandas/NumPy-Check bestätigt identische OLS-Zeitstempel,
  Ziele, Masken/Referenzspalten und unabhängig berechnete HGB-Kennzahlen.
  Keine negativen CO₂-Werte, kein EE außerhalb 0–100 % in diesem Test.
  CO₂-Spanne 120,17–729,03; EE 16,77–88,09. Kein Clipping.
- **Abbildungen:** `scripts/plot_linear_year2025.py --hist`: separate PNG/PDF
  für CO₂ und EE unter `reports/hist_gradient_boosting_test2025_v1/figures/`,
  alle 8.760 Stunden, keine Mittelung, nur HGB und tatsächliche Zielwerte.
- **Hinweis:** CPU-Erkennungswarnung der Umgebung; Training erfolgreich,
  Rechenthreads auf eins beschränkt. Keine Änderung an alten Experimenten,
  kein XGBoost-Training, kein Zugriff auf 2026, kein Commit/Push.

- **Auftrag:** Nur HistGradientBoosting, getrennt für CO₂ und EE, Training
  2022–2024 und retrospektiver Test 2025. Kein Training anderer Verfahren.
- **Umsetzung/Plan:** Bestehendes Skript um `--test-2025` erweitert, separater
  Ordner `reports/hist_gradient_boosting_test2025_v1`. Unveränderte Parameter
  und Features werden gegen den Entwicklungsdurchlauf geprüft. 100 Iterationen,
  Lernrate 0,1, maximal 31 Blätter, mindestens 20 Zeilen je Blatt, kein Early
  Stopping, Seed 42. Kein Tuning anhand 2025, kein Clipping.
- **Datenregeln:** Exakt die OLS-Trainingsvorverarbeitung und Bewertungsmaske
  für denselben Zeitraum; Skalierung gegen Trainingsmittel prüfen. Historisches
  ERA5, revidierte Ziele und MaStR-Nettoleistungsproxy unverändert. Kein realer
  72h-Test, 2026 ausgeschlossen. Ergebnisse/Diagramme anschließend prüfen.

## 25.10.2026 – Gewünschter Jahresverlauf statt Jahrestabelle

- **Korrektur/Auftrag:** Nutzer meinte ein Liniendiagramm für das ganze Jahr,
  nicht die zuvor erstellte Jahrestabelle. Zwei Jahresdiagramme erstellt.
- **Ausführung:** `scripts/plot_linear_year2025.py`, pandas/Matplotlib,
  vorhandene OLS-Testvorhersagen; kein Training, keine Datenaufbereitung.
  CO₂ und Grünanteil jeweils tatsächlicher Zielwert plus Vorhersage,
  Januar–Dezember 2025 in UTC, alle 8.760 Stunden ohne Aggregation/Glättung.
- **Prüfung:** Exaktes vollständiges Stundenraster, endliche Werte und
  unveränderte Quelldateihashes geprüft; CO₂-PNG visuell kontrolliert.
  Unplausible Vorhersagen bleiben sichtbar, physikalische Grenzen markiert.
- **Dateien:** `reports/linear_regression_test2025_v1/figures/`:
  `co2_jahresverlauf_2025` und `gruenanteil_jahresverlauf_2025` als PNG/PDF,
  separates Manifest. Vorhandene Tabellen und Wochenabbildungen nicht gelöscht.
- **Grenzen:** Stundenkurven im Jahresmaßstab dicht; keine geglätteten Daten
  als Stundenwerte ausgegeben. ERA5-Retrospektive, kein echter 72h-Test.
  Erster Lauf meldete temporären Matplotlib-Cache; unnötigen frühen Import
  entfernt, damit bestehende Cache-Konfiguration künftig zuerst greift.

## 25.10.2026 – Jahrestabelle 2025 zur linearen Regression

- **Status:** Auf Nutzerauftrag mit `scripts/table_linear_test2025.py`
  aus vorhandener `metrics_common.csv` erstellt. Kein Training, keine neuen Daten.
- **Darstellung:** Zwei Zeilen (CO₂/EE), jeweils vollständiges UTC-Testjahr
  2025 mit 8.760 Stunden, MAE/RMSE/R², Training 2022–2024 und Einheiten.
  Hinweis auf ERA5-Retrospektive, keinen realistischen 72h-Test und ungeclippte
  Vorhersagen aufgenommen. Keine Wochen-/Monatsunterteilung.
- **Dateien:** `reports/linear_regression_test2025_v1/figures/jahrestabelle_2025`
  als PNG/PDF und deutsch formatierte CSV (Semikolon, Dezimalkomma).
  CSV enthält zusätzlich Einheiten und Trainingszeitraum; Kennzahlen ungerundet.
- **Prüfung:** Genau eine Quellzeile je Ziel/Jahr/Verfahren, Stundenumfang
  und unveränderten Quellhash geprüft; PNG visuell kontrolliert. Bestehende
  Streudiagramme bleiben erhalten. Quellhash im separaten Manifest gespeichert.

## 25.10.2026 – Diagramme zum OLS-Test 2025

- **Status:** Auf Nutzerauftrag erstellt, ausgeführt und visuell geprüft.
- **Methode:** `scripts/plot_linear_test2025.py`, pandas und Matplotlib.
  Nur gespeicherte Testvorhersagen und Kennzahlen gelesen, kein Training.
  Je Ziel eine Abbildung mit Zeitverlauf, Jahresstreudiagramm und Kennzahlentabelle.
- **Auswahl:** Erste vollständige Montag–Sonntag-Kalenderwoche 2025,
  06.01. 00:00 bis 13.01. 00:00 exklusiv, Europe/Berlin, 168 Stunden.
  Kalenderregel vor Sichtung der Fehler festgelegt, keine Auswahl einer
  besonders guten Woche. Streudiagramm/Kennzahlen: alle 8.760 UTC-Teststunden.
- **Prüfungen:** Eindeutige geordnete Zeitstempel, Wochenumfang, Jahresumfang,
  Kennzahlen unabhängig nachgerechnet und unveränderte Quelldateihashes geprüft.
  Negative CO₂-Werte und EE über 100 % bleiben sichtbar, gleiche Achsenskalierung
  im Streudiagramm und Diagonale als perfekte Vorhersage. Beide PNG visuell geprüft.
- **Dateien:** `reports/linear_regression_test2025_v1/figures/` enthält
  `co2_test2025` und `gruenanteil_test2025`, jeweils PNG/PDF, sowie Manifest
  mit Quell-/Skripthashes, Softwareversionen und Auswahlregel.
- **Grenzen:** Tatsächlicher Zielwert meint den gespeicherten Referenzwert,
  nicht zwingend eine direkte Emissionsmessung. Retrospektives ERA5-Wetter,
  kein realistischer 72h-Test. Keine Baseline-/Fremdmodellkurven hinzugefügt.

## 25.10.2026 – Lineare Regression: separater Test 2025

- **Auftrag/Plan:** Nutzer beauftragt nur lineare Regression. Zwei Ziele,
  Training 2022–2024, Test 2025, 2026 ausgeschlossen. Unveränderte OLS-
  Einstellungen, Eingabespalten, Zieldefinitionen und Bewertungsregeln.
- **Umsetzung:** Bestehendes Skript um `--test-2025` ergänzt; neuer Ordner
  `reports/linear_regression_test2025_v1`, kein Überschreiben alter Ergebnisse.
  Kalenderkodierung fest, Skalierung ausschließlich auf Trainingszeilen.
  Durchschnitt/Vorwoche werden wie bisher nur als Referenzen mitberechnet.
- **Entscheidung:** Gemeinsame Maske inklusive gültigem Vorwochenziel bleibt
  unverändert für den späteren fairen Vergleich. Kein Tuning auf 2025.
- **Grenzen:** Retrospektives ERA5-Wetter und revidierte Daten; kein operativer
  72h-Test. 2025 ist im Neustart zurückgehalten, nicht zwingend in früheren
  archivierten Projektversuchen. Monatlicher MaStR-Nettoleistungsproxy bleibt.
- **Status:** Skript angepasst; Training und Ergebnisprüfung stehen noch aus.
- **Ausgeführt:** `.venv-stage0/bin/python scripts/train_linear_stage0.py --test-2025`
  erfolgreich; zwei Modelle gespeichert. Training umfasst 26.280 geeignete
  CO₂-Stunden bzw. 26.304 EE-Stunden; Test jeweils alle 8.760 UTC-Stunden 2025.
- **Ergebnisse:** CO₂ MAE 51,75096, RMSE 65,15282 gCO₂eq/kWh, R² 0,841246.
  EE MAE 6,40318, RMSE 8,01963 Prozentpunkte, R² 0,834100.
- **Prüfung abgeschlossen:** 24 bestehende Tests bestanden. Separates Skript
  `verify_linear_stage0.py --test-2025` reproduziert zwei Modelle mittels
  einsum (maximale Abweichung 5,68e-13), sechs Kennzahlenzeilen und Quellhashes.
  136 Rohmerkmale/173 transformierte Spalten stimmen exakt mit Entwicklung
  überein; Skalierung beider Ziele unabhängig gegen reine Trainingsmittel geprüft.
  Rang jeweils 173; `git diff --check` erfolgreich. Keine alten Ergebnisse ersetzt.
- **Warnungen/Grenzen:** Wie zuvor matmul-Warnungen (overflow/invalid/divide),
  trotz endlicher, unabhängig bestätigter Vorhersagen. Pandas-Prüfung meldet
  gemischte Typen einer nicht verwendeten Textspalte; numerische Prüfungen bestanden.
  Ohne nachträgliches Clipping: 58 negative CO₂-Werte (Minimum −137,39),
  112 EE-Werte über 100 % (Maximum 118,44 %). Physikalische Grenzen werden
  von unbeschränkter OLS nicht garantiert. Kein nachträgliches Tuning.
- **Nächster Schritt:** Andere Verfahren für 2025 nur nach weiterem Auftrag;
  2026 wurde nicht gelesen. Dokumentation lokal, kein Commit/Push.

## 25.10.2026 – XGBoost auf ausdrücklichen Auftrag trainiert

- **Status:** Training ausgeführt; Diagramme und unabhängige Kennzahlenprüfung anschließend gestartet.
- **Abschlussprüfung:** Beide Diagrammsätze als PNG/PDF erzeugt; Vergleich
  bestätigt exakt gleiche Zeitstempel und Zielwerte aller drei Verfahren.
  Kennzahlen unabhängig aus gespeicherten Vorhersagen nachgerechnet.
  Erster Prüflauf scheiterte an zu strenger Toleranz (MAE-Abstand 1,44e-8
  durch float32-CSV-Rundung); mit rtol=1e-7/atol=1e-8 bestanden.
  Keine Modell- oder Ergebnisanpassung. `git diff --check` bestanden.
- **Daten/Methode:** Unveränderte V2-Daten, 136 Rohmerkmale/173 transformierte
  Spalten wie lineare Regression. Zwei getrennte Ziele; sieben rollierende
  Fenster: 2015–2017 → 2018 bis 2021–2023 → 2024. 2025/2026 nicht gelesen.
  Trainingsskalierung aus passenden OLS-Folds übernommen und Trainingsmittel
  unabhängig geprüft. Keine neue Datenaufbereitung, kein Tuning oder Clipping.
- **Ausführung:** XGBoost 2.1.4 installiert und festgeschrieben;
  `scripts/train_hist_stage0.py --xgboost`. 100 Bäume, Tiefe 6, Lernrate 0,1,
  hist/max_bin 255, L2=1, vollständige Zeilen/Spalten, Seed 42, ein Thread,
  kein Early Stopping. Alle Parameter stehen in `reports/xgboost_v1/run.json`.
- **Entscheidung:** Feste Ausgangskonfiguration statt Optimierung anhand der
  Validierung. Gleiche Daten bedeuten nicht gleiche effektive Modellkomplexität;
  dies ist ein Vergleich dieser Konfigurationen, kein Optimalitätsnachweis.
- **Prüfungen:** 24 bestehende Tests bestanden; Eingabehashes unverändert,
  identische Bewertungsmasken mit OLS, alle 14 gespeicherten Modelle erneut
  geladen und Vorhersagen reproduziert. Endliche Vorhersagen geprüft.
- **Ergebnisse:** CO₂: n=61.161, MAE 48,82480, RMSE 61,27452 gCO₂eq/kWh,
  R² 0,820716. EE: n=61.176, MAE 4,40022, RMSE 5,86990 Prozentpunkte,
  R² 0,882673. HGB liegt insgesamt bei beiden Zielen etwas besser; kein
  statistischer Signifikanznachweis. XGBoost ist nicht automatisch überlegen.
- **Darstellung:** XGBoost-Einzeldiagramme sowie Vergleich OLS/HGB/XGBoost
  mit pandas/Matplotlib; Baselines bleiben auf Nutzerwunsch aus Diagrammen.
  Skripte `plot_linear_results.py --xgboost`, `compare_stage0_models.py`.
- **Grenzen:** Retrospektive ERA5-Untersuchung mit revidierten Daten und
  rekonstruiertem MaStR-Nettoleistungsproxy, kein realer 72h-Prognosetest und
  keine Garantie vollständiger historischer Informationsverfügbarkeit.
  Modelle/Prognose-CSV ignoriert; Dokumentation lokal, kein Commit/Push.

## 25.10.2026 – Markdown nicht mehr versionieren

- **Status:** auf ausdrücklichen Wunsch umgesetzt. Sieben bisher verfolgte
  .md-Dateien mit `git rm --cached` aus dem Index genommen, einschließlich
  AGENTS.md und README-Dateien. Lokale Inhalte unverändert erhalten.
- **Durchführung:** Vorher getrackte Pfade und leeren Staging-Diff geprüft;
  Indexänderung nach Sandbox-Freigabe. Vorhandene *.md-Ignore-Regel beibehalten.
- **Grenzen:** Löschungen sind nur für den nächsten Commit vorgemerkt;
  kein Commit/Push durchgeführt. Frühere Git-Commits enthalten weiterhin
  historische Markdown-Versionen. Keine Historienumschreibung.

## 25.10.2026 – HistGradientBoosting einzeln darstellen

- **Status:** auf Nutzerauftrag umgesetzt; Modellvergleich erst nach XGBoost.
- **Durchführung:** HGB-Plot zeigt ausschließlich HistGradientBoosting in
  Balken, Jahreslinien, Titel und Legende. `plot_linear_results.py --hist`
  erneut ausgeführt; CO₂-/EE-Diagramme jeweils als PNG und PDF aktualisiert.
- **Grenzen:** Nur Darstellung geändert; Vergleichskennzahlen bleiben
  gespeichert. Keine Änderung der Modelle, Daten oder Bewertungsstunden.

## 25.10.2026 – Baselines aus den Modellvergleichsdiagrammen ausgeblendet

- **Status:** Nutzerauftrag umgesetzt, reine Darstellungsänderung.
- **Durchführung:** scripts/plot_linear_results.py zeigt im linearen Bericht
  nur OLS, im HGB-Bericht HGB und OLS. Durchschnitt und Vorwoche aus Balken,
  Jahreslinien und Legenden entfernt. Beide Plot-Aufrufe erneut ausgeführt.
- **Ergebnis:** Vier aktualisierte PNG- und vier PDF-Dateien an bisherigen
  Pfaden. Baseline-Kennzahlen bleiben in Ergebnistabellen und Quelldateien;
  kein Training und keine Veränderung der Bewertungsstunden.
- **Abgrenzung:** Das separate historische Durchschnittsbaseline-Diagramm
  unter reports/mean_baseline_v1 ist kein Modellvergleich und bleibt erhalten.

## 25.10.2026 – HistGradientBoosting mit Matplotlib dargestellt

- **Status:** auf Auftrag erstellt, ausschließlich gespeicherte Kennzahlen.
- **Durchführung:** Bestehendes Plot-Skript um optionales `--hist` erweitert:
  `.venv-stage0/bin/python scripts/plot_linear_results.py --hist`.
- **Quelle:** reports/hist_gradient_boosting_v1/metrics_common.csv und run.json.
- **Ergebnis:** Je CO₂ und EE-Anteil eine PNG-/PDF-Abbildung unter
  reports/hist_gradient_boosting_v1/figures; MAE/RMSE/R² gepoolt und jährlich,
  Vergleich mit OLS und beiden Baselines. Zusätzlich CSV-Tabellen und Manifest.
- **Prüfung/Grenzen:** Identische Stichprobengrößen innerhalb jedes Jahres
  geprüft, Eingabehashes unverändert. Einheiten getrennt, negative R² sichtbar.
  Kein Training, keine Veränderung der Modelle/Daten und kein Zugriff auf Holdout.

## 25.10.2026 – HistGradientBoosting trainiert und verglichen

- **Status:** auf ausdrücklichen Auftrag ausgeführt; 14 getrennte Ziel/Fold-Modelle.
- **Daten:** V2 2015–2024, dieselben Merkmale und Eignungsflags wie OLS,
  dieselben gemeinsamen Bewertungsstunden (61.161 CO₂, 61.176 EE).
- **Methode:** 100 Iterationen, Lernrate 0,1, 31 Blätter, min_samples_leaf=20,
  L2=0, squared_error, random_state=42, early_stopping=False. Keine Optimierung.
  Gespeicherte trainingsangepasste OLS-Vorverarbeitung kopiert, 173 identische
  Eingabespalten. PV weiterhin netto. 2025/2026 nicht geladen.
- **Durchführung:** scripts/train_hist_stage0.py in .venv-stage0; pandas,
  sklearn 1.6.1, NumPy, joblib. Ergebnisversion reports/hist_gradient_boosting_v1.
  Neues Experiment überschreibt keine Vorversion. Git ignoriert neue Modelle
  und zeilenweise Prognosen. Archiv und vorbereitete Daten unverändert.
- **Prüfung:** 24 Tests bestanden; Hashes, Skaler-Trainingsmittel, Spaltenfolge,
  Zeitstempel/Ziele und alte Kennzahlen abgeglichen. Alle Modellvorhersagen
  nach Neuladen reproduziert. Acht gepoolte Kennzahlzeilen unabhängig aus
  gespeicherten Prognosen nachgerechnet. Warnung über physische Kernzahl im
  Sandbox-Kontext dokumentiert; Threads auf eins begrenzt.
- **Ergebnis:** HGB CO₂ MAE 48,75, RMSE 61,00, R² 0,822;
  EE MAE 4,28, RMSE 5,69, R² 0,890. Insgesamt besser als OLS und Baselines;
  beim CO₂-MAE 2020/2022 bleibt OLS besser. Keine nachträgliche Parameteränderung.
- **Grenzen/nächster Schritt:** Retrospektive ERA5-/Registeruntersuchung,
  kein zeitgetreuer operativer 72h-Test. Details in docs/stufe0_hist_gradient_boosting.md.
  XGBoost bleibt untrainiert und benötigt separaten Auftrag.

## 25.10.2026 – pandas-Auswertung und Matplotlib-Ergebnisdiagramme

- **Status:** auf ausdrücklichen Auftrag umgesetzt, ohne neues Training.
- **Ziel:** Ergebnisse beider linearen Regressionen tabellarisch und grafisch
  mit den vorhandenen Baselines darstellen.
- **Durchführung:** pandas 2.3.3 und Matplotlib 3.9.4 in .venv-stage0 installiert
  und in requirements-stage0.txt ergänzt. `scripts/plot_linear_results.py`
  liest ausschließlich metrics_common.csv und run.json des bestehenden Laufs.
- **Entscheidung:** Zwei Abbildungen, je Ziel getrennte Bereiche für MAE,
  RMSE und R²; oben gepoolt, unten jährliche Entwicklung. Baselines ebenfalls
  auf identischen Bewertungsstunden. Keine Vermischung der Fehlereinheiten.
- **Artefakte:** reports/linear_regression_v1/figures mit PNG/PDF,
  zielbezogenen CSV-Tabellen und Quellenhash-/Versionsmanifest.
- **Schutz:** Quellergebnisse vor/nach per SHA-256 geprüft; keine Änderung
  der Modelle, Trainingsdaten oder Kennzahlen, kein Zugriff auf 2025/2026.
- **Grenzen:** Visualisierung vorhandener retrospektiver Ergebnisse, keine
  neue Aussage über realistische 72h-Vorhersagen. Training bleibt bei NumPy/
  sklearn; pandas wird zunächst gezielt in der Ergebnisauswertung verwendet.

## 25.10.2026 – Bibliotheken des Altprojekts nachgesehen

- **Status:** geprüft, reine Bestandsauskunft auf Nutzerfrage.
- **Quelle/Durchführung:** Archivierte requirements.txt gelesen und Imports
  in archive/legacy_2026-10-20/src sowie app.py mit rg geprüft.
- **Ergebnis:** Unter anderem sklearn 1.6.1, XGBoost 2.1.4, NumPy 2.0.2,
  SciPy 1.13.1, pandas 2.3.3, joblib 1.5.3, matplotlib 3.9.4,
  Streamlit 1.50.0 gelistet. Archivierte lineare Regression importiert
  LinearRegression, StandardScaler und Pipeline aus sklearn.
- **Grenze:** Versionsliste belegt die archivierte Konfiguration, nicht die
  tatsächlich verwendete Laufzeit jedes historischen Experiments. Archiv
  unverändert; keine Installation und kein Training bei dieser Prüfung.

## 25.10.2026 – Lineare Regression und Vorwochenbaseline ausgeführt

- **Status:** vom Nutzer mit „lass mal machen“ ausdrücklich beauftragt und ausgeführt.
- **Ziel:** Zwei separate OLS-Ziele mit allen vorgesehenen Eingaben gegen zwei
  einfache Referenzen vergleichen. Keine A/B/C-Aufteilung und kein XGBoost.
- **Durchführung:** `scripts/train_linear_stage0.py`, sieben Entwicklungsfolds
  (2015–2017 → 2018 bis 2021–2023 → 2024), V2-Eingaben unverändert.
  173 transformierte Spalten nach Kalender-One-Hot und Entfernen Wochenende;
  numerischer Skaler nur auf jeweiligem Training gelernt. PV bleibt netto.
- **Umgebung:** Alte .venv nicht ausführbar, unverändert gelassen. Separate
  .venv-stage0 mit festgelegten Versionen in requirements-stage0.txt installiert.
  .gitignore nur um diese Umgebung und neue binäre/zeilenweise Artefakte ergänzt.
- **Vergleich:** Gleiche zielbezogene Trainingsmasken wie bisher; Vorwoche aus
  exaktem UTC-Zeitstempel −168h. Gemeinsame Bewertung ohne fehlende/geschätzte
  CO₂-Lagwerte: 61.161 CO₂- und 61.176 EE-Stunden; 27 zusätzliche CO₂-Ausschlüsse.
- **Ergebnis:** Gepoolte lineare Regression: CO₂ MAE 70,16, RMSE 87,47,
  R² 0,635; EE MAE 5,54, RMSE 7,10, R² 0,828. Insgesamt vor beiden Baselines.
  Keine Clipping-Korrektur: 94 negative CO₂-, 51 EE-Prognosen über 100 %
  auf der ursprünglichen Validierungsmaske. Kein finaler Produktionsfit.
- **Prüfung:** 22 Unit-Tests bestanden; Vorhersagen nach Joblib-Laden geprüft,
  Eingabehashes unverändert. Numerische Matrixproduktwarnungen trotz endlicher
  Ausgaben veranlassten unabhängige einsum-Nachrechnung durch
  `scripts/verify_linear_stage0.py`; Ergebnis in verification.json.
- **Artefakte/Dokumentation:** reports/linear_regression_v1 mit Modellen,
  Koeffizienten, Prognosen, Kennzahlen, Maskengrößen und Manifest;
  docs/stufe0_lineare_regression.md mit vollständigen Regeln/Grenzen.
- **Leakage/Grenzen:** 2025/2026 nicht gelesen. Kein zeitgetreuer 72h-Backtest,
  keine Publikationslatenzsimulation; ERA5/revidierte Ziele/MaStR-Proxy.
  Weitere Modelle und reale Vorhersagetests bleiben separate nächste Schritte.

## 25.10.2026 – Diagramm der Durchschnittsbaseline

- **Status:** ausgeführt auf Nutzerauftrag; reine Visualisierung.
- **Quelle:** Gespeicherte `pooled_metrics` aus `reports/mean_baseline_v1/run.json`,
  Bewertungsstunden 2018–2024, getrennte gültige Stichproben je Ziel.
- **Durchführung:** `python3 scripts/plot_mean_baseline.py`; Grafik unter
  `reports/mean_baseline_v1/kennzahlen_diagramm.svg`.
- **Entscheidung:** MAE/RMSE je Ziel getrennt wegen unterschiedlicher Einheiten;
  R² gemeinsam dimensionslos auf Skala 0–1. Balkenachsen beginnen bei null.
  Gepoolte Kennzahlen, nicht Mittelwerte jährlicher R²-Werte.
- **Prüfung:** SVG als XML erfolgreich geprüft, Werte direkt aus Ergebnisdatei.
  Matplotlib nicht installiert und `.venv/bin/python` nicht vorhanden;
  deshalb Standardbibliothek und SVG ohne Installation verwendet.
- **Grenzen:** Kein neuer Modellvergleich, kein Training, keine Änderung von
  Daten oder Kennzahlen. SVG nicht zusätzlich visuell gerendert geprüft.

## Eintragsvorlage

### Datum – Titel

- **Status:** geplant / ausgeführt / geprüft / verworfen
- **Ziel:**
- **Daten und Quellen:**
- **Entscheidung und Begründung:**
- **Alternativen und Grenzen:**
- **Durchführung:** Skript, Parameter, Versionen, Dateipfade
- **Prüfung und Schutz vor Data Leakage:**
- **Ergebnis:** nur tatsächlich beobachtete Ergebnisse
- **Offene Punkte und nächster Schritt:**

## 21.10.2026 – Dokumentationsregeln festgehalten

- **Status:** ausgeführt.
- **Ziel:** Nachvollziehbare Dokumentation des Neustarts für die Bachelorarbeit.
- **Durchführung:** Dieses Protokoll angelegt und in `AGENTS.md` verankert.
- **Ergebnis:** Regeln und Eintragsvorlage vorhanden. Keine Trainingsdaten
  aufbereitet und kein Modell trainiert.

## 22.10.2026 – MaStR in Stufe 0: nationale monatliche Leistung

- **Status:** Planänderung beschlossen und dokumentiert; Umsetzung noch offen.
- **Ziel:** Den Ausbau der Wind- und Solarleistung im Deutschland-Modell
  berücksichtigen, ohne bereits regionale Modelle aufzubauen.
- **Entscheidung:** Aus MaStR drei nationale Monatsreihen ab Januar 2015
  vorsehen: installierte PV-Leistung, Windleistung an Land und Windleistung auf
  See, jeweils in MW. Standorte werden in Stufe 0 nicht als Merkmale genutzt;
  räumliche Zuordnung folgt erst in Stufe 1.
- **Definition:** Gemeint ist der zu einem Monatsstichtag aktive Gesamtbestand,
  nicht nur der monatliche Zubau und nicht die Stromerzeugung. Bestand vor 2015
  mit einbeziehen; spätere Inbetriebnahmen addieren und Stilllegungen abziehen.
- **Datenbedarf:** Energieträger bzw. Technologie, Unterscheidung Onshore/Offshore,
  einheitliches Leistungsfeld, Inbetriebnahme, Stilllegung und Status.
  Historische Leistungsänderungen und unplausible Datumsangaben prüfen.
- **Begründung und Alternative:** Drei nationale Merkmale halten Stufe 0
  überschaubar und bilden Veränderungen des Anlagenbestands ab. Die bisherige
  Alternative ohne Anlagenleistung bleibt für einen späteren Vergleich sinnvoll;
  ein Genauigkeitsgewinn ist noch nicht belegt.
- **Historische Grenzen:** Ein aktueller MaStR-Export ist keine vollständige
  historische Datenversion. Rekonstruierte Bestände, fehlende Einträge und
  nachträgliche Korrekturen müssen als Einschränkungen dokumentiert werden.
- **Schutz vor Data Leakage:** Monatsstichtag und Verfügbarkeitsregel vorab
  festlegen. Keine späteren Inbetriebnahmen desselben Monats in frühere
  Stunden einfließen lassen. Nur zum Prognosestart bekannte Bestände verwenden;
  rekonstruierter historischer Bestand ist nicht automatisch damals bekannter
  Bestand. Falls historische Veröffentlichungsstände fehlen, die Einschränkung
  im Test ausdrücklich ausweisen.
- **Offen:** Leistungsfeld (Brutto/Netto), Monatsstichtag, historische Abdeckung
  und Veröffentlichungsverzögerungen prüfen, bevor Daten aufbereitet werden.
- **Durchführung/Ergebnis:** Nur dieses Protokoll aktualisiert. Keine Daten
  aufbereitet, keine Trainingspipeline implementiert und kein Modell trainiert.

## 22.10.2026 – Inhalt des MaStR-Exports geprüft

- **Status:** Dateiverzeichnis und Feld-Stichproben geprüft, keine Vollprüfung.
- **Quelle:** `/Users/ziaul-mustafa/Downloads/Gesamtdatenexport_20261020_26.2.zip`;
  offizielle Feldübersicht und Exporthilfe:
  https://www.marktstammdatenregister.de/MaStRHilfe/subpages/datenexport.html
- **Durchführung:** ZIP-Verzeichnis gelesen; die ersten 100 Solar-Einheiten
  in `EinheitenSolar_1.xml` und 100 Wind-Einheiten in `EinheitenWind.xml`
  mit Python-Standardbibliothek gelesen, ohne das Archiv zu entpacken.
- **Ergebnis:** 443 ZIP-Einträge; 66 Dateien `EinheitenSolar_*` und eine
  `EinheitenWind.xml`. Weitere Gruppen enthalten u.a. Biomasse, Wasser,
  Verbrennung, Kernkraft, Speicher, Gas, EEG-/KWK-Anlagen, Marktakteure,
  Netzanschlusspunkte und Katalogwerte.
- **Bestätigte relevante Felder:** `EinheitMastrNummer`, `Bruttoleistung`,
  `Nettonennleistung`, `Inbetriebnahmedatum`, `EinheitBetriebsstatus`,
  `Registrierungsdatum`, `DatumLetzteAktualisierung`; bei Wind zusätzlich
  `WindAnLandOderAufSee` und in der Stichprobe `DatumEndgueltigeStilllegung`.
- **Grenzen:** Feldvorhandensein beweist keine Vollständigkeit oder Richtigkeit.
  Solar-Stilllegungen wurden mit dieser kleinen Stichprobe nicht vollständig
  geprüft. Katalogcodes müssen anhand der enthaltenen Katalogwerte entschlüsselt
  werden. Monatsreihen liegen nicht fertig vor; sie müssten erst rekonstruiert
  werden. Registrierungsdatum und Inbetriebnahmedatum sind zu unterscheiden.
- **Ergebnis der Arbeit:** Keine Leistungsreihen erstellt, keine Rohdaten
  verändert und kein Training ausgeführt.

## 22.10.2026 – Alte Baseline anhand des Codes geprüft

- **Status:** geprüft, ohne Ausführung der alten Skripte.
- **Quelle:** `archive/legacy_2026-10-20/src/baseline_model.py`.
- **Ergebnis:** Die alte Baseline berechnet aus `train_2015_2022.csv` den
  durchschnittlichen erneuerbaren Erzeugungsanteil je Kombination aus Wochentag
  und lokaler Stunde. Diese bis zu 168 Mittelwerte werden für die Vorhersagen
  in `validation_2023.csv` verwendet. Bei fehlender Kombination dient der
  Gesamtmittelwert des Trainings als Ersatz.
- **Abgrenzung:** Das ist eine Wochentag-Stunden-Mittelwertbaseline, keine
  naive Vorwochenbaseline mit dem Einzelwert von vor 168 Stunden. Die zuvor
  für den Neustart vorgeschlagene Vorwochenbaseline ist ein anderer Ansatz.
- **Zielgröße damals:** Erneuerbarer Anteil in Prozent, nicht CO₂-Intensität.
- **Durchführung:** Nur Quelltext gelesen und Erkenntnis dokumentiert;
  keine Trainingsdaten aufbereitet und kein Modell trainiert.

## 22.10.2026 – Wettervorhersagearchive recherchiert

- **Status:** Offizielle Dokumentation geprüft; keine API-Datenabrufe oder
  Prüfung der tatsächlichen Vollständigkeit an unseren 23 Standorten.
- **Historical Forecast API:** Ab etwa 2022, modellabhängig. Verknüpft die
  ersten Stunden aufeinanderfolgender Läufe; keine vollständige 72-h-Prognose
  eines festen damaligen Prognosestarts.
  Quelle: https://open-meteo.com/en/docs/historical-forecast-api
- **Previous Runs API:** Feste Vorlaufzeiten von 1 bis 7 Tagen; überwiegend
  ab Januar 2024. Ausnahme GFS-Temperatur in 2 m ab März 2021. Geeignet für
  Vorlaufvergleiche, nicht ohne Weiteres für eine zusammenhängende Kurve aus
  einem einzelnen Lauf.
  Quelle: https://open-meteo.com/en/docs/previous-runs-api
- **Single Runs API:** Einzelne Läufe mit Initialisierungszeit über `run`;
  ECMWF IFS HRES 9 km ab März 2024, übrige Modelle laut Dokumentation ab
  02.04.2026. Daher Empfehlung, ECMWF IFS HRES als Kandidat für den
  realistischen 72-h-Test zu prüfen; noch keine endgültige Modellfestlegung.
  Quelle: https://open-meteo.com/en/docs/single-runs-api
- **Geplanter Ablauf:** Zuerst Zusammenhangstest mit Reanalyse ab 2015;
  anschließend realistischer Test mit archivierten Läufen und dort Bewertung
  nach Horizont. ERA5 ist eine Reanalyse, keine fehlerfreie Beobachtung.
  Der 168-h-Lag bleibt relativ zur Zielstunde.
- **Offen:** Alle benötigten Wettervariablen und Höhen, Einheiten, Stundenraster,
  23 Standorte, Lücken und Kosten/Zugangsbedingungen praktisch prüfen.
  Initialisierungszeit ist nicht Veröffentlichungszeit: Nur rechtzeitig
  verfügbare Läufe nutzen und Bereitstellungsverzögerungen berücksichtigen.
  Kandidat: Validierung ab März 2024 und Abschlusstest 2025, vorbehaltlich
  vollständiger Abdeckung und noch unbenutzter Testdaten. Keine 2025-Zielwerte
  im Training oder bei der Parameterauswahl dieses Tests verwenden.
- **Durchführung:** Nur Recherche und Dokumentation; keine Aufbereitung,
  kein Download von Wetterzeitreihen und kein Training.

## 22.10.2026 – Datenbestand für Stufe 0 lesend geprüft

- **Status:** ausgeführt; Bestands- und grundlegende Qualitätsprüfung.
- **Auftrag:** Dateien prüfen und dokumentieren, ohne Datenänderungen oder Training.
- **Durchführung:** Vollständige CSV-/JSON-Leseprüfung mit System-Python und
  Standardbibliothek; MaStR-Link geprüft. Keine alten Aufbereitungsskripte gestartet.
- **Ergebnis:** Siehe `docs/datenbestand_stufe0_2026-10-22.md` für Zeiträume,
  Variablen, Einheiten, Fehlwerte, SMARD-Versionskonflikte und Prüfgrenzen.
  CO₂: 103.461 Stunden, 218 als geschätzt markiert. Wetter: 23 Standorte,
  lückenlos bis 23.09.2026. SMARD-Zeitachsen bis 18.10.2026 vorhanden, aber
  Feldlücken und widersprüchliche Exportversionen. MaStR-Monatsreihen fehlen;
  Vorhersagearchiv enthält nur einzelne 2026-Abrufe.
- **Schutz vor Data Leakage:** Keine Modellauswahl, keine Zielwertoptimierung
  und kein Training. Spätere Auswahl von Datenversionen muss von ihrer
  damaligen Verfügbarkeit unterschieden werden.
- **Nächster Schritt (Empfehlung, nicht umgesetzt):** Datenregeln für
  SMARD-Revisionen/Fehlwerte und beide Zielgrößen festlegen. Keine automatische
  Bereinigung; Testzeiträume erst nach Abdeckungsklärung verbindlich festlegen.
- **Änderungen:** Nur Dokumentation erstellt/ergänzt. Keine Rohdaten verändert,
  keine Trainingsdaten gespeichert, keine Modelle trainiert.

## 22.10.2026 – Ergänzende Archiv-Inventur

- **Status:** ausgeführt, nur Dateilisten und ausgewählte Quelltexte/CSV-Köpfe gelesen.
- **Ergebnis:** Im alten Archiv sind nicht nur Rohdaten vorhanden, sondern auch
  aufbereitete SMARD-/Wettertabellen, berechneter Grünanteil, Kalendermerkmale,
  72-h-/168-h-Lags, alte Train-/Validierungs-/Testtabellen, acht Joblib-Modelle,
  Baseline-, Walk-Forward- und Testberichte sowie Download-, Trainings- und
  Prognoseskripte und die Streamlit-App.
- **Präzisierung:** Kalender und Grünanteil fehlen nicht grundsätzlich: Sie
  existieren für das alte Modell. Für den Neustart sind diese Artefakte noch
  nicht auf ihre Eignung geprüft oder übernommen. Alte Wettertabellen enthalten
  räumliche Mittelwerte, nicht die geplanten nationalen MaStR-Leistungsmerkmale.
- **Alte Fehlwertbehandlung im Code:** `prepare_smard.py` setzt leere
  Kernenergiewerte ab 16.04.2023 auf null. `clean_model_data.py` verwirft Zeilen
  ohne Grünanteilszielwert. Dies beschreibt die bisherige Implementierung,
  keine erneute fachliche Freigabe für den Neustart.
- **Fehlt für den neuen Aufbau:** Monatliche nationale MaStR-Leistungsreihen,
  durchgehendes geeignetes Vorhersagearchiv für den realistischen Test und ein
  geprüfter neuer Datenaufbau für beide Zielgrößen. CO₂-Rohdaten liegen außerhalb
  des Altarchivs unter `data/raw/electricitymaps/`.
- **Grenzen:** Modelle nicht geladen/ausgeführt und alte Ergebnisberichte
  nicht reproduziert. Dateiexistenz ist kein Nachweis ihrer wissenschaftlichen
  Eignung für den neuen Plan. Keine Rohdaten oder alten Artefakte verändert.

## 22.10.2026 – Extrapolation bei wachsender Anlagenleistung

- **Status:** Methodische Prüfung anhand offizieller Dokumentation; kein Experiment.
- **Befund:** Baum-XGBoost und HistGradientBoosting setzen außerhalb der
  gelernten Teilungsschwellen keine linearen Trends fort. Bei unveränderten
  übrigen Eingaben wird zusätzliche Leistung oberhalb des Trainingsmaximums
  nicht als fortlaufender Kapazitätseffekt extrapoliert. Das ist keine generelle
  Aussage, dass XGBoost-Ausgaben stets innerhalb des Zielwertbereichs bleiben.
- **Interaktionsmerkmal:** Strahlung × PV-Leistung ist ein sinnvoll zu prüfender
  physikalisch motivierter Proxy, keine gemessene PV-Erzeugung und keine
  garantierte Lösung der Baum-Extrapolationsgrenze. Es kann neue Kapazitäten mit
  geringerer Strahlung in bekannte Produktwerte überführen; oberhalb des
  Trainingsbereichs des Produkts bleibt das Problem bestehen.
- **Alternative:** Lineare Regression kann Trends fortsetzen, ist dabei aber
  nicht automatisch korrekt. Auch sie kann bei Strukturwandel unplausible
  CO₂-/Anteilswerte liefern. XGBoost bietet außerdem einen linearen Booster;
  die Aussage bezieht sich auf den geplanten Baumvergleich.
- **Empfehlung, noch nicht umgesetzt:** In den zeitlichen Validierungsfenstern
  Eingaben mit/ohne PV-Interaktion bei gleichen Modellen und Teststunden
  vergleichen. Anteil außerhalb des Trainingsbereichs protokollieren;
  Trainingsgrenzen ausschließlich aus dem jeweiligen Trainingsfenster bestimmen.
  Den finalen Test nicht zur Merkmalsauswahl verwenden. Tatsächliche historische
  MaStR-Leistungsreihen sind noch nicht erstellt; der konkrete Umfang des
  Bereichsüberschreitens ist daher noch nicht geprüft.
- **Quellen:** https://scikit-learn.org/1.5/modules/tree.html und
  https://xgboost.readthedocs.io/en/stable/parameter.html
- **Änderungen:** Nur Dokumentation, keine Merkmalsberechnung und kein Training.

## 22.10.2026 – Erste Rohdatenaufbereitung ausdrücklich beauftragt und ausgeführt

- **Status:** ausgeführt und technisch geprüft; kein Modelltraining.
- **Auftrag:** Nutzer: „lass daten tarning breit macen“. Damit ist die neue
  Datenaufbereitung autorisiert, nicht das Training. Alte vorbereitete Daten
  und Modelle bleiben ausgeschlossen.
- **Entscheidungen:** Rohquellen zeitlich auf UTC zusammenführen; 23 Wetterpunkte
  einzeln erhalten; CO₂- und EE-Ziele getrennt; SMARD-Rückblicke exakt 168 h;
  nationale monatliche MaStR-Nettonennleistungen rekonstruieren. Fehlwerte
  erhalten und Eignungsflags ausgeben statt pauschaler Imputation. Kernenergie
  ab 16.04.2023 mit dokumentierter struktureller Null-Regel.
- **Methodik und Quellen:** Siehe `docs/stufe0_aufbereitung.md` für sämtliche
  Regeln, Alternativen, Quellenbegründung, Einschränkungen und Befehle.
- **Durchführung:** `scripts/prepare_stage0.py`, Standardbibliothek Python 3.9.6.
  Ausgaben: `data/processed/stage0_v1_2026-10-22/`. XML direkt gestreamt;
  kein 23-GB-Entpacken. Rohdaten unverändert, kein Download neuer Quellen.
- **Ergebnisse:** 102.816 Stunden 2015–23.09.2026, 114 Eingabespalten,
  zwei Zielgrößen. 102.248 Stunden mit vollständigen Eingaben und beiden
  für den primären Vergleich gültigen Zielen. Zwölf Jahrestabellen, Monatsreihe,
  Qualitätsberichte, Konfliktliste, Feature-Positivliste, Splitplan und
  Rohdatenmanifest erstellt.
- **Prüfung:** Neun Unit-Tests bestanden. `scripts/verify_stage0.py` prüfte alle
  Ergebniszeilen und erneut die SHA-256-Prüfsummen aller 505 Eingabedateien.
  Keine Änderungen an den Rohdateien festgestellt.
- **Zeitplan:** Sieben Entwicklungsfenster mit je drei Trainingsjahren und
  folgendem Validierungsjahr (2018–2024), final 2022–2024 → 2025;
  2026 separat. Noch keine statistische Anpassung oder Auswertung der Modelle.
- **Wichtige Einschränkung:** Retrospektive ERA5-Untersuchung mit 2026-
  Registerrekonstruktion und revidierten SMARD-Dateien. Kein Beleg eines
  zeitgetreuen, leakagefreien operativen Backtests. Das gilt ausdrücklich auch
  trotz zurückversetzter Monatsstichtage. Publikationshistorien fehlen weiterhin.
- **Holdout-Präzisierung:** 2025 bleibt im Neustart ohne Modellauswertung;
  das Altprojekt hatte diesen Zeitraum aber bereits ausgewertet. Daher nicht
  als im gesamten Projekt historisch unangetastet bezeichnen.
- **Nächster Schritt:** Aufbereitungsregeln und MaStR-Plausibilität prüfen;
  Training erst auf ausdrücklichen Auftrag. Keine Freigabe für operative
  Horizontevaluation ohne archivierte As-issued-Wetterdaten.

## 22.10.2026 – Sonnenscheindauer heruntergeladen und V2 erstellt

- **Status:** ausgeführt und geprüft; ausdrücklich vom Nutzer beauftragt.
- **Quelle:** Open-Meteo Historical Weather API, `models=era5`, stündlich,
  Variable `sunshine_duration`, Sekunden, UTC. Definition und Grenzen siehe
  `docs/stufe0_sonnenscheindauer.md` und https://open-meteo.com/en/docs/historical-weather-api.
- **Durchführung:** `python3 scripts/add_sunshine_stage0.py`; 276 rohe
  Jahresantworten für 23 Standorte gespeichert. Zeitraum 2015–23.09.2026.
- **Ergebnis:** 2.364.768 neue Werte, lückenlos und im Bereich 0–3600 s.
  Neue Version `data/processed/stage0_v2_sunshine/` mit 102.816 Stunden und
  137 Eingabespalten. Neue Rohdaten in `data/raw/open_meteo_sunshine_era5/`.
- **Zeitbezug:** Sonnenscheindauer ist modellbasiert abgeleitet und beschreibt
  die vorangegangene Stunde zum API-Zeitstempel. Explizite Spaltennamen
  `sunshine_duration_preceding_hour_s`, keine Umdeutung zur beginnenden Stunde.
  Sonnenstrahlung und alle übrigen alten Spalten unverändert beibehalten.
- **Prüfung:** Zeitraster, Einheiten, Rasterkoordinaten, fehlende Werte und
  Wertebereich geprüft. Alle Jahrestabellen vollständig erneut verglichen;
  V1 und neue Rohdaten per Hash kontrolliert. 14 Unit-Tests bestanden.
- **Vorhersage-Stichprobe:** ECMWF-Single-Run für Berlin am 01.06.2025 00 UTC:
  HTTP 200, 72 Zeitstempel, 71 gültige Werte, Initialisierungsschritt leer.
  Kein Nachweis eines lückenlosen Archivs. Dokumentation bezeichnet ältere
  ECMWF-Läufe als Hindcasts; damalige tatsächliche Verfügbarkeit bleibt offen.
  Quelle: https://open-meteo.com/en/docs/single-runs-api.
- **Grenzen:** Keine Prüfung des Modellnutzens und kein Training. V1 bleibt
  unverändert. MaStR-Abgleich gehört nicht zu diesem Auftrag und bleibt offen.

## 22.10.2026 – MaStR mit SMARD-Jahresleistungen verglichen

- **Status:** auf ausdrücklichen Auftrag ausgeführt; Plausibilitätsprüfung,
  keine automatische Korrektur, kein Training.
- **Ziel:** Nationale PV-/Onshore-/Offshore-Nettoleistungen auf auffällige
  Abweichungen zu amtlichen Jahresangaben prüfen.
- **Daten/Quellen:** Vorhandene MaStR-Monatsreihe in V2; SMARD DE, Serien
  188/186/4076, 2015–2026, MW. Konfiguration und deutsche Beschreibungen
  von www.smard.de zusätzlich geladen. 41 JSON-Rohantworten unter
  `data/raw/smard_capacity_audit_2026-10-22/`. Lizenzprüfung dieser
  Rohantworten nicht separat durchgeführt; keine externe Veröffentlichung.
- **Durchführung:** `python3 scripts/check_mastr_smard_capacity.py`,
  Python-Standardbibliothek. Recherche über SMARD-Wikiseite und öffentliche
  Anwendung, anschließend Jahres-API verwendet. Quell-URLs und Hashes im
  Ergebnismanifest `reports/mastr_smard_capacity_2026-10-22/audit.json`.
- **Entscheidung:** 2015–2024 zum ausdrücklich beschriebenen 1. Januar
  vergleichen; sechs Werte 2025–2026 nur nebeneinanderstellen, da der
  fachliche Stichtag ab 2025 nicht ausdrücklich bestätigt ist. Keine
  Identität der Grundgesamtheit unterstellen (SMARD-Beschreibung ab 1 MW,
  MaStR alle Größen). Ab 2025 gemeinsame MaStR-Datenbasis beachten.
- **Ergebnis:** 36 Zeilen in `comparison.csv`, davon 30 mit Differenzen:
  PV −9,12 bis −2,21 %, Onshore −6,06 bis +1,87 %, Offshore +0,20 bis
  +9,34 %. Ursachen nicht eindeutig bestimmt; keine pauschale Freigabe.
- **Prüfung/Leakage:** Serien, Region, Einheit, Jahre und Eindeutigkeit
  geprüft; MaStR-Eingabedatei bytegleich. Monatszwischenwerte und damalige
  Veröffentlichungshistorie damit nicht validiert. Kein Zugriff auf
  Modellergebnisse zur Datenkorrektur, vorbereitete Daten unverändert.
- **Dokumentation/Alternativen:** `docs/stufe0_mastr_smard_abgleich.md`.
  Keine automatische Skalierung. Alternative ohne Kapazitätsmerkmale erst
  später auf unabhängigen Testdaten vergleichen.
- **Offen:** PV-Leistungsbezug, tatsächlicher SMARD-Erfassungsumfang und
  fachliche Stichtage ab 2025 klären. Monatliche Rekonstruktion weiterhin
  als retrospektiven Proxy behandeln, nicht als zeitgetreue Historie.

## 22.10.2026 – PV-Abweichung 2018 vertieft geprüft

- **Status:** ausgeführt und geprüft auf Auftrag „lass mal prüfen die Daten“.
- **Ziel:** Brutto/Netto, Ausschlüsse, Stilllegungen und Stichtagsrand als
  mögliche Ursachen des PV-Abstands untersuchen; keine Datenkorrektur.
- **Durchführung:** `python3 scripts/audit_pv_2018.py`, Standardbibliothek,
  6.590.938 Solar-XML-Einträge des vorhandenen MaStR-ZIP vollständig gestreamt.
  Auswahlregeln der bestehenden Rekonstruktion nachgebildet. Nur aggregierte
  Ergebnisse unter `reports/mastr_smard_capacity_2026-10-22/pv_2018_diagnostic.json`.
- **Ergebnis:** Anfang 2018: SMARD 42.804 MW; MaStR netto 38.898,83 MW
  (−9,12 %), brutto für denselben Bestand 42.404,74 MW (−0,93 %).
  Rund 90 % der bisherigen Lücke entsprechen numerisch dem Brutto-Netto-Abstand.
  Leistungsbezug als starke Hypothese, nicht als bewiesene SMARD-Ursache.
- **Weitere Prüfungen:** 1.684.341 damals aktive Einheiten; keine fehlenden
  Bruttowerte. Unplausible Frühdaten nur 1,027066 MW netto ausgeschlossen.
  Stichtags-Inbetriebnahmen 5,52936 MW. Heute stillgelegte, damals aktive
  Einheiten mit 220,73 MW sind enthalten. Keine Erklärung der großen Lücke
  durch diese Ausschlüsse oder den Stichtagsrand.
- **Korrektur früherer Einordnung:** Allgemeiner SMARD-Hinweis ab 1 MW ist
  keine bestätigte Filterregel für einzelne PV-Registereinheiten. Nur Einheiten
  ab 1 MW ergäben lediglich 10.114,59 MW; dies wäre keine passende Korrektur.
- **Prüfung/Schutz:** Netto-Summe reproduziert vorhandene CSV auf <0,00001 MW;
  deren SHA-256 vor/nach identisch. ZIP-Hash gespeichert. 14 bestehende
  Unit-Tests bestanden (keine speziellen neuen Diagnosetests). Kein Training,
  keine Modell-/Holdoutauswertung, keine Änderung der vorbereiteten Daten.
- **Quellen/Grenzen/Empfehlung:** Amtliche Definitionsunterlagen und Details
  in `docs/stufe0_mastr_smard_abgleich.md`. Keine automatische Umstellung auf
  Bruttoleistung allein wegen besserer Übereinstimmung. Baseline ohne MaStR
  als nächster Schritt möglich; konkrete historische SMARD-Definition und
  gelöschte/historisch geänderte Anlagen weiterhin offen. Diagnose gilt 2018.

## 22.10.2026 – Durchschnittsbaseline implementiert und bewertet

- **Status:** ausgeführt, vom Nutzer ausdrücklich mit „mach“ beauftragt.
- **Ziel:** Einfache trainierbare Referenz für CO₂ und EE-Anteil schaffen.
- **Daten:** V2-Jahrestabellen 2015–2024; Zielherkunft Electricity Maps/SMARD.
  Zeitstempel, zwei Ziele und vorhandene zielbezogene Eignungsflags gelesen.
  Keine Wetter-/MaStR-Werte als lernende Eingaben.
- **Methode:** 168 Mittelwerte je Ziel aus Wochentag/Stunde Europe/Berlin,
  ausschließlich Trainingsdaten. Vorhandene UTC-Jahresfolds: drei Jahre
  Training, Folgejahr Validierung, 2018–2024. Modell jährlich unverändert.
- **Maskenentscheidung:** Bestehende zielbezogene Eignungsflags für Fit und
  Bewertung verwenden; diese schließen auch unvollständige andere Merkmale
  aus, um die gemeinsame Modellvergleichsstichprobe zu erhalten. CO₂-
  Schätzwerte nicht bewertet. Keine fehlenden Zielwerte erfunden.
- **Durchführung:** `python3 scripts/train_mean_baseline.py`; neue Tests
  `tests/test_mean_baseline.py`; Ergebnisse `reports/mean_baseline_v1/`.
  Quelle-/Skripthashes, Gruppenmittel, Stichprobengrößen und Prognosen gespeichert.
- **Ergebnis:** Sieben Entwicklungsfolds abgeschlossen. Erstes Jahr 2018:
  CO₂ MAE 92,24, RMSE 120,25 gCO₂eq/kWh, R² −0,011;
  EE MAE 9,67, RMSE 12,32 Prozentpunkte, R² 0,117.
  Vollständige Tabelle und Interpretation in `docs/stufe0_durchschnittsbaseline.md`.
- **Prüfung:** 19 Tests bestanden. Zeitraster/Eindeutigkeit und unveränderte
  Eingabehashes geprüft; 2025/2026 nicht geöffnet. Keine anderen Modelle
  trainiert, kein Hyperparametertuning. Validierungswerte beeinflussen die
  jeweiligen Trainingsmittel nicht.
- **Grenzen:** Retrospektive Jahresvalidierung revidierter Daten, kein
  as-issued 72h-Backtest; Publikationslatenzen nicht simuliert. Kalenderbaseline
  benötigt weniger Informationen als spätere Wetter-/Marktmodelle. Für reine
  Verfahrensvergleiche bekommen diese später identische Merkmalsgruppen.
- **Nächster Schritt:** Ergebnisse gemeinsam prüfen; weitere Modellverfahren
  nur auf Auftrag umsetzen. Abschlusstest 2025 bleibt im Neustart unbewertet.

## 25.10.2026 – Voraussetzungen einer 72-Stunden-Vorhersage geprüft

- **Status:** nur Bestand und Archiv geprüft; keine Daten aufbereitet, kein
  Modell trainiert und keine Vorhersage erzeugt.
- **Ziel:** Klären, wie die alte XGBoost-Pipeline SMARD-Werte von 168 Stunden
  vorher verwendete und welche Eingaben für einen ungesehenen Zeitraum vom
  24.09. bis 26.09.2026 benötigt werden.
- **Alte Pipeline:** `archive/legacy_2026-10-20/src/predict_next_72h.py`
  ordnete jeder Zielstunde exakt die SMARD-Stunde `Zielzeit - 168 Stunden` zu.
  Verwendet wurden EE-Anteil, erneuerbare und gesamte Erzeugung, Netzlast,
  Onshore-/Offshore-Wind, Solar, Gas, Stein- und Braunkohle. Das alte Modell
  sagte ausschließlich den EE-Anteil voraus und nutzte räumlich gemittelte
  Wetterwerte.
- **Aktuelles finales XGBoost-Modell:** Training laut Run-Metadaten von
  01.01.2015 00:00 UTC bis 23.09.2026 23:00 UTC; 136 Eingangsmerkmale und
  getrennte Modelle für CO2-Intensität und EE-Anteil. Die 13 Energiemerkmale
  bestehen aus zwölf Erzeugungsarten sowie Netzlast, jeweils um 168 Stunden
  verschoben.
- **Datenprüfung:** Für einen UTC-Zielblock 24.09.2026 00:00 bis 26.09.2026
  23:00 werden SMARD-Werte vom 17.09.2026 00:00 bis 19.09.2026 23:00 benötigt.
  Diese 72 Ursprungsstunden sind vorhanden. Die aufbereitete Tabelle endet
  erwartungsgemäß am Trainingsende und enthält keine Zielzeilen danach.
- **Wetterprüfung:** Im Archiv vorhandene ausgegebene 72-Stunden-Prognosen
  beginnen erst am 29.09.2026, außerdem am 08.10. und 18.10.2026. Eine damals
  gespeicherte Wettervorhersage für 24.–26.09.2026 wurde nicht gefunden.
- **Bewertung:** Der UTC-Zielblock liegt vollständig außerhalb des Trainings.
  Für die drei lokalen Kalendertage 24.–26.09. wäre der aktuelle Trainings-
  cutoff dagegen um zwei Stunden zu spät, weil 23.09. 22:00/23:00 UTC bereits
  dem 24.09. in Europe/Berlin entsprechen. Für einen echten damaligen
  Prognosetest fehlt die as-issued Wetterprognose; ERA5 wäre nur eine
  retrospektive Simulation mit tatsächlich eingetretenem Wetter.

## 25.10.2026 – Wege zum erneuten Rohdatenabruf geprüft

- **Status:** vorhandene Download-Skripte und Schnittstellen geprüft; keine
  Archivdaten kopiert, keine API aufgerufen und keine Daten aufbereitet.
- **SMARD:** Das Altskript `download_smard_latest.py` sendet einen POST an den
  Download-Manager der SMARD-Webseite. Region DE, Stundenauflösung und die
  Modul-IDs für zwölf Erzeugungsarten beziehungsweise vier Lastreihen werden
  angefordert. Für die neue Vorhersage müssen daraus nur die tatsächlich
  benötigten Erzeugungsreihen und die Netzlast für `Zielzeit - 168 h` frisch
  als unveränderte CSV-Rohdaten gespeichert werden. Die Schnittstelle ist eine
  von der Webanwendung verwendete Download-Schnittstelle, keine zugesicherte
  stabile öffentliche API.
- **Wetter:** Das Altskript `download_weather_forecast.py` ruft die öffentliche
  Open-Meteo Forecast API für 23 Punkte und 72 Stunden ab. Es lädt Temperatur,
  Bewölkung, Wind in 100 m und Kurzwelleneinstrahlung. Für das aktuelle Modell
  fehlt dort Sonnenscheindauer; außerdem dürfen die 23 Punktreihen nicht wie
  beim Altmodell gemittelt werden. Für einen retrospektiven ERA5-Lauf können
  dieselben fünf Größen über die Open-Meteo Archive API frisch geladen werden.
- **CO2-Ziel:** `download_electricitymaps_full.py` lädt stündliche, erzeugungs-
  bezogene Lebenszyklus-CO2-Intensität für DE über
  `/v4/carbon-intensity/past-range`; der Schlüssel kommt aus `.env`. Diese
  Werte dürfen erst nach gespeicherter Prognose zur Bewertung geladen werden,
  nicht als Eingabe für die vorhergesagten 72 Stunden.
- **Anlagenleistung:** MaStR wurde nicht per API geladen. Grundlage war der
  manuell heruntergeladene Gesamtdatenexport der MaStR-Webseite. Ein neuer
  Gesamtexport wäre ein neuer Register-Snapshot und kann rückwirkend vom alten
  Snapshot abweichen; deshalb Quelle, Abrufdatum und Hash einfrieren.
- **Kalender:** Stunde, Wochentag, Monat, bundesweite Feiertage und angenäherte
  Tageslänge werden lokal berechnet und nicht heruntergeladen.
- **Bewertung:** Ein frischer Abruf reproduziert nicht automatisch denselben
  Datenstand, weil SMARD, Electricity Maps und MaStR nachträglich revidiert
  werden können. Für 24.–26.09.2026 kann die Open-Meteo Archive API tatsächliches
  Wetter liefern, aber keine am 23.09. gespeicherte Vorhersage ersetzen.

## 01.11.2026 – Day-Ahead-Preis als Zusatzmerkmal für CO2-Modell beauftragt

- **Auftrag:** Explizit durch den Nutzer beauftragt: Day-Ahead-Spotpreis als
  zusätzliches Eingabemerkmal für das CO2-Modell ergänzen und komplett neu
  trainieren (kein inkrementelles Nachtrainieren möglich, da
  HistGradientBoostingRegressor mit `warm_start` nur weitere Bäume auf
  demselben Merkmalsschema erlaubt, keine neue Spalte). Grünanteil-Modell
  bewusst unverändert gelassen, nicht Teil des Auftrags.
- **Geplant:** Preis-Rohdaten (`data/raw/energycharts_price/20261027T203022Z/`,
  bereits vorher heruntergeladen) zu einer Stundenspalte `price_eur_mwh_lag168h`
  aufbereiten, analog `energy_lag_time_utc` (Zielzeit − 168h) wie die übrigen
  Energiemerkmale, damit der Wert zum Vorhersagezeitpunkt für das gesamte 72h-
  Fenster garantiert bekannt war (der tatsächliche Day-Ahead-Preis des Zieltags
  wäre dagegen für Stunde 48/72 eines einmalig ausgegebenen 72h-Fensters noch
  nicht veröffentlicht). Bestehende Skripte `train_linear_stage0.py` und
  `train_hist_stage0.py` als Kopien mit neuem Datenpfad wiederverwenden, nicht
  die Originale ändern (bestehende Report-Ordner bleiben unangetastet).
- **Ausgeführt:** Vor Beginn `.venv-stage0/bin/python -m unittest discover -s
  tests -q` (26 Tests bestanden). Neues Skript `scripts/add_price_stage0.py`
  erstellt: liest alle Preis-JSON-Dateien (Zonenwechsel DE-AT-LU→DE-LU
  unverändert übernommen), ordnet jeder Zeile den Preis zur Stunde
  `energy_lag_time_utc` zu, schreibt Ergebnis nach
  `data/processed/stage0_v3_price/` (alle Altspalten unverändert, neue Spalte
  zusätzlich; unabhängiger Rückvergleich alt/neu im Skript). Dabei entdeckt:
  die Preisdaten 2025/2026 liegen teils in 15-Minuten-Auflösung vor (EU-weite
  Marktumstellung); diese Werte wurden zur vollen Stunde gemittelt, um mit dem
  bestehenden Stundenraster kompatibel zu bleiben — eigene Entscheidung, nicht
  vom Nutzer vorgegeben, hier dokumentiert statt verschwiegen.
  Zwei Trainingsskript-Kopien erstellt (`train_linear_price_stage0.py`,
  `train_hist_price_stage0.py`), jeweils nur Datenpfad, Report-Namen und
  Merkmalsanzahl (136→137) gegenüber dem Original geändert; Logik sonst
  identisch. Beide Skripte zuerst für die sieben Entwicklungsfolds
  (2018–2024), danach mit `--test-2025` für den unabhängigen Abschlusstest
  ausgeführt.
- **Geprüft:** Erste Woche Januar 2015 hat keinen Preis (Lag reicht in
  Dezember 2014, vor Beginn der Preis-Rohdaten 2015-01-01) — betroffene Zeilen
  beim Training ausgeschlossen statt erfunden; davon waren nur 2 Zeilen
  überhaupt für das CO2-/Grünanteil-Training zulässig (restliche Stunden
  bereits durch andere Eignungsflags ausgeschlossen). Im 2025-Testjahr keine
  fehlenden Preisstunden. Bestehende Mittelwert-/Vorwochen-Kennzahlen in
  beiden neuen Läufen exakt identisch mit den unveränderten Altwerten
  (Skript-interner Vergleichscheck bestanden); das bestätigt, dass nur die
  neue Preisspalte etwas verändert hat. Während des linearen Trainings
  traten `RuntimeWarning`-Meldungen (Overflow/division durch null im
  Matrixprodukt) auf, vermutlich durch Multikollinearität der neuen
  Preisspalte mit bestehenden Merkmalen in einzelnen Entwicklungsfolds;
  alle `assert np.isfinite(...)`-Prüfungen im Skript bestanden trotzdem, die
  gepoolten OLS-Kennzahlen änderten sich nur geringfügig (CO2-MAE 70,16→70,29).
  Dies betrifft nur die lineare Vergleichsmethode, nicht das hier relevante
  HistGradientBoosting-Modell; nicht weiter untersucht, da außerhalb des
  Auftrags. Alle 26 bestehenden Unit-Tests nach Abschluss erneut bestanden.
- **Ergebnisse (gepoolt, CO2-Ziel, HistGradientBoosting):**
  Entwicklung 2018–2024: MAE 48,34 / RMSE 60,61 / R² 0,825
  (vorher ohne Preis: MAE 48,75 / RMSE 61,00 / R² 0,822).
  Unabhängiger 2025-Test: MAE 45,88 / RMSE 57,64 / R² 0,876
  (vorher ohne Preis: MAE 46,37 / RMSE 58,11 / R² 0,874).
  Kleine, aber auf Entwicklung und unabhängigem Test gleichgerichtete
  Verbesserung in dieselbe Richtung.
- **Grenzen:** Nur das CO2-Modell wurde erweitert und neu trainiert; das
  bestehende Grünanteil-Modell ist unverändert (ein Nebenprodukt für
  Grünanteil wurde zwar mitberechnet, da beide Ziele im selben Skriptlauf
  verarbeitet werden, aber nicht genutzt und nicht als Ergebnis gewertet).
  Verbesserung ist klein (unter 1,5 % relative MAE-Reduktion) und beruht auf
  genau einer zusätzlichen Spalte ohne weitere Abstimmung; keine Aussage zur
  operativen Güte mit echter Day-Ahead-Preis-Verfügbarkeit zum Ausgabezeitpunkt
  über den gesamten 72h-Horizont getroffen — das neue Merkmal ist bewusst mit
  168h-Lag eingesetzt, nicht mit dem tatsächlichen Preis des Zieltags.
  Kein finales Produktionsmodell (2015–23.09.2026) mit diesem Merkmal trainiert
  und kein Dashboard/Inferenzskript angepasst; das wäre ein separater,
  eigener Auftrag.

## 01.11.2026 – Vergleichsdiagramm MAE/RMSE/R² angefordert

- **Auftrag:** Diagramm, das HistGradientBoosting mit/ohne Preis über MAE,
  RMSE und R² vergleicht.
- **Ausgeführt:** `scripts/plot_price_comparison.py` erstellt; liest die
  gepoolten CO2-Kennzahlen direkt aus `reports/hist_gradient_boosting_test2025_v1/run.json`
  und `reports/hist_gradient_boosting_price_test2025_v1/run.json` (unabhängiger
  2025-Test, keine neu berechneten Zahlen). Drei Teildiagramme (eigene Achse je
  Kennzahl statt einer gemeinsamen Skala, da Einheiten unterschiedlich), zwei
  Balken je Kennzahl. Ausgabe `reports/price_feature_comparison_v1/co2_mae_rmse_r2.png`
  plus `values.json` mit den verwendeten Rohwerten und Quellpfaden.
- **Geprüft:** Werte im Diagramm (MAE 46,37→45,88; RMSE 58,11→57,64;
  R² 0,874→0,876) stimmen mit den bereits dokumentierten 2025-Testwerten
  überein. Keine neue Berechnung, reine Visualisierung bestehender Ergebnisse.

## 01.11.2026 – Finales Preis-Modell mit Trainingsende 30.06.2026 (Schritt 1 von 3)

- **Auftrag:** Nutzer plant einen Vergleich Vorhersage vs. tatsächliche
  CO2-Intensität aus Electricity Maps bis 30.06.2026. Drei Schritte verabredet:
  (1) finales Preis-Modell mit Trainingsende 30.06.2026 fertigstellen,
  (2) Istwerte von Electricity Maps für die Zeit danach laden,
  (3) Vergleich rechnen. Hier nur Schritt 1.
- **Geplant:** Analog zu `train_final_linear_stage0.py` /
  `train_final_boosting_stage0.py`, aber auf `data/processed/stage0_v3_price`
  (mit Preis-Merkmal) und Trainingsende 2026-06-30T23:00:00Z statt
  2026-09-23T23:00:00Z, damit Juli 2026 und danach für einen späteren
  Vergleich ungesehen bleiben. Keine neuen Rohdaten nötig, nur ein früherer
  Cutoff auf bereits vorhandenen, aufbereiteten Daten.
- **Ausgeführt:** Zwei neue Skripte erstellt: `train_final_linear_price_stage0.py`
  und `train_final_boosting_price_stage0.py` (Kopien der Originale, Datenpfad,
  137-Merkmal-Prüfung, Cutoff und Preis-Lücken-Filter wie bei den bisherigen
  Preis-Trainingsskripten). Beide ausgeführt. Finales lineares Modell:
  CO2-Training 100.270 Zeilen, Grünanteil 100.368 Zeilen, volle Rangzahl 174
  (keine Kollinearitätsprobleme trotz der zuvor beobachteten Warnungen).
  Finales HistGradientBoosting-Modell auf denselben Zeilen und derselben
  wiederverwendeten Skalierung trainiert.
  Ausgabe: `reports/final_linear_price_2015_20260630_v1/`,
  `reports/final_hist_gradient_boosting_price_2015_20260630_v1/`.
- **Geprüft:** Erwartetes lückenloses Stundenraster 2015-01-01 bis
  2026-06-30 23:00 UTC bestätigt (Assertion im Skript). Modell-Reload
  reproduziert Vorhersagen exakt (rtol 1e-12). Alle 26 bestehenden Unit-Tests
  weiterhin bestanden. Quellhashes der verwendeten CSV-Dateien geprüft.
- **Ergebnis:** Zwei einsatzbereite Modelle (CO2 und Grünanteil, mit
  Preis-Merkmal) vorhanden, trainiert exakt bis 30.06.2026 23:00 UTC. **Noch
  keine Vorhersage für Juli 2026 ff. berechnet, noch keine Istwerte geladen,
  noch kein Vergleich gerechnet** — das sind Schritt 2 und 3, noch offen.
- **Grenzen:** Wie beim bisherigen Preis-Modell: Preis-Merkmal mit 168h-Lag,
  kein Echtzeitpreis; retrospektives ERA5-Wetter für die Trainingsdaten bis
  30.06.2026 (kein Problem für das Training selbst, da hier nur vergangene,
  bereits bekannte Stunden gelernt werden). Für die spätere Vorhersage ab
  Juli 2026 wird echtes Wetter für diesen Zeitraum benötigt (ERA5 rückblickend
  oder eine damals gespeicherte Prognose) — noch nicht beschafft.

## 01.11.2026 – Vergleich Vorhersage vs. Istwert für 01.07.–23.09.2026 (Schritt 2+3)

- **Auftrag:** Nutzer wollte zunächst Istwerte für Jan–Juni 2026 von
  Electricity Maps laden. Hinweis gegeben: Dieser Zeitraum ist exakt der
  Trainingszeitraum des neuen Preis-Modells (Cutoff 30.06.2026) — ein
  Vergleich dort wäre kein unabhängiger Test, nur Trainingsanpassung.
  Per Rückfrage (`AskUserQuestion`) geklärt; Nutzer hat stattdessen bestätigt,
  den Vergleich für den ungesehenen Zeitraum zu rechnen.
- **Entdeckt:** Kein neuer Download nötig. Die bereits aufbereitete Tabelle
  `data/processed/stage0_v3_price/hourly_2026.csv` enthält Zielzeiten bis
  23.09.2026 23:00 UTC vollständig mit allen 137 Eingabemerkmalen UND den
  echten Electricity-Maps-CO2-Istwerten (dieselbe Quelle wie bei allen
  anderen Jahren, keine frische API-Abfrage für diese Auswertung). Da das
  Preis-Modell nur bis 30.06.2026 trainiert wurde, ist 01.07.–23.09.2026
  (2040 Stunden) ein echter, ungesehener Zeitraum.
- **Ausgeführt:** `scripts/evaluate_price_model_jul_sep2026.py` lädt das
  finale CO2-Preis-Modell, wählt die 2040 Zielstunden 01.07.–23.09.2026,
  prüft `eligible_co2_nonestimated==1`, `co2_is_estimated==0` und
  vollständige Zielwerte für alle Zeilen, berechnet Vorhersagen und
  vergleicht mit den Istwerten. Ergebnis in
  `reports/price_model_eval_20260701_0923_v1/` (`predictions_vs_actual.csv`,
  `run.json`). Zusätzlich `scripts/plot_price_model_eval.py`:
  Tagesmittel-Liniendiagramm Ist vs. Vorhersage,
  `reports/price_model_eval_20260701_0923_v1/predicted_vs_actual.png`.
- **Geprüft:** Modell-Trainingsende im geladenen Bundle (`training_end`)
  exakt `2026-06-30 23:00:00+00:00` bestätigt, bevor gerechnet wurde.
  Alle 26 bestehenden Unit-Tests weiterhin bestanden.
- **Ergebnis:** MAE 34,58 gCO2eq/kWh, RMSE 44,50, Bias −7,83 (Modell
  unterschätzt im Mittel leicht), R² 0,926 über 2040 Stunden.
- **Grenzen:** Deutlich bessere Werte als der ganzjährige 2025-Test
  (MAE 45,88/R² 0,876) — das ist aber kein Beleg für ein generell besseres
  Modell, sondern am ehesten durch den Sommerzeitraum erklärbar (Juli–
  September hat typischerweise gleichmäßigere Erzeugungsmuster als
  Winter-/Übergangsmonate). Nur 2040 Stunden, nicht mit den gepoolten
  Jahreswerten direkt vergleichbar. Retrospektives ERA5-Wetter in den
  Eingabemerkmalen, kein as-issued-Wetterprognosetest. Keine Aussage für
  24.09.–20.10.2026 getroffen (dafür fehlen noch aufbereitete
  Eingabemerkmale; Electricity-Maps-Istwerte dafür wären zwar schon im
  Rohdatenbestand vorhanden, aber ungenutzt).

## 01.11.2026 – Scatter-Diagramm für Bachelorarbeit angefordert

- **Auftrag:** Zusätzliches Diagramm, das für die Bachelorarbeit geeignet ist.
- **Beratung:** Empfehlung gegeben: Scatter-Diagramm (Vorhersage vs. Istwert,
  1:1-Linie) als Ergänzung zum Zeitreihen-Diagramm, da in der Forschung
  Standard zur Bewertung von Regressionsmodellen und zeigt Bias/Streuung
  direkter als die Zeitreihe. Nutzer hat zugestimmt.
- **Ausgeführt:** `scripts/plot_price_model_scatter.py` erstellt: Stundenwerte
  (n=2040) aus `predictions_vs_actual.csv`, 1:1-Ideallinie, Kennzahlen und
  Einordnung (Holdout-Test, Trainingsende, retrospektives ERA5-Wetter) direkt
  im Titel, damit das Diagramm auch ohne Fließtext verständlich ist. Ausgabe
  `reports/price_model_eval_20260701_0923_v1/predicted_vs_actual_scatter.png`.
- **Geprüft:** Werte identisch mit bereits dokumentiertem Ergebnis
  (MAE 34,58/RMSE 44,50/R² 0,926/Bias −7,83), reine Visualisierung,
  keine neue Berechnung.

## 01.11.2026 – Haupt-Preismodell (Produktionsstand) trainiert

- **Auftrag:** Preis-Modell als neues Hauptmodell fertig trainieren, mit
  demselben Trainingsende wie das bisherige Hauptmodell ohne Preis.
- **Rückfrage:** Nutzer wollte ursprünglich bis 30.09.2026, dafür fehlen aber
  aufbereitete Daten (nur bis 23.09.2026 vorhanden). Per `AskUserQuestion`
  geklärt: Cutoff 23.09.2026 gewählt — identisch mit
  `final_hist_gradient_boosting_2015_2026_v1`, direkt vergleichbar, keine
  neue Datenbeschaffung nötig.
- **Ausgeführt:** Zwei neue Skripte `train_final_linear_price_full_stage0.py`
  und `train_final_boosting_price_full_stage0.py` (wie die bisherigen
  `train_final_*_stage0.py`, aber auf `data/processed/stage0_v3_price`, 137
  Merkmale, Preis-Lücken-Zeilen ausgeschlossen). Beide ausgeführt.
  CO2-Training 102.310 Zeilen, Grünanteil 102.408 Zeilen (mehr als beim
  Juni-Zwischenstand, da jetzt bis September statt Juni). Rang 174 (volle
  Rangzahl) trotz der bekannten Overflow-Warnungen im linearen Modell.
  Ausgabe: `reports/final_linear_price_2015_2026_v1/`,
  `reports/final_hist_gradient_boosting_price_2015_2026_v1/`.
- **Geprüft:** Lückenloses Stundenraster 2015-01-01 bis 2026-09-23 23:00 UTC
  bestätigt. Modell-Reload reproduziert Vorhersagen exakt (rtol 1e-12).
  Alle 26 bestehenden Unit-Tests weiterhin bestanden. Quellhashes geprüft.
- **Ergebnis:** Preis-Hauptmodell (CO2 und Grünanteil) jetzt auf demselben
  Trainingsstand wie das bisherige Hauptmodell ohne Preis vorhanden. Noch
  keine interne Testbewertung für diesen vollen Trainingsstand (wie beim
  bisherigen Hauptmodell auch: kein eigener Testscore nach finalem Refit —
  die Güteangaben stammen aus den getrennten Entwicklungs-/2025-/Juli-
  September-Tests mit früherem Trainingsstand).
- **Grenzen:** Kein ungenutzter Holdout bleibt nach diesem finalen Refit für
  den Zeitraum bis 23.09.2026 übrig (wie beim Original-Hauptmodell auch).
  Noch keine Dashboard-/Inferenzintegration vorgenommen — reine
  Modell-Artefakte.

## 01.11.2026 – Preis-Modell ins Dashboard eingebunden

- **Auftrag:** CO2 im Dashboard auf das Preis-Modell umstellen, Grünanteil
  unverändert lassen. Per Rückfrage geklärt: Für 2018–2025 die bereits
  berechneten echten Out-of-Fold-Preis-Vorhersagen verwenden; für Tage ab
  24.09.2026 das volle Preis-Hauptmodell (Trainingsende 23.09.2026); nicht
  das Hauptmodell rückwirkend auf bereits gelernte Jahre anwenden (wäre kein
  echter Test mehr).
- **Ausgeführt:**
  1. `train_linear_price_stage0.py --test-2026` und
     `train_hist_price_stage0.py --test-2026` ausgeführt (Teiljahr-Test
     Jan.–23.09.2026, Training 2023–2025) für Konsistenz mit dem bisherigen
     Dashboard, das diesen Zeitraum ebenfalls über einen Testfold zeigt.
  2. Neues Skript `scripts/predict_hist_price_20260924_29.py` (Kopie von
     `predict_hist_20260924_26.py`, aber mit dem Preis-Hauptmodell und
     zusätzlichem Preis-Merkmal aus den bereits geladenen Preis-Rohdaten,
     gleiche 15-Minuten-Mittelung wie in `add_price_stage0.py`). Für beide
     bestehenden Zeitfenster ausgeführt:
     `reports/hist_prediction_price_20260924_26_v1/`,
     `reports/hist_prediction_price_20260927_29_v1/` (nur CO2, da das
     Preis-Modell kein Grünanteil-Ziel hat).
  3. `src/dashboard_logic.py`: `load_predictions()` liest CO2 jetzt aus den
     `_price_*`-Report-Ordnern (bzw. den neuen `hist_prediction_price_*`-
     Dateien für die Spezialtage), Grünanteil weiterhin aus den
     unveränderten alten Ordnern; beide Quellen werden pro Zeitstempel
     zusammengeführt (`merge`, `validate='one_to_one'`).
- **Geprüft:** `load_predictions()` isoliert aufgerufen: 76.410 Zeilen,
  2018-01-01 bis 2026-09-29, keine fehlenden Werte in
  `predicted_co2`/`predicted_renewable`. Alle 26 bestehenden Unit-Tests
  weiterhin bestanden. Dashboard lokal gestartet
  (`.venv-stage0/bin/streamlit run app.py`), HTTP 200, keine Tracebacks im
  Log.
- **Ergebnis:** Dashboard zeigt jetzt für CO2 durchgehend das Preis-Modell,
  für Grünanteil weiterhin das alte Modell — ohne Vermischung von
  Trainings- und Testdaten für einen Zeitraum.
- **Grenzen:** Für 24.–29.09.2026 unterscheidet sich die angezeigte CO2-
  Vorhersage jetzt vom früheren Dashboardstand (anderes Modell); Grünanteil
  für diesen Zeitraum stammt weiterhin aus den alten
  `hist_prediction_2026*_v1`-Dateien (unverändert).

## 01.11.2026 – 30.09.–02.10.2026 ebenfalls ins Dashboard aufgenommen

- **Auftrag:** Auch diesen Zeitraum im Dashboard sichtbar machen.
- **Ausgeführt:** `scripts/predict_hist_price_20260924_29.py --target-start
  2026-09-30 --smard-dir data/raw/smard_prediction_inputs/20261026T164810Z`
  (bereits vorhandene Rohdaten, kein neuer Download) →
  `reports/hist_prediction_price_20260930_02_v1/`. Drittes Eintragspaar in
  `src/dashboard_logic.py`s `extra_paths` ergänzt (CO2 aus der neuen
  Preis-Datei, Grünanteil aus der bestehenden
  `reports/hist_prediction_20260930_02_v1/predictions.csv`). Zeitraumhinweis
  in `app.py` auf „24.09.–02.10.2026" aktualisiert.
- **Geprüft:** `load_predictions()` isoliert aufgerufen: 76.482 Zeilen, jetzt
  bis 2026-10-02 23:00 UTC. Alle 26 Unit-Tests weiterhin bestanden. Dashboard
  lokal gestartet, HTTP 200, keine Tracebacks.
- **Ergebnis:** Dashboard deckt jetzt 2018-01-01 bis 2026-10-02 ab.

## 01.11.2026 – Stundenvergleich 30.09.–02.10.2026 ausgewertet und geplottet

- **Auftrag:** Kennzahlen und je ein Diagramm für CO2 und Grünanteil für
  diese 72 Stunden.
- **Ausgeführt:** `scripts/plot_20260930_02_hourly.py` erstellt: verbindet
  `reports/actuals_20260930_02_v1/actuals.csv` mit
  `reports/hist_prediction_price_20260930_02_v1/predictions.csv` (CO2,
  Preis-Modell) bzw. `reports/hist_prediction_20260930_02_v1/predictions.csv`
  (Grünanteil, alte Modellversion ohne Preis). Zwei stündliche
  Zeitreihen-Diagramme (nicht geglättet, da nur 72 Punkte), Kennzahlen im
  Titel. Ausgabe `reports/comparison_20260930_02_v1/co2_hourly.png` und
  `renewable_hourly.png`, Kennzahlen zusätzlich in `hourly_plot_metrics.json`.
- **Geprüft:** 72 eindeutige, deckungsgleiche Stunden für beide Ziele
  (`validate='one_to_one'` beim Verbinden). Alle 26 Unit-Tests weiterhin
  bestanden.
- **Ergebnis:** CO2 (Preis-Modell): MAE 23,56 gCO2eq/kWh, RMSE 29,98,
  Bias −1,51, R² 0,954. Grünanteil (Modell ohne Preis): MAE 3,39
  Prozentpunkte, RMSE 4,13, Bias −0,28, R² 0,944.
- **Grenzen:** Nur 72 Stunden, ein einzelnes Wetterereignis — kein Ersatz für
  die großen Jahrestests. Retrospektives ERA5-Wetter, kein operativer Test.

## 01.11.2026 – Hauptmodell (Preis) bis 26.10.2026 neu trainiert

- **Auftrag:** Nutzer wollte ursprünglich bis 01.11.2026 trainieren.
- **Geprüft vor Beginn:** Aktualität aller vier benötigten Quellen verglichen.
  Electricity Maps (CO2) aktuell bis 01.11. 17:00 UTC, SMARD bis ca. 01.11.
  15:00 UTC — beide ausreichend. ERA5-Archiv (Open-Meteo) nur bis 26.10.2026
  23:00 UTC vollständig, danach `null`-Werte (~5–6 Tage Veröffentlichungs-
  verzug). Day-Ahead-Preis bereits bis 27.10. geladen, für den 168h-Lag bis
  25.10. ausreichend.
- **Alternative geprüft:** Open-Meteo Forecast-API mit `past_days` liefert
  tatsächlich Werte bis 01.11., aber aus einer anderen Berechnungsmethode als
  die bisher durchgehend verwendete ERA5-Reanalyse — hätte eine inkonsistente
  Wetterquelle für die letzten Tage bedeutet. Nutzer hat sich für die saubere
  Variante entschieden: Cutoff 26.10.2026, durchgehend ERA5.
- **Ausgeführt (Downloads):**
  1. `scripts/download_smard_range.py --start 2026-09-17 --end-exclusive
     2026-11-02` → `data/raw/smard_range/20261101T171602Z/` (1104 Stunden,
     deckt Lag- und Zielzeitraum ab). Dabei Zeitumstellung am 25.10.2026
     entdeckt (doppelte lokale Stunde 02:00–03:00); bestehende fold-sichere
     Umrechnung `local_to_utc` aus `prepare_stage0.py` nachträglich
     eingebaut statt eigener naiver Zeitzonenkonvertierung.
  2. `scripts/download_weather_range.py --start 2026-09-24 --end 2026-10-26`
     → `data/raw/weather_range_20260924_20261026_era5/` (23 Orte, je 792
     Stunden, 5 Variablen, vollständig geprüft).
  3. `scripts/download_electricitymaps_range.py --start 2026-09-24 --end
     2026-10-26` → `data/raw/electricitymaps_range/20261101T172727Z/` (792
     Stunden, keine Lücken, keine Schätzwerte).
  4. Kein neuer Preis-Download nötig (168h-Lag bis 25.10. bereits durch
     bestehende Preisdaten gedeckt).
- **Ausgeführt (Tabellenerweiterung):** `scripts/extend_stage0_to_1026.py`
  baut 792 neue Zeilen (24.09.–26.10.2026) exakt im bestehenden Schema auf
  (Kalender, Wetter, Kapazität, 168h-Energie-Lag, Preis-Lag, Zielwerte,
  Eignungsflags), unter Wiederverwendung der Original-Funktionen aus
  `prepare_stage0.py` (`renewables`, `local_to_utc`, `capacity_reference`,
  `daylight`, `holidays`). MaStR-Kapazitätsreferenz unverändert übernommen
  (deckt Oktober 2026 bereits ab). Ausgabe `data/processed/stage0_v4_oct26/`.
  Beim ersten Versuch zwei Fehler gefunden und korrigiert: Schema-Feature-
  anzahl fälschlich auf 137 statt 138 (inkl. `is_weekend`) geprüft, und
  Spaltenreihenfolge fälschlich aus dem Schema statt aus der bestehenden
  Datei übernommen (Sonnenschein- und Preisspalten stehen dort nach den
  Zielspalten, nicht davor).
- **Geprüft:** Alle 792 neuen Zeilen vollständig (`features_complete`,
  `eligible_both` = 1 für alle), keine fehlenden Werte. Stichprobe für
  30.09.2026 00:00 UTC exakt gegen bereits bekannte Istwerte abgeglichen
  (CO2 370, Grünanteil 62,832 — beide identisch). Alle 26 bestehenden
  Unit-Tests weiterhin bestanden.
- **Ausgeführt (Training):** Neue Kopien `train_final_linear_price_1026_stage0.py`
  und `train_final_boosting_price_1026_stage0.py` (wie die bisherigen
  `_full_stage0`-Skripte, aber `DATA=stage0_v4_oct26`, Trainingsende
  2026-10-26T23:00:00Z). Beide ausgeführt. CO2-Training 103.102 Zeilen,
  Grünanteil 103.200 Zeilen. Volle Rangzahl 174 trotz bekannter
  Overflow-Warnungen im linearen Modell (wie bei den vorherigen Preis-Läufen).
  Ausgabe: `reports/final_linear_price_2015_20261026_v1/`,
  `reports/final_hist_gradient_boosting_price_2015_20261026_v1/`.
- **Geprüft:** `training_start`/`training_end` im gespeicherten Modell exakt
  `2015-01-01T00:00:00Z` / `2026-10-26T23:00:00Z` bestätigt. Modell-Reload
  reproduziert Vorhersagen exakt. Alle 26 Unit-Tests weiterhin bestanden.
- **Ergebnis:** Neues Hauptmodell (CO2 + Grünanteil, mit Preis) jetzt bis
  26.10.2026 trainiert — 33 Tage weiter als zuvor (23.09.2026). Noch nicht
  ins Dashboard eingebunden.
- **Grenzen:** Nicht 01.11.2026 wie ursprünglich gewünscht, wegen der
  ERA5-Veröffentlichungsverzögerung. Für Vorhersagen nach dem 26.10.2026
  wird entweder eine echte Wettervorhersage (echter operativer Test,
  bisher noch nie gemacht) oder späteres rückblickendes ERA5 benötigt.
  Kein eigener Testscore nach diesem finalen Refit (wie bei allen bisherigen
  Hauptmodellen); Gütebeleg stammt weiterhin aus den getrennten
  Entwicklungs-/2025-/Juli-September-Tests mit früherem Trainingsstand.

## 01.11.2026 – Erste echte operative Vorhersage (02.11.2026)

- **Auftrag:** Mit dem neuen Preis-Hauptmodell (Trainingsende 26.10.2026)
  eine echte Vorhersage für einen noch ungesehenen, zukünftigen Tag rechnen
  — erstmals mit echter Wettervorhersage statt rückblickendem ERA5.
- **Vorab geklärt:** Altes Archivskript `download_weather_forecast.py`
  geprüft; nutzt zwar die richtige Open-Meteo-Forecast-API, mittelt aber alle
  23 Orte zu einem Deutschlandwert und hat keine Sonnenscheindauer — beides
  nicht kompatibel mit dem aktuellen Modell. Nur das Prinzip (Endpunkt)
  übernommen, Logik neu nach dem Muster von `download_weather_range.py`
  gebaut, mit allen 5 Variablen pro Einzelstandort.
- **Ausgeführt (Downloads):**
  1. `scripts/download_energycharts_price_gap.py` lädt die fehlenden
     Tage nach dem letzten Preis-Bulk-Download (27.10.–01.11.2026) →
     `data/raw/energycharts_price_gap/20261101T175239Z/`.
  2. `scripts/download_weather_forecast_range.py --target-start 2026-11-02
     --days 1` lädt eine echte Wettervorhersage (nicht ERA5) über die
     Open-Meteo Forecast-API, 23 Orte einzeln, 5 Variablen, 24 Stunden →
     `data/raw/weather_forecast_20261102_2d/` (zunächst für 2 Tage versucht,
     dazu mehr unten).
- **Fehler gefunden und korrigiert:** Koordinatenprüfung schlug erst fehl,
  weil die Forecast-API ein feineres Modellgitter nutzt als das ERA5-Archiv
  (z. B. 52.5126 statt 52.5) — Tolerenz entsprechend angepasst, keine
  Ortsverwechslung. Zweitens: Für den ursprünglich geplanten 3-Tage-Zeitraum
  (02.–04.11.) reichte die MaStR-Kapazitätsreferenz nicht — diese endet
  bewusst zum Snapshot-Datum (20.10.2026) und wird nicht in die Zukunft
  extrapoliert (`if boundary > snapshot: continue` in `prepare_stage0.py`).
  Zeitraum deshalb auf den 02.11.2026 (24 Stunden) begrenzt, für den die
  Kapazitätsreferenz (01.10.2026) noch gültig ist, statt zu extrapolieren.
- **Ausgeführt (Vorhersage):** Neues Skript `scripts/predict_price_forecast.py`
  (erstmals `operational=True, retrospective_era5=False` statt wie bisher
  immer rückblickend). Nutzt echte Wettervorhersage für die Zielstunden,
  bereits vorhandene SMARD-/Preisdaten für den 168h-Lag (das sind
  Vergangenheitswerte, keine Vorhersage). Ausgabe
  `reports/forecast_price_20261102_1d_v1/` (`inputs.csv`, `predictions.csv`,
  `run.json`).
- **Geprüft:** `training_end` des geladenen Modells (`2026-10-26T23:00:00Z`)
  liegt vor dem Zielzeitraum (02.11.), per Assertion im Skript erzwungen.
  Alle 26 bestehenden Unit-Tests weiterhin bestanden.
- **Ergebnis:** CO2-Vorhersage für 02.11.2026, 00:00–23:00 UTC: Minimum
  447, Maximum 652, Mittel 541 gCO2eq/kWh. Tagesverlauf mit Spitzen morgens
  (00–01 UTC, 650–652) und abends (22–23 UTC, 525–535), Tiefpunkt mittags
  gegen 10–12 UTC (447–448).
- **Grenzen:** Erste echte operative Vorhersage in diesem Projekt — noch
  keine Istwerte zum Vergleich vorhanden (die gibt es erst nach dem 02.11.).
  Nur CO2 vorhergesagt, kein Grünanteil in diesem Lauf. SMARD-/Preis-Lag-
  Daten sind aktuelle Snapshot-Revisionen, keine damals veröffentlichten
  historischen Stände.

## 01.11.2026 – Operative Vorhersage (02.11.2026) ins Dashboard eingebunden

- **Auftrag:** Grünanteil für den 02.11. ergänzen und beides ins Dashboard
  einbinden.
- **Ausgeführt:** Neues Skript `scripts/predict_renewable_forecast.py`
  berechnet Grünanteil mit dem alten Modell ohne Preis (Trainingsende
  23.09.2026) auf denselben bereits gespeicherten Eingaben
  (`inputs.csv`) — für dieses Modell ist der 02.11. ebenfalls ungesehen.
  Ergebnis in `predictions.csv` ergänzt. `src/dashboard_logic.py`:
  viertes Eintragspaar in `extra_paths` (CO2-Pfad mit `None` für
  Grünanteil-Pfad, da beide jetzt in derselben Datei stehen).
  `app.py`: neuer, spezifischer Zeitraumhinweis für den 02.11.
  („erste echte operative Vorhersage, echte Wettervorhersage statt ERA5").
- **Geprüft:** `load_predictions()` isoliert aufgerufen: 76.506 Zeilen, bis
  2026-11-02 23:00 UTC (Lücke 03.10.–01.11. bleibt bestehen, von `app.py`
  bereits über die „keine Daten"-Warnung abgefangen). Alle 26 Unit-Tests
  weiterhin bestanden. Dashboard lokal gestartet, HTTP 200, keine
  Tracebacks.
- **Ergebnis:** Dashboard zeigt jetzt auch den 02.11.2026 mit CO2- und
  Grünanteil-Vorhersage, klar als erste echte operative Vorhersage
  gekennzeichnet (nicht retrospektiv).

## 05.11.2026 – MaStR-Kapazität aktualisiert, operative Vorhersage für 05.11. gebaut

- **Auftrag:** Nutzer möchte die MaStR-Kapazitätsreferenz aktualisieren,
  damit Vorhersagen über den 02.11. hinaus möglich werden, und danach eine
  operative Vorhersage (CO2 + Grünanteil) für den aktuellen Tag (05.11.)
  bauen und ins Dashboard einbinden.
- **Ausgeführt:**
  1. MaStR-Stichtag-Export (01.10.2026) manuell heruntergeladen und mit
     neuem Skript `scripts/update_mastr_capacity.py` neu rekonstruiert
     (gleiche Screening-Logik wie `prepare_stage0.py`). Dabei Fehler
     festgestellt: Stichtag-Exporte erscheinen nur vierteljährlich
     (Jan/Apr/Jul/Okt) und waren mit Stand 01.10.2026 **älter** als die
     bereits im Training verwendete Datei vom 20.10.2026 — dieser Download
     war unnötig und brachte keine neue Kapazitätsreichweite.
  2. Stattdessen den **täglichen** Gesamtdatenexport vom 05.11.2026
     (`Gesamtdatenexport_20261105_26.2.zip`, 3.274.467.592 Bytes) geladen
     und mit `update_mastr_capacity.py` neu rekonstruiert
     (`data/processed/mastr_capacity_20261105/`). Dabei Katalogtext-
     Abweichung gegenüber `prepare_stage0.py` festgestellt ("Windkraft"
     statt "Windenergie" an Land/auf See in dieser Export-Version) und
     Prüfung im Skript auf die stabilen Katalog-IDs (888/889) statt auf den
     Text umgestellt.
  3. Echte Wettervorhersage für den 05.11. geladen
     (`scripts/download_weather_forecast_range.py --target-start
     2026-11-05 --days 1`, Open-Meteo Forecast-API, 23 Stationen).
  4. SMARD-Rohdaten neu geladen (`scripts/download_smard_range.py --start
     2026-10-27 --end-exclusive 2026-11-05`), weil die für den 168h-Lag
     benötigten Steinkohle-Werte vom 29.10. beim vorherigen Abruf (01.11.)
     noch nicht veröffentlicht waren ("-" in der Rohdatei) und inzwischen
     nachgetragen wurden.
  5. `scripts/predict_price_forecast.py` auf die neue Kapazitätsdatei und
     den neuen SMARD-Ordner umgestellt, CO2-Vorhersage für 05.11. berechnet
     (`reports/forecast_price_20261105_1d_v1/`). Trainingsende des Modells
     (26.10.2026) liegt per Assertion vor dem Zielzeitraum.
  6. `scripts/predict_renewable_forecast.py` auf denselben Eingaben mit dem
     alten Modell (Trainingsende 23.09.2026, ohne Preis-Merkmal) ausgeführt.
  7. `src/dashboard_logic.py`: fünftes Eintragspaar in `extra_paths`
     ergänzt. `app.py`: neuer Zeitraumhinweis ab 05.11.2026.
- **Geprüft:** `load_predictions()` isoliert aufgerufen: Daten jetzt bis
  2026-11-05 23:00 UTC vorhanden, keine fehlenden Werte. Alle Assertions in
  den Vorhersage-Skripten (Trainingsende vor Zielzeitraum, vollständige
  Eingaben, endliche Werte) erfolgreich.
- **Ergebnis:** CO2-Vorhersage für 05.11.2026: Minimum 349, Maximum 506,
  Mittel 443 gCO2eq/kWh. Grünanteil-Vorhersage: Spanne ca. 40–63 %, Mittel
  ca. 49 %. Kapazitätsreferenz reicht jetzt bis zum Monat 01.11.2026,
  rechnerisch ausreichend für Zieltage bis ca. 03.12.2026.
- **Grenzen:** Noch keine Istwerte zum Vergleich vorhanden (gibt es erst
  nach dem 05.11.). SMARD-/Preis-Lag-Daten sind aktuelle Snapshot-
  Revisionen, keine damals veröffentlichten historischen Stände. Der
  unnötige Stichtag-Download (01.10.2026) bleibt als Altlast im Projekt
  liegen (`data/raw/mastr_stichtag/`), wurde aber in keinem Modell oder
  keiner Vorhersage verwendet.
- Außerdem: 3-Tage-Vorhersage (05.–07.11.2026) mit denselben Modellen und
  derselben aktualisierten MaStR-Kapazität gebaut (3-Tage-Wettervorhersage
  statt 1 Tag), alte 1-Tages-Datei dafür ersetzt
  (`reports/forecast_price_20261105_3d_v1/`). CO2: Minimum 349, Maximum
  651, Mittel 488 gCO2eq/kWh. Stündliche Werte-Tabelle im Dashboard
  (`app.py`) überarbeitet: Zeit nur als HH:MM, CO2 gerundet, Grünanteil als
  Fortschrittsbalken, Ampel als Emoji statt Text.

## Geplant, noch nicht umgesetzt: automatischer täglicher Vorhersage-Lauf

- **Frage des Nutzers:** Wie soll die tägliche Aktualisierung um 00:00 Uhr
  automatisch ablaufen, sobald die App gehostet ist?
- **Empfehlung (noch nicht implementiert):** GitHub-Actions-Cron-Job, der
  täglich (UTC-Zeit, umgerechnet auf Berlin) läuft, Wettervorhersage und
  aktuelle SMARD-/Preis-Daten holt, CO2- und Grünanteil-Vorhersage berechnet
  und `predictions.csv` ins Repo committed. Die gehostete Streamlit-App
  liest beim nächsten Aufruf einfach die neueste Datei — kein eigener
  Dauerbetrieb-Server nötig. Alternative (nur falls ein eigener Server
  läuft, nicht bei reinem Streamlit-Cloud-Hosting): klassischer
  `cron`-Eintrag auf dem Server selbst.
- **Status:** Bewusst zurückgestellt, auf ausdrücklichen Wunsch des
  Nutzers. Keine Workflow-Datei oder Implementierung bisher vorhanden.

## 08.11.2026 – GitHub-/GitLab-Anbindung geprüft

- **Frage:** Nutzer fragt, was eingerichtet wurde, damit das Repository auf
  GitLab und GitHub liegt.
- **Ausgeführt:** Lokale Git-Remotes, Branch-Verfolgung, `.git/config` und
  Projektverweise auf GitHub/GitLab geprüft. Keine Remote-Änderung, kein
  Commit und kein Push ausgeführt.
- **Geprüftes Ergebnis:** Aktuell ist ausschließlich `origin` mit
  `https://gitlab.rz.htw-berlin.de/s0587448/grid-forecaster.git` für Abruf
  und Push konfiguriert; `main` verfolgt `origin/main`. Ein GitHub-Remote,
  eine zweite Push-URL oder eine automatische Spiegelung ist lokal nicht
  nachweisbar. Der frühere Protokolleintrag zu GitHub Actions war nur eine
  nicht umgesetzte Empfehlung.
- **Empfehlung:** Wenn das Repository künftig auf beiden Plattformen
  synchron liegen soll, GitLab als Haupt-Remote behalten und GitHub als
  zweiten, ausdrücklich benannten Remote ergänzen; Änderungen anschließend
  gezielt zu beiden Remotes pushen. Eine automatische Spiegelung erst nach
  Prüfung der gewünschten führenden Plattform einrichten.

## Geplant, später: Grünanteil nach Energiequelle aufgeschlüsselt

- **Auftrag/Wunsch des Nutzers:** Das Grünanteil-Modell soll zusätzlich
  angeben können, aus welcher Energiequelle der Strom konkret kommt
  (Wind, Solar, Biomasse, Wasserkraft, usw.), nicht nur der
  Gesamt-Grünanteil in %.
- **Geplanter Ansatz (noch nicht umgesetzt):** Statt einer Zielgröße
  (`target_renewable_share_pct`) mehrere Zielgrößen, eine je
  Energiequelle (z. B. `target_wind_onshore_share_pct`,
  `target_solar_share_pct`, usw.). Die nötigen SMARD-Erzeugungsdaten je
  Quelle liegen bereits vor (bisher nur als 168h-verzögerte Eingabe
  genutzt); für die neuen Zielgrößen bräuchte man dieselben Werte
  unverzögert für die Zielstunde, wie beim bestehenden
  Gesamt-Grünanteil-Ziel. Separates Modell je Quelle, gleiche
  Eingabe-Merkmale, gleiche Validierungsmethode wie bisher.
- **Umfang:** Vergleichbar mit einem zweiten vollständigen
  Modellsystem (mehrere einzelne Modelle statt einem) — bewusst als
  eigener, späterer Auftrag zurückgestellt, nicht parallel zum
  anstehenden CO2-Lizenz-Umbau.
- **Status:** Nur besprochen und dokumentiert, keine Daten
  aufbereitet, kein Training gestartet.

## Emissionsfaktoren für die selbstberechnete CO2-Zielgröße recherchiert

- **Auftrag:** Erster Schritt des CO2-Umbaus (Ersatz der Electricity-Maps-
  Zielgröße): amtliche Emissionsfaktoren je Energieträger recherchieren,
  keine selbst erfundenen Werte.
- **Ausgeführt:** UBA-Bericht "Entwicklung der spezifischen
  Treibhausgas-Emissionen des deutschen Strommix in den Jahren 1990-2025"
  (Icha & Lauf, Climate Change 16/2026, UBA, März 2026) heruntergeladen
  und Tabelle 4 (Seite 24) sowie Methodik-Kapitel ausgewertet. Zusätzliche
  Websuche zu Pumpspeicher- und "Sonstige Konventionelle"-Faktoren bei
  UBA, Agora Energiewende und Fraunhofer ISE/energy-charts.info.
- **Geprüft/Ergebnis:**
  - Braunkohle: 1.119 g/kWh, Steinkohle: 860 g/kWh, Erdgas: 394 g/kWh
    (amtlich, Tabelle 4, Jahr 2025, vorläufig).
  - Erneuerbare (Wind, Solar, Wasserkraft, Biomasse, Sonstige
    Erneuerbare), Kernenergie: 0 g/kWh direkte Emission (amtlich, gemäß
    UNFCCC-Berichtskonvention für Erneuerbare).
  - Pumpspeicher: 0 g/kWh — begründet über Fraunhofer-ISE/energy-charts-
    Quelle: keine eigene Erzeugung, nur Wiederabgabe bereits anderweitig
    erzeugten und mitgezählten Stroms (keine Doppelzählung).
  - "Sonstige Konventionelle" (Müllverbrennung, Industriegase, ca. 1,4 %
    der Gesamterzeugung laut BDEW-Strommix-Bericht): **kein** amtlicher
    Einzelfaktor auffindbar (UBA berechnet diese Kategorie intern
    granularer aus Einzelbrennstoffen, veröffentlicht keine
    zusammengefasste Zahl). Entscheidung des Nutzers: als Näherung den
    Steinkohle-Faktor (860 g/kWh) ansetzen, explizit als Schätzung
    gekennzeichnet, nicht als amtlicher Wert.
- **Für die Bachelorarbeit:** Formulierungsvorschlag für Methodik-/
  Limitations-Kapitel erstellt und mit dem Nutzer abgestimmt (UBA-Quelle
  für Hauptfaktoren zitieren, Vereinfachung bei "Sonstige Konventionelle"
  explizit als Limitation ausweisen).
- **Grenzen:** Die neue CO2-Zielgröße ist produktionsbasiert (nur
  deutsche Erzeugung), nicht verbrauchsbasiert wie Electricity Maps
  (das zusätzlich Importe/Exporte per Flow-Tracing einrechnet) — beide
  Werte sind methodisch nicht direkt vergleichbar.
- **Noch offen:** Berechnungsskript, Neuaufbau der Stage-0-Tabelle mit
  neuer Zielgröße, komplettes Neutraining (Rolling-Fold 2018-2024 +
  Testjahre 2025/2026) — noch nicht begonnen, auf expliziten Auftrag des
  Nutzers zurückgestellt.

## Fehlender Emissionsfaktor "Sonstige Konventionelle" selbst berechnet

- **Auftrag:** Für die SMARD-Kategorie "Sonstige Konventionelle" einen
  Emissionsfaktor auf Basis echter Quellen ermitteln, nicht raten.
- **Vorgehen:** energy-charts.info (Fraunhofer ISE, Datenquelle UBA)
  liefert absolute jährliche CO2-Emissionen getrennt nach Braunkohle,
  Steinkohle, Erdgas, Öl, Müll (fossil), Sonstige. SMARD fasst Öl + Müll
  (fossil) + Sonstige in einer einzigen Kategorie "Sonstige
  Konventionelle" zusammen. Deshalb: Emissionen dieser drei
  energy-charts-Spalten je Jahr summiert und durch die tatsächliche
  SMARD-Erzeugungsmenge derselben Kategorie (aus den bereits
  vorhandenen SMARD-Rohdaten) geteilt.
- **Geprüft:** Für vier Jahre berechnet und auf Konsistenz geprüft:
  2020: 2.039 g/kWh, 2022: 2.517 g/kWh, 2024: 1.705 g/kWh,
  2025: 1.739 g/kWh. Werte in plausibler, ähnlicher Größenordnung
  (höher als reine Kohle, erklärbar durch ineffiziente Ölkraftwerke als
  Spitzenlastreserve und Müllverbrennung mit primärem Wärme- statt
  Stromfokus).
- **Ergebnis/Entscheidung:** 4-Jahres-Durchschnitt (2020, 2022, 2024,
  2025) verwendet: **2.000,1 g/kWh** für "Sonstige Konventionelle".
  Dieser Wert ist selbst berechnet (aus zwei echten Quellen kombiniert:
  energy-charts.info/UBA-Emissionen und eigene SMARD-Erzeugungsdaten),
  kein amtlich direkt veröffentlichter Einzelwert — in der Arbeit
  entsprechend als abgeleiteter Wert zu kennzeichnen, nicht als
  amtlicher UBA-Wert wie die drei Hauptfaktoren.
- **Damit vollständig für alle Kategorien:** Braunkohle 1.119,
  Steinkohle 860, Erdgas 394, Sonstige Konventionelle 2.000,1
  (alle g/kWh, selbst berechnet/amtlich wie beschrieben), Pumpspeicher
  und alle Erneuerbaren/Kernenergie 0 g/kWh.

## Self-berechnete CO2-Zielgröße: Stage-0-Tabelle neu aufgebaut und Modell neu trainiert

- **Auftrag:** Mit den recherchierten Faktoren die Electricity-Maps-
  CO2-Zielgröße ersetzen und das Modell exakt mit denselben Testjahren
  wie bisher neu trainieren, danach alt vs. neu vergleichen.
- **Ausgeführt:**
  1. Neues Skript `scripts/compute_self_co2_target.py`: baut
     `data/processed/stage0_v5_selfco2/` als Kopie von `stage0_v4_oct26`
     (alle 137 Eingabe-Merkmale, Preis-Merkmal, Grünanteil-Ziel
     unverändert), ersetzt nur `target_co2_gco2eq_kwh` durch den
     erzeugungsgewichteten Durchschnitt aus den unverzögerten
     SMARD-Erzeugungsdaten (2015-2026, Archiv- plus
     Erweiterungs-SMARD-Quelle kombiniert) und den recherchierten
     UBA-Faktoren. `co2_is_estimated` auf 0 gesetzt,
     `co2_estimation_method` auf `self_computed_smard_uba_v1`,
     Eignungs-Flags entsprechend neu berechnet.
  2. Fehler beim ersten Lauf gefunden und behoben: Die Kernenergie-
     Null-Regel (nach Atomausstieg) fehlte für den Erweiterungs-
     SMARD-Zeitraum, dadurch 960 fehlende Stunden in 2026 — nach Fix
     nur noch 120 von 103.608 Stunden ohne Wert (0,12 %, kleine echte
     SMARD-Datenlücken 2016/2018, nicht durch das Skript verursacht).
  3. Plausibilitätsprüfung 2024: Korrelation zu den alten
     Electricity-Maps-Werten 0,988, Mittelwert 376,3 vs. 400,6 g/kWh
     (neu etwas niedriger, plausibel: produktionsbasiert statt
     verbrauchsbasiert mit Importen).
  4. Neues Skript `scripts/train_self_co2_stage0.py`: eigenständiges
     Training (nicht an ein bestehendes Linear-Referenzmodell
     gekoppelt), exakt dieselbe Methodik wie bisher — Rolling-Fold
     2018-2024, finales Training 2022-2024, Test 2025 (unberührt),
     Holdout 2026 (teilweise), aus unverändert übernommener
     `splits.json`. Gleicher Modelltyp/Parameter
     (HistGradientBoostingRegressor, 100 Iterationen) wie das
     bestehende Preis-Modell. Nur das CO2-Modell wurde neu trainiert;
     das Grünanteil-Modell bleibt unverändert, da von der Lizenzfrage
     nicht betroffen.
  5. Vergleichsdiagramm `scripts/plot_self_co2_comparison.py` erstellt
     (`reports/self_co2_comparison_v1/co2_target_comparison.png`):
     MAE/RMSE/R² alt vs. neu, je Dev-Fold/Test 2025/Holdout 2026.
- **Geprüft/Ergebnis:**
  | Zeitraum | Alt (MAE/RMSE/R²) | Neu (MAE/RMSE/R²) |
  |---|---|---|
  | Dev-Fold 2018-2024 (gepoolt) | 48,34 / 60,61 / 0,825 | 42,79 / 54,62 / 0,821 |
  | Test 2025 (unberührt) | 45,88 / 57,64 / 0,876 | 43,43 / 54,60 / 0,865 |
  | Holdout 2026 (teilweise) | 38,83 / 49,16 / 0,907 | 44,24 / 54,86 / 0,865 |

  Neues Modell insgesamt vergleichbar gut, teils etwas besser
  (Dev-Fold, 2025), teils etwas schwächer (2026) als das alte.
- **Grenzen:** Kein direkter 1:1-Genauigkeitsvergleich möglich, da
  beide Modelle leicht unterschiedliche Zielgrößen vorhersagen (alt:
  verbrauchsbasiert mit Importen/Flow-Tracing; neu: rein
  produktionsbasiert Deutschland). Ähnliche Fehlerwerte zeigen, dass
  das neue Modell seine eigene Zielgröße ungefähr gleich gut erklärt
  wie das alte seine — keine Aussage über absolute Richtigkeit
  gegenüber der Realität.
- **Noch offen:** Neues Modell ist noch nicht im Dashboard verbunden
  (aktuell läuft weiterhin das Electricity-Maps-Modell im produktiven
  Einsatz); Umstellung des Dashboards/der operativen Vorhersage-Skripte
  auf das neue Modell steht noch aus, auf expliziten Auftrag des
  Nutzers zurückgestellt.

## Grünanteil nach Energiequelle: 6 Modelle trainiert und ins Dashboard eingebunden

- **Auftrag:** Grünanteil-Modell soll zusätzlich zeigen, aus welcher
  Quelle der Strom kommt; außerdem das selbstberechnete CO2-Modell ins
  Dashboard einbinden.
- **Ausgeführt:**
  1. Neues Skript `scripts/compute_renewable_breakdown_targets.py`:
     baut `data/processed/stage0_v6_renewable_breakdown/` (Kopie von
     `stage0_v4_oct26`), fügt 6 neue Zielspalten hinzu — eine je
     erneuerbarer Quelle (Wind Onshore/Offshore, Solar, Biomasse,
     Wasserkraft, Sonstige Erneuerbare), berechnet aus den
     unverzögerten SMARD-Erzeugungsdaten zur Zielstunde. Geprüft: Summe
     der 6 Zielspalten entspricht für jede Zeile exakt dem bestehenden
     Gesamt-Grünanteil-Ziel (0 Abweichungen).
  2. Neues Skript `scripts/train_renewable_breakdown_stage0.py`: 6
     getrennte HistGradientBoosting-Modelle, gleiche Methodik wie
     bisher (Rolling-Fold 2018-2024, Test 2025, Holdout 2026), 136
     Merkmale ohne Preis (wie das bestehende Grünanteil-Hauptmodell;
     Preis wurde hier bewusst nicht getestet, da kein plausibler
     Wirkungszusammenhang zwischen Strompreis und Wind-/Solarerzeugung
     besteht — erneuerbare Anlagen haben Einspeisevorrang).
  3. `src/dashboard_logic.py`: CO2 wird jetzt aus dem selbstberechneten
     Modell geladen (`hist_gradient_boosting_self_co2_v1` /
     `final_hist_gradient_boosting_self_co2_...`) statt aus dem
     Electricity-Maps-trainierten Preis-Modell, für die Jahre
     2018-2026. Zusätzlich werden die 6 Quellen-Vorhersagen als neue
     Spalten gemerged. Grünanteil-Gesamtwert bleibt unverändert vom
     bestehenden Hauptmodell.
  4. `app.py`: neuer Abschnitt "Grünanteil nach Energiequelle" —
     gestapeltes Flächendiagramm (Altair, validierte kategoriale
     Farbpalette), nur sichtbar wenn Aufschlüsselung für das gewählte
     Datum vorliegt (historische Jahre 2018-2026; nicht für aktuelle
     operative Live-Vorhersagen, da dafür keine Breakdown-Modelle
     laufen).
- **Geprüft/Ergebnis (Test 2025 / Holdout 2026, R²):** Wind Onshore
  0,948 / 0,931, Solar 0,968 / 0,959, Wind Offshore 0,807 / 0,755,
  Biomasse 0,887 / 0,836 — gut bis sehr gut. Wasserkraft 0,558 /
  **−0,25** und Sonstige Erneuerbare 0,679 / 0,065 — nicht brauchbar
  (Holdout schlechter als der einfache Mittelwert). Grund: fehlende
  Niederschlags-/Pegelstanddaten als Eingabe, nicht im Projekt
  verfügbar.
- **Entscheidung zur Darstellung:** Wasserkraft und Sonstige
  Erneuerbare werden im Diagramm zu "Sonstiges" zusammengefasst
  (Summe ihrer — unzuverlässigen — Einzelvorhersagen), statt sie
  einzeln als vermeintlich verlässliche Werte zu zeigen.
- **Wichtige Einschränkung, mit Nutzer besprochen:** Die 6
  Einzelvorhersagen summieren sich **nicht exakt** zur separat
  vorhergesagten Gesamt-Grünanteil-Zahl (an einzelnen Stunden geprüfte
  Abweichung bis ~16 Prozentpunkte), weil alle Modelle unabhängig
  voneinander trainiert sind und eigene Fehler machen. Nur die
  **tatsächlichen** (nicht vorhergesagten) Werte summieren sich exakt,
  das ist reine Arithmetik aus der Zielgrößen-Konstruktion.
  Diskutierte Alternativen — (a) ein Modell mit 6 Ausgängen, (b) Rest
  als Differenz zur Hauptmodell-Zahl berechnen — wurden besprochen;
  Nutzer-Entscheidung: Hauptmodell unverändert lassen, Aufschlüsselung
  separat mit Hinweistext zeigen, keine künstliche Normierung.
- **Status:** Alle Änderungen automatisch committed und zu GitLab
  gepusht (Commit `a67fc1b`), inkl. `app.py`, `dashboard_logic.py` und
  aller neuen Report-Ordner. 26 bestehende Unit-Tests weiterhin
  bestanden. Live-Hosting (Streamlit Cloud) übernimmt die Änderung
  automatisch über den GitHub-Mirror.

## Bundesland-Modell: Datenaufbau, gepooltes Training, Vergleich, Live-Betrieb

- **Auftrag:** Zusätzliches Modell für CO2-Intensität und Grünanteil
  je Bundesland (16 deutsche Länder), gleiche Methodik/Testjahre wie
  die bestehenden nationalen Modelle (`splits.json`: Dev-Folds
  2018-2024, finales Training 2022-2024, Test 2025, Holdout 2026).
  Nutzer-Entscheidung: zuerst ein **gepooltes** Modell (ein Modell je
  Zielgröße, "Bundesland" als zusätzliches kategoriales Eingabe-
  Merkmal, analog zu `hour_local`/`weekday`/`month`), 16 getrennte
  Modelle als Vergleich erst später.
- **Ausgeführt — Datengrundlage (alles neu beschafft, vorher nicht
  vorhanden):**
  1. Wetter je Bundesland: Zuordnung der bereits vorhandenen 23
     ERA5-Wetterstationen zu den 16 Bundesländern
     (`scripts/bundesland.py`); Länder mit 2 Stationen (Baden-
     Württemberg, Bayern, Mecklenburg-Vorpommern, Nordrhein-Westfalen,
     Sachsen) bekommen 2 getrennte Feature-Spalten (`station1__*`,
     `station2__*`), nicht gemittelt — auf Nutzer-Einwand korrigiert
     (ursprünglich fälschlich für Mittelung argumentiert).
  2. Erzeugung je Bundesland: wöchentliche JSON-Dateien von
     energy-charts.info (`scripts/download_energycharts_bundesland.py`,
     2015 bis heute, 618+ Dateien); Lizenz geprüft (CC BY 4.0 laut
     offizieller API-Dokumentation, keine ML-Einschränkung wie bei
     Electricity Maps).
  3. CO2-/Grünanteil-Ziel je Bundesland
     (`scripts/compute_bundesland_targets.py`): gleiche Methodik wie
     beim nationalen selbstberechneten Modell (Erzeugung × UBA-
     Emissionsfaktor ÷ Gesamterzeugung); zwei zusätzliche, **selbst
     berechnete** Emissionsfaktoren nötig (Öl 1971,0 g/kWh, Müll
     (fossil) 850,9 g/kWh — aus echten UBA-Emissionswerten ÷ echter
     Generation, 4-Jahres-Mittel, gleiche Methode wie "Sonstige
     Konventionelle" beim nationalen Modell; ausdrücklich als
     selbstberechnet gekennzeichnet).
  4. MaStR-Kapazität je Bundesland
     (`scripts/update_mastr_capacity_bundesland.py`): Auswertung des
     `Bundesland`-Felds in den MaStR-Rohdaten, gleicher
     Rekonstruktions-Algorithmus wie national. Snapshot vom
     05.11.2026, rückgerechnet ab 2015.
  5. Feiertage je Bundesland (`scripts/download_holidays_bundesland.py`,
     Nager.Date API, 2015-2026).
  6. `scripts/build_bundesland_stage0.py`: baut die gepoolte Stage-0-
     Tabelle (16 Bundesländer × Stunde = eine Zeile), lädt alle oben
     genannten Teile zusammen. 3 Bugs vor dem finalen Lauf gefunden
     und behoben (Zeitzone bei Kapazitäts-Referenzdatum, bei
     Feiertagsprüfung, bei Tageslängen-Berechnung — jeweils fehlende
     Berlin-Zeitzone-Konvertierung). Ergebnis: alle 12 Jahre zu 100%
     vollständig (keine fehlenden Werte).
- **Ausgeführt — Training** (`scripts/train_bundesland_stage0.py`):
  gleiche HistGradientBoosting-Parameter wie überall im Projekt, 19
  Eingabe-Merkmale (Wetter, Kapazität, Tageslänge, Feiertag) +
  "Bundesland" als 4. kategoriales Merkmal neben Stunde/Wochentag/
  Monat.
- **Geprüft/Ergebnis (gepooltes Modell, Test 2025 / Holdout 2026):**

  | Ziel | MAE / RMSE / R² Test 2025 | MAE / RMSE / R² Holdout 2026 |
  |---|---|---|
  | CO2 (g/kWh) | 59,7 / 80,2 / 0,863 | 68,7 / 93,5 / 0,810 |
  | Grünanteil (%) | 7,6 / 9,8 / 0,872 | 8,9 / 11,6 / 0,822 |

  Vergleich mit nationalem Modell (`scripts/plot_bundesland_comparison.py`,
  `reports/bundesland_comparison_v1/`): Bundesland-Modell durchgehend
  etwas schwächer (z.B. CO2 Test 2025 national R² 0,874 vs. Bundesland
  0,863), aber nie katastrophal — nachvollziehbar, da pro Bundesland
  nur 1-2 statt 23 Wetterstationen einfließen. Verlauf über alle
  Testjahre 2018-2026 (`reports/bundesland_trend_v1/`) stabil, kein
  systematischer Abfall über die Zeit, nur 2019 (CO2) auffällig
  schwächer — gleiches Muster wie beim nationalen Modell.
  Einzelbeispiele (Bayern, Scatter-Plot ganzes Jahr 2025,
  `reports/bundesland_scatter2025_bayern_v1/`): R² 0,748 (CO2) / 0,765
  (Grünanteil) — unter dem 16-Länder-Durchschnitt. Berlin schlechtester
  Einzelfall (R² 0,662 übers Jahr) — kleine Stadtstaaten mit kaum
  Eigenerzeugung sind strukturell am schwersten zu treffen (kleine
  absolute MW-Werte, prozentual starke Schwankungen); zusätzlich wird
  der Grünanteil nur aus **Erzeugung innerhalb** des Bundeslands
  berechnet, nicht aus dem tatsächlichen Verbrauchsmix inkl. Importen
  (z.B. Berlin importiert die meiste Energie aus Brandenburg) — eine
  strukturelle Einschränkung der Zielgrößen-Definition, nicht nur des
  Modells.
- **Live-Betrieb aufgebaut:**
  1. `scripts/predict_bundesland_forecast.py`: operative Vorhersage für
     alle 16 Bundesländer, nutzt die bereits vorhandene 23-Stationen-
     Wettervorhersage (kein Preis/SMARD-Lag nötig, da das gepoolte
     Modell das nie als Merkmal hatte).
  2. `data/live_capacity/mastr_monthly_reconstructed_bundesland.csv`:
     periodisch aktualisierter Snapshot, gleiche Konvention wie beim
     nationalen Modell (nicht täglich automatisch aktualisiert — das
     ist beim nationalen Modell ebenfalls so, frühere Aussage, es
     würde täglich aktualisiert, war falsch und wurde korrigiert).
  3. GitHub-Actions-Workflow (`grid-forecaster-data/.github/workflows/
     daily_forecast.yml`) um Schritt "Predict Bundesland forecast"
     erweitert; Ergebnis landet als `predictions_bundesland.csv` im
     Daten-Repo.
  4. `data/raw/holidays_bundesland/` musste explizit von `.gitignore`
     ausgenommen werden (zur Laufzeit im CI-Checkout benötigt).
  5. `src/dashboard_logic.py` / `app.py`: neue Sektion "Bundesland-
     Vorhersage" mit Dropdown, zeigt sowohl die historischen
     Dev-Fold-/Test-/Holdout-Vorhersagen (2018-2026) als auch die
     laufende Live-Vorhersage, gleicher Chart-Stil wie die nationale
     Ansicht.
- **Lücke 27.10.-09.11.2026 geschlossen (teilweise):**
  Historischer Datenaufbau endete am 26.10.2026, Live-Pipeline startete
  erst am 10.11.2026 — dazwischen gab es für beide Modelle
  (national + Bundesland) keine Vorhersage. Mit
  `scripts/predict_price_backtest.py` und
  `scripts/predict_bundesland_backtest.py` rückwirkend berechnet,
  unter Verwendung von **echtem** ERA5-Archiv-Wetter (keine Vorhersage)
  für die betroffenen Tage; Modelle sind exakt die bereits
  eingefrorenen finalen Modelle, kein Neutraining. **Wichtige
  Erkenntnis:** Das echte ERA5-Archiv hat ca. 5-6 Tage Verzögerung —
  deshalb konnte nur 27.10.-04.11.2026 gefüllt werden, 05.-09.11.2026
  bleibt offen, bis das Archiv nachzieht (keine Abkürzung über ein
  anderes, schneller aktualisiertes Wettermodell genommen, um
  Konsistenz mit dem Rest des Projekts zu wahren).
  Datenqualitätsproblem bei dieser Gelegenheit gefunden: Energy-Charts-
  Rohdaten für Berlin haben am 30.10.2026 eine Lücke/einen Fehler
  (fälschlich "100% Grünanteil" durch fehlende konventionelle
  Erzeugungsdaten in der Quelle) — als Datenfehler erkannt und beim
  Auswerten ausgeschlossen, nicht als echter Wert verwendet.
- **Noch offen / für später vom Nutzer vorgemerkt:**
  1. Vergleich mit 16 getrennten Bundesland-Modellen (bewusst
     zurückgestellt, s.o.).
  2. Mögliche zusätzliche Datenquellen identifiziert, aber nicht
     umgesetzt: mehrere echte MaStR-Stichtage statt nur einem
     rückgerechneten Snapshot; mehr Wetterstationen pro (großem)
     Bundesland; Strom-Austausch zwischen Bundesländern (ob es dazu
     überhaupt stündliche Daten gibt, noch nicht recherchiert);
     Niederschlag/Pegelstände für Wasserkraft.
  3. Die 6-Quellen-Aufschlüsselung (Grünanteil nach Energiequelle,
     siehe oben) ist weiterhin nicht in die Live-Pipeline eingebunden
     — nur für historische Jahre 2018-2026 verfügbar.
  4. Die bereits oben dokumentierte Inkonsistenz zwischen dem
     Grünanteil-Gesamtmodell und der Summe der 6 Einzelquellen-Modelle
     wurde am 10.11.2026 nochmal am laufenden Dashboard bestätigt
     (Beispiel 01.08.2026, 12 Uhr: Hauptmodell 86,5%, Summe der
     Einzelmodelle 84,9%). Nutzer-Entscheidung: vorerst so lassen,
     spätere Behebung (z.B. Residuum-Konstruktion) selbst vormerken,
     nicht jetzt umsetzen.

## Neuer Modellvergleich, Schritt 1: Lineare Regression mit wachsendem Trainingszeitraum

- **Auftrag:** Modellvergleich für das nationale Modell von vorne:
  Lineare Regression, HistGradientBoosting und XGBoost mit identischen
  Daten. Neu: kein festes 3-Jahres-Fenster mehr, sondern ein
  wachsender Trainingszeitraum ab 2015 ("ein Modell, das weiter
  lernt"). Zuerst nur die Lineare Regression. Zielgrößen nach
  Nutzer-Entscheidung: CO2 von Electricity Maps (selbst berechnetes
  CO2 kommt später), Grünanteil gesamt und die 6 Quellen.
- **Geplant und so ausgeführt:**
  - Skript `scripts/train_linear_expanding.py`, Daten
    `data/processed/stage0_v6_renewable_breakdown`.
  - 137 Eingaben: 115 Wetter (23 Stationen × 5), 5 Kalender, 3
    Kapazität, 13 Erzeugung/Netzlast vor 168 h, 1 Day-Ahead-Preis vor
    168 h. `is_weekend` nicht verwendet (wie bisher).
  - 8 Ziele, je eine eigene Lineare Regression (gewöhnliche kleinste
    Quadrate, keine Regularisierung, keine Begrenzung der
    Vorhersagen auf 0-100 %).
  - Zeilen: `eligible_both == 1`, Preis vorhanden, alle 8 Ziele und
    alle 137 Eingaben vorhanden. Pro Jahr ausgeschlossene Zeilen in
    `run.json`. Dieselben Zeilen sollen HistGB und XGBoost bekommen.
  - Vorbereitung: StandardScaler für Zahlenwerte, One-Hot (drop first)
    für Stunde, Wochentag, Monat; jeweils nur auf den Lernjahren
    angepasst.
  - Wachsender Zeitraum, 9 Schritte: 2015-2017 → Test 2018, 2015-2018 →
    2019, …, 2015-2024 → 2025, 2015-2025 → 2026 (bis 26.10.2026). Bei
    der Linearen Regression ist Neurechnen auf allen bisherigen Jahren
    mathematisch identisch mit Weitertrainieren.
- **Geprüft:**
  - Lernjahre und Stundenzahl je Schritt in `run.json` und
    `metrics.csv` (von 25.954 Stunden für 2018 bis 95.863 für 2026).
  - Laufzeitwarnungen ("overflow in matmul") sind ein Fehlalarm der
    macOS-Rechenbibliothek (Accelerate): Vorhersagen weichen von einer
    Kontrollrechnung in reinem Python um höchstens 3·10⁻¹³ ab, größter
    Koeffizient 68.
  - Summe der 6 Quellen-Vorhersagen = Vorhersage des Gesamt-Grünanteils,
    maximale Abweichung 0,0 in allen Schritten (folgt aus der
    Linearität, weil das echte Gesamtziel exakt die Summe der 6
    Quellen ist).
- **Ergebnis (R² / MAE):**

  | Testjahr | CO2 (g/kWh) | Grünanteil (%) | Solar | Wind Onshore | Wind Offshore | Biomasse | Wasser | Sonstige |
  |---|---|---|---|---|---|---|---|---|
  | 2018 | 0,411 / 79,9 | 0,836 / 4,41 | 0,931 | 0,895 | 0,589 | 0,689 | 0,166 | 0,524 |
  | 2019 | 0,043 / 108,9 | 0,708 / 6,34 | 0,936 | 0,847 | 0,418 | 0,111 | −0,230 | −5,197 |
  | 2020 | 0,779 / 51,1 | 0,863 / 4,64 | 0,929 | 0,910 | 0,553 | 0,741 | 0,773 | 0,694 |
  | 2021 | 0,807 / 45,1 | 0,865 / 4,55 | 0,919 | 0,912 | 0,544 | 0,750 | 0,811 | 0,558 |
  | 2022 | 0,831 / 46,0 | 0,852 / 4,80 | 0,912 | 0,911 | 0,621 | 0,735 | 0,652 | 0,753 |
  | 2023 | 0,775 / 62,9 | 0,786 / 6,79 | 0,865 | 0,851 | 0,495 | 0,642 | 0,694 | 0,473 |
  | 2024 | 0,796 / 58,0 | 0,813 / 6,36 | 0,857 | 0,866 | 0,445 | 0,732 | 0,674 | 0,621 |
  | 2025 | 0,812 / 57,7 | 0,821 / 6,83 | 0,873 | 0,856 | 0,509 | 0,764 | 0,380 | 0,748 |
  | 2026 | 0,774 / 60,9 | 0,809 / 6,85 | 0,906 | 0,849 | 0,547 | 0,780 | 0,501 | 0,655 |

  (Bei den Quellen nur R²; MAE in `metrics.csv`.)
- **Auffällig, noch nicht geklärt:** 2019 sehr schwach (CO2 R² 0,043).
  Vermutung, nicht geprüft: 2019 stieg der CO2-Zertifikatspreis stark,
  viel Kohle wurde durch Gas ersetzt; ein linearer Zusammenhang aus
  2015-2018 passt dann nicht mehr. Das negative R² bei "Sonstige
  Erneuerbare" 2019 kommt vor allem von der sehr kleinen Streuung
  dieses Ziels (Werte 0,1-0,6 %), nicht von großen absoluten Fehlern.
- **Grenzen:** Noch kein Vergleich mit HistGB/XGBoost auf denselben
  Zeilen und demselben Schema; die alten HistGB-Zahlen (3-Jahres-
  Fenster) sind wegen anderem Trainingszeitraum nicht direkt
  vergleichbar.
- **Noch offen:** HistGradientBoosting und XGBoost mit demselben
  wachsenden Schema; dabei klären, ob "weitertrainieren" (neue Bäume
  anhängen) oder "neu auf allen bisherigen Jahren trainieren"
  verwendet wird, da das bei Baumverfahren nicht dasselbe ist.

### Diagramme für die Bachelorarbeit (10.11.2026, ausgeführt)

- **Skript:** `scripts/plot_linear_expanding.py`, liest nur
  `reports/linear_regression_expanding_v1` (kein neues Training).
- **Ausgabe:** `reports/linear_regression_expanding_plots_v1`:
  - `co2_{r2,mae,rmse}.png`, `renewable_share_{r2,mae,rmse}.png`:
    Metrik je Testjahr 2018-2026.
  - `sources_r2.png`: R² der sechs Quellen je Testjahr. Die y-Achse ist
    bei -0,5 abgeschnitten; der eine abgeschnittene Wert ("Sonstige
    Erneuerbare" 2019: -5,2) steht als Zahl am Balken.
  - `{co2,renewable_share}_year2025.png`: Tagesmittel echt vs.
    vorhergesagt im Testjahr 2025 (gelernt aus 2015-2024).
  - `{co2,renewable_share}_scatter2025.png`: stündlich echt vs.
    vorhergesagt 2025.
- **Beobachtung aus dem Streudiagramm (geprüft am Bild):** Bei CO2 sagt
  das Modell bei niedrigen echten Werten (ca. 100-200 g/kWh) zu hohe Werte
  voraus, bei sehr hohen Werten zu niedrige. Einzelne Vorhersagen sind
  negativ (bis ca. -60 g/kWh), weil die Lineare Regression nicht begrenzt
  ist. Das zeigt den nichtlinearen Zusammenhang, den ein lineares Modell
  nicht abbilden kann.

## Neuer Modellvergleich, Schritt 2: HistGradientBoosting mit wachsendem Trainingszeitraum (10.11.2026)

- **Auftrag:** HistGradientBoosting genau wie die Lineare Regression
  trainieren, nur CO2 (Electricity Maps) und Grünanteil. Nutzer hat Weg A
  gewählt: in jedem Schritt ein neues Modell von Null auf allen Jahren ab
  2015 bis zum Vorjahr; keine Bäume werden zwischen Schritten übernommen.
  Weg B (Bäume anhängen) verworfen: alte Bäume würden nie korrigiert und das
  Modell wüchse von Schritt zu Schritt (nicht gleich groß wie im Vergleich).
- **Entscheidung (Nutzer, vorher):** Modellwahl zuerst nur mit CO2 und
  Grünanteil; die sechs Quellen später nur mit dem gewählten Verfahren.
- **Ausgeführt:** `scripts/train_hist_expanding.py` →
  `reports/hist_gradient_boosting_expanding_v1` (`metrics.csv`,
  `predictions_2018…2026.csv`, `run.json`). Laufzeit ca. 99 s, 1 Thread.
- **Gleich wie Lineare Regression:** 137 Eingaben, Zeilenfilter, Vorverarbeitung
  (StandardScaler + One-Hot, nur auf Trainingsjahren angepasst), Schema
  2015-2017 → 2018 … 2015-2025 → 2026. Feste Parameter wie in den früheren
  HistGB-Läufen (100 Bäume, Lernrate 0,1, 31 Blätter, min. 20 je Blatt,
  random_state 42, kein Early Stopping, kein Tuning).
- **Geprüft:** Ausgeschlossene Zeilen je Jahr identisch zum LR-Lauf; je
  Testjahr gleiche Zeitstempel und gleiche Istwerte wie in den
  LR-Vorhersagedateien; je Modell genau 100 Iterationen.
- **Ergebnisse (geprüft, R² / MAE; LR zum Vergleich):**

  | Test | CO2 HGB | CO2 LR | Grün HGB | Grün LR |
  |---|---|---|---|---|
  | 2018 | 0,875 / 33,6 | 0,411 / 79,9 | 0,922 / 2,88 | 0,836 / 4,41 |
  | 2019 | 0,606 / 65,6 | 0,043 / 108,9 | 0,854 / 4,29 | 0,708 / 6,34 |
  | 2020 | 0,810 / 47,2 | 0,779 / 51,1 | 0,895 / 3,91 | 0,863 / 4,64 |
  | 2021 | 0,848 / 38,4 | 0,807 / 45,1 | 0,915 / 3,40 | 0,865 / 4,55 |
  | 2022 | 0,794 / 54,1 | 0,831 / 46,0 | 0,904 / 3,78 | 0,852 / 4,80 |
  | 2023 | 0,857 / 49,6 | 0,775 / 62,9 | 0,784 / 6,71 | 0,786 / 6,79 |
  | 2024 | 0,883 / 42,4 | 0,796 / 58,0 | 0,902 / 4,43 | 0,813 / 6,36 |
  | 2025 | 0,876 / 46,5 | 0,812 / 57,7 | 0,921 / 4,34 | 0,821 / 6,83 |
  | 2026 | 0,917 / 36,6 | 0,774 / 60,9 | 0,932 / 3,97 | 0,809 / 6,85 |

- **Einordnung:** HGB ist in 16 von 18 Fällen besser. Ausnahmen: CO2 2022
  (LR besser, 0,831 vs. 0,794) und Grünanteil 2023 (praktisch gleich).
  2019 bleibt auch bei HGB das schwächste CO2-Jahr; Ursache weiter nicht
  geprüft (Vermutung CO2-Preis/Kohle-Gas-Wechsel). Mögliche Vermutung für
  2022 (nicht geprüft): Energiekrise mit ungewöhnlichen Preisen.
- **Grenzen:** Keine Signifikanzprüfung; feste Parameter ohne Tuning; ERA5
  statt echter Wettervorhersage.
- **Noch offen:** XGBoost mit demselben Schema; danach Vergleichsdiagramm
  aller drei Verfahren.

### Diagramme HistGB (10.11.2026, ausgeführt)

- `scripts/plot_linear_expanding.py` um Verfahrensnamen (`METHOD`) und
  Schalter für das Quellen-Diagramm erweitert (LR-Ausgabe unverändert);
  neues `scripts/plot_hist_expanding.py` nutzt dieselben Funktionen.
- Ausgabe `reports/hist_gradient_boosting_expanding_plots_v1`: R²/MAE/RMSE je
  Testjahr, Jahresverlauf 2025, Streudiagramm 2025 (CO2 und Grünanteil;
  keine Quellen, da nicht trainiert). Nur gelesene Ergebnisse, kein Training.
- **Geprüft (selbst berechnet aus predictions_2025.csv):** keine negativen
  CO2-Vorhersagen (min. 112,7), Grünanteil 17,1-90,6 % (nie unter 0 oder über
  100). CO2 2025 im Mittel **+32,9 g/kWh zu hoch** (systematischer Versatz,
  auch im Streudiagramm sichtbar). Vermutung, nicht geprüft: Bäume können
  den fallenden CO2-Trend nicht über die Trainingswerte hinaus fortschreiben.

## Neuer Modellvergleich, Schritt 3: XGBoost mit wachsendem Trainingszeitraum (10.11.2026)

- **Auftrag:** XGBoost mit genau denselben Daten und demselben Schema wie
  HistGB (Weg A, nur CO2 und Grünanteil).
- **Ausgeführt:** `scripts/train_hist_expanding.py` um Schalter `--xgboost`
  erweitert (HistGB-Pfad unverändert) → `reports/xgboost_expanding_v1`.
  Laufzeit ca. 46 s, 1 Thread. Diagramme: `scripts/plot_xgb_expanding.py` →
  `reports/xgboost_expanding_plots_v1`.
- **Parameter (fest, wie im früheren XGBoost-Vergleich):** 100 Bäume,
  Lernrate 0,1, max. Tiefe 6, min_child_weight 1, reg_lambda 1, kein
  Subsampling, tree_method hist, max_bin 255, random_state 42, kein Early
  Stopping, kein Tuning. Gleiche Vorverarbeitung wie LR/HistGB.
- **Geprüft:** gleiche ausgeschlossene Zeilen, Zeitstempel und Istwerte wie
  im LR-Lauf; je Modell genau 100 Runden.
- **Ergebnisse (geprüft, R² / MAE):**

  | Test | Train | CO2 | Grünanteil |
  |---|---|---|---|
  | 2018 | 2015-2017 | 0,874 / 33,3 | 0,918 / 2,89 |
  | 2019 | 2015-2018 | 0,594 / 66,3 | 0,848 / 4,39 |
  | 2020 | 2015-2019 | 0,810 / 46,8 | 0,894 / 3,95 |
  | 2021 | 2015-2020 | 0,839 / 39,3 | 0,910 / 3,50 |
  | 2022 | 2015-2021 | 0,798 / 53,4 | 0,904 / 3,77 |
  | 2023 | 2015-2022 | 0,861 / 48,9 | 0,776 / 6,82 |
  | 2024 | 2015-2023 | 0,881 / 42,5 | 0,891 / 4,63 |
  | 2025 | 2015-2024 | 0,871 / 47,0 | 0,914 / 4,50 |
  | 2026 | 2015-2025 | 0,914 / 37,1 | 0,927 / 4,08 |

- **Geprüft (selbst berechnet, 2025):** keine negativen CO2-Vorhersagen
  (min. 106,6), Grünanteil 16,7-90,7 %. CO2 2025 im Mittel +33,8 g/kWh zu
  hoch (ähnlich HistGB).
- **Noch offen (Nutzer: Vergleich später):** Vergleich LR/HistGB/XGBoost.

## Neuer Modellvergleich, Schritt 4: Vergleich LR / HistGB / XGBoost (10.11.2026)

- **Ausgeführt:** `scripts/compare_expanding_models.py` →
  `reports/model_comparison_expanding_v1` (`metrics_per_year.csv`,
  `metrics_pooled_2018_2026.csv`, `best_per_year_by_mae.csv`,
  `mae_gap_bootstrap.csv`, `{co2,renewable_share}_r2_comparison.png`).
  Nur Auswertung vorhandener Vorhersagen, kein Training.
- **Geprüft:** Alle drei Verfahren haben dieselben 77.085 Teststunden
  (2018-26.10.2026) mit identischen Istwerten.
- **Gepoolt über alle Teststunden 2018-2026 (geprüft, MAE / R² / mittlerer Versatz):**

  | Verfahren | CO2 | Grünanteil |
  |---|---|---|
  | Lineare Regression | 63,37 / 0,726 / +2,5 | 5,71 / 0,848 / -0,19 |
  | HistGradientBoosting | 46,22 / 0,851 / +12,7 | 4,20 / 0,910 / -1,97 |
  | XGBoost | 46,29 / 0,849 / +13,7 | 4,29 / 0,905 / -2,19 |

- **Beste MAE je Testjahr (9 Jahre):** CO2: HistGB 5, XGBoost 3, LR 1 (2022).
  Grünanteil: HistGB 8, XGBoost 1.
- **Unsicherheit (Tages-Block-Bootstrap, 2000 Wiederholungen, 95 %-Intervall
  der MAE-Differenz):**
  - HistGB − XGBoost, CO2: -0,07 [-0,31; +0,18] → **kein belastbarer
    Unterschied** (Intervall enthält 0).
  - HistGB − XGBoost, Grünanteil: -0,09 [-0,11; -0,07] → HistGB knapp,
    aber belastbar besser; praktisch sehr klein (0,09 %-Punkte).
  - Beide Boosting-Verfahren gegenüber LR: CO2 ca. -17 g/kWh, Grünanteil ca.
    -1,4 bis -1,5 %-Punkte; Intervalle weit von 0 → klar besser.
- **Einordnung/Empfehlung:** Boosting klar besser als LR. Zwischen HistGB
  und XGBoost bei CO2 kein Unterschied, beim Grünanteil HistGB minimal besser.
  Empfehlung HistGB (gleich gut oder knapp besser, eine Bibliothek weniger,
  bereits im Live-Betrieb). Grenzen: nur feste Parameter ohne Tuning; mit
  Tuning könnte sich die Reihenfolge HistGB/XGBoost ändern. Boosting hat
  einen größeren positiven CO2-Versatz als LR (+12,7 vs. +2,5 g/kWh);
  Ursache nicht geprüft.

## Korrektur: Unterschied Electricity Maps vs. selbst berechnetes CO2 (10.11.2026)

- **Frühere Aussage falsch:** In den Abschnitten zum selbst berechneten CO2
  steht, Electricity Maps sei "verbrauchsbasiert mit Importen/Flow-Tracing".
  Das stimmt für unsere Daten nicht: `prepare_stage0.py` prüft für jede
  Stunde `flowTraced = false` und `emissionFactorType = lifecycle`. Die
  verwendeten Electricity-Maps-Werte sind also **erzeugungsbezogen,
  Lebenszyklus**.
- **Richtiger Hauptunterschied:** Electricity Maps = Lebenszyklus-Emissionen
  (inkl. Vorketten, daher auch Wind/Solar > 0); selbst berechnet = direkte
  Emissionen (UBA-Faktoren, Erneuerbare/Kernenergie = 0). Beide nur
  deutsche Erzeugung.
- **Beispiel (selbst berechnet, aus SMARD 08.06.2025 14-15 Uhr):**
  6.391.831 kg-Äquivalent-Summe / 53.482,75 MWh ≈ 119,5 g/kWh; davon fast die
  Hälfte aus "Sonstige Konventionelle" (Faktor 2.000,1 selbst abgeleitet)
  → dieser Faktor ist die größte Unsicherheit der Zielgröße.

## XGBoost mit selbst berechnetem CO2: getrennt vs. Mehrziel (10.11.2026)

- **Auftrag:** Nationales Modell soll CO2 (selbst berechnet), Grünanteil
  gesamt und die 6 Quellen vorhersagen. Zwei Varianten mit XGBoost 2.1.4:
  getrennt (8 Modelle) und Mehrziel (`multi_strategy="multi_output_tree"`,
  1 Modell). CO2 nicht mehr von Electricity Maps.
- **Ausgeführt:** `scripts/train_xgb_selfco2_expanding.py` (ohne/mit
  `--multi`) → `reports/xgboost_selfco2_separate_expanding_v1`,
  `reports/xgboost_selfco2_multi_expanding_v1`. Laufzeit 182 s / 173 s.
- **Daten:** Eingaben + Grünanteil/Quellen aus `stage0_v6_renewable_breakdown`,
  CO2 aus `stage0_v5_selfco2`; beide aus `stage0_v4_oct26`, Zeitstempel je
  Jahr als identisch geprüft. Zeilenfilter: `eligible_both` der Selbst-CO2-
  Tabelle + Preis + alle 8 Ziele vorhanden. Dadurch 77.112 Teststunden
  (EM-Läufe: 77.085; leicht andere Zeilen, da Electricity-Maps-Schätzstunden
  hier nicht mehr wegfallen).
- **Gleich in beiden Varianten:** 137 Eingaben, Vorverarbeitung, Schema
  2015-2017 → 2018 … 2015-2025 → 2026 (je Schritt neues Modell), feste
  XGBoost-Parameter wie im vorigen Lauf, Ziele mit Mittelwert/Std der
  Trainingsjahre standardisiert und zurückgerechnet.
- **Ergebnisse gepoolt 2018-2026 (geprüft, MAE / R²):**

  | Ziel | Getrennt | Mehrziel |
  |---|---|---|
  | CO2 (g/kWh) | 40,97 / 0,850 | 43,45 / 0,831 |
  | Grünanteil direkt | 4,28 / 0,906 | 4,47 / 0,897 |
  | Grünanteil = Summe der Quellen | **3,98 / 0,917** | 4,47 / 0,897 |
  | Biomasse | 0,596 / 0,819 | 0,613 / 0,804 |
  | Wasserkraft | 0,545 / 0,678 | 0,532 / 0,700 |
  | Wind auf See | 1,158 / 0,801 | 1,229 / 0,778 |
  | Wind an Land | 2,429 / 0,948 | 2,781 / 0,934 |
  | Solar | 1,602 / 0,964 | 2,164 / 0,948 |

## Electricity-Maps-Rohdatenbeispiel und Methodikquelle geprüft (10.11.2026)

- **Auftrag:** Für den Methodiktext den originalen API-Datensatz vom
  15.06.2025, 12:00 UTC, und einen offiziellen Methodik-Link angeben.
- **Geplant:** Vorhandene heruntergeladene JSON-Datei lesen, Felder und Wert
  mit Tabelle 3.0 abgleichen und die offiziellen Electricity-Maps-Seiten auf
  Erreichbarkeit und Inhalt prüfen. Keine Datenaufbereitung und kein Training.
- **Ausgeführt:** In
  `data/raw/electricitymaps/full_DE_20261020T2100Z/20250606T23.json` den
  Datensatz `2025-06-15T12:00:00.000Z` gesucht. Die offiziellen Seiten
  `https://www.electricitymaps.com/data/methodology` und
  `https://app.electricitymaps.com/docs/concepts/emission-factors` am
  10.11.2026 geöffnet.
- **Geprüftes Ergebnis:** Der Rohdatensatz enthält Zone `DE`,
  `carbonIntensity: 155`, `emissionFactorType: lifecycle`,
  `flowTraced: false`, `isEstimated: false` und `estimationMethod: null`.
  Damit stimmt der Tabellenwert. Für die verwendete erzeugungsbezogene
  Ausprägung wurden Importe und Exporte nicht per Flow-Tracing zugerechnet.
  Die Methodikseite erläutert unter anderem Flow-Tracing sowie direkte und
  Lebenszyklus-Emissionsfaktoren; die API-Dokumentation erklärt zusätzlich
  den Parameter `emissionFactorType`. Keine Code- oder Datenänderung und kein
  Training ausgeführt.
  | Sonstige Erneuerbare | 0,036 / 0,605 | 0,038 / 0,566 |

- **Bootstrap (Tagesblöcke, 2000×, 95 %, MAE getrennt − Mehrziel):** CO2
  -2,47 [-2,82; -2,12]; Grünanteil -0,19 [-0,23; -0,16]; alle Quellen
  getrennt besser außer Wasserkraft (+0,013 [0,008; 0,018], Mehrziel knapp
  besser). Bottom-up − direkt (getrennt): -0,30 [-0,33; -0,27] → Summe der
  Quellen trifft den Grünanteil belastbar besser als das direkte Modell.
- **Summenlücke:** Getrennt: Summe der Quellen weicht im Mittel 2,07
  %-Punkte (max. 20,2) vom direkt vorhergesagten Grünanteil ab. Mehrziel:
  Lücke 0. Begründung (selbst hergeleitet, nicht in der Doku geprüft):
  Blattwerte sind lineare Mittel der Gradienten aller Ziele; da Grünanteil
  = Summe der Quellen in den Daten, bleibt diese Beziehung in jedem Baum
  erhalten.
- **Einordnung/Empfehlung:** Getrennt ist in 7 von 8 Zielen belastbar
  besser. Empfehlung: getrennte Modelle; Grünanteil als Summe der 6
  Quellen ausgeben (genauer und automatisch konsistent). CO2-Versatz
  weiterhin positiv (+12,9 getrennt, +14,2 Mehrziel g/kWh).
- **Grenzen:** feste Parameter ohne Tuning; Mehrziel-Funktion in XGBoost
  experimentell.
- **Diagramme (nur getrennte Modelle, ausgeführt):** `scripts/plot_xgb_selfco2_separate.py`
  → `reports/xgboost_selfco2_separate_expanding_plots_v1` (R²/MAE/RMSE je
  Testjahr für CO2 und Grünanteil direkt, R² der 6 Quellen, Jahresverlauf und
  Streudiagramm 2025). Nur gelesene Ergebnisse, kein Training.

### Vergleich CO2 Electricity Maps vs. selbst berechnet (XGBoost getrennt, 10.11.2026)

- **Ausgeführt:** nur Auswertung vorhandener Vorhersagen
  (`xgboost_expanding_v1` vs. `xgboost_selfco2_separate_expanding_v1`) auf den
  77.085 gemeinsamen Teststunden 2018-2026; kein Training, keine Datei erzeugt.
- **Zielgrößen selbst (geprüft):** Mittel 425,0 (EM, Lebenszyklus) vs. 395,1
  g/kWh (selbst, direkt); Streuung 150,4 vs. 134,9; Korrelation 0,990.
- **Modellgüte gepoolt (geprüft):** EM: MAE 46,29, R² 0,849, Versatz +13,7;
  selbst: MAE 40,98, R² 0,850, Versatz +12,9. MAE relativ zum Mittel
  (selbst berechnet): 10,9 % vs. 10,4 %.
- **Einordnung:** R² praktisch gleich; kleinere MAE beim Selbst-CO2 vor allem
  wegen kleinerer Werte/Streuung, nicht zwingend besseres Modell. Beide
  Zielgrößen sind etwa gleich gut vorhersagbar. Kein Bootstrap gerechnet,
  da unterschiedliche Zielgrößen.
- **Diagramme (ausgeführt):** `scripts/plot_co2_target_comparison.py` →
  `reports/co2_target_comparison_expanding_v1` (`targets_daily_2025.png`:
  echte Tagesmittel beider Zielgrößen 2025; `r2_per_year.png`;
  `relative_mae_per_year.png`; `metrics_per_year.csv`). Relativer Fehler
  beim Selbst-CO2 in 7 von 9 Testjahren kleiner (2020 und 2024 größer).
- **Diagramme Mehrziel + Vergleich (ausgeführt):** `scripts/plot_xgb_selfco2_multi.py`
  → `reports/xgboost_selfco2_multi_expanding_plots_v1` (gleiche Diagramme wie
  getrennt). `scripts/compare_xgb_separate_multi.py` →
  `reports/xgboost_separate_vs_multi_v1` (`co2_r2_per_year.png`,
  `renewable_share_r2_per_year.png` mit getrennt direkt / getrennt Summe der
  Quellen / Mehrziel, `sources_r2_pooled.png`,
  `metrics_pooled_and_bootstrap.csv`). Zahlen identisch zur Tabelle oben.
  Nur Auswertung, kein Training.
- **Text für die Arbeit (ausgeführt):** `docs/bachelorarbeit_xgboost_hauptmodell.docx`
  mit Motivation („Warum dieses Vorgehen“), Methodik, 2 Tabellen, 5 Abbildungen
  mit Unterschriften, Modellwahl und Grenzen. Zahlen aus den geprüften
  Ergebnissen oben, keine neuen Berechnungen.

## Warum 2019 bei allen Modellen schwach ist: Datenprüfung (10.11.2026)

- **Ausgeführt:** nur Lesen vorhandener Daten (`stage0_v5_selfco2`, Jahresmittel)
  und der Vorhersagen `xgboost_selfco2_separate_expanding_v1`; keine Datei erzeugt.
- **Geprüft (Jahresmittel, selbst berechnet):** CO2 selbst berechnet 2015-2018:
  494 / 497 / 479 / 469 g/kWh, 2019: **396** (−16 % zum Vorjahr, größter
  Sprung im ganzen Zeitraum). Braunkohle 14.652 → 11.755 MWh/h (−20 %),
  Steinkohle 8.108 → 5.505 (−32 %), Erdgas 4.832 → 6.233 (+29 %), Grünanteil
  37 → 42 %.
- **Modell 2019 (XGBoost getrennt):** im Mittel **+55,5 g/kWh zu hoch**
  (2018: +8,6; 2020: +26,6). Monatlicher Versatz steigt von +11 (Januar) auf
  +70 bis +83 (Juni bis Oktober).
- **Einordnung:** 2019 lag die CO2-Intensität weit unter allem, was das Modell
  aus 2015-2018 kannte (Kohle → Gas). Baumverfahren sagen nur Werte im Bereich
  der Trainingsdaten voraus; die Lineare Regression überträgt die alten
  Zusammenhänge falsch. Die Ursache des Kohle-Gas-Wechsels (gestiegener
  CO2-Zertifikatspreis, niedrige Gaspreise) ist nicht in unseren Daten
  enthalten und muss mit Quellen belegt werden; nicht selbst geprüft.
- **Quellen für die Ursache (geprüft, 10.11.2026, Originaltext gelesen):**
  - UBA, Pressemitteilung Nr. 11/2020 vom 16.03.2020 „Treibhausgasemissionen
    gingen 2019 um 6,3 Prozent zurück“: Ursachen Reform des EU-Emissionshandels
    und niedriger Gaspreis; CO2-Durchschnittspreis 2019 24,65 €/t, „fast doppelt
    so hoch wie 2018“; Kohlekraftwerke 2019 „häufig teurer“ als Gaskraftwerke.
    https://www.umweltbundesamt.de/presse/pressemitteilungen/treibhausgasemissionen-gingen-2019-um-63-prozent
  - Agora Energiewende, Pressemitteilung vom 07.01.2020 „CO2-Preis drückt
    Treibhausgasemissionen und Kohleverstromung 2019 auf Rekordtiefs“
    (Jahresauswertung „Die Energiewende im Stromsektor – Stand der Dinge
    2019“): Steinkohle −31 %, Braunkohle −22 %, Gas +11 % Stromerzeugung.
    https://www.agora-energiewende.de/fileadmin/Projekte/2019/Jahresauswertung_2019/2020-01-07-PM_Agora-Jahresauswertung_2019.pdf
  - Unsere SMARD-Werte (selbst berechnet, Jahresmittel der Lag-Spalten) zeigen
    für Erdgas +29 %, Agora +11 %: unterschiedliche Abgrenzung der Erdgas-
    Erzeugung (SMARD-Kategorie vs. Agora-Bilanz), nicht weiter geprüft.

### Rückfragen zum Abschnitt XGBoost getrennt vs. Mehrziel geprüft (10.11.2026)

- **Bootstrap fehlende Zeilen (geprüft, aus `metrics_pooled_and_bootstrap.csv`):**
  Wind auf See −0,072 [−0,081; −0,062], Biomasse −0,017 [−0,023; −0,011],
  Sonstige Erneuerbare −0,0018 [−0,0022; −0,0014]. Kein Intervall enthält 0;
  „7 von 8 belastbar“ bleibt richtig.
- **Summe Mehrziel (nachgerechnet):** größte Abweichung Summe der Quellen vs.
  Grünanteil über alle Teststunden 4,8·10⁻⁵ %-Punkte (Rechengenauigkeit,
  XGBoost rechnet mit 32-Bit-Zahlen); in den Daten selbst max. 2,6·10⁻⁶.
  Frühere Aussage „exakt 0“ beruhte auf Rundung; richtig: „bis auf
  Rechengenauigkeit“.
- **77.112 vs. 77.085 Teststunden (geprüft):** Ursache ist NICHT ein Fehlen
  beim Selbst-CO2, sondern umgekehrt: Im Electricity-Maps-Lauf fielen
  Stunden weg, die Electricity Maps als geschätzt markiert (2018: 3 Stunden
  mehr ausgeschlossen, 2023: 24 Stunden). 27 Stunden Unterschied.
- **Einheit:** Selbst-CO2 enthält nur CO2 → Einheit in den Diagrammen von
  `plot_xgb_selfco2_separate.py` und `plot_xgb_selfco2_multi.py` auf gCO₂/kWh
  geändert, beide Ordner neu erzeugt. Word-Entwurf neu erzeugt (Einheit,
  vollständige Bootstrap-Tabelle, Formulierung Summe).

## Live-Betrieb auf das Hauptmodell umgestellt (11.11.2026)

- **Auftrag:** Live-Betrieb (tägliche Vorhersage, Dashboard) auf das
  Hauptmodell der Arbeit umstellen: getrennte XGBoost-Modelle, CO2 selbst
  berechnet, Grünanteil = Summe der 6 Quellen.
- **Ausgeführt:**
  1. `scripts/train_final_xgb_selfco2.py` → `reports/final_xgboost_selfco2_2015_20261026_v1`
     (`xgboost_selfco2_separate.joblib`, `run.json`): 8 Modelle, gleiche
     Einstellungen wie im Test, einmal auf allen Daten 2015 bis 26.10.2026
     (103.200 Stunden, Trainingsende 2026-10-26 23:00 UTC). Kein Testjahr
     (Güte ist aus dem wachsenden Schema bekannt). Gespeicherte Datei neu
     geladen und gegen das Modell im Speicher geprüft.
  2. `scripts/predict_xgb_forecast.py --forecast-dir …`: nutzt die von
     `predict_price_forecast.py` gebaute `inputs.csv`, schreibt CO2, 6 Quellen,
     Grünanteil (Summe) und den direkten Grünanteil zum Vergleich; alte
     HistGB-Werte bleiben als `hist_gradient_boosting_*` erhalten; prüft
     Trainingsende < erste Zielstunde.
  3. Nachgerechnet (alle nach dem Trainingsende, also ungesehen):
     `backtest_price_20261027_20261104_v1`, `forecast_price_20261102_1d_v1`,
     `forecast_price_20261105_3d_v1`.
  4. `src/dashboard_logic.py`: Verlauf 2018-26.10.2026 jetzt aus dem
     wachsenden Test des Hauptmodells (`xgboost_selfco2_separate_expanding_v1`,
     jedes Jahr nur aus 2015 bis Vorjahr gelernt), danach die drei
     nachgerechneten Ordner, dann die Live-Datei (Quellen optional).
     `app.py`: Einheit national gCO₂/kWh, Texte angepasst. Bundesland-Teil
     unverändert (weiter gepooltes HistGB).
  5. GitHub-Workflow im Daten-Repo um Schritt „Predict main model (XGBoost)“
     nach den bisherigen Schritten ergänzt.
- **Geprüft:** Streamlit-AppTest ohne Fehler für 15.06.2025 und 30.10.2026,
  Quellen-Aufschlüsselung wird angezeigt; vorhandener Unit-Test grün.
- **Grenzen/offen:** Bis zum nächsten Workflow-Lauf (23:00 UTC) zeigt die
  Live-Datei noch das alte Modell ohne Quellen. Bundesland-Modell nicht
  umgestellt. MaStR-Kapazität live weiterhin aus dem Snapshot.

### Live-Vorhersage: Starttag und negative Quellenwerte korrigiert (11.11.2026)

- **Problem 1 (geprüft):** Der Workflow läuft um 23:00 UTC und nutzte
  „heute (UTC)“ als Start → Vorhersage 10.–12.11. statt 11.–13.11. (erster Tag
  fast vorbei). **Änderung:** Start = morgen (UTC), Variablen `TARGET_DATE`/
  `TARGET_TAG` einmal gesetzt. Lag-Daten (t−168 h) reichen weiter: späteste
  benötigte Stunde liegt 3 Tage vor dem Laufdatum, SMARD bis heute geladen.
- **Problem 2 (geprüft):** Bäume liefern teils leicht negative Quellenanteile
  (Solar in 13,0 % der Teststunden, Wind auf See 0,1 %). **Änderung:** Quellen
  in `predict_xgb_forecast.py` und im Dashboard bei 0 abgeschnitten,
  Grünanteil = Summe der abgeschnittenen Quellen. Wirkung im Test 2018-2026
  (selbst berechnet): MAE Solar 1,6025 → 1,5990, Grünanteil (Summe)
  3,9797 → 3,9793; also leicht besser. Ergebnisse der Arbeit bleiben die
  ungeschnittenen Werte aus dem Test.
- **Fehler Dashboard (11.11.2026, behoben):** Endete das beste Zeitfenster um
  Mitternacht (z. B. 21-24 Uhr), war `end_exclusive.hour` = 0 → grüne Fläche
  von 0 bis 21 Uhr (verkehrt). Jetzt Ende = Start + Jobdauer, x-Achse 0-24.
  Fehler betraf nur die Darstellung, nicht die Berechnung des Fensters.
  AppTest ohne Fehler (12.11.2026, 15.06.2025 mit 3 und 6 Stunden).

## Bundesland-Modell neu: Plan (11.11.2026, GEPLANT, noch nicht ausgeführt)

- **Entscheidung Nutzer:** Bundesland-Modell wie das nationale Hauptmodell neu
  aufsetzen, in zwei Stufen.
- **Modell:** XGBoost 2.1.4, getrennte Modelle je Ziel, gepoolt über alle 16
  Länder (Bundesland als Merkmal), feste Parameter wie national.
- **Ziele je Land und Stunde (aus Energy-Charts-Erzeugung je Land):**
  CO2 (selbst berechnet, UBA-Faktoren), Anteile Wind an Land, Solar,
  Biomasse, Wasser (Laufwasser + Speicher), Sonstige (Geothermie);
  Grünanteil = Summe der 5 Quellen. Wind auf See nicht möglich (Energy-Charts
  weist ihn nur für Nord-/Ostsee aus, keinem Land zugeordnet; geprüft).
- **Stufe 1 (19 Eingaben):** Wetter (1-2 Stationen, je 5), installierte
  Leistung je Land (3), Kalender/Land (Stunde, Wochentag, Monat, Feiertag,
  Tageslänge, Bundesland) = Eingaben des alten Bundesland-Modells.
- **Stufe 2 (45 Eingaben):** Stufe 1 + Deutschland vor 7 Tagen (12
  Erzeugungsarten, Netzlast, Preis) + Erzeugung im eigenen Land vor 14 Tagen
  (12 Energieträger). 14 Tage, weil Energy-Charts je Land erst nach ca.
  6 Tagen veröffentlicht; 7 Tage wären live nicht sicher verfügbar.
- **Schema:** wachsender Zeitraum ab 2015, Test 2018-2026, je Schritt neues
  Modell. Bewertung MAE/R² je Testjahr und je Land, Bootstrap Stufe 2 vs. 1.
- **Danach:** bessere Stufe final auf allen Daten bis 26.10.2026, Live und
  Dashboard.

## Bundesland-Modell neu: Datenaufbau v2 (11.11.2026, ausgeführt)

- **Ausgeführt:** `scripts/build_bundesland_v2.py` →
  `data/processed/bundesland_pooled_v2/hourly_2015…2026.csv` +
  `feature_schema.json` (kein Training).
- **Ziele je (Stunde, Land)** neu aus den Energy-Charts-Rohdaten: CO2 (UBA-
  Faktoren wie `compute_bundesland_targets.py`), Anteile Wind an Land, Solar,
  Biomasse, Wasser (Laufwasser + Speicher), Sonstige (Geothermie); Grünanteil
  = Summe. Fehlt eine Technik in einem Land ganz → 0; fehlender Einzelwert →
  leer.
- **Stufe-2-Eingaben:** nationale Werte t−168 h aus `stage0_v6` (12 Erzeugungs-
  arten, Netzlast, Preis) und Erzeugung im eigenen Land t−336 h (12
  Techniken, MW). Stufe-1-Eingaben unverändert aus `bundesland_pooled_v1`.
- **Geprüft:** CO2 und Grünanteil stimmen mit den bisherigen Bundesland-Zielen
  überein (max. Abweichung 5·10⁻⁷, Rundung). Zeilen je Jahr wie v1
  (z. B. 2025: 140.160); vollständige Ziele + Stufe-2-Eingaben fehlen v. a. in
  den ersten 2 Wochen 2015 (Lag) und in 2026 bei 1.888 Zeilen ohne Ziel.

## Bundesland-Modell neu: Stufe 1 vs. Stufe 2 trainiert (11.11.2026, ausgeführt)

- **Ausgeführt:** `scripts/train_bundesland_xgb_expanding.py --stage 1/2` →
  `reports/xgboost_bundesland_stage{1,2}_expanding_v1` (Vorhersagedateien je 325 MB, nur lokal, per .gitignore nicht in Git; metrics.csv und run.json in Git). Erster Lauf brach ab
  (R² mit Division durch 0 bei Ländern ohne Geothermie, Ziel konstant 0);
  behoben mit der R²-Funktion aus `train_bundesland_stage0.py` (R² leer bei
  konstantem Ziel), dann neu gerechnet. XGBoost mit 8 Threads (sonst gleiche
  Parameter wie national; Hist-Verfahren, Ergebnis bis auf Rundung
  unabhängig von der Thread-Zahl). Laufzeit ca. 2 bzw. 3 Minuten.
- **Gleiche Zeilen beider Stufen geprüft.** Trainingsstunden (Land×Stunde)
  wachsen von 415.104 auf 1.535.616.
- **Gepoolt über alle Länder und Testjahre 2018-2026 (geprüft, MAE / R²):**

  | Ziel | Stufe 1 | Stufe 2 | Diff. MAE S2−S1 [95 %] |
  |---|---|---|---|
  | CO2 (g/kWh) | 74,57 / 0,825 | 61,73 / 0,877 | −12,84 [−13,20; −12,51] |
  | Grünanteil (Summe) | 8,32 / 0,834 | 6,78 / 0,888 | −1,55 [−1,58; −1,51] |
  | Wind an Land | 4,80 / 0,904 | 4,52 / 0,917 | −0,28 [−0,30; −0,27] |
  | Solar | 2,95 / 0,906 | 2,30 / 0,941 | −0,64 [−0,66; −0,63] |
  | Biomasse | 2,56 / 0,743 | 2,26 / 0,790 | −0,31 [−0,32; −0,30] |
  | Wasser | 1,53 / 0,700 | 0,75 / 0,941 | −0,79 [−0,81; −0,77] |
  | Sonstige (Geothermie) | 0,005 / 0,930 | 0,014 / 0,582 | +0,009 [0,008; 0,009] |

  Bootstrap: Blöcke = Tag je Land, 2000×, 95 %.
- **Je Land, Testjahr 2025 (R² CO2 / Grünanteil):** größte Verbesserungen bei
  Bremen (−1,79 → 0,27 / 0,44 → 0,70), Sachsen (−0,56 → 0,66), Saarland
  (0,07 → 0,74), Berlin (0,04 → 0,35 / 0,57 → 0,78), Baden-Württemberg
  (Grün 0,38 → 0,82). Schwach bleiben Berlin, Bremen und
  Mecklenburg-Vorpommern (Grün 0,58).
- **Einordnung:** Stufe 2 ist bei 6 von 7 Zielen belastbar besser. Nur
  Geothermie schlechter (absolut sehr klein, Anteile meist < 0,1 %; Ursache
  nicht geprüft). Empfehlung: Stufe 2 als neues Bundesland-Modell.
- **Grenze:** Vergleich zum alten Bundesland-Modell nur grob (anderes
  Schema, 3 Lernjahre); alt Test 2025 CO2 R² 0,863, neu Stufe 2 0,876.

## Bundesland-Modell neu: final, Live und Dashboard (11.11.2026, ausgeführt)

- **Final:** `scripts/train_final_bundesland_xgb.py` →
  `reports/final_xgboost_bundesland_2015_20261026_v1` (Stufe 2, 6 Modelle,
  1.646.656 Zeilen, Trainingsende 2026-10-26 23:00 UTC; gespeicherte Datei
  neu geladen und geprüft).
- **Live:** `scripts/predict_bundesland_xgb_forecast.py --bundesland-dir …
  --national-dir …` ergänzt den Bundesland-Ordner (Stufe-1-Eingaben aus dessen
  inputs.csv) um nationale t−168 h-Werte (inputs.csv des nationalen Ordners)
  und die Landeserzeugung t−336 h (Energy-Charts-Wochendateien; bricht ab,
  wenn eine fehlt). Quellen bei 0 abgeschnitten, Grünanteil = Summe; alte
  HistGB-Spalten bleiben als `hist_gradient_boosting_*`.
  `build_bundesland_v2.load_generation` nimmt dafür optional eine Dateiliste.
- **Backtest 27.10.-04.11.2026 nachgerechnet (ungesehen, geprüft, 2.640
  Zeilen mit Istwert):** CO2 R² 0,738 / MAE 82,0 (alt 0,711 / 84,6);
  Grünanteil R² 0,438 / MAE 12,9 (alt 0,413 / 13,5). Nur 9 Tage.
- **Dashboard:** `scripts/export_bundesland_history.py` → kompakte gzip-Kopie
  der Testvorhersagen 2018-2026 (`…stage2_expanding_v1/dashboard`, 23 MB);
  `src/dashboard_logic.py` liest Verlauf, Backtest und Live (Quellen optional),
  `app.py` zeigt je Land zusätzlich die Quellen; Einheit gCO₂/kWh.
  AppTest ohne Fehler (15.06.2025, 30.10.2026, 12.11.2026).
- **Workflow:** Download der Energy-Charts-Wochendateien je Land und neuer
  Vorhersageschritt nach dem bisherigen Bundesland-Schritt.
- **Workflow (ausgeführt):** Daten-Repo `daily_forecast.yml` um „Download
  Energy-Charts generation per Bundesland“ und „Predict Bundesland main model“
  ergänzt (Commit 5670ab2, nach Spiegelung des Codes nach GitHub). Die
  Live-Datei enthält ab dem nächsten Lauf CO2 und 5 Quellen je Land.
- **Diagramme und Text (ausgeführt):** `scripts/compare_bundesland_stages.py` →
  `reports/bundesland_stage_comparison_v1` (R² je Testjahr CO2/Grünanteil,
  R² der Quellen, R² je Land 2025 für CO2 und Grünanteil,
  `metrics_pooled_and_bootstrap.csv`; Zahlen identisch zur Tabelle oben).
  Word-Entwurf `docs/bachelorarbeit_bundesland_modell.docx` (Motivation,
  Daten, Eingaben, Schema, 2 Tabellen, 5 Abbildungen, Modellwahl, Grenzen).
## Bluehands Carbon-Aware-Computing eingeordnet (11.11.2026)

- **Auftrag:** Erklären, was die Referenz „Carbon-Aware-Computing
  (bluehands) – Referenz-SDK, später für Runtime-Integration“ bedeutet.
- **Geplant:** Verlinktes Repository und README prüfen und die mögliche Rolle
  im Grid-Forecaster von bereits umgesetzten Funktionen abgrenzen.
- **Ausgeführt:** Öffentliches Repository
  `https://github.com/bluehands/Carbon-Aware-Computing` am 11.11.2026 gelesen.
  Keine Installation, Codeänderung, Datenaufbereitung oder Modellberechnung.
- **Geprüftes Ergebnis:** Das .NET-orientierte Open-Source-Projekt verschiebt
  aufschiebbare Rechenaufgaben innerhalb eines Zeitfensters auf einen laut
  Prognose emissionsärmeren Zeitpunkt. Es bietet unter anderem eine Bibliothek,
  Web-APIs, Hangfire-Anbindung und PowerShell-Befehle. Für Deutschland nutzt es
  eigene Prognosedaten aus Energy-Charts; es ist daher nicht automatisch die
  Laufzeitkomponente des Grid-Forecasters und verwendet nicht dessen Modell.
- **Einordnung:** Als Architektur- und Schnittstellenreferenz für eine spätere
  Ausführungsschicht geeignet. Eine direkte Integration ist derzeit nicht
  empfohlen, bevor Anforderungen, Programmiersprache, Scheduler und Vergleich
  mit einer kleinen projektspezifischen Python-Lösung feststehen. Die
  Vorhersage ist vom späteren tatsächlichen Start eines Jobs zu unterscheiden.

## Sichtbares Frontend von Bluehands geprüft (11.11.2026)

- **Auftrag:** Klären, wo das Frontend des Bluehands-Projekts sichtbar ist.
- **Geplant:** Repository-Ordner `web`, öffentliche Projektseite und
  API-Oberfläche prüfen. Keine lokale Ausführung oder Implementierung.
- **Ausgeführt:** `web/index.html`, `https://www.carbon-aware-computing.com/`,
  die Startseite der Forecast-API und deren Swagger-Link geprüft.
- **Geprüftes Ergebnis:** Die öffentliche Projektseite ist eine statische
  Informationsseite mit Erklärung, Grafiken, Diensten und Codebeispielen,
  aber kein interaktives Prognose-Dashboard. Die Forecast-Adresse zeigt auf
  der Startseite nur den Azure-Functions-Standardbildschirm; die Swagger-UI
  ist eine technische API-Testoberfläche. Das Repository liefert daher kein
  mit dem Grid-Forecaster vergleichbares Endnutzer-Frontend.
- **Einordnung:** Zum visuellen Vergleich nur die Informationsseite öffnen.
  Für die Bachelorarbeit Bluehands als Runtime-/API-Referenz einordnen, nicht
  als Vorlage für das vorhandene Streamlit-Dashboard. Keine Code- oder
  Datenänderung und kein Training ausgeführt.


## Lücken im Dashboard geschlossen, Live-Verlauf eingeführt (11.11.2026, ausgeführt)

- **Ursachen (geprüft):** (1) Bundesland 31.10.: Zeilen ohne Istwert (Berlin ab
  30.10. 22 Uhr, Energy-Charts) wurden mit entfernt, obwohl die Vorhersage
  vorlag. (2) 05.-09.11. (Länder) bzw. 08.-09.11. (national): nie
  vorhergesagt. (3) Die Live-Datei wird täglich überschrieben → frühere Tage
  (z. B. 11.11.) verschwanden.
- **Behoben:** (1) Zeilen ohne Istwert bleiben. (2) Mit den damals gespeicherten
  echten Wettervorhersagen nachgerechnet: `forecast_price_20261108_3d_v1`
  (national, Hauptmodell) sowie `forecast_bundesland_20261105_3d_v1` und
  `…20261108_3d_v1` (neues Bundesland-Modell; nationale Eingaben aus den
  passenden nationalen Ordnern). Alle nach dem Trainingsende, also ungesehen.
  (3) `scripts/append_live_history.py` hängt jede Live-Vorhersage an
  `predictions_history.csv` / `predictions_bundesland_history.csv` im
  Daten-Repo an (neuester Wert gewinnt); das Dashboard liest diese.
  Startbestand aus den Commits e1f545b (10.-12.11.) und 475dc8b (12.-14.11.).
- **Geprüft:** 25.10.-14.11.2026 jeder Tag 24 Stunden, national und je Land.
  **Grenze:** Länderwerte für 11.11. stammen noch vom alten HistGB-Modell
  (ohne Quellen), da die Bundesland-Live-Datei dieses Laufs noch alt war.
