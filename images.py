import json
import time
import urllib.parse
import urllib.request

from config import _STOPPWOERTER


# Unsplash-Format: "portrait" für Hochformat, "squarish" für quadratisch (Social Media)
BILD_FORMAT = "squarish"
MAX_FOTOS_PRO_QUERY = 5
MAX_FOTOS_GESAMT = 10


def _claude_keywords_extrahieren(client, headline, kategorie, artikeltext="") -> list[str]:
    """
    Stufe 1: Claude analysiert den Artikel und extrahiert 3 englische,
    visuell starke Suchanfragen für Unsplash.

    Ziel: Fotos die auf den ersten Blick zum Artikel passen und im
    Mobile-Feed / Social Media stark wirken.
    """
    kontext = f"Headline: {headline}\n"
    if kategorie and kategorie != "Sonstiges":
        kontext += f"Kategorie: {kategorie}\n"
    if artikeltext:
        kontext += f"Artikelanfang: {artikeltext[:300]}\n"

    prompt = (
        "Du bist Bildredakteur einer mobilen News-App. "
        "Nutzer scrollen durch einen Feed und entscheiden in Sekunden ob sie bleiben. "
        "Das Foto ist der erste Eindruck – es muss sofort verständlich und visuell stark sein.\n\n"
        "Deine Aufgabe: Erstelle 3 englische Suchanfragen für Unsplash "
        "die ein thematisch passendes, visuell attraktives Foto liefern.\n\n"
        "Regeln:\n"
        "- Nur Englisch\n"
        "- Konkrete, fotografierbare Motive – keine abstrakten Begriffe\n"
        "- Bilder sollen für Mobile Feed und Social Media stark wirken\n"
        "- Keine echten Personen, Politiker oder erkennbare Gesichter suchen\n"
        "- Eigennamen generalisieren: 'politician speech' statt Name, 'city street' statt Stadtname\n"
        "- Von spezifisch nach generisch sortieren\n"
        "- Jede Query: 2–3 Wörter\n\n"
        "Beispiele:\n"
        "'Bundesregierung erhöht Steuern' → ['tax money stress', 'euro coins bills', 'government finance']\n"
        "'Überschwemmungen in Bayern' → ['flood disaster water', 'heavy rain street', 'natural disaster rescue']\n"
        "'Bayern München gewinnt Champions League' → ['soccer trophy celebration', 'football stadium crowd', 'sports victory']\n\n"
        f"{kontext}\n"
        "Antworte NUR mit validem JSON, kein Text davor oder danach:\n"
        '{"queries": ["query1", "query2", "query3"]}'
    )

    for versuch in range(3):
        try:
            antwort = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            text = antwort.content[0].text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            daten = json.loads(text)
            queries = daten.get("queries", [])
            if queries:
                print(f"[IMG] Keywords extrahiert: {queries}")
                return queries
        except Exception as e:
            wartezeit = 2 ** versuch
            print(f"[IMG] Keyword-Extraktion Versuch {versuch + 1} fehlgeschlagen: {e} – warte {wartezeit}s")
            time.sleep(wartezeit)

    # Fallback: einfache Extraktion aus Headline
    print("[IMG] Fallback auf einfache Keyword-Extraktion")
    sonderzeichen = '„""»«\'"\\-.,!?:'
    woerter = [
        w.strip(sonderzeichen) for w in headline.split()
        if len(w) > 3 and w.lower().strip(sonderzeichen) not in _STOPPWOERTER
    ]
    return [" ".join(woerter[:4])]


def _unsplash_fotos_holen(query, access_key) -> list[tuple[str, str]]:
    """
    Sucht Fotos auf Unsplash für eine Query.
    Format: squarish (optimal für Mobile Feed + Social Media).
    Gibt Liste von (url, beschreibung) zurück.
    """
    params = urllib.parse.urlencode({
        "query": query,
        "per_page": MAX_FOTOS_PRO_QUERY,
        "orientation": BILD_FORMAT,
        "order_by": "relevant",
        "content_filter": "high",
        "client_id": access_key
    })
    url = f"https://api.unsplash.com/search/photos?{params}"

    for versuch in range(3):
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                daten = json.loads(resp.read().decode())
                rohe = daten.get("results", [])
                fotos = [
                    (
                        r["urls"]["regular"],
                        r.get("description") or r.get("alt_description") or ""
                    )
                    for r in rohe
                    if r.get("urls", {}).get("regular")
                ]
                print(f"[IMG] Query '{query}' → {len(fotos)} Fotos gefunden")
                return fotos
        except Exception as e:
            wartezeit = 2 ** versuch
            print(f"[IMG] Unsplash Versuch {versuch + 1} fehlgeschlagen für '{query}': {e} – warte {wartezeit}s")
            time.sleep(wartezeit)

    return []


def _claude_bestes_foto_waehlen(client, headline, kategorie, fotos: list[tuple[str, str]]) -> str:
    """
    Stufe 3: Claude wählt aus allen gesammelten Fotos das beste aus.

    Kriterien:
    - Thematische Relevanz zum Artikel
    - Visuelle Stärke im Mobile Feed
    - Emotionale Wirkung auf den ersten Blick
    - Eignung für Social Media
    """
    if not fotos:
        return ""
    if len(fotos) == 1:
        return fotos[0][0]

    foto_zeilen = "\n".join(
        f"Foto {i + 1}: {url} – {desc}"
        for i, (url, desc) in enumerate(fotos)
    )

    kontext = f"Headline: {headline}"
    if kategorie and kategorie != "Sonstiges":
        kontext += f" | Kategorie: {kategorie}"

    prompt = (
        "Du bist Bildredakteur einer mobilen News-App. "
        "Nutzer scrollen durch einen Feed – das Foto entscheidet ob sie stoppen oder weiterscrollen.\n\n"
        "Wähle das beste Foto nach diesen Kriterien:\n"
        "1. Thematisch eindeutig passend zur Headline\n"
        "2. Visuell stark und aufmerksamkeitsstark im Mobile Feed\n"
        "3. Emotionale Wirkung auf den ersten Blick\n"
        "4. Gut geeignet für Social Media (quadratisches Format)\n"
        "5. Keine erkennbaren Personen oder Gesichter bevorzugen\n\n"
        f"{kontext}\n\n"
        f"{foto_zeilen}\n\n"
        "Antworte NUR mit der vollständigen URL des besten Fotos, nichts anderes."
    )

    for versuch in range(3):
        try:
            antwort = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            gewaehlte_url = antwort.content[0].text.strip()
            bekannte_urls = [u for u, _ in fotos]
            if gewaehlte_url in bekannte_urls:
                print(f"[IMG] Claude hat Foto gewählt: {gewaehlte_url[:60]}...")
                return gewaehlte_url
            else:
                print("[IMG] Claude-Antwort war keine bekannte URL – nehme erstes Foto als Fallback")
                return fotos[0][0]
        except Exception as e:
            wartezeit = 2 ** versuch
            print(f"[IMG] Foto-Auswahl Versuch {versuch + 1} fehlgeschlagen: {e} – warte {wartezeit}s")
            time.sleep(wartezeit)

    return fotos[0][0]


def unsplash_bild_suchen(client, headline, kategorie, access_key, artikeltext="") -> str:
    """
    Hauptfunktion: Findet automatisch das beste Unsplash-Foto für einen News-Artikel.

    Optimiert für:
    - Mobile News Feed (erster Eindruck entscheidet)
    - Social Media (quadratisches Format)
    - Copyright-freie Nutzung (Unsplash Free License)
    - Vollautomatischer Betrieb ohne manuelles Eingreifen

    Ablauf:
      1. Claude analysiert Artikel und extrahiert 3 englische visuelle Keywords
      2. Unsplash wird mit Fallback-Kette durchsucht (Query 1 → 2 → 3)
      3. Claude wählt aus allen Ergebnissen das visuell stärkste Foto

    Args:
        client:      Anthropic-Client
        headline:    Artikel-Headline (deutsch)
        kategorie:   Artikel-Kategorie (z.B. "Politik", "Sport", "Wirtschaft")
        access_key:  Unsplash API Key (Free License)
        artikeltext: Optionaler Artikelanfang für bessere Keywords (rückwärtskompatibel)

    Returns:
        URL des besten Fotos (Unsplash Free License) oder "" bei Fehler
    """
    if not access_key:
        print("[IMG] Kein Unsplash Access Key – überspringe Bildsuche")
        return ""

    print(f"[IMG] Starte Bildsuche für: {headline[:60]}...")

    # Stufe 1: Claude extrahiert englische visuelle Keywords
    queries = _claude_keywords_extrahieren(client, headline, kategorie, artikeltext)

    # Stufe 2: Unsplash mit Fallback-Kette – sammle bis zu MAX_FOTOS_GESAMT Fotos
    alle_fotos: list[tuple[str, str]] = []
    gesehene_urls: set[str] = set()

    for query in queries:
        if not query:
            continue
        fotos = _unsplash_fotos_holen(query, access_key)
        for foto in fotos:
            if foto[0] not in gesehene_urls:
                alle_fotos.append(foto)
                gesehene_urls.add(foto[0])
        if len(alle_fotos) >= MAX_FOTOS_GESAMT:
            break

    if not alle_fotos:
        print(f"[IMG] Keine Fotos gefunden für: {headline[:60]}")
        return ""

    print(f"[IMG] {len(alle_fotos)} Fotos gesammelt – Claude wählt das beste...")

    # Stufe 3: Claude wählt das visuell stärkste, thematisch passendste Foto
    return _claude_bestes_foto_waehlen(client, headline, kategorie, alle_fotos[:MAX_FOTOS_GESAMT])
