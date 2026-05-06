import json
import urllib.parse
import urllib.request

from config import _STOPPWOERTER


def unsplash_bild_suchen(client, headline, kategorie, access_key):
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
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=3&client_id={access_key}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            daten = json.loads(resp.read().decode())
            rohe = daten.get("results", [])
            fotos = [
                (r["urls"]["regular"], r.get("description") or r.get("alt_description") or "")
                for r in rohe
                if r.get("urls", {}).get("regular")
            ]
    except Exception:
        return ""

    if not fotos:
        return ""
    if len(fotos) == 1:
        return fotos[0][0]

    # Sonnet wählt das passendste Foto
    foto_zeilen = "\n".join(
        f"Foto {i + 1}: {foto_url} – {desc}"
        for i, (foto_url, desc) in enumerate(fotos)
    )
    prompt = (
        "Du bist Bildredakteur für eine News-App. "
        "Wähle das attraktivste Foto das am besten zur Nachricht passt.\n"
        f"Headline: {headline}\n"
        f"{foto_zeilen}\n\n"
        "Antworte NUR mit der URL des besten Fotos, nichts anderes."
    )
    try:
        antwort = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        gewaehlte = antwort.content[0].text.strip()
        bekannte = [u for u, _ in fotos]
        if gewaehlte in bekannte:
            return gewaehlte
    except Exception:
        pass

    return fotos[0][0]
