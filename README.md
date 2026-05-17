# ungefärbt-agent

Automatischer News-Agent für das Projekt **ungefärbt** – sammelt täglich deutsche Nachrichtenquellen aus über 140 RSS-Feeds, clustert sie semantisch, bewertet Bias, Relevanz und Social-Media-Potenzial und verschickt einen täglichen Report per E-Mail.

---

## Pipeline

Die Pipeline wird über `pipeline.py` gesteuert und läuft sequenziell in 7 Schritten. Alle Ausgabedateien landen im Unterordner `output/`.

```
python3 pipeline.py
```

### Schritt 1 — `main.py`

Ruft RSS-Feeds ab, bereinigt und dedupliziert Artikel, erstellt semantische Fingerprints, clustert mit FastEmbed + HDBSCAN und synthetisiert Cluster zu einer Story via Claude Sonnet.

**Output:** `output/news_YYYYMMDD_HHMMSS.json`

---

### Schritt 2 — `qualitycheck.py`

Prüft Stories auf inhaltliche Duplikate, merged ähnliche Cluster mit TF-IDF- und Claude-gestütztem Paarvergleich.

**Input:** `output/news_YYYYMMDD_HHMMSS.json`  
**Output:** `output/final_news_checked.json`, `output/quality_report.json`

---

### Schritt 3 — `bias_barometer.py`

Bewertet jede Story nach politischem Spektrum der berichtenden Quellen und vergibt ein Bias-Label (z. B. „Mehrere Perspektiven", „Rechts-lastig").

**Input:** `output/final_news_checked.json`  
**Output:** `output/final_news_with_barometer.json`, `output/bias_barometer_report.json`

---

### Schritt 4 — `social_eval.py`

Bewertet jede Story auf Social-Media-Eignung (Score 0–100), vergibt ein Format-Label (`breaking_post`, `bias_barometer_carousel`, `blindspot_carousel`, …) und führt optional einen Kontrast-Check durch (vergleicht Headlines verschiedener Quellen auf semantische Unterschiede).

**Input:** `output/final_news_with_barometer.json`  
**Output:** `output/final_news_social.json`, `output/final_social_candidates.json`, `output/social_eval_report.json`

---

### Schritt 4b — `social_pack.py`

Baut fertige Social-Media-Posts aus den Kandidaten:
- **Kontrast-Post** (wenn `has_contrast == true`): stellt zwei Quellen-Headlines direkt gegenüber
- **Standard-Post** (wenn `social_post_worthy == true`): Headline + Summary in max. 2 Sätzen

**Input:** `output/final_social_candidates.json`  
**Output:** `output/social_pack_output.json`

---

### Schritt 5 — `supabase_upload.py` *(optional)*

Lädt `final_news_social.json` in die Supabase-Datenbank hoch. Wird übersprungen wenn `supabase` nicht installiert oder `SUPABASE_URL`/`SUPABASE_KEY` nicht gesetzt sind.

**Input:** `output/final_news_social.json`

---

### Schritt 6 — `email_report.py`

Versendet einen täglichen E-Mail-Report mit den Social-Kandidaten via Resend API.

**Input:** `output/final_social_candidates.json`

---

## Output-Dateien

Alle Dateien liegen in `output/` relativ zum Projektverzeichnis:

| Datei | Erzeugt von | Inhalt |
|---|---|---|
| `news_YYYYMMDD_HHMMSS.json` | `main.py` | Alle geclusterten Stories nach dem ersten Lauf |
| `final_news_checked.json` | `qualitycheck.py` | Stories nach Duplikat-Bereinigung |
| `quality_report.json` | `qualitycheck.py` | Merge-Statistiken und Warnungen |
| `final_news_with_barometer.json` | `bias_barometer.py` | Stories mit Bias-Labels |
| `bias_barometer_report.json` | `bias_barometer.py` | Label-Verteilung und Fehler |
| `final_news_social.json` | `social_eval.py` | Alle Stories mit Social-Scores und Kontrast-Daten |
| `final_social_candidates.json` | `social_eval.py` | Nur Kandidaten (score ≥ Schwelle), sortiert |
| `social_eval_report.json` | `social_eval.py` | Score-Verteilung, Top-Kandidaten, Kontrast-Statistik |
| `social_pack_output.json` | `social_pack.py` | Fertige Post-Texte, sortiert nach Priorität |

---

## Konfiguration

Alle Einstellungen werden über Umgebungsvariablen gesetzt (`.env`-Datei im Projektverzeichnis wird automatisch geladen).

| Variable | Standard | Beschreibung |
|---|---|---|
| `ANTHROPIC_API_KEY` | – | Pflichtfeld. API-Key für Claude (main.py, qualitycheck.py, social_eval.py) |
| `EMBEDDING_BACKEND` | `fastembed` | Embedding-Backend für Clustering: `fastembed`, `sentence_transformers` |
| `SIMILARITY_THRESHOLD` | `0.80` | Cosine-Schwelle für Ausreißer-Zuweisung beim Clustering |
| `ALLOW_TFIDF_FALLBACK` | `false` | `true` = TF-IDF als Notfall-Fallback wenn Embedding-Backend ausfällt |
| `CONTRAST_MODEL` | `claude-sonnet-4-6` | Claude-Modell für den Kontrast-Check in `social_eval.py` |
| `SUPABASE_URL` | – | URL der Supabase-Instanz (optional, für Upload-Schritt) |
| `SUPABASE_KEY` | – | API-Key der Supabase-Instanz (optional, für Upload-Schritt) |
| `RESEND_API_KEY` | – | API-Key für Resend (E-Mail-Versand in `email_report.py`) |

### Beispiel `.env`

```env
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDING_BACKEND=fastembed
CONTRAST_MODEL=claude-sonnet-4-6
RESEND_API_KEY=re_...
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=eyJ...
```

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # Werte eintragen
python3 pipeline.py
```

Einzelne Schritte können auch direkt aufgerufen werden:

```bash
python3 main.py
python3 qualitycheck.py output/news_20260517_115523.json
python3 bias_barometer.py output/final_news_checked.json
python3 social_eval.py output/final_news_with_barometer.json
python3 social_pack.py output/final_social_candidates.json
python3 email_report.py output/final_social_candidates.json
```
