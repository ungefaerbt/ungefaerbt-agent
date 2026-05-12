import html
import logging
import re

import feedparser

from config import QUELLEN

logger = logging.getLogger("fetcher")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.propagate = False


def teaser_bereinigen(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500]


def _feeds_fuer_quelle(daten):
    """Gibt Liste von (ressort, rss_url) zurück — unterstützt alte und neue Struktur."""
    if "feeds" in daten:
        return [
            (f.get("ressort", "allgemein"), f["rss"])
            for f in daten["feeds"]
            if f.get("enabled", True)
        ]
    return [("allgemein", daten["rss"])]


def schlagzeilen_abrufen(max_pro_quelle=5, gesamt_limit=None, verbose=True):
    alle = []
    feeds_geladen = 0

    if verbose:
        print("\nRufe RSS-Feeds ab ...")

    for name, daten in QUELLEN.items():
        if not daten.get("enabled", True):
            continue

        for ressort, rss_url in _feeds_fuer_quelle(daten):
            try:
                feed = feedparser.parse(rss_url)
                eintraege = feed.entries[:max_pro_quelle]
                for eintrag in eintraege:
                    teaser = teaser_bereinigen(
                        eintrag.get("summary", "") or eintrag.get("description", "")
                    )
                    alle.append({
                        "headline": eintrag.get("title", "").strip(),
                        "teaser": teaser,
                        "link": eintrag.get("link", ""),
                        "published_at": eintrag.get("published", "") or eintrag.get("updated", ""),
                        "image_url": "",
                        "source": name,
                        "political_leaning": daten["ausrichtung"],
                        "ressort": ressort,
                    })
                feeds_geladen += 1
                if verbose:
                    print(f"  ✓ {name} [{ressort}] ({len(eintraege)} Artikel)")
            except Exception as fehler:
                if verbose:
                    print(f"  ✗ {name} [{ressort}] – Fehler: {fehler}")

    logger.info("Feeds geladen: %s | Artikel gesamt: %s", feeds_geladen, len(alle))
    return alle[:gesamt_limit] if gesamt_limit else alle
