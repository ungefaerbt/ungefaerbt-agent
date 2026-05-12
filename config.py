BREAKING_SEEN_DATEI = "breaking_seen.json"
BREAKING_QUELLEN_SCHWELLE = 3
NORMAL_ZEITEN = ["06:00", "11:00", "16:00", "20:00"]
BREAKING_INTERVALL_MIN = 15

QUELLEN = {
    # ── DEUTSCHLAND ÜBERREGIONAL ────────────────────────────────
    "tagesschau.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",    "rss": "https://www.tagesschau.de/xml/rss2",                          "enabled": True},
            {"ressort": "inland",       "rss": "https://www.tagesschau.de/inland/index~rss2.xml",             "enabled": True},
            {"ressort": "ausland",      "rss": "https://www.tagesschau.de/ausland/index~rss2.xml",            "enabled": True},
            {"ressort": "wirtschaft",   "rss": "https://www.tagesschau.de/wirtschaft/index~rss2.xml",         "enabled": True},
            {"ressort": "wissen",       "rss": "https://www.tagesschau.de/wissen/index~rss2.xml",             "enabled": True},
            {"ressort": "faktenfinder", "rss": "https://www.tagesschau.de/faktenfinder/index~rss2.xml",       "enabled": True},
        ],
    },
    "zdf.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "nachrichten",         "rss": "https://www.zdf.de/rss/zdf/nachrichten",          "enabled": True},
            {"ressort": "politik_gesellschaft", "rss": "https://www.zdf.de/rss/zdf/politik-gesellschaft", "enabled": True},
        ],
    },
    "deutschlandfunk.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "nachrichten",  "rss": "https://www.deutschlandfunk.de/nachrichten-100.rss",    "enabled": True},
            {"ressort": "politik",      "rss": "https://www.deutschlandfunk.de/politikportal-100.rss",  "enabled": True},
            {"ressort": "wirtschaft",   "rss": "https://www.deutschlandfunk.de/wirtschaft-106.rss",     "enabled": True},
            {"ressort": "wissen",       "rss": "https://www.deutschlandfunk.de/wissen-106.rss",         "enabled": True},
            {"ressort": "kultur",       "rss": "https://www.deutschlandfunk.de/kulturportal-100.rss",   "enabled": True},
            {"ressort": "europa",       "rss": "https://www.deutschlandfunk.de/europa-112.rss",         "enabled": True},
            {"ressort": "gesellschaft", "rss": "https://www.deutschlandfunk.de/gesellschaft-106.rss",   "enabled": True},
            {"ressort": "sport",        "rss": "https://www.deutschlandfunk.de/sportportal-100.rss",    "enabled": True},
        ],
    },
    "mdr.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "nachrichten", "rss": "https://www.mdr.de/nachrichten/index-rss.xml", "enabled": True},
        ],
    },
    "ndr.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.ndr.de/home/index-rss.xml", "enabled": True},
        ],
    },
    "wdr.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "newsticker", "rss": "https://www.wdr.de/xml/newsticker.rdf", "enabled": True},
        ],
    },
    "swr.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "swraktuell", "rss": "https://www.swr.de/~rss/swraktuell/swraktuell-100.xml", "enabled": True},
        ],
    },
    "rbb24.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "aktuell", "rss": "https://www.rbb24.de/aktuell/index.xml/feed=rss.xml", "enabled": True},
        ],
    },
    "br.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "nachrichten", "rss": "https://www.br.de/nachrichten/meldungen/nachrichten-bayerischer-rundfunk100~newsRss.xml", "enabled": True},
        ],
    },
    "phoenix.de": {
        "ausrichtung": "Mitte",
        "enabled": False,
        "feeds": [
            {"ressort": "runde_podcast", "rss": "https://www.phoenix.de/podcast/runde/video/rss.xml", "enabled": False},
        ],
    },
    "spiegel.de": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",          "rss": "https://www.spiegel.de/schlagzeilen/index.rss",              "enabled": True},
            {"ressort": "eilmeldungen",        "rss": "https://www.spiegel.de/schlagzeilen/eilmeldungen/index.rss", "enabled": True},
            {"ressort": "politik",             "rss": "https://www.spiegel.de/politik/index.rss",                   "enabled": True},
            {"ressort": "politik_deutschland", "rss": "https://www.spiegel.de/politik/deutschland/index.rss",       "enabled": True},
            {"ressort": "ausland",             "rss": "https://www.spiegel.de/ausland/index.rss",                   "enabled": True},
            {"ressort": "wirtschaft",          "rss": "https://www.spiegel.de/wirtschaft/index.rss",                "enabled": True},
            {"ressort": "panorama",            "rss": "https://www.spiegel.de/panorama/index.rss",                  "enabled": True},
            {"ressort": "kultur",              "rss": "https://www.spiegel.de/kultur/index.rss",                    "enabled": True},
            {"ressort": "wissenschaft",        "rss": "https://www.spiegel.de/wissenschaft/index.rss",              "enabled": True},
            {"ressort": "netzwelt",            "rss": "https://www.spiegel.de/netzwelt/index.rss",                  "enabled": True},
            {"ressort": "sport",               "rss": "https://www.spiegel.de/sport/index.rss",                     "enabled": True},
        ],
    },
    "zeit.de": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",    "rss": "https://newsfeed.zeit.de/index",             "enabled": True},
            {"ressort": "news",         "rss": "https://newsfeed.zeit.de/news/index",         "enabled": True},
            {"ressort": "politik",      "rss": "https://newsfeed.zeit.de/politik/index",      "enabled": True},
            {"ressort": "wirtschaft",   "rss": "https://newsfeed.zeit.de/wirtschaft/index",   "enabled": True},
            {"ressort": "gesellschaft", "rss": "https://newsfeed.zeit.de/gesellschaft/index", "enabled": True},
            {"ressort": "kultur",       "rss": "https://newsfeed.zeit.de/kultur/index",       "enabled": False},
            {"ressort": "wissen",       "rss": "https://newsfeed.zeit.de/wissen/index",       "enabled": True},
            {"ressort": "digital",      "rss": "https://newsfeed.zeit.de/digital/index",      "enabled": True},
            {"ressort": "sport",        "rss": "https://newsfeed.zeit.de/sport/index",        "enabled": True},
        ],
    },
    "sueddeutsche.de": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",    "rss": "https://rss.sueddeutsche.de/alles",            "enabled": True},
            {"ressort": "topthemen",    "rss": "https://rss.sueddeutsche.de/rss/Topthemen",    "enabled": True},
            {"ressort": "politik",      "rss": "https://rss.sueddeutsche.de/rss/Politik",      "enabled": True},
            {"ressort": "wirtschaft",   "rss": "https://rss.sueddeutsche.de/rss/Wirtschaft",   "enabled": True},
            {"ressort": "panorama",     "rss": "https://rss.sueddeutsche.de/rss/Panorama",     "enabled": True},
            {"ressort": "gesellschaft", "rss": "https://rss.sueddeutsche.de/rss/Gesellschaft", "enabled": False},
            {"ressort": "kultur",       "rss": "https://rss.sueddeutsche.de/rss/Kultur",       "enabled": True},
            {"ressort": "wissen",       "rss": "https://rss.sueddeutsche.de/rss/Wissen",       "enabled": True},
            {"ressort": "sport",        "rss": "https://rss.sueddeutsche.de/rss/Sport",        "enabled": True},
            {"ressort": "medien",       "rss": "https://rss.sueddeutsche.de/rss/Medien",       "enabled": False},
        ],
    },
    "faz.net": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",       "rss": "https://www.faz.net/rss/aktuell/",                 "enabled": True},
            {"ressort": "politik",         "rss": "https://www.faz.net/rss/aktuell/politik/",         "enabled": True},
            {"ressort": "politik_inland",  "rss": "https://www.faz.net/rss/aktuell/politik/inland/",  "enabled": False},
            {"ressort": "politik_ausland", "rss": "https://www.faz.net/rss/aktuell/politik/ausland/", "enabled": False},
            {"ressort": "wirtschaft",      "rss": "https://www.faz.net/rss/aktuell/wirtschaft/",      "enabled": True},
            {"ressort": "finanzen",        "rss": "https://www.faz.net/rss/aktuell/finanzen/",        "enabled": True},
            {"ressort": "feuilleton",      "rss": "https://www.faz.net/rss/aktuell/feuilleton/",      "enabled": True},
            {"ressort": "wissen",          "rss": "https://www.faz.net/rss/aktuell/wissen/",          "enabled": True},
            {"ressort": "technik_motor",   "rss": "https://www.faz.net/rss/aktuell/technik-motor/",   "enabled": False},
            {"ressort": "sport",           "rss": "https://www.faz.net/rss/aktuell/sport/",           "enabled": True},
        ],
    },
    "welt.de": {
        "ausrichtung": "Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",  "rss": "https://www.welt.de/feeds/latest.rss",             "enabled": True},
            {"ressort": "politik",    "rss": "https://www.welt.de/feeds/section/politik.rss",    "enabled": True},
            {"ressort": "wirtschaft", "rss": "https://www.welt.de/feeds/section/wirtschaft.rss", "enabled": True},
            {"ressort": "finanzen",   "rss": "https://www.welt.de/feeds/section/finanzen.rss",   "enabled": True},
            {"ressort": "panorama",   "rss": "https://www.welt.de/feeds/section/panorama.rss",   "enabled": False},
            {"ressort": "sport",      "rss": "https://www.welt.de/feeds/section/sport.rss",      "enabled": True},
            {"ressort": "kultur",     "rss": "https://www.welt.de/feeds/section/kultur.rss",     "enabled": True},
            {"ressort": "wissen",     "rss": "https://www.welt.de/feeds/section/wissen.rss",     "enabled": False},
            {"ressort": "gesundheit", "rss": "https://www.welt.de/feeds/section/gesundheit.rss", "enabled": False},
            {"ressort": "debatte",    "rss": "https://www.welt.de/feeds/section/debatte.rss",    "enabled": False},
        ],
    },
    "bild.de": {
        "ausrichtung": "Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",    "rss": "https://www.bild.de/rssfeeds/rss3-20745882,feed=alles.bild.html",        "enabled": True},
            {"ressort": "home",         "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=home.bild.html",         "enabled": True},
            {"ressort": "news",         "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=news.bild.html",         "enabled": True},
            {"ressort": "politik",      "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=politik.bild.html",      "enabled": True},
            {"ressort": "unterhaltung", "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=unterhaltung.bild.html", "enabled": False},
            {"ressort": "sport",        "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=sport.bild.html",        "enabled": True},
            {"ressort": "lifestyle",    "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=lifestyle.bild.html",    "enabled": False},
            {"ressort": "ratgeber",     "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=ratgeber.bild.html",     "enabled": False},
            {"ressort": "auto",         "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=auto.bild.html",         "enabled": False},
            {"ressort": "digital",      "rss": "https://www.bild.de/rss-feeds/rss-16725492,feed=digital.bild.html",      "enabled": True},
        ],
    },
    # ── MITTE-LINKS ─────────────────────────────────────────────
    "stern.de": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",        "rss": "https://www.stern.de/feed/standard/all/",            "enabled": True},
            {"ressort": "alle_nachrichten", "rss": "https://www.stern.de/feed/standard/alle-nachrichten/","enabled": True},
            {"ressort": "politik",          "rss": "https://www.stern.de/feed/standard/politik/",         "enabled": True},
            {"ressort": "panorama",         "rss": "https://www.stern.de/feed/standard/panorama/",        "enabled": True},
            {"ressort": "wirtschaft",       "rss": "https://www.stern.de/feed/standard/wirtschaft/",      "enabled": True},
            {"ressort": "kultur",           "rss": "https://www.stern.de/feed/standard/kultur/",          "enabled": True},
            {"ressort": "sport",            "rss": "https://www.stern.de/feed/standard/sport/",           "enabled": True},
            {"ressort": "digital",          "rss": "https://www.stern.de/feed/standard/digital/",         "enabled": True},
            {"ressort": "wissen",           "rss": "https://www.stern.de/feed/standard/wissen/",          "enabled": True},
            {"ressort": "gesundheit",       "rss": "https://www.stern.de/feed/standard/gesundheit/",      "enabled": False},
            {"ressort": "lifestyle",        "rss": "https://www.stern.de/feed/standard/lifestyle/",       "enabled": False},
            {"ressort": "reise",            "rss": "https://www.stern.de/feed/standard/reise/",           "enabled": False},
            {"ressort": "auto",             "rss": "https://www.stern.de/feed/standard/auto/",            "enabled": False},
            {"ressort": "genuss",           "rss": "https://www.stern.de/feed/standard/genuss/",          "enabled": False},
            {"ressort": "familie",          "rss": "https://www.stern.de/feed/standard/familie/",         "enabled": False},
            {"ressort": "video",            "rss": "https://www.stern.de/feed/standard/video/",           "enabled": False},
        ],
    },
    "augsburger-allgemeine.de": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.augsburger-allgemeine.de/rss", "enabled": True},
        ],
    },
    "rnd.de": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",        "rss": "https://www.rnd.de/arc/outboundfeeds/rss/",                            "enabled": True},
            {"ressort": "politik",          "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/politik/",           "enabled": True},
            {"ressort": "wirtschaft",       "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/wirtschaft/",        "enabled": True},
            {"ressort": "sport",            "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/sport/",             "enabled": True},
            {"ressort": "panorama",         "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/panorama/",          "enabled": True},
            {"ressort": "digital",          "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/digital/",           "enabled": True},
            {"ressort": "kultur",           "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/kultur/",            "enabled": True},
            {"ressort": "wissen",           "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/wissen/",            "enabled": True},
            {"ressort": "geld_finanzen",    "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/geld-finanzen/",     "enabled": True},
            {"ressort": "promis",           "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/promis/",            "enabled": False},
            {"ressort": "reise",            "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/reise/",             "enabled": False},
            {"ressort": "medien",           "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/medien/",            "enabled": False},
            {"ressort": "familie",          "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/familie/",           "enabled": False},
            {"ressort": "gesundheit",       "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/gesundheit/",        "enabled": False},
            {"ressort": "lifestyle",        "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/lifestyle/",         "enabled": False},
            {"ressort": "bauen_wohnen",     "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/bauen-wohnen/",      "enabled": False},
            {"ressort": "liebe_partnerschaft","rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/liebe-partnerschaft/","enabled": False},
            {"ressort": "beruf_bildung",    "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/beruf-bildung/",     "enabled": False},
            {"ressort": "e_mobility",       "rss": "https://www.rnd.de/arc/outboundfeeds/rss/category/e-mobility/",        "enabled": False},
        ],
    },
    # ── LINKS ───────────────────────────────────────────────────
    "taz.de": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",    "rss": "https://taz.de/!p4608;rss/",              "enabled": True},
            {"ressort": "politik",      "rss": "https://taz.de/Politik/!p4615;rss/",      "enabled": True},
            {"ressort": "oeko",         "rss": "https://taz.de/Oeko/!p4610;rss/",         "enabled": True},
            {"ressort": "gesellschaft", "rss": "https://taz.de/Gesellschaft/!p4611;rss/", "enabled": True},
            {"ressort": "kultur",       "rss": "https://taz.de/Kultur/!p4639;rss/",       "enabled": True},
            {"ressort": "sport",        "rss": "https://taz.de/Sport/!p4646;rss/",        "enabled": True},
            {"ressort": "berlin",       "rss": "https://taz.de/Berlin/!p4647;rss/",       "enabled": False},
            {"ressort": "nord",         "rss": "https://taz.de/Nord/!p4648;rss/",         "enabled": False},
        ],
    },
    "netzpolitik.org": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://netzpolitik.org/feed/", "enabled": True},
        ],
    },
    "junge-welt.de": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "newsticker", "rss": "https://www.jungewelt.de/feeds/newsticker.rss", "enabled": True},
        ],
    },
    "nd-aktuell.de": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "aktuell", "rss": "https://www.nd-aktuell.de/rss/aktuell.php", "enabled": True},
        ],
    },
    "jungle.world": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://jungle.world/rss.xml", "enabled": True},
        ],
    },
    "freitag.de": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.freitag.de/rss.xml",            "enabled": True},
            {"ressort": "politik",   "rss": "https://www.freitag.de/politik/@@rss.xml",  "enabled": False},
            {"ressort": "kultur",    "rss": "https://www.freitag.de/kultur/@@rss.xml",   "enabled": False},
        ],
    },
    "correctiv.org": {
        "ausrichtung": "Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",                       "rss": "https://correctiv.org/feed/",                                                    "enabled": True},
            {"ressort": "faktencheck",                     "rss": "https://correctiv.org/faktencheck/feed/",                                         "enabled": True},
            {"ressort": "faktencheck_politik",             "rss": "https://correctiv.org/faktencheck/politik/feed/",                                 "enabled": True},
            {"ressort": "faktencheck_gesellschaft",        "rss": "https://correctiv.org/faktencheck/gesellschaft/feed/",                            "enabled": True},
            {"ressort": "faktencheck_klima",               "rss": "https://correctiv.org/faktencheck/klima/feed/",                                   "enabled": True},
            {"ressort": "faktencheck_europa",              "rss": "https://correctiv.org/faktencheck/europa/feed/",                                  "enabled": True},
            {"ressort": "faktencheck_russland_ukraine",    "rss": "https://correctiv.org/faktencheck/russland-ukraine/feed/",                        "enabled": True},
            {"ressort": "faktencheck_wirtschaft_umwelt",   "rss": "https://correctiv.org/faktencheck/wirtschaft-und-umwelt/feed/",                   "enabled": True},
            {"ressort": "faktencheck_naher_osten",         "rss": "https://correctiv.org/faktencheck/naher-osten/feed/",                             "enabled": True},
            {"ressort": "faktencheck_hintergrund",         "rss": "https://correctiv.org/faktencheck/hintergrund/feed/",                             "enabled": False},
            {"ressort": "faktencheck_russische_desinformation","rss": "https://correctiv.org/faktencheck/russische-desinformation/feed/",             "enabled": False},
            {"ressort": "faktencheck_community",           "rss": "https://correctiv.org/faktencheck/aus-der-community/feed/",                       "enabled": False},
            {"ressort": "faktencheck_gesundheit",          "rss": "https://correctiv.org/faktencheck/medizin-und-gesundheit/feed/",                  "enabled": False},
            {"ressort": "faktencheck_justiz",              "rss": "https://correctiv.org/faktencheck/justiz/feed/",                                  "enabled": False},
            {"ressort": "faktencheck_polizei",             "rss": "https://correctiv.org/faktencheck/polizei/feed/",                                 "enabled": False},
            {"ressort": "faktencheck_tipps",               "rss": "https://correctiv.org/faktencheck/tipps/feed/",                                   "enabled": False},
        ],
    },
    # ── MITTE-RECHTS ────────────────────────────────────────────
    "handelsblatt.com": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",       "rss": "https://feeds.cms.handelsblatt.com/schlagzeilen",    "enabled": True},
            {"ressort": "finanzen",        "rss": "https://feeds.cms.handelsblatt.com/finanzen",        "enabled": True},
            {"ressort": "unternehmen",     "rss": "https://feeds.cms.handelsblatt.com/unternehmen",     "enabled": True},
            {"ressort": "politik",         "rss": "https://feeds.cms.handelsblatt.com/politik",         "enabled": True},
            {"ressort": "technologie",     "rss": "https://feeds.cms.handelsblatt.com/technologie",     "enabled": True},
            {"ressort": "marktberichte",   "rss": "https://feeds.cms.handelsblatt.com/marktberichte",   "enabled": False},
            {"ressort": "anlagestrategie", "rss": "https://feeds.cms.handelsblatt.com/anlagestrategie", "enabled": False},
        ],
    },
    "manager-magazin.de": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": False,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.manager-magazin.de/news/index.rss", "enabled": False},
        ],
    },
    "capital.de": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": False,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.capital.de/rss", "enabled": False},
        ],
    },
    "focus.de": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",  "rss": "https://www.focus.de/rss",            "enabled": True},
            {"ressort": "politik",    "rss": "https://www.focus.de/politik/rss",    "enabled": True},
            {"ressort": "finanzen",   "rss": "https://www.focus.de/finanzen/rss",   "enabled": True},
            {"ressort": "digital",    "rss": "https://www.focus.de/digital/rss",    "enabled": True},
            {"ressort": "gesundheit", "rss": "https://www.focus.de/gesundheit/rss", "enabled": False},
            {"ressort": "auto",       "rss": "https://www.focus.de/auto/rss",       "enabled": False},
            {"ressort": "reisen",     "rss": "https://www.focus.de/reisen/rss",     "enabled": False},
            {"ressort": "immobilien", "rss": "https://www.focus.de/immobilien/rss", "enabled": False},
            {"ressort": "kultur",     "rss": "https://www.focus.de/kultur/rss",     "enabled": True},
            {"ressort": "sport",      "rss": "https://www.focus.de/sport/rss",      "enabled": True},
            {"ressort": "panorama",   "rss": "https://www.focus.de/panorama/rss",   "enabled": True},
        ],
    },
    "merkur.de": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.merkur.de/rssfeed.rdf", "enabled": True},
        ],
    },
    "morgenpost.de": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.morgenpost.de/rss", "enabled": True},
        ],
    },
    "n-tv.de": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",    "rss": "https://www.n-tv.de/rss",              "enabled": True},
            {"ressort": "politik",      "rss": "https://www.n-tv.de/politik/rss",      "enabled": True},
            {"ressort": "wirtschaft",   "rss": "https://www.n-tv.de/wirtschaft/rss",   "enabled": True},
            {"ressort": "boerse",       "rss": "https://www.n-tv.de/boersenkurse/rss", "enabled": False},
            {"ressort": "sport",        "rss": "https://www.n-tv.de/sport/rss",        "enabled": True},
            {"ressort": "panorama",     "rss": "https://www.n-tv.de/panorama/rss",     "enabled": True},
            {"ressort": "unterhaltung", "rss": "https://www.n-tv.de/leute/rss",        "enabled": False},
            {"ressort": "technik",      "rss": "https://www.n-tv.de/technik/rss",      "enabled": True},
            {"ressort": "wissen",       "rss": "https://www.n-tv.de/wissen/rss",       "enabled": True},
            {"ressort": "auto",         "rss": "https://www.n-tv.de/auto/rss",         "enabled": False},
        ],
    },
    # ── RECHTS ──────────────────────────────────────────────────
    "junge-freiheit.de": {
        "ausrichtung": "Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",  "rss": "https://jungefreiheit.de/feed/",            "enabled": True},
            {"ressort": "politik",    "rss": "https://jungefreiheit.de/politik/feed/",    "enabled": True},
            {"ressort": "wirtschaft", "rss": "https://jungefreiheit.de/wirtschaft/feed/", "enabled": False},
            {"ressort": "kultur",     "rss": "https://jungefreiheit.de/kultur/feed/",     "enabled": True},
        ],
    },
    "cicero.de": {
        "ausrichtung": "Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.cicero.de/rss.xml", "enabled": True},
        ],
    },
    # ── FACHMEDIEN ──────────────────────────────────────────────
    "heise.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",     "rss": "https://www.heise.de/rss/heise-atom.xml",                        "enabled": True},
            {"ressort": "top_news",      "rss": "https://www.heise.de/rss/heise-top-atom.xml",                    "enabled": True},
            {"ressort": "it",            "rss": "https://www.heise.de/rss/heise-Rubrik-IT-atom.xml",              "enabled": True},
            {"ressort": "wissen",        "rss": "https://www.heise.de/rss/heise-Rubrik-Wissen-atom.xml",          "enabled": True},
            {"ressort": "netzpolitik",   "rss": "https://www.heise.de/rss/heise-Rubrik-Netzpolitik-atom.xml",     "enabled": True},
            {"ressort": "wirtschaft",    "rss": "https://www.heise.de/rss/heise-Rubrik-Wirtschaft-atom.xml",      "enabled": True},
            {"ressort": "security",      "rss": "https://www.heise.de/security/feed.xml",                         "enabled": True},
            {"ressort": "mobiles",       "rss": "https://www.heise.de/rss/heise-Rubrik-Mobiles-atom.xml",         "enabled": False},
            {"ressort": "entertainment", "rss": "https://www.heise.de/rss/heise-Rubrik-Entertainment-atom.xml",   "enabled": False},
            {"ressort": "journal",       "rss": "https://www.heise.de/rss/heise-Rubrik-Journal-atom.xml",         "enabled": False},
            {"ressort": "developer",     "rss": "https://www.heise.de/developer/rss/news-atom.xml",               "enabled": False},
            {"ressort": "autos",         "rss": "https://www.heise.de/autos/feed.xml",                            "enabled": False},
        ],
    },
    "t3n.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://t3n.de/rss.xml", "enabled": True},
        ],
    },
    "golem.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://rss.golem.de/rss.php?feed=RSS2.0",                    "enabled": True},
            {"ressort": "security",  "rss": "https://rss.golem.de/rss.php?feed=RSS2.0&ms=security",        "enabled": True},
        ],
    },
    # ── DEUTSCHLAND (Ergänzung) ─────────────────────────────
    "t-online.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "politik",             "rss": "https://www.t-online.de/nachrichten/feed.rss",          "enabled": True},
            {"ressort": "ukraine",             "rss": "https://www.t-online.de/nachrichten/ukraine/feed.rss",  "enabled": True},
            {"ressort": "panorama",            "rss": "https://www.t-online.de/nachrichten/panorama/feed.rss", "enabled": True},
            {"ressort": "sport",               "rss": "https://www.t-online.de/sport/feed.rss",                "enabled": True},
            {"ressort": "fussball",            "rss": "https://www.t-online.de/sport/fussball/feed.rss",       "enabled": False},
            {"ressort": "unterhaltung",        "rss": "https://www.t-online.de/unterhaltung/feed.rss",         "enabled": False},
            {"ressort": "digital",             "rss": "https://www.t-online.de/digital/feed.rss",              "enabled": True},
            {"ressort": "wirtschaft_finanzen", "rss": "https://www.t-online.de/finanzen/feed.rss",             "enabled": True},
            {"ressort": "mobilitaet",          "rss": "https://www.t-online.de/mobilitaet/feed.rss",           "enabled": False},
            {"ressort": "gesundheit",          "rss": "https://www.t-online.de/gesundheit/feed.rss",           "enabled": False},
            {"ressort": "leben",               "rss": "https://www.t-online.de/leben/feed.rss",                "enabled": False},
            {"ressort": "nachhaltigkeit",      "rss": "https://www.t-online.de/nachhaltigkeit/feed.rss",       "enabled": True},
        ],
    },
    "dw.com": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",   "rss": "https://rss.dw.com/rdf/rss-de-all",  "enabled": True},
            {"ressort": "nachrichten", "rss": "https://rss.dw.com/rdf/rss-de-news", "enabled": True},
        ],
    },
    # ── SPORT ───────────────────────────────────────────────────
    "kicker.de": {
        "ausrichtung": "Mitte",
        "enabled": False,
        "feeds": [
            {"ressort": "fussball", "rss": "https://newsfeed.kicker.de/news/fussball", "enabled": False},
        ],
    },
    "sportschau.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "sport", "rss": "https://www.sportschau.de/index~rss2.xml", "enabled": True},
        ],
    },
    # ── REGIONAL ────────────────────────────────────────────────
    "haz.de": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.haz.de/arc/outboundfeeds/rss", "enabled": True},
        ],
    },
    "mopo.de": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.mopo.de/feed/", "enabled": True},
        ],
    },
    # ── ÖSTERREICH ──────────────────────────────────────────────
    "derstandard.at": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",     "rss": "https://www.derstandard.at/rss",               "enabled": True},
            {"ressort": "international", "rss": "https://www.derstandard.at/rss/international", "enabled": True},
            {"ressort": "inland",        "rss": "https://www.derstandard.at/rss/inland",        "enabled": True},
            {"ressort": "wirtschaft",    "rss": "https://www.derstandard.at/rss/wirtschaft",    "enabled": True},
            {"ressort": "web",           "rss": "https://www.derstandard.at/rss/web",           "enabled": True},
            {"ressort": "sport",         "rss": "https://www.derstandard.at/rss/sport",         "enabled": True},
            {"ressort": "panorama",      "rss": "https://www.derstandard.at/rss/panorama",      "enabled": True},
            {"ressort": "kultur",        "rss": "https://www.derstandard.at/rss/kultur",        "enabled": True},
            {"ressort": "wissenschaft",  "rss": "https://www.derstandard.at/rss/wissenschaft",  "enabled": True},
            {"ressort": "etat",          "rss": "https://www.derstandard.at/rss/etat",          "enabled": False},
            {"ressort": "gesundheit",    "rss": "https://www.derstandard.at/rss/gesundheit",    "enabled": False},
            {"ressort": "lifestyle",     "rss": "https://www.derstandard.at/rss/lifestyle",     "enabled": False},
            {"ressort": "karriere",      "rss": "https://www.derstandard.at/rss/karriere",      "enabled": False},
            {"ressort": "immobilien",    "rss": "https://www.derstandard.at/rss/immobilien",    "enabled": False},
            {"ressort": "diskurs",       "rss": "https://www.derstandard.at/rss/diskurs",       "enabled": False},
            {"ressort": "live",          "rss": "https://www.derstandard.at/rss/live",          "enabled": False},
            {"ressort": "video",         "rss": "https://www.derstandard.at/rss/video",         "enabled": False},
            {"ressort": "podcast",       "rss": "https://www.derstandard.at/rss/podcast",       "enabled": False},
            {"ressort": "recht",         "rss": "https://www.derstandard.at/rss/recht",         "enabled": False},
        ],
    },
    "diepresse.com": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.diepresse.com/rss", "enabled": True},
        ],
    },
    "krone.at": {
        "ausrichtung": "Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "nachrichten", "rss": "https://api.krone.at/v1/rss/rssfeed-nachrichten.html", "enabled": True},
        ],
    },
    "kleinezeitung.at": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",  "rss": "https://www.kleinezeitung.at/rss",           "enabled": True},
            {"ressort": "politik",    "rss": "https://www.kleinezeitung.at/rss/politik",   "enabled": True},
            {"ressort": "wirtschaft", "rss": "https://www.kleinezeitung.at/rss/wirtschaft","enabled": True},
            {"ressort": "sport",      "rss": "https://www.kleinezeitung.at/rss/sport",     "enabled": True},
            {"ressort": "kultur",     "rss": "https://www.kleinezeitung.at/rss/kultur",    "enabled": True},
        ],
    },
    "kurier.at": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",                  "rss": "https://kurier.at/xml/rssd",                                              "enabled": True},
            {"ressort": "politik",                    "rss": "https://kurier.at/politik/xml/rssd",                                      "enabled": True},
            {"ressort": "politik_inland",             "rss": "https://kurier.at/politik/inland/xml/rssd",                               "enabled": True},
            {"ressort": "politik_ausland",            "rss": "https://kurier.at/politik/ausland/xml/rssd",                              "enabled": True},
            {"ressort": "wirtschaft",                 "rss": "https://kurier.at/wirtschaft/xml/rssd",                                   "enabled": True},
            {"ressort": "wirtschaftspolitik",         "rss": "https://kurier.at/wirtschaft/wirtschaftspolitik/xml/rssd",                "enabled": True},
            {"ressort": "finanzen",                   "rss": "https://kurier.at/wirtschaft/finanzen/xml/rssd",                          "enabled": True},
            {"ressort": "boerse",                     "rss": "https://kurier.at/wirtschaft/Börse/xml/rssd",                             "enabled": False},
            {"ressort": "marktplatz",                 "rss": "https://kurier.at/wirtschaft/marktplatz/xml/rssd",                        "enabled": False},
            {"ressort": "chronik",                    "rss": "https://kurier.at/chronik/xml/rssd",                                      "enabled": True},
            {"ressort": "chronik_oesterreich",        "rss": "https://kurier.at/chronik/oesterreich/xml/rssd",                          "enabled": True},
            {"ressort": "chronik_wien",               "rss": "https://kurier.at/chronik/wien/xml/rssd",                                 "enabled": False},
            {"ressort": "chronik_niederoesterreich",  "rss": "https://kurier.at/chronik/niederoesterreich/xml/rssd",                    "enabled": False},
            {"ressort": "chronik_burgenland",         "rss": "https://kurier.at/chronik/burgenland/xml/rssd",                           "enabled": False},
            {"ressort": "chronik_oberoesterreich",    "rss": "https://kurier.at/chronik/oberoesterreich/xml/rssd",                      "enabled": False},
            {"ressort": "sport",                      "rss": "https://kurier.at/sport/xml/rssd",                                        "enabled": True},
            {"ressort": "sport_fussball",             "rss": "https://kurier.at/sport/fussball/xml/rssd",                               "enabled": False},
            {"ressort": "sport_motorsport",           "rss": "https://kurier.at/sport/motorsport/xml/rssd",                             "enabled": False},
            {"ressort": "sport_wintersport",          "rss": "https://kurier.at/sport/wintersport/xml/rssd",                            "enabled": False},
            {"ressort": "sport_sportmix",             "rss": "https://kurier.at/sport/sportmix/xml/rssd",                               "enabled": False},
            {"ressort": "kultur",                     "rss": "https://kurier.at/kultur/xml/rssd",                                       "enabled": True},
            {"ressort": "kultur_musik",               "rss": "https://kurier.at/kultur/musik/xml/rssd",                                 "enabled": False},
            {"ressort": "kultur_film",                "rss": "https://kurier.at/kultur/film/xml/rssd",                                  "enabled": False},
            {"ressort": "kultur_buehne",              "rss": "https://kurier.at/kultur/buehne/xml/rssd",                                "enabled": False},
            {"ressort": "kultur_kunst",               "rss": "https://kurier.at/kultur/kunst/xml/rssd",                                 "enabled": False},
            {"ressort": "kultur_literatur",           "rss": "https://kurier.at/kultur/literatur/xml/rssd",                             "enabled": False},
            {"ressort": "kultur_medien",              "rss": "https://kurier.at/kultur/medien/xml/rssd",                                "enabled": False},
            {"ressort": "kultur_fotografie",          "rss": "https://kurier.at/kultur/fotografie/xml/rssd",                            "enabled": False},
            {"ressort": "lebensart_technik",          "rss": "https://kurier.at/lebensart/technik/xml/rssd",                            "enabled": True},
            {"ressort": "lebensart",                  "rss": "https://kurier.at/lebensart/xml/rssd",                                    "enabled": False},
            {"ressort": "lebensart_style",            "rss": "https://kurier.at/lebensart/style/xml/rssd",                              "enabled": False},
            {"ressort": "lebensart_reise",            "rss": "https://kurier.at/lebensart/reise/xml/rssd",                              "enabled": False},
            {"ressort": "lebensart_genuss",           "rss": "https://kurier.at/lebensart/genuss/xml/rssd",                             "enabled": False},
            {"ressort": "lebensart_wohnen",           "rss": "https://kurier.at/lebensart/wohnen/xml/rssd",                             "enabled": False},
            {"ressort": "lebensart_motor",            "rss": "https://kurier.at/lebensart/motor/xml/rssd",                              "enabled": False},
            {"ressort": "lebensart_leben",            "rss": "https://kurier.at/lebensart/leben/xml/rssd",                              "enabled": False},
            {"ressort": "lebensart_familie",          "rss": "https://kurier.at/lebensart/familie/xml/rssd",                            "enabled": False},
            {"ressort": "menschen",                   "rss": "https://kurier.at/menschen/xml/rssd",                                     "enabled": False},
            {"ressort": "menschen_international",     "rss": "https://kurier.at/menschen/international/xml/rssd",                       "enabled": False},
            {"ressort": "menschen_oesterreich",       "rss": "https://kurier.at/menschen/oesterreich/xml/rssd",                         "enabled": False},
            {"ressort": "menschen_portrait",          "rss": "https://kurier.at/menschen/im-portraet/xml/rssd",                         "enabled": False},
            {"ressort": "menschen_gespraech",         "rss": "https://kurier.at/menschen/im-gespraech/xml/rssd",                        "enabled": False},
            {"ressort": "kult",                       "rss": "https://kurier.at/kult/xml/rssd",                                         "enabled": False},
            {"ressort": "kult_quiz",                  "rss": "https://kurier.at/thema/quiz/xml/rssd",                                   "enabled": False},
            {"ressort": "kult_gewinnspiele",          "rss": "https://kurier.at/kult/gewinnspiele/xml/rssd",                            "enabled": False},
        ],
    },
    # ── ÖSTERREICH (Ergänzung) ──────────────────────────────
    "orf.at": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "news",        "rss": "https://rss.orf.at/news.xml",        "enabled": True},
            {"ressort": "sport",       "rss": "https://rss.orf.at/sport.xml",       "enabled": True},
            {"ressort": "science",     "rss": "https://rss.orf.at/science.xml",     "enabled": True},
            {"ressort": "oesterreich", "rss": "https://rss.orf.at/oesterreich.xml", "enabled": True},
            {"ressort": "debatte",     "rss": "https://rss.orf.at/debatten.xml",    "enabled": False},
            {"ressort": "help",        "rss": "https://rss.orf.at/help.xml",        "enabled": False},
            {"ressort": "oe3",         "rss": "https://rss.orf.at/oe3.xml",         "enabled": False},
            {"ressort": "fm4",         "rss": "https://rss.orf.at/fm4.xml",         "enabled": False},
        ],
    },
    # ── SCHWEIZ ─────────────────────────────────────────────────
    "nzz.ch": {
        "ausrichtung": "Mitte-Rechts",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",     "rss": "https://www.nzz.ch/recent.rss",                  "enabled": True},
            {"ressort": "startseite",    "rss": "https://www.nzz.ch/startseite.rss",              "enabled": True},
            {"ressort": "schweiz",       "rss": "https://www.nzz.ch/schweiz.rss",                 "enabled": True},
            {"ressort": "international", "rss": "https://www.nzz.ch/international.rss",           "enabled": True},
            {"ressort": "wirtschaft",    "rss": "https://www.nzz.ch/wirtschaft.rss",              "enabled": True},
            {"ressort": "finanzen",      "rss": "https://www.nzz.ch/finanzen.rss",                "enabled": True},
            {"ressort": "panorama",      "rss": "https://www.nzz.ch/panorama.rss",                "enabled": True},
            {"ressort": "gesellschaft",  "rss": "https://www.nzz.ch/gesellschaft.rss",            "enabled": True},
            {"ressort": "feuilleton",    "rss": "https://www.nzz.ch/feuilleton.rss",              "enabled": True},
            {"ressort": "wissenschaft",  "rss": "https://www.nzz.ch/wissenschaft.rss",            "enabled": True},
            {"ressort": "technologie",   "rss": "https://www.nzz.ch/technologie.rss",             "enabled": True},
            {"ressort": "sport",         "rss": "https://www.nzz.ch/sport.rss",                   "enabled": True},
            {"ressort": "meinung",       "rss": "https://www.nzz.ch/meinung.rss",                 "enabled": False},
            {"ressort": "zuerich",       "rss": "https://www.nzz.ch/zuerich.rss",                 "enabled": False},
            {"ressort": "reisen",        "rss": "https://www.nzz.ch/reisen.rss",                  "enabled": False},
            {"ressort": "mobilitaet",    "rss": "https://www.nzz.ch/mobilitaet.rss",              "enabled": False},
            {"ressort": "auto",          "rss": "https://www.nzz.ch/mobilitaet/auto-mobil.rss",   "enabled": False},
            {"ressort": "video",         "rss": "https://www.nzz.ch/video.rss",                   "enabled": False},
            {"ressort": "fotografie",    "rss": "https://www.nzz.ch/fotografie.rss",              "enabled": False},
        ],
    },
    "tagesanzeiger.ch": {
        "ausrichtung": "Mitte-Links",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://www.tagesanzeiger.ch/rss.html", "enabled": True},
        ],
    },
    "blick.ch": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein",  "rss": "https://www.blick.ch/rss.xml",          "enabled": True},
            {"ressort": "schweiz",    "rss": "https://www.blick.ch/schweiz/rss.xml",  "enabled": True},
            {"ressort": "ausland",    "rss": "https://www.blick.ch/ausland/rss.xml",  "enabled": True},
            {"ressort": "wirtschaft", "rss": "https://www.blick.ch/wirtschaft/rss.xml","enabled": True},
            {"ressort": "politik",    "rss": "https://www.blick.ch/politik/rss.xml",  "enabled": True},
            {"ressort": "sport",      "rss": "https://www.blick.ch/sport/rss.xml",    "enabled": True},
            {"ressort": "digital",    "rss": "https://www.blick.ch/digital/rss.xml",  "enabled": True},
            {"ressort": "people",     "rss": "https://www.blick.ch/people/rss.xml",   "enabled": False},
            {"ressort": "life",       "rss": "https://www.blick.ch/life/rss.xml",     "enabled": False},
        ],
    },
    "20min.ch": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "allgemein", "rss": "https://partner-feeds.20min.ch/rss/20minuten", "enabled": True},
        ],
    },
    "srf.ch": {
        "ausrichtung": "Mitte",
        "enabled": True,
        "feeds": [
            {"ressort": "news",          "rss": "https://www.srf.ch/news/bnf/rss/1646",      "enabled": True},
            {"ressort": "das_neueste",   "rss": "https://www.srf.ch/news/bnf/rss/19032223",  "enabled": True},
            {"ressort": "schweiz",       "rss": "https://www.srf.ch/news/bnf/rss/1890",      "enabled": True},
            {"ressort": "international", "rss": "https://www.srf.ch/news/bnf/rss/1900",      "enabled": False},
            {"ressort": "wirtschaft",    "rss": "https://www.srf.ch/news/bnf/rss/1922",      "enabled": True},
            {"ressort": "sport",         "rss": "https://www.srf.ch/sport/bnf/rss/1648",     "enabled": False},
            {"ressort": "kultur",        "rss": "https://www.srf.ch/kultur/bnf/rss/1649",    "enabled": False},
            {"ressort": "wissen",        "rss": "https://www.srf.ch/wissen/bnf/rss/1650",    "enabled": False},
        ],
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
