# ungefärbt-agent

Automatischer News-Agent für das Projekt **ungefärbt** – sammelt stündlich deutsche Nachrichtenquellen, analysiert sie neutral mit Claude AI und erkennt Breaking News in Echtzeit.

## Was der Agent macht

- Ruft RSS-Feeds von 10 deutschen Nachrichtenquellen ab
- Analysiert jede Schlagzeile mit Claude AI: neutrale Zusammenfassung, Kategorie, Breaking-News-Einschätzung
- Clustert Artikel, die über dasselbe Thema berichten
- Erkennt Breaking News automatisch: wenn dieselbe Story bei 3+ Quellen erscheint
- Speichert Ergebnisse als JSON-Dateien für die Weiterverarbeitung

## Quellen & politische Einordnung

| Quelle | Einordnung |
|---|---|
| tagesschau.de | Mitte |
| spiegel.de | Mitte-Links |
| faz.net | Mitte-Rechts |
| zeit.de | Mitte-Links |
| welt.de | Rechts |
| sueddeutsche.de | Links |
| bild.de | Rechts |
| taz.de | Links |
| netzpolitik.org | Links |
| handelsblatt.com | Mitte-Rechts |

## Scheduling

| Modus | Intervall | Was passiert |
|---|---|---|
| Normal | 06:00 / 11:00 / 16:00 / 20:00 Uhr | RSS abrufen → Claude analysiert → JSON speichern |
| Breaking News | alle 15 Minuten | Nur RSS checken, kein Claude-Aufruf – bei 3+ Quellen zur selben Story: Claude aufrufen, als `breaking_*.json` speichern |

## Setup

### 1. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2. `.env` Datei erstellen

```env
ANTHROPIC_API_KEY=dein-key-hier
UNSPLASH_ACCESS_KEY=optional-für-bilder
```

Den Anthropic API Key gibt es unter [console.anthropic.com](https://console.anthropic.com).  
Den Unsplash Access Key (optional) unter [unsplash.com/developers](https://unsplash.com/developers).

### 3. Starten

```bash
py news_agent.py
```

Der Agent macht beim Start sofort einen ersten Durchlauf und läuft danach dauerhaft im Hintergrund. Beenden mit `Strg+C`.

## Ausgabe

**Normaler Durchlauf** → `news_YYYYMMDD_HHMMSS.json`  
**Breaking News** → `breaking_YYYYMMDD_HHMMSS.json`

```json
{
  "headline": "Bundesregierung beschließt ...",
  "summary": "Neutrale Zusammenfassung in 2-3 Sätzen.",
  "source": "tagesschau.de",
  "political_leaning": "Mitte",
  "category": "Politik",
  "is_breaking": true,
  "breaking_sources": ["tagesschau.de", "spiegel.de", "faz.net"],
  "image_url": "https://...",
  "link": "https://...",
  "timestamp": "2026-05-04T11:00:12"
}
```

## Logging

Jeder Durchlauf wird in `log.txt` protokolliert:

```
2026-05-04 11:00:12  NORMAL DURCHLAUF: 8 Artikel analysiert, 2 uebersprungen -> news_20260504_110012.json
2026-05-04 11:15:00  BREAKING CHECK: Keine Kandidaten. 47 Artikel gecheckt.
2026-05-04 11:30:05  BREAKING NEWS: "Titel..." (3 Quellen: faz.net, spiegel.de, tagesschau.de)
```

## Terminal-Anzeige

```
============================================================
  UNGEFAERBT NEWS AGENT  –  Scheduling aktiv
  Normal-Durchlauf:     06:00, 11:00, 16:00, 20:00 Uhr
  Breaking-News-Check:  alle 15 Minuten
============================================================

[11:00] Breaking-News-Check ... Alles ruhig. (47 Artikel gecheckt)

────────────────────────────────────────────────────────────
  Breaking-News-Check: 11:15 Uhr  (in 14 Min.)
  Normal-Durchlauf:    16:00 Uhr  (in 299 Min.)
────────────────────────────────────────────────────────────
```
