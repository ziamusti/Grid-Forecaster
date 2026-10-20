# Archiv des alten Projekts

Am 20.10.2026 auf ausdrücklichen Wunsch verschoben nach legacy_2026-10-20/:

- app.py, src/, requirements.txt und die bisherige .gitignore
- sämtliche bisherigen data/, models/ und reports/
- PROJEKTKLAERUNG.md und newlandmodel.md
- die bisherige Finder-Metadatendatei .DS_Store

Es wurde nichts aus diesen Verzeichnissen gelöscht. Verschieben auf demselben
Laufwerk vermeidet eine weitere Kopie. Alte Skripte mit relativen Pfaden müssen
bei Bedarf aus dem archivierten Projektverzeichnis gestartet werden.
Der vorherige Git-Stand war e65322ad03954860e02ecca45163f24f8d59fbeb.
Der Git-Verlauf und die bestehende Python-Umgebung bleiben im Projektstamm;
AGENTS.md bleibt als aktuelle Arbeitsanweisung erhalten.

Wichtig: Die MaStR-ZIP unter legacy_2026-10-20/data/raw/mastr/ ist weiterhin nur
eine absolute Verknüpfung in den Downloads-Ordner. Das Archiv enthält daher
keine unabhängige Sicherung dieser ZIP. Das Original nicht löschen.

Große archivierte Daten, Modelle und Berichte sind lokal vorhanden, aber im
neuen .gitignore ausgeschlossen. Dieses lokale Archiv ersetzt kein Backup.

Neue Experimente dürfen die archivierten Rohdaten lesen, aber nicht ändern.
Insbesondere werden alte Feature-Tabellen und trainierte Modelle nicht
unbemerkt in die neue Pipeline übernommen.

Nach dem Verschieben wurden die Inhalte von 203 zuvor versionierten Dateien
gegen ihre Git-Objektprüfsummen geprüft: keine Abweichungen. Die MaStR-Verknüpfung
war erreichbar. Dies ist keine vollständige Prüfsummenprüfung aller zuvor
unversionierten Rohdateien.
