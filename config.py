BREAKING_SEEN_DATEI = "breaking_seen.json"
BREAKING_QUELLEN_SCHWELLE = 3
NORMAL_ZEITEN = ["06:00", "11:00", "16:00", "20:00"]
BREAKING_INTERVALL_MIN = 15

QUELLEN = {
    "tagesschau.de": {
        "rss": "https://www.tagesschau.de/xml/rss2/",
        "ausrichtung": "Mitte"
    },
    "spiegel.de": {
        "rss": "https://www.spiegel.de/schlagzeilen/index.rss",
        "ausrichtung": "Mitte-Links"
    },
    "faz.net": {
        "rss": "https://www.faz.net/rss/aktuell/",
        "ausrichtung": "Mitte-Rechts"
    },
    "zeit.de": {
        "rss": "https://newsfeed.zeit.de/index",
        "ausrichtung": "Mitte-Links"
    },
    "welt.de": {
        "rss": "https://www.welt.de/feeds/latest.rss",
        "ausrichtung": "Rechts"
    },
    "sueddeutsche.de": {
        "rss": "https://rss.sueddeutsche.de/alles",
        "ausrichtung": "Links"
    },
    "bild.de": {
        "rss": "https://www.bild.de/rssfeeds/rss3-20745882,feed=alles.bild.html",
        "ausrichtung": "Rechts"
    },
    "taz.de": {
        "rss": "https://taz.de/!p4608;rss/",
        "ausrichtung": "Links"
    },
    "netzpolitik.org": {
        "rss": "https://netzpolitik.org/feed/",
        "ausrichtung": "Links"
    },
    "handelsblatt.com": {
        "rss": "https://www.handelsblatt.com/contentexport/feed/schlagzeilen",
        "ausrichtung": "Mitte-Rechts"
    },
}

ALLE_AUSRICHTUNGEN = ["Links", "Mitte-Links", "Mitte", "Mitte-Rechts", "Rechts"]

KATEGORIE_FALLBACK_BILDER = {
    "Politik":      "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800",
    "Wirtschaft":   "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800",
    "Gesellschaft": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=800",
    "Technologie":  "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800",
    "Sport":        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
    "Kultur":       "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
    "Umwelt":       "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800",
    "International":"https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800",
}

KATEGORIE_REIHENFOLGE = [
    "Politik", "Wirtschaft", "Gesellschaft", "International",
    "Technologie", "Sport", "Kultur", "Umwelt",
]

SYSTEM_PROMPT = """Du bist ein neutraler Nachrichtenanalyst für das Projekt "ungefärbt".
Deine Aufgabe: Nachrichtenüberschriften sachlich und ohne Wertung zusammenfassen.
Regeln:
- Nur belegbare Fakten, keine Meinungen oder Spekulationen
- Klare, einfache Sprache auf Deutsch
- 2–3 Sätze pro Zusammenfassung
- relevance_score (0–100): Wichtigkeit für die deutschsprachige Öffentlichkeit
- is_top_story: true nur für die bedeutendsten Meldungen des Tages (ca. 15–20 % aller Artikel)
- Antworte ausschließlich mit dem angeforderten JSON, ohne weiteren Text"""

_STOPPWOERTER = {
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "für", "von",
    "mit", "bei", "nach", "vor", "an", "auf", "in", "ist", "sind", "hat",
    "haben", "wird", "werden", "als", "auch", "sich", "im", "des", "dem",
    "den", "zu", "zur", "zum", "nicht", "was", "wie", "es", "er", "sie",
    "wir", "ich", "am", "aus", "um", "bis", "war", "wird", "kann", "mehr",
}
