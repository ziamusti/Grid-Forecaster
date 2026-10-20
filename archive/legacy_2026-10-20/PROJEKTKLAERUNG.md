# Projektklärung: Grid Forecaster

Stand: 24.09.2026

Dieses Dokument dient dazu, Thema, Ziel, Methodik und Technologieauswahl der Bachelorarbeit gemeinsam zu klären. Alle Angaben unter „Bisheriges Verständnis“ sind vorläufig und müssen bestätigt oder korrigiert werden. Offene Fragen sind bewusst noch nicht als feste Projektentscheidungen formuliert.

## Themenbeschreibung des Betreuers

Die folgende Beschreibung wurde per E-Mail vom Betreuer übermittelt und bildet die fachliche Ausgangsbasis der Bachelorarbeit.

### Thema

**Grid Forecaster: Entwicklung und Evaluation eines datengetriebenen Prognosemodells zur Identifikation CO₂-armer Stromnutzungsfenster auf Basis meteorologischer und energiewirtschaftlicher Zeitreihen**

**Geeignet für:** Bachelorarbeit  
**Status:** Das Thema ist aktuell für Zia reserviert.

### Ziel der Arbeit

Untersucht werden soll, wie offene Strommarktdaten von **SMARD** und Wetterdaten, beispielsweise von **Open-Meteo**, genutzt werden können, um den CO₂- beziehungsweise „Grünheitsgrad“ des deutschen Strommixes vorherzusagen.

Dabei sollen insbesondere folgende Punkte untersucht werden:

- Entwicklung und Evaluation eines Prognosemodells für einen Vorhersagehorizont von beispielsweise bis zu drei Tagen
- Vergleich einfacher Wettermerkmale wie **Sonnenscheindauer, Windgeschwindigkeit, Temperatur, Tageslänge und Kalenderdaten** mit energiemarktbasierten Eingangsgrößen
- Untersuchung, ob wetterbasierte Approximationen komplexere Energiedaten teilweise ersetzen können
- Entwicklung eines Demonstrators für **Carbon-aware Scheduling**, beispielsweise zur Verschiebung von Backups, Batch-Jobs oder anderen nicht zeitkritischen Prozessen in emissionsärmere Zeitfenster

### Vorbereitung

Zur Vorbereitung soll die folgende Roadmap bearbeitet werden:

[Roadmap zur Vorbereitung](https://roadmap.sh/r?id=6a4e2246143790b66e26dbdd)

### Konsequenzen für die Umsetzung

- SMARD-Daten werden benötigt, um den tatsächlichen historischen Grünheitsgrad beziehungsweise die Zielvariable zu bestimmen und energiemarktbasierte Eingangsgrößen zu untersuchen.
- Wetter-, Tageslängen- und Kalenderdaten bilden eine eigene Gruppe möglicher Eingangsmerkmale.
- Mindestens ein wetterbasiertes, ein energiemarktbasiertes und ein kombiniertes Modell sollten vergleichbar evaluiert werden.
- Der genaue Grünheitsindikator (zum Beispiel Erneuerbaren-Anteil oder CO₂-Intensität) muss noch wissenschaftlich festgelegt werden.
- Der Demonstrator soll flexible IT-Prozesse in prognostizierte emissionsärmere Zeitfenster einplanen.
- „Bis zu drei Tage“ entspricht einem maximalen Prognosehorizont von ungefähr 72 Stunden; die endgültigen Horizonte müssen noch festgelegt werden.

## Bisheriges Verständnis (bitte bestätigen)

- Es handelt sich tatsächlich um eine Bachelorarbeit im Studiengang Ingenieurinformatik an der HTW Berlin.
- Arbeitstitel: „Grid Forecaster: Entwicklung und Evaluation eines datengetriebenen Prognosemodells zur Identifikation CO₂-armer Stromnutzungsfenster auf Basis meteorologischer und energiewirtschaftlicher Zeitreihen“.
- Untersucht wird der deutsche Strommix auf stündlicher Ebene.
- Das Modell soll günstige beziehungsweise möglichst CO₂-arme Zeitfenster bis zu 72 Stunden im Voraus erkennen.
- Ein Demonstrator soll flexible IT-Jobs, zum Beispiel Backups oder Batch-Jobs, in geeignete zusammenhängende Zeitfenster verschieben.
- Als primäre ML-Zielvariable ist derzeit eher der Anteil erneuerbarer Energien vorgesehen; eine endgültige Entscheidung steht noch aus.
- Als Datenquellen sind SMARD und Open-Meteo beziehungsweise zugrunde liegende Wettermodelle vorgesehen.
- Verglichen werden einfache Baselines, lineare Regression und XGBoost.
- Die Evaluation soll zeitlich korrekt, insbesondere ohne Data Leakage, erfolgen.
- Der aktuelle Schwerpunkt liegt auf Datenbeschaffung und Datenaufbereitung, noch nicht auf dem Training von XGBoost.

## Fragen zum Thema und zum formalen Rahmen

1. Ist dies wirklich deine Bachelorarbeit, oder ist es zunächst nur eine Projektidee beziehungsweise Vorstudie?
   - Antwort:

2. Ist der oben genannte Titel bereits offiziell angemeldet oder darf er noch verändert werden?
   - Antwort:

3. Beschreibe bitte in deinen eigenen Worten in zwei bis fünf Sätzen, worum es in deiner Arbeit geht. Was ist das eigentliche Problem, das du lösen möchtest?
   - Antwort:

4. Wer ist die wichtigste Zielgruppe des Ergebnisses: Forschende, Rechenzentrumsbetreiber, Unternehmen, Privatpersonen oder eine andere Gruppe?
   - Antwort:

5. Was muss am Ende zwingend abgegeben werden: schriftliche Arbeit, Quellcode, Notebooks, Datensatz, lauffähige Anwendung, Präsentation oder weitere Bestandteile?
   - Antwort:

6. Ist der Abgabetermin 24.11.2026 korrekt? Gibt es vorher wichtige Meilensteine?
   - Antwort:

7. Welche Anforderungen oder Vorgaben haben Erst- und Zweitbetreuer bereits ausdrücklich genannt?
   - Antwort:

## Fragen zum wissenschaftlichen Ziel

8. Was ist der wichtigste wissenschaftliche Beitrag: die Prognosegüte, der Vergleich der Feature-Gruppen, das Carbon-aware Scheduling oder die Bewertung möglicher CO₂-Einsparungen?
   - Antwort:

9. Sind die vier Forschungsfragen bereits mit den Betreuern abgestimmt oder noch veränderbar?
   - Antwort:

10. Soll das System ausschließlich Deutschland betrachten? Wenn ja, welche Gebietsdefinition soll gelten (zum Beispiel deutsche Gebotszone)?
    - Antwort:

11. Was bedeutet in deiner Arbeit genau ein „grünes“ oder „günstiges“ Stromnutzungsfenster?
    - Antwort:

12. Soll das Ergebnis eine wissenschaftliche Offline-Evaluation bleiben oder auch echte zukünftige Zeitfenster prognostizieren können?
    - Antwort:

13. Soll der Demonstrator nur zeigen, wann ein Job laufen sollte, oder einen realen Job tatsächlich starten?
    - Antwort:

## Fragen zur Zielvariable

14. Welche Zielvariable möchtest du primär prognostizieren: Anteil erneuerbarer Energien, CO₂-Intensität oder beide in getrennten Experimenten?
    - Antwort:

15. Falls der EE-Anteil verwendet wird: Soll er als erneuerbare Erzeugung geteilt durch Verbrauch, gesamte Erzeugung oder eine andere Bezugsgröße definiert werden?
    - Antwort:

16. Darf der EE-Anteil über 100 % liegen, wenn die erneuerbare Erzeugung den inländischen Verbrauch übersteigt? Wie sollen Export, Import und Speicher behandelt werden?
    - Antwort:

17. Falls CO₂-Intensität berechnet wird: Sollen durchschnittliche oder marginale Emissionen betrachtet werden?
    - Antwort:

18. Welche Emissionsfaktoren und Systemgrenzen sollen gelten: nur direkte Emissionen oder Lebenszyklusemissionen?
    - Antwort:

19. Muss die prognostizierte Größe zwingend direkt als „CO₂-arm“ interpretierbar sein, oder ist der EE-Anteil nur ein Proxy, dessen Grenzen klar diskutiert werden?
    - Antwort:

## Fragen zu Daten und Prognosezeitpunkt

20. Welcher historische Zeitraum soll untersucht werden?
    - Antwort:

21. Welche zeitliche Auflösung soll durchgehend verwendet werden: 15 Minuten oder eine Stunde?
    - Antwort:

22. Liegen bereits SMARD-Daten vor? Falls ja: als CSV-Dateien, über einen API-Zugriff oder in einem anderen Format?
    - Antwort:

23. Welche SMARD-Zeitreihen sollen konkret genutzt werden?
    - Antwort:

24. Sollen Wetterdaten für einen einzelnen repräsentativen Ort, mehrere Standorte, ein räumliches Raster oder einen gewichteten Deutschland-Mittelwert verwendet werden?
    - Antwort:

25. Welche Wetterquelle soll für historische Daten verbindlich sein: ERA5, Open-Meteo Historical Weather API oder eine andere Quelle?
    - Antwort:

26. Welche Wettervorhersage wäre bei einem echten Prognoselauf verfügbar: ICON, GFS, Open-Meteo oder eine andere?
    - Antwort:

27. Soll das Modell mit tatsächlich archivierten historischen Wettervorhersagen trainiert und getestet werden, oder zunächst mit Reanalyse-/Beobachtungsdaten? Die zweite Variante kann die spätere reale Prognosegüte zu optimistisch darstellen.
    - Antwort:

28. Welche energiewirtschaftlichen Werte sind am Prognosezeitpunkt wirklich bekannt und dürfen deshalb als Features dienen?
    - Antwort:

29. Wie sollen fehlende Werte, nachträgliche Datenrevisionen, Zeitumstellungen und doppelte Zeitstempel behandelt werden?
    - Antwort:

30. Dürfen Rohdaten im Git-Repository gespeichert werden, oder sollen sie wegen Größe/Lizenz nur per Skript reproduzierbar heruntergeladen werden?
    - Antwort:

## Fragen zur Modellierung und Evaluation

31. Soll ein einziges Modell alle Horizonte von 1 bis 72 Stunden prognostizieren, oder soll es getrennte Modelle pro Horizont beziehungsweise Horizontgruppe geben?
    - Antwort:

32. Welche Baselines sind zwingend vorgesehen: letzter Wert, Wert vor 24 Stunden, Wert vor 168 Stunden oder Saisonmittel?
    - Antwort:

33. Reichen lineare Regression und XGBoost als Vergleichsmodelle, oder verlangen die Betreuer weitere Verfahren?
    - Antwort:

34. Wie sollen Trainings-, Validierungs- und Testzeiträume zeitlich aufgeteilt werden?
    - Antwort:

35. Soll Walk-Forward-Validierung mit wachsendem Trainingsfenster oder mit festem rollierendem Fenster erfolgen?
    - Antwort:

36. Welche Metrik entscheidet hauptsächlich über das beste Modell: MAE, RMSE, R² oder eine Scheduler-bezogene Metrik?
    - Antwort:

37. Soll die Modellgüte separat für jeden Prognosehorizont ausgewertet werden?
    - Antwort:

38. Wie genau soll die Ablationsstudie aussehen? Sind die Gruppen „Wetter + Kalender“, „Energiemarkt“ und „alle Features“ verbindlich?
    - Antwort:

39. Wie soll Feature-Wichtigkeit wissenschaftlich analysiert werden: Modellkoeffizienten, Permutation Importance, SHAP oder nur Ablationsvergleiche?
    - Antwort:

40. Gibt es eine Mindestverbesserung gegenüber der Baseline, ab der das Modell als nützlich gilt?
    - Antwort:

## Fragen zum Scheduler und zur CO₂-Bewertung

41. Welche Jobdauern und Flexibilitätsfenster sollen untersucht werden?
    - Antwort:

42. Wird während eines Jobs ein konstanter Stromverbrauch angenommen? Falls nein, wie sieht das Lastprofil aus?
    - Antwort:

43. Darf ein Job unterbrochen werden, oder muss er in einem zusammenhängenden Zeitfenster laufen?
    - Antwort:

44. Muss der Job spätestens zu einer festen Deadline beendet sein?
    - Antwort:

45. Wird das beste Fenster nach dem Mittelwert, der Summe oder dem schlechtesten Stundenwert innerhalb des Fensters ausgewählt?
    - Antwort:

46. Wie oft und über welchen Testzeitraum sollen „sofort“, „zufällig“ und „modellbasiert“ verglichen werden?
    - Antwort:

47. Wie soll die Zufallsstrategie reproduzierbar gemacht werden (fester Seed und mehrere Wiederholungen)?
    - Antwort:

48. Welche verlässliche CO₂-Intensitätsreihe soll zur nachgelagerten Bewertung verwendet werden?
    - Antwort:

49. Soll neben absolut eingespartem CO₂ auch die prozentuale Einsparung und die zeitliche Verzögerung des Jobs berichtet werden?
    - Antwort:

## Fragen zum Technologie-Stack

50. Welche Python-Version soll verwendet werden?
    - Antwort:

51. Wie soll die Umgebung reproduzierbar verwaltet werden: `requirements.txt`, Conda, Poetry, uv oder etwas anderes?
    - Antwort:

52. Warum sollen Jupyter Notebooks verwendet werden, und welche Teile sollen als wiederverwendbare Python-Module unter `src/` umgesetzt werden?
    - Antwort:

53. Soll pandas für Laden, Bereinigung und Zusammenführung aller Zeitreihen verwendet werden?
    - Antwort:

54. Soll scikit-learn die Datenvorverarbeitung, lineare Regression, Metriken und Validierungslogik übernehmen?
    - Antwort:

55. Ist XGBoost als Hauptmodell fest vorgegeben? Wenn ja, warum wurde es fachlich gewählt?
    - Antwort:

56. Soll matplotlib allein für Diagramme verwendet werden, oder sind seaborn beziehungsweise Plotly erlaubt?
    - Antwort:

57. Soll der Demonstrator ein Notebook, ein Kommandozeilenprogramm, eine kleine Weboberfläche oder nur eine Python-Funktion sein?
    - Antwort:

58. Werden automatisierte Tests erwartet? Falls ja, für welche kritischen Teile (zum Beispiel Zeitstempel, Zielvariable, Fensterwahl und Leakage-Prüfungen)?
    - Antwort:

59. Wo soll das Projekt laufen: nur lokal, auf Hochschulrechnern, in einer Cloud oder in einem Container?
    - Antwort:

60. Gibt es Grenzen bei Rechenleistung, Laufzeit, Speicher oder externen APIs?
    - Antwort:

## Fragen zu Reproduzierbarkeit und Dokumentation

61. Soll die gesamte Datenpipeline mit einem einzigen Befehl reproduzierbar sein?
    - Antwort:

62. Müssen Datenstände, API-Abfragen und Modellparameter versioniert oder protokolliert werden?
    - Antwort:

63. In welcher Sprache sollen Code-Kommentare, README und Notebooks geschrieben werden: Deutsch oder Englisch?
    - Antwort:

64. Gibt es Zitierstil-, Datenschutz-, Lizenz- oder Veröffentlichungsanforderungen?
    - Antwort:

65. Soll das Repository später öffentlich veröffentlicht werden?
    - Antwort:

## Nächste Entscheidung

Nach Beantwortung der Fragen werden aus den bestätigten Angaben eine klare Projektspezifikation, ein realistischer Arbeitsplan und die technische Struktur abgeleitet. Erst danach sollte die eigentliche Datenpipeline verbindlich implementiert werden.
