# ungefärbt – News Agent

## Wichtigste Schreibregel

ungefärbt schreibt EIGENE Artikel. Wir verweisen NIE auf Quellen in Headlines oder Summaries. Keine Formulierungen wie:

- "Laut einem Bericht von..."
- "Der Artikel beschreibt..."
- "Laut FAZ..."
- "Wie Spiegel berichtet..."
- "Der Beitrag beleuchtet..."

Wir haben die Informationen – wir schreiben sie neutral neu.

**Richtig:** "BMW verzeichnet Gewinnrückgang durch US-Zölle."
**Falsch:** "Laut FAZ verzeichnet BMW einen Gewinnrückgang."

## Projektstruktur

- Pipeline läuft lokal mit: `python3 pipeline.py`
- Alle JSON-Outputs landen in `output/`
- Konfiguration über `.env`

## Pipeline-Schritte

1. `main.py` — Artikel fetchen, clustern, synthetisieren
2. `qualitycheck.py input.json` — Duplikate mergen, quality_status setzen
3. `bias_barometer.py input.json` — Blindspot-Score und Spektren berechnen
4. `social_eval.py input.json` — Social-Kandidaten bewerten
5. `social_pack.py input.json` — Social-Posts bauen
6. `supabase_upload.py input.json` — Upload zu Supabase (optional)
7. `email_report.py input.json` — Mail mit Top-Kandidaten senden

## Wichtige Konventionen

- Logging immer über Python `logging`-Modul, nie `print()` in Modulen
- Pfade immer über `OUTPUT_DIR = Path(__file__).parent / "output"`
- Alle Module schreiben ihre JSON-Outputs nach `output/`
- Niemals auto-deployen auf Railway
- `ALLOW_TFIDF_FALLBACK=false` in `.env` — Pipeline bricht bei Embedding-Fehler ab
- Embedding-Backend: fastembed (primär) → TF-IDF (Fallback)

## ENV-Variablen

`ANTHROPIC_API_KEY`, `EMBEDDING_BACKEND`, `SIMILARITY_THRESHOLD`,
`ALLOW_TFIDF_FALLBACK`, `CONTRAST_MODEL`, `SUPABASE_URL`, `SUPABASE_KEY`, `RESEND_API_KEY`

## Was Claude Code nie tun soll

- Nie auf Railway deployen ohne explizite Aufforderung
- Nie `print()` statt `logging` in Modulen verwenden
- Nie Output-Pfade ohne `OUTPUT_DIR` hardcoden
- Nie den Schreibstil ändern (keine Quellenverweise in Headlines/Summaries)
