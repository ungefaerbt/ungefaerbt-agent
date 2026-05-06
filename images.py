import json
import urllib.parse
import urllib.request

from config import _STOPPWOERTER


def unsplash_bild_suchen(headline, kategorie, access_key):
    if not access_key:
        return ""
    sonderzeichen = '„""»«\'"\\-.,!?:'
    woerter = [
        w.strip(sonderzeichen) for w in headline.split()
        if len(w) > 3 and w.lower().strip(sonderzeichen) not in _STOPPWOERTER
    ]
    keywords = " ".join(woerter[:4])
    if kategorie and kategorie != "Sonstiges":
        keywords = f"{keywords} {kategorie}"
    query = urllib.parse.quote(keywords)
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&client_id={access_key}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            daten = json.loads(resp.read().decode())
            ergebnisse = daten.get("results", [])
            if ergebnisse:
                return ergebnisse[0]["urls"].get("regular", "")
    except Exception:
        pass
    return ""
