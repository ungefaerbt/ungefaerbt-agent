BREAKING_SEEN_DATEI = "breaking_seen.json"
BREAKING_QUELLEN_SCHWELLE = 3
NORMAL_ZEITEN = ["06:00", "11:00", "16:00", "20:00"]
BREAKING_INTERVALL_MIN = 15

QUELLEN = {
    # ── DEUTSCHLAND ÜBERREGIONAL ────────────────────────────────
    "tagesschau.de":            {"rss": "https://www.tagesschau.de/xml/rss2/",                                          "ausrichtung": "Mitte"},
    "zdf.de":                   {"rss": "https://www.zdfheute.de/rss/zdf/nachrichten",                                  "ausrichtung": "Mitte"},
    "deutschlandfunk.de":       {"rss": "https://www.deutschlandfunk.de/rss/nachrichten",                               "ausrichtung": "Mitte"},
    "mdr.de":                   {"rss": "https://www.mdr.de/nachrichten/index-rss.xml",                                 "ausrichtung": "Mitte"},
    "ndr.de":                   {"rss": "https://www.ndr.de/home/index-rss.xml",                                  "ausrichtung": "Mitte"},
    "wdr.de":                   {"rss": "https://www.wdr.de/xml/newsticker.rdf",                                        "ausrichtung": "Mitte"},
    "swr.de":                   {"rss": "https://www.swr.de/~rss/swraktuell/swraktuell-100.xml",                        "ausrichtung": "Mitte"},
    "rbb24.de":                 {"rss": "https://www.rbb24.de/aktuell/index.xml/feed=rss.xml",                          "ausrichtung": "Mitte"},
    "phoenix.de":               {"rss": "https://www.phoenix.de/podcast/runde/video/rss.xml",                       "ausrichtung": "Mitte"},
    "spiegel.de":               {"rss": "https://www.spiegel.de/schlagzeilen/index.rss",                                "ausrichtung": "Mitte-Links"},
    "zeit.de":                  {"rss": "https://newsfeed.zeit.de/index",                                               "ausrichtung": "Mitte-Links"},
    "sueddeutsche.de":          {"rss": "https://rss.sueddeutsche.de/alles",                                            "ausrichtung": "Links"},
    "faz.net":                  {"rss": "https://www.faz.net/rss/aktuell/",                                             "ausrichtung": "Mitte-Rechts"},
    "welt.de":                  {"rss": "https://www.welt.de/feeds/latest.rss",                                         "ausrichtung": "Rechts"},
    "bild.de":                  {"rss": "https://www.bild.de/rssfeeds/rss3-20745882,feed=alles.bild.html",              "ausrichtung": "Rechts"},
    # ── MITTE-LINKS ─────────────────────────────────────────────
    "stern.de":                 {"rss": "https://www.stern.de/feed/standard/all/",                                    "ausrichtung": "Mitte-Links"},
    "augsburger-allgemeine.de": {"rss": "https://www.augsburger-allgemeine.de/rss",                                     "ausrichtung": "Mitte-Links"},
    # ── LINKS ───────────────────────────────────────────────────
    "taz.de":                   {"rss": "https://taz.de/!p4608;rss/",                                                   "ausrichtung": "Links"},
    "netzpolitik.org":          {"rss": "https://netzpolitik.org/feed/",                                                "ausrichtung": "Links"},
    "junge-welt.de":            {"rss": "https://www.jungewelt.de/feeds/newsticker.rss",                             "ausrichtung": "Links"},
    "nd-aktuell.de":            {"rss": "https://www.nd-aktuell.de/rss/aktuell.php",                                    "ausrichtung": "Links"},
    "jungle.world":             {"rss": "https://jungle.world/rss.xml",                                                 "ausrichtung": "Links"},
    "freitag.de":               {"rss": "https://www.freitag.de/rss.xml",                                               "ausrichtung": "Links"},
    # ── MITTE-RECHTS ────────────────────────────────────────────
    "handelsblatt.com":         {"rss": "https://www.handelsblatt.com/contentexport/feed/schlagzeilen",                 "ausrichtung": "Mitte-Rechts"},
    "manager-magazin.de":       {"rss": "https://www.manager-magazin.de/news/index.rss",                               "ausrichtung": "Mitte-Rechts"},
    "capital.de":               {"rss": "https://www.capital.de/feed",                                                  "ausrichtung": "Mitte-Rechts"},
    "focus.de":                 {"rss": "https://www.focus.de/rss",                                                     "ausrichtung": "Mitte-Rechts"},
    "merkur.de":                {"rss": "https://www.merkur.de/rssfeed.rdf",                                            "ausrichtung": "Mitte-Rechts"},
    "morgenpost.de":            {"rss": "https://www.morgenpost.de/rss",                                                "ausrichtung": "Mitte-Rechts"},
    "n-tv.de":                  {"rss": "https://www.n-tv.de/rss",                                                      "ausrichtung": "Mitte-Rechts"},
    # ── RECHTS ──────────────────────────────────────────────────
    "junge-freiheit.de":        {"rss": "https://jungefreiheit.de/feed/",                                               "ausrichtung": "Rechts"},
    "cicero.de":                {"rss": "https://www.cicero.de/rss.xml",                                                "ausrichtung": "Rechts"},
    # ── FACHMEDIEN ──────────────────────────────────────────────
    "heise.de":                 {"rss": "https://www.heise.de/rss/heise-atom.xml",                                      "ausrichtung": "Mitte"},
    "t3n.de":                   {"rss": "https://t3n.de/rss.xml",                                                       "ausrichtung": "Mitte"},
    "golem.de":                 {"rss": "https://www.golem.de/rss",                                                     "ausrichtung": "Mitte"},
    # ── DEUTSCHLAND (Ergänzung) ─────────────────────────────
    "t-online.de":              {"rss": "https://www.t-online.de/feed.rss",                                             "ausrichtung": "Mitte"},
    "dw.com":                   {"rss": "https://rss.dw.com/rdf/rss-de-all",                                            "ausrichtung": "Mitte"},
    # ── SPORT ───────────────────────────────────────────────────
    "kicker.de":                {"rss": "https://newsfeed.kicker.de/news/fussball",                                     "ausrichtung": "Mitte"},
    "sportschau.de":            {"rss": "https://www.sportschau.de/index~rss2.xml",                                     "ausrichtung": "Mitte"},
    # ── REGIONAL ────────────────────────────────────────────────
    "haz.de":                   {"rss": "https://www.haz.de/arc/outboundfeeds/rss",                                  "ausrichtung": "Mitte"},
    "mopo.de":                  {"rss": "https://www.mopo.de/feed/",                                                    "ausrichtung": "Mitte-Links"},
    # ── ÖSTERREICH ──────────────────────────────────────────────
    "derstandard.at":           {"rss": "https://www.derstandard.at/rss",                                               "ausrichtung": "Mitte-Links"},
    "diepresse.com":            {"rss": "https://www.diepresse.com/rss",                                             "ausrichtung": "Mitte-Rechts"},
    "krone.at":                 {"rss": "https://api.krone.at/v1/rss/rssfeed-nachrichten.html",                     "ausrichtung": "Rechts"},
    "kleinezeitung.at":         {"rss": "https://www.kleinezeitung.at/rss",                                             "ausrichtung": "Mitte"},
    # ── ÖSTERREICH (Ergänzung) ──────────────────────────────
    "orf.at":                   {"rss": "https://rss.orf.at/news.xml",                                                  "ausrichtung": "Mitte"},
    # ── SCHWEIZ ─────────────────────────────────────────────────
    "tagesanzeiger.ch":         {"rss": "https://www.tagesanzeiger.ch/rss.html",                                       "ausrichtung": "Mitte-Links"},
    "blick.ch":                 {"rss": "https://www.blick.ch/rss.xml",                                                 "ausrichtung": "Mitte"},
    "20min.ch":                 {"rss": "https://partner-feeds.20min.ch/rss/20minuten",                               "ausrichtung": "Mitte"},
    "srf.ch":                   {"rss": "https://www.srf.ch/news/bnf/rss/1646",                                         "ausrichtung": "Mitte"},
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
