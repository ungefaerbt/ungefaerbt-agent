import html
import re

import feedparser

from config import QUELLEN


def teaser_bereinigen(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500]




def schlagzeilen_abrufen(max_pro_quelle=5, gesamt_limit=None, verbose=True):
    alle = []
    if verbose:
        print("\nRufe RSS-Feeds ab ...")

    for name, daten in QUELLEN.items():
        try:
            feed = feedparser.parse(daten["rss"])
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
                })
            if verbose:
                print(f"  ✓ {name} ({len(eintraege)} Artikel)")
        except Exception as fehler:
            if verbose:
                print(f"  ✗ {name} – Fehler: {fehler}")

    return alle[:gesamt_limit] if gesamt_limit else alle
