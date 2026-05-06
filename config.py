BREAKING_SEEN_DATEI = "breaking_seen.json"
BREAKING_QUELLEN_SCHWELLE = 3
NORMAL_ZEITEN = ["06:00", "11:00", "16:00", "20:00"]
BREAKING_INTERVALL_MIN = 15

QUELLEN = {
    # ── DEUTSCHLAND ÜBERREGIONAL ────────────────────────────────
    "tagesschau.de":            {"rss": "https://www.tagesschau.de/xml/rss2/",                                          "ausrichtung": "Mitte"},
    "zdf.de":                   {"rss": "https://www.zdf.de/rss/zdf/nachrichten.xml",                                   "ausrichtung": "Mitte"},
    "deutschlandfunk.de":       {"rss": "https://www.deutschlandfunk.de/rss/nachrichten",                               "ausrichtung": "Mitte"},
    "mdr.de":                   {"rss": "https://www.mdr.de/nachrichten/index-rss.xml",                                 "ausrichtung": "Mitte"},
    "ndr.de":                   {"rss": "https://www.ndr.de/nachrichten/aktuell/index-rss.xml",                         "ausrichtung": "Mitte"},
    "br.de":                    {"rss": "https://www.br.de/nachrichten/index.rss",                                      "ausrichtung": "Mitte"},
    "wdr.de":                   {"rss": "https://www1.wdr.de/nachrichten/rss/alles100.rss",                             "ausrichtung": "Mitte"},
    "swr.de":                   {"rss": "https://www.swr.de/nachrichten/feed/nachrichten-rss.xml",                      "ausrichtung": "Mitte"},
    "rbb24.de":                 {"rss": "https://www.rbb24.de/rss/rbb24.xml",                                           "ausrichtung": "Mitte"},
    "phoenix.de":               {"rss": "https://www.phoenix.de/rss/phoenix.rss",                                       "ausrichtung": "Mitte"},
    "spiegel.de":               {"rss": "https://www.spiegel.de/schlagzeilen/index.rss",                                "ausrichtung": "Mitte-Links"},
    "zeit.de":                  {"rss": "https://newsfeed.zeit.de/index",                                               "ausrichtung": "Mitte-Links"},
    "sueddeutsche.de":          {"rss": "https://rss.sueddeutsche.de/alles",                                            "ausrichtung": "Links"},
    "faz.net":                  {"rss": "https://www.faz.net/rss/aktuell/",                                             "ausrichtung": "Mitte-Rechts"},
    "welt.de":                  {"rss": "https://www.welt.de/feeds/latest.rss",                                         "ausrichtung": "Rechts"},
    "bild.de":                  {"rss": "https://www.bild.de/rssfeeds/rss3-20745882,feed=alles.bild.html",              "ausrichtung": "Rechts"},
    # ── MITTE-LINKS ─────────────────────────────────────────────
    "fr.de":                    {"rss": "https://www.fr.de/rss/aktuell.rss",                                            "ausrichtung": "Mitte-Links"},
    "rnd.de":                   {"rss": "https://www.rnd.de/feed.rss",                                                  "ausrichtung": "Mitte-Links"},
    "berliner-zeitung.de":      {"rss": "https://www.berliner-zeitung.de/feed.rss",                                     "ausrichtung": "Mitte-Links"},
    "tagesspiegel.de":          {"rss": "https://www.tagesspiegel.de/contentexport/feed/home",                          "ausrichtung": "Mitte-Links"},
    "stern.de":                 {"rss": "https://www.stern.de/feed.rss",                                                "ausrichtung": "Mitte-Links"},
    "augsburger-allgemeine.de": {"rss": "https://www.augsburger-allgemeine.de/rss",                                     "ausrichtung": "Mitte-Links"},
    # ── LINKS ───────────────────────────────────────────────────
    "taz.de":                   {"rss": "https://taz.de/!p4608;rss/",                                                   "ausrichtung": "Links"},
    "netzpolitik.org":          {"rss": "https://netzpolitik.org/feed/",                                                "ausrichtung": "Links"},
    "correctiv.org":            {"rss": "https://correctiv.org/feed/",                                                  "ausrichtung": "Links"},
    "junge-welt.de":            {"rss": "https://www.jungewelt.de/feed.rss",                                            "ausrichtung": "Links"},
    "nd-aktuell.de":            {"rss": "https://www.nd-aktuell.de/rss.xml",                                            "ausrichtung": "Links"},
    "jungle.world":             {"rss": "https://jungle.world/rss.xml",                                                 "ausrichtung": "Links"},
    "freitag.de":               {"rss": "https://www.freitag.de/rss.xml",                                               "ausrichtung": "Links"},
    # ── MITTE-RECHTS ────────────────────────────────────────────
    "handelsblatt.com":         {"rss": "https://www.handelsblatt.com/contentexport/feed/schlagzeilen",                 "ausrichtung": "Mitte-Rechts"},
    "wiwo.de":                  {"rss": "https://www.wiwo.de/rss/newsfeed.rss",                                         "ausrichtung": "Mitte-Rechts"},
    "manager-magazin.de":       {"rss": "https://www.manager-magazin.de/schlagzeilen/index.rss",                        "ausrichtung": "Mitte-Rechts"},
    "capital.de":               {"rss": "https://www.capital.de/feed",                                                  "ausrichtung": "Mitte-Rechts"},
    "focus.de":                 {"rss": "https://rss.focus.de/fol/XML/rss_folnews.xml",                                 "ausrichtung": "Mitte-Rechts"},
    "merkur.de":                {"rss": "https://www.merkur.de/rss.xml",                                                "ausrichtung": "Mitte-Rechts"},
    "morgenpost.de":            {"rss": "https://www.morgenpost.de/rss.xml",                                            "ausrichtung": "Mitte-Rechts"},
    "rp-online.de":             {"rss": "https://rp-online.de/feed.rss",                                                "ausrichtung": "Mitte-Rechts"},
    "n-tv.de":                  {"rss": "https://www.n-tv.de/rss",                                                      "ausrichtung": "Mitte-Rechts"},
    # ── RECHTS ──────────────────────────────────────────────────
    "tichyseinblick.de":        {"rss": "https://www.tichyseinblick.de/feed/",                                          "ausrichtung": "Rechts"},
    "junge-freiheit.de":        {"rss": "https://jungefreiheit.de/feed/",                                               "ausrichtung": "Rechts"},
    "achgut.com":               {"rss": "https://www.achgut.com/feed",                                                  "ausrichtung": "Rechts"},
    "cicero.de":                {"rss": "https://www.cicero.de/feed.rss",                                               "ausrichtung": "Rechts"},
    # ── FACHMEDIEN ──────────────────────────────────────────────
    "heise.de":                 {"rss": "https://www.heise.de/rss/heise-atom.xml",                                      "ausrichtung": "Mitte"},
    "t3n.de":                   {"rss": "https://t3n.de/rss.xml",                                                       "ausrichtung": "Mitte"},
    "golem.de":                 {"rss": "https://www.golem.de/rss",                                                     "ausrichtung": "Mitte"},
    # ── SPORT ───────────────────────────────────────────────────
    "kicker.de":                {"rss": "https://newsfeed.kicker.de/",                                                  "ausrichtung": "Mitte"},
    "sportschau.de":            {"rss": "https://www.sportschau.de/rss/sportschau100-rss.xml",                          "ausrichtung": "Mitte"},
    # ── REGIONAL ────────────────────────────────────────────────
    "stuttgarter-zeitung.de":   {"rss": "https://www.stuttgarter-zeitung.de/rss/topthemen.rss",                         "ausrichtung": "Mitte"},
    "stuttgarter-nachrichten.de":{"rss": "https://www.stuttgarter-nachrichten.de/rss/topthemen.rss",                   "ausrichtung": "Mitte"},
    "haz.de":                   {"rss": "https://www.haz.de/rss/topthemen.rss",                                         "ausrichtung": "Mitte"},
    "mopo.de":                  {"rss": "https://www.mopo.de/feed/",                                                    "ausrichtung": "Mitte-Links"},
    "ksta.de":                  {"rss": "https://www.ksta.de/rss.xml",                                                  "ausrichtung": "Mitte"},
    # ── ÖSTERREICH ──────────────────────────────────────────────
    "derstandard.at":           {"rss": "https://www.derstandard.at/rss",                                               "ausrichtung": "Mitte-Links"},
    "diepresse.com":            {"rss": "https://www.diepresse.com/rss/home",                                           "ausrichtung": "Mitte-Rechts"},
    "krone.at":                 {"rss": "https://www.krone.at/rss/feed.rss",                                            "ausrichtung": "Rechts"},
    "kurier.at":                {"rss": "https://www.kurier.at/rss",                                                    "ausrichtung": "Mitte"},
    "kleinezeitung.at":         {"rss": "https://www.kleinezeitung.at/rss",                                             "ausrichtung": "Mitte"},
    # ── SCHWEIZ ─────────────────────────────────────────────────
    "nzz.ch":                   {"rss": "https://www.nzz.ch/recent.rss",                                                "ausrichtung": "Mitte-Rechts"},
    "tagesanzeiger.ch":         {"rss": "https://www.tagesanzeiger.ch/rss",                                             "ausrichtung": "Mitte-Links"},
    "blick.ch":                 {"rss": "https://www.blick.ch/rss.xml",                                                 "ausrichtung": "Mitte"},
    "watson.ch":                {"rss": "https://www.watson.ch/rss",                                                    "ausrichtung": "Mitte-Links"},
    "20min.ch":                 {"rss": "https://www.20min.ch/rss/feeds/news.rss",                                      "ausrichtung": "Mitte"},
    "srf.ch":                   {"rss": "https://www.srf.ch/news/bnf/rss/1646",                                         "ausrichtung": "Mitte"},
    "republik.ch":              {"rss": "https://www.republik.ch/feed.atom",                                            "ausrichtung": "Links"},
    # ── NACHRICHTENAGENTUREN ────────────────────────────────────
    "dpa.com":                  {"rss": "https://www.dpa.com/de/nachrichten/feed",                                      "ausrichtung": "Mitte"},
    "afp.com":                  {"rss": "https://www.afp.com/en/latest-news/feed",                                      "ausrichtung": "Mitte"},
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
