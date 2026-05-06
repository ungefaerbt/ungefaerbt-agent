import sys
import re
import html
import json
import os
import time
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from collections import Counter, defaultdict

import feedparser
import anthropic
import schedule
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

# ─── Logging (nur Datei, Terminal läuft via print) ───────────────
_log_handler = logging.FileHandler("log.txt", encoding="utf-8")
_log_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger = logging.getLogger("news_agent")
logger.addHandler(_log_handler)
logger.setLevel(logging.INFO)

# ─── Konfiguration ──────────────────────────────────────────────
BREAKING_SEEN_DATEI = "breaking_seen.json"
BREAKING_QUELLEN_SCHWELLE = 3
NORMAL_ZEITEN = ["06:00", "11:00", "16:00", "20:00"]
BREAKING_INTERVALL_MIN = 15

# ─── Nachrichtenquellen ─────────────────────────────────────────
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


# ─── Hilfsfunktionen ─────────────────────────────────────────────
def teaser_bereinigen(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500]


def ist_zu_vage(headline):
    if not headline or not headline.strip():
        return True
    woerter = headline.split()
    if len(woerter) < 5:
        return True
    stripped = headline.strip()
    if (stripped[0] in ('„', '"', '"', "'") and
            stripped[-1] in ('"', '"', '"', "'") and
            len(woerter) < 8):
        return True
    return False


def bild_aus_eintrag(eintrag):
    if hasattr(eintrag, "media_content") and eintrag.media_content:
        return eintrag.media_content[0].get("url", "")
    if hasattr(eintrag, "media_thumbnail") and eintrag.media_thumbnail:
        return eintrag.media_thumbnail[0].get("url", "")
    if hasattr(eintrag, "links"):
        for link in eintrag.links:
            if link.get("type", "").startswith("image"):
                return link.get("href", "")
    return ""


_STOPPWOERTER = {
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "für", "von",
    "mit", "bei", "nach", "vor", "an", "auf", "in", "ist", "sind", "hat",
    "haben", "wird", "werden", "als", "auch", "sich", "im", "des", "dem",
    "den", "zu", "zur", "zum", "nicht", "was", "wie", "es", "er", "sie",
    "wir", "ich", "am", "aus", "um", "bis", "war", "wird", "kann", "mehr",
}


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


def schlagzeilen_clustern(artikel_liste):
    sonderzeichen = '„""»«\'"\\-.,!?:()'

    def keywords(text):
        return {
            w.strip(sonderzeichen).lower()
            for w in text.split()
            if len(w.strip(sonderzeichen)) > 3
            and w.strip(sonderzeichen).lower() not in _STOPPWOERTER
        }

    n = len(artikel_liste)
    eltern = list(range(n))

    def find(x):
        while eltern[x] != x:
            eltern[x] = eltern[eltern[x]]
            x = eltern[x]
        return x

    # Stufe 1: 2+ gemeinsame Keywords aus Headline
    kw_headline = [keywords(a["headline"]) for a in artikel_liste]
    for i in range(n):
        for j in range(i + 1, n):
            if len(kw_headline[i] & kw_headline[j]) >= 2:
                eltern[find(i)] = find(j)

    # Singletons nach Stufe 1 ermitteln
    wurzeln_s1 = [find(i) for i in range(n)]
    groessen_s1 = Counter(wurzeln_s1)
    singletons = [i for i in range(n) if groessen_s1[wurzeln_s1[i]] == 1]

    # Stufe 2: Headline + Teaser kombiniert, 3+ Keywords, nur für Singletons
    kw_kombi = [
        keywords(a["headline"] + " " + a.get("teaser", ""))
        for a in artikel_liste
    ]
    for idx_i in range(len(singletons)):
        i = singletons[idx_i]
        for idx_j in range(idx_i + 1, len(singletons)):
            j = singletons[idx_j]
            if find(i) != find(j) and len(kw_kombi[i] & kw_kombi[j]) >= 3:
                eltern[find(i)] = find(j)

    # Singletons nach Stufe 2 ermitteln
    wurzeln_s2 = [find(i) for i in range(n)]
    groessen_s2 = Counter(wurzeln_s2)
    singletons_s2 = [i for i in range(n) if groessen_s2[wurzeln_s2[i]] == 1]

    # Stufe 4: Kernthema – häufigstes Named Entity (Großbuchstabe, ≥6 Zeichen) in Headline+Teaser
    # Bindestrich-Komposita werden gesplittet: „Hondius"-Passagier → "Hondius" + "Passagier"
    # Jedes Teil wird nochmals gestrippt um Restzeichen wie „Hondius" → Hondius zu bereinigen
    def kernthema(text):
        kandidaten = []
        for w in text.split():
            for teil in w.strip(sonderzeichen).split('-'):
                teil = teil.strip(sonderzeichen)
                if teil and teil[0].isupper() and len(teil) >= 6 and teil.lower() not in _STOPPWOERTER:
                    kandidaten.append(teil.lower())
        if not kandidaten:
            return None
        return Counter(kandidaten).most_common(1)[0][0]

    thema_zu_idx = defaultdict(list)
    for i in singletons_s2:
        kt = kernthema(
            artikel_liste[i]["headline"] + " " + artikel_liste[i].get("teaser", "")
        )
        if kt:
            thema_zu_idx[kt].append(i)

    for indices in thema_zu_idx.values():
        if len(indices) >= 2:
            for k in indices[1:]:
                ri, rk = find(indices[0]), find(k)
                if ri != rk:
                    eltern[rk] = ri

    wurzeln = [find(i) for i in range(n)]
    groessen = Counter(wurzeln)

    for i, artikel in enumerate(artikel_liste):
        artikel["cluster_id"] = wurzeln[i]
        artikel["cluster_size"] = groessen[wurzeln[i]]

    # Spectrum-Analyse pro Cluster
    cluster_gruppen = defaultdict(list)
    for a in artikel_liste:
        cluster_gruppen[a["cluster_id"]].append(a)

    for gruppe in cluster_gruppen.values():
        vorhandene = {a.get("political_leaning", "") for a in gruppe}
        stille = [s for s in ALLE_AUSRICHTUNGEN if s not in vorhandene]
        count = len(vorhandene & set(ALLE_AUSRICHTUNGEN))
        score = round(len(stille) / len(ALLE_AUSRICHTUNGEN) * 100)

        if len(gruppe) == 1:
            label = "Einzelmeldung"
        elif not stille:
            label = "Vollspektrum"
        elif set(stille) <= {"Rechts", "Mitte-Rechts"}:
            label = "Rechts-Blindspot"
        elif set(stille) <= {"Links", "Mitte-Links"}:
            label = "Links-Blindspot"
        elif stille == ["Mitte"]:
            label = "Mitte-Blindspot"
        else:
            label = "Gemischter Blindspot"

        for a in gruppe:
            a["spectrum_count"] = count
            a["silent_spectrums"] = stille
            a["blindspot_score"] = score
            a["blindspot_label"] = label

    return artikel_liste


def _cluster_fingerprint(artikel_list):
    """Erstellt einen stabilen Fingerprint für einen Artikel-Cluster."""
    sonderzeichen = '„""»«\'"\\-.,!?:()'
    alle_woerter = []
    for a in artikel_list:
        alle_woerter.extend([
            w.strip(sonderzeichen).lower()
            for w in a["headline"].split()
            if len(w.strip(sonderzeichen)) > 3
            and w.strip(sonderzeichen).lower() not in _STOPPWOERTER
        ])
    counter = Counter(alle_woerter)
    top_woerter = sorted(w for w, _ in counter.most_common(5))
    return "|".join(top_woerter)


def _artikel_staerke(a):
    """Sortierschlüssel: höherer Score = stärker; Bild und lange Summary als Tiebreaker."""
    return (
        a.get("relevance_score", 0),
        1 if a.get("image_url") else 0,
        len(a.get("summary", "")),
    )


def pro_quelle_filtern(artikel_liste, max_immer=3, dominanz_schwelle=0.25):
    """Weiche Quellen-Begrenzung:
    - Breaking News: unbegrenzt
    - Normale Artikel: bis 3 pro Quelle immer erlaubt
    - Mehr als 3 nur entfernen wenn Quelle die Ausgabe dominiert (> 25 %)
    - Bei Kürzung: schwächste Artikel zuerst entfernen
    """
    breaking = [a for a in artikel_liste if a.get("is_breaking", False)]
    normal = [a for a in artikel_liste if not a.get("is_breaking", False)]

    nach_quelle = defaultdict(list)
    for a in normal:
        nach_quelle[a["source"]].append(a)

    # Innerhalb jeder Quelle: stärkste Artikel zuerst
    for src in nach_quelle:
        nach_quelle[src].sort(key=_artikel_staerke, reverse=True)

    gesamt_normal = sum(len(arts) for arts in nach_quelle.values())

    gefiltert = []
    for src, arts in nach_quelle.items():
        if len(arts) <= max_immer:
            gefiltert.extend(arts)
        else:
            anteil = len(arts) / gesamt_normal if gesamt_normal else 0
            if anteil > dominanz_schwelle:
                gefiltert.extend(arts[:max_immer])
            else:
                gefiltert.extend(arts)

    return breaking + gefiltert


def feed_sortieren(artikel_liste):
    """Abwechslungsreiche Sortierung:
    - Breaking News ganz oben
    - Dann Kategorien im Wechsel (KATEGORIE_REIHENFOLGE)
    - Innerhalb jeder Kategorie: höchster relevance_score zuerst
    - is_top_story Artikel gleichmäßig über den Feed verteilt
    """
    breaking = [a for a in artikel_liste if a.get("is_breaking", False)]
    normal = [a for a in artikel_liste if not a.get("is_breaking", False)]

    nach_kategorie = defaultdict(list)
    for a in normal:
        nach_kategorie[a.get("category", "Sonstiges")].append(a)

    for kat in nach_kategorie:
        nach_kategorie[kat].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Reihenfolge: erst definierte Kategorien, dann Restliche
    cats = [k for k in KATEGORIE_REIHENFOLGE if k in nach_kategorie]
    cats += [k for k in nach_kategorie if k not in KATEGORIE_REIHENFOLGE]

    reihe = []
    while any(nach_kategorie[k] for k in cats):
        for kat in cats:
            if nach_kategorie[kat]:
                reihe.append(nach_kategorie[kat].pop(0))

    # is_top_story gleichmäßig verteilen
    top_stories = [a for a in reihe if a.get("is_top_story", False)]
    non_top = [a for a in reihe if not a.get("is_top_story", False)]

    if not top_stories:
        return breaking + reihe

    gesamt = len(reihe)
    schritt = gesamt / len(top_stories)
    ergebnis = []
    top_idx = 0
    non_top_idx = 0

    for i in range(gesamt):
        if top_idx < len(top_stories) and i >= round(top_idx * schritt):
            ergebnis.append(top_stories[top_idx])
            top_idx += 1
        elif non_top_idx < len(non_top):
            ergebnis.append(non_top[non_top_idx])
            non_top_idx += 1

    ergebnis.extend(top_stories[top_idx:])
    ergebnis.extend(non_top[non_top_idx:])

    return breaking + ergebnis


def breaking_seen_laden():
    """Lädt Fingerprints bekannter Breaking News (max. 24h alt)."""
    if not os.path.exists(BREAKING_SEEN_DATEI):
        return set()
    try:
        with open(BREAKING_SEEN_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
        grenze = time.time() - 86400
        return {fp for fp, ts in daten.items() if ts > grenze}
    except Exception:
        return set()


def breaking_seen_speichern(seen):
    """Speichert Fingerprints mit Zeitstempel, löscht Einträge älter als 24h."""
    try:
        vorherige = {}
        if os.path.exists(BREAKING_SEEN_DATEI):
            with open(BREAKING_SEEN_DATEI, "r", encoding="utf-8") as f:
                vorherige = json.load(f)
        jetzt = time.time()
        grenze = jetzt - 86400
        aktuell = {fp: ts for fp, ts in vorherige.items() if ts > grenze}
        for fp in seen:
            if fp not in aktuell:
                aktuell[fp] = jetzt
        with open(BREAKING_SEEN_DATEI, "w", encoding="utf-8") as f:
            json.dump(aktuell, f, ensure_ascii=True)
    except Exception as e:
        print(f"  Warnung: {BREAKING_SEEN_DATEI} konnte nicht gespeichert werden: {e}")


# ─── RSS-Abruf ──────────────────────────────────────────────────
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
                    "image_url": bild_aus_eintrag(eintrag),
                    "source": name,
                    "political_leaning": daten["ausrichtung"],
                })
            if verbose:
                print(f"  ✓ {name} ({len(eintraege)} Artikel)")
        except Exception as fehler:
            if verbose:
                print(f"  ✗ {name} – Fehler: {fehler}")

    return alle[:gesamt_limit] if gesamt_limit else alle


# ─── Claude-Analyse ─────────────────────────────────────────────
def klassifizieren_mit_haiku(client, schlagzeile):
    teaser_block = ""
    if schlagzeile.get("teaser"):
        teaser_block = f'\nBeschreibung: "{schlagzeile["teaser"]}"\n'

    nutzer_nachricht = f"""Klassifiziere diesen Nachrichtenartikel von {schlagzeile['source']}:

Headline: "{schlagzeile['headline']}"{teaser_block}

Antworte NUR mit diesem JSON (kein weiterer Text):
{{
  "category": "Eines von: Politik / Wirtschaft / Gesellschaft / International / Technologie / Sport / Kultur / Umwelt",
  "is_breaking": false,
  "relevance_score": 65,
  "is_top_story": false
}}"""

    antwort = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": nutzer_nachricht}]
    )

    text = antwort.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        category_match = re.search(r'"category"\s*:\s*"([^"]+)"', text)
        breaking_match = re.search(r'"is_breaking"\s*:\s*(true|false)', text)
        score_match = re.search(r'"relevance_score"\s*:\s*(\d+)', text)
        top_match = re.search(r'"is_top_story"\s*:\s*(true|false)', text)
        return {
            "category": category_match.group(1) if category_match else "Sonstiges",
            "is_breaking": breaking_match.group(1) == "true" if breaking_match else False,
            "relevance_score": int(score_match.group(1)) if score_match else 50,
            "is_top_story": top_match.group(1) == "true" if top_match else False,
        }


def zusammenfassen_mit_sonnet(client, schlagzeile):
    teaser_block = ""
    if schlagzeile.get("teaser"):
        teaser_block = f'\nBeschreibung: "{schlagzeile["teaser"]}"\n'

    nutzer_nachricht = f"""Fasse diesen Nachrichtenartikel von {schlagzeile['source']} zusammen:

Headline: "{schlagzeile['headline']}"{teaser_block}

Schreibe außerdem eine eigene sachliche Headline auf Deutsch in max. 10 Wörtern. Keine Meinung, keine Wertung, keine Ausrufezeichen, kein Clickbait. Nur belegbare Fakten.

Antworte NUR mit diesem JSON (kein weiterer Text):
{{
  "headline": "Eigene neutrale Headline",
  "summary": "Neutrale Zusammenfassung in 2–3 Sätzen."
}}"""

    antwort = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": nutzer_nachricht}]
    )

    text = antwort.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        headline_match = re.search(r'"headline"\s*:\s*"(.*?)"(?=\s*,\s*"|\s*\})', text, re.DOTALL)
        summary_match = re.search(r'"summary"\s*:\s*"(.*?)"(?=\s*,\s*"|\s*\})', text, re.DOTALL)
        if not summary_match:
            raise
        return {
            "headline": headline_match.group(1).replace('\\"', '"') if headline_match else "",
            "summary": summary_match.group(1).replace('\\"', '"'),
        }


def analyse_mit_claude(client, schlagzeile):
    klassifikation = klassifizieren_mit_haiku(client, schlagzeile)
    zusammenfassung = zusammenfassen_mit_sonnet(client, schlagzeile)
    return {**klassifikation, **zusammenfassung}


def cluster_synthese_mit_sonnet(client, cluster_artikel):
    """Synthetisiert mehrere Cluster-Artikel zu einer einzigen neutralen Zusammenfassung."""
    artikel_texte = []
    for i, a in enumerate(cluster_artikel, 1):
        artikel_texte.append(
            f"Quelle {i} ({a['source']}, {a['political_leaning']}):\n"
            f"Headline: \"{a['headline']}\"\n"
            f"Zusammenfassung: {a.get('summary', '')}"
        )

    nutzer_nachricht = (
        f"Synthetisiere folgende {len(cluster_artikel)} Berichte über dasselbe Ereignis "
        f"zu einer einzigen neutralen Zusammenfassung:\n\n"
        + "\n\n".join(artikel_texte)
        + "\n\nFalls die Artikel NICHT dasselbe Ereignis beschreiben, antworte ausschließlich mit:\n"
        '{"summary": "KEIN_CLUSTER"}\n\n'
        "Andernfalls schreibe auch eine eigene sachliche Headline auf Deutsch in max. 10 Wörtern "
        "(keine Meinung, kein Clickbait, nur belegbare Fakten) und antworte NUR mit diesem JSON:\n"
        '{\n  "headline": "Eigene neutrale Headline",\n  "summary": "Neutrale Synthese in 2–3 Sätzen ohne eine Meinung."\n}'
    )

    antwort = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": nutzer_nachricht}]
    )

    text = antwort.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        headline_match = re.search(r'"headline"\s*:\s*"(.*?)"(?=\s*,\s*"|\s*\})', text, re.DOTALL)
        m = re.search(r'"summary"\s*:\s*"(.*?)"(?=\s*,\s*"|\s*\})', text, re.DOTALL)
        return {
            "headline": headline_match.group(1).replace('\\"', '"') if headline_match else "",
            "summary": m.group(1).replace('\\"', '"') if m else "",
        }


# ─── Durchläufe ─────────────────────────────────────────────────
def normaler_durchlauf(client, unsplash_key):
    jetzt_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n{'=' * 60}")
    print(f"  NORMALER DURCHLAUF -- {jetzt_str}")
    print(f"{'=' * 60}")

    alle = schlagzeilen_abrufen()

    if not alle:
        print("\nKeine Schlagzeilen gefunden. Bitte Internetverbindung prüfen.")
        logger.info("NORMAL DURCHLAUF: Keine Schlagzeilen gefunden.")
        return

    # Schritt 1: Vage Headlines vorfiltern
    gefiltert = [a for a in alle if not ist_zu_vage(a["headline"])]
    uebersprungen = len(alle) - len(gefiltert)
    if uebersprungen:
        print(f"\n  {uebersprungen} Artikel wegen zu vager Headline übersprungen.")

    # Schritt 2: Clustering VOR der API-Analyse
    print(f"\nClustere {len(gefiltert)} Artikel ...")
    schlagzeilen_clustern(gefiltert)
    synthetisierte_cluster = len({
        a["cluster_id"] for a in gefiltert if a.get("cluster_size", 1) > 1
    })
    print(f"  {synthetisierte_cluster} Cluster mit 2+ Quellen erkannt.")

    # Schritt 3: Claude-Analyse
    print(f"\nAnalysiere {len(gefiltert)} Schlagzeilen mit Claude ...\n")
    ergebnisse = []

    for i, artikel in enumerate(gefiltert, 1):
        print(f"  [{i}/{len(gefiltert)}] {artikel['headline'][:70]}...")
        try:
            analyse = analyse_mit_claude(client, artikel)
            kategorie = analyse.get("category", "Sonstiges")
            image_url = artikel["image_url"]
            if not image_url:
                image_url = unsplash_bild_suchen(artikel["headline"], kategorie, unsplash_key)
                if image_url:
                    print(f"    Unsplash-Bild gefunden.")
            if not image_url:
                image_url = KATEGORIE_FALLBACK_BILDER.get(kategorie, "")
            ergebnisse.append({
                "headline": analyse.get("headline") or artikel["headline"],
                "summary": analyse.get("summary", ""),
                "source": artikel["source"],
                "political_leaning": artikel["political_leaning"],
                "category": kategorie,
                "is_breaking": analyse.get("is_breaking", False),
                "relevance_score": analyse.get("relevance_score", 50),
                "is_top_story": analyse.get("is_top_story", False),
                "image_url": image_url,
                "link": artikel["link"],
                "timestamp": datetime.now().isoformat(),
                "cluster_id": artikel["cluster_id"],
                "cluster_size": artikel["cluster_size"],
                "blindspot_label": artikel.get("blindspot_label", "Einzelmeldung"),
                "blindspot_score": artikel.get("blindspot_score", 100),
                "silent_spectrums": artikel.get("silent_spectrums", []),
                "spectrum_count": artikel.get("spectrum_count", 0),
            })
            time.sleep(0.5)
        except Exception as fehler:
            print(f"    Fehler bei Analyse: {fehler}")

    # Schritt 4: Cluster-Synthese
    print(f"\nSynthetisiere Cluster ...")
    nach_cluster = defaultdict(list)
    for a in ergebnisse:
        nach_cluster[a["cluster_id"]].append(a)

    finale_artikel = []
    cluster_synthetisiert = 0

    for cid, gruppe in nach_cluster.items():
        if len(gruppe) == 1:
            finale_artikel.append(gruppe[0])
            continue

        bester = max(gruppe, key=lambda x: x.get("relevance_score", 0))

        try:
            synthese = cluster_synthese_mit_sonnet(client, gruppe)
            summary = synthese.get("summary", bester.get("summary", ""))
            cluster_headline = synthese.get("headline") or bester["headline"]
            if summary == "KEIN_CLUSTER":
                for a in gruppe:
                    a["cluster_size"] = 1
                finale_artikel.extend(gruppe)
                print(f"    ↳ Kein echter Cluster – {len(gruppe)} Artikel als Einzelmeldungen")
                continue
        except Exception as e:
            print(f"    Synthese-Fehler Cluster {cid}: {e}")
            summary = bester.get("summary", "")
            cluster_headline = bester["headline"]

        alle_quellen = ", ".join(dict.fromkeys(a["source"] for a in gruppe))
        vorhandene_spektren = [s for s in ALLE_AUSRICHTUNGEN if any(a["political_leaning"] == s for a in gruppe)]
        alle_spektren = ", ".join(vorhandene_spektren)
        image_url = next((a["image_url"] for a in gruppe if a.get("image_url")), "")
        if not image_url:
            image_url = unsplash_bild_suchen(cluster_headline, bester["category"], unsplash_key)
        if not image_url:
            image_url = KATEGORIE_FALLBACK_BILDER.get(bester["category"], "")

        finale_artikel.append({
            "headline": cluster_headline,
            "summary": summary,
            "source": alle_quellen,
            "political_leaning": alle_spektren,
            "category": bester["category"],
            "is_breaking": bester.get("is_breaking", False),
            "relevance_score": bester.get("relevance_score", 50),
            "is_top_story": bester.get("is_top_story", False),
            "image_url": image_url,
            "link": bester["link"],
            "timestamp": bester["timestamp"],
            "cluster_id": cid,
            "cluster_size": bester["cluster_size"],
            "blindspot_label": bester.get("blindspot_label", "Einzelmeldung"),
            "blindspot_score": bester.get("blindspot_score", 100),
            "silent_spectrums": bester.get("silent_spectrums", []),
            "spectrum_count": len(vorhandene_spektren),
        })
        cluster_synthetisiert += 1
        print(f"  ✓ Cluster: {len(gruppe)} Artikel → 1 Story  [{alle_quellen[:55]}]")

    ergebnisse = feed_sortieren(finale_artikel)

    # Sicherheitsnetz: Einzelartikel dürfen nie spectrum_count > 1 oder falsches Label haben
    for a in ergebnisse:
        if a.get("cluster_size", 1) == 1:
            a["spectrum_count"] = 1
            a["blindspot_label"] = "Einzelmeldung"

    dateiname = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dateiname, "w", encoding="utf-8") as f:
        json.dump(ergebnisse, f, ensure_ascii=True, indent=2)

    breaking_count = sum(1 for a in ergebnisse if a.get("is_breaking", False))
    top_story_count = sum(1 for a in ergebnisse if a.get("is_top_story", False))
    normal_count = len(ergebnisse) - breaking_count
    scores = [a.get("relevance_score", 0) for a in ergebnisse]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    print(f"\n Fertig! {len(ergebnisse)} Stories gespeichert in: {dateiname}")
    print(f" ({breaking_count} Breaking, {normal_count} Normal, {cluster_synthetisiert} Cluster synthetisiert)")
    if uebersprungen:
        print(f" ({uebersprungen} Artikel wegen zu vager Headline übersprungen)")

    print(f"\n{'─' * 60}")
    print(f"  LAUF-STATISTIK")
    print(f"{'─' * 60}")
    print(f"  Gesamtanzahl Stories:        {len(ergebnisse)}")
    print(f"  Cluster synthetisiert:       {cluster_synthetisiert}")
    print(f"  is_top_story = true:         {top_story_count}")
    print(f"  Durchschnittlicher Score:    {avg_score}")

    top_beispiel = next((a for a in ergebnisse if a.get("is_top_story")), None)
    if top_beispiel:
        print(f"\n  Beispiel Top Story:")
        print(f"    Headline:   {top_beispiel['headline'][:65]}")
        print(f"    Kategorie:  {top_beispiel['category']}")
        print(f"    Score:      {top_beispiel.get('relevance_score', '–')}")
        print(f"    Blindspot:  {top_beispiel.get('blindspot_label', '–')}")
        print(f"    Cluster:    {top_beispiel.get('cluster_size', 1)} Quelle(n)")
        print(f"    Bild:       {'ja' if top_beispiel.get('image_url') else 'nein'}")
    print(f"{'─' * 60}\n")

    print("-" * 60)

    breaking_artikel = [a for a in ergebnisse if a.get("is_breaking", False)]
    multi_artikel = [a for a in ergebnisse if not a.get("is_breaking", False) and a["cluster_size"] > 1]
    einzel_artikel = [a for a in ergebnisse if not a.get("is_breaking", False) and a["cluster_size"] == 1]

    def _zeige_artikel(artikel, breaking=False):
        leaning = artikel["political_leaning"].ljust(12)
        kategorie = artikel["category"].ljust(15)
        breaking_label = " *** BREAKING ***" if breaking else ""
        print(f"[{leaning}] [{kategorie}]{breaking_label}")
        print(f"  {artikel['headline']}")
        print(f"  {artikel['source']}")
        print()

    if breaking_artikel:
        print("\n" + "*" * 60)
        print("  *** BREAKING NEWS ***")
        print("*" * 60)
        letzter_cluster_id = None
        for artikel in breaking_artikel:
            cluster_id = artikel["cluster_id"]
            cluster_size = artikel["cluster_size"]
            if cluster_size > 1 and cluster_id != letzter_cluster_id:
                fueller = "-" * (44 - len(str(cluster_size)))
                print(f"\n-- {cluster_size} Quellen berichten {fueller}")
            letzter_cluster_id = cluster_id
            _zeige_artikel(artikel, breaking=True)

    if multi_artikel:
        letzter_cluster_id = None
        for artikel in multi_artikel:
            cluster_id = artikel["cluster_id"]
            cluster_size = artikel["cluster_size"]
            if cluster_id != letzter_cluster_id:
                fueller = "-" * (44 - len(str(cluster_size)))
                print(f"\n-- {cluster_size} Quellen berichten {fueller}")
            letzter_cluster_id = cluster_id
            _zeige_artikel(artikel)

    if einzel_artikel:
        print("\n-- Einzelmeldungen " + "-" * 41)
        for artikel in einzel_artikel:
            _zeige_artikel(artikel)

    logger.info(
        f"NORMAL DURCHLAUF: {len(ergebnisse)} Stories, "
        f"{cluster_synthetisiert} Cluster synthetisiert, "
        f"{uebersprungen} uebersprungen -> {dateiname}"
    )
    _zeige_naechsten_lauf()


def breaking_news_check(client, unsplash_key):
    jetzt = datetime.now()
    print(f"\n[{jetzt.strftime('%H:%M')}] Breaking-News-Check ...", end="", flush=True)

    alle = schlagzeilen_abrufen(max_pro_quelle=5, gesamt_limit=None, verbose=False)
    artikel = [a for a in alle if not ist_zu_vage(a["headline"])]

    if not artikel:
        print(" Keine Artikel abrufbar.")
        logger.info("BREAKING CHECK: Keine Artikel abgerufen.")
        return

    schlagzeilen_clustern(artikel)

    cluster_quellen = defaultdict(set)
    cluster_artikel = defaultdict(list)
    for a in artikel:
        cid = a["cluster_id"]
        cluster_quellen[cid].add(a["source"])
        cluster_artikel[cid].append(a)

    kandidaten = [
        cid for cid, quellen in cluster_quellen.items()
        if len(quellen) >= BREAKING_QUELLEN_SCHWELLE
    ]

    if not kandidaten:
        print(f" Alles ruhig. ({len(artikel)} Artikel gecheckt)")
        logger.info(f"BREAKING CHECK: Keine Kandidaten. {len(artikel)} Artikel gecheckt.")
        return

    print(f"\n  {len(kandidaten)} Kandidat(en) mit {BREAKING_QUELLEN_SCHWELLE}+ Quellen gefunden!")

    seen = breaking_seen_laden()
    neu = []
    for cid in kandidaten:
        fingerprint = _cluster_fingerprint(cluster_artikel[cid])
        if fingerprint not in seen:
            neu.append((cid, fingerprint, cluster_artikel[cid], cluster_quellen[cid]))

    if not neu:
        print(f"  Alle {len(kandidaten)} Kandidaten bereits bekannt.")
        logger.info(f"BREAKING CHECK: {len(kandidaten)} Kandidaten, alle bereits bekannt.")
        return

    print(f"  {len(neu)} neue Breaking News! Rufe Claude auf ...")
    ergebnisse = []

    for cid, fingerprint, arts, quellen in neu:
        bester = arts[0]
        quellen_str = ", ".join(sorted(quellen))
        print(f"\n  *** BREAKING: \"{bester['headline'][:65]}\"")
        print(f"      Quellen ({len(quellen)}): {quellen_str}")

        try:
            analyse = analyse_mit_claude(client, bester)
        except Exception as e:
            print(f"      Claude-Fehler: {e}")
            continue

        bild = bester["image_url"]
        if not bild and unsplash_key:
            bild = unsplash_bild_suchen(
                bester["headline"], analyse.get("category", ""), unsplash_key
            )
        if not bild:
            bild = KATEGORIE_FALLBACK_BILDER.get(analyse.get("category", ""), "")

        ergebnisse.append({
            "headline": bester["headline"],
            "summary": analyse.get("summary", ""),
            "source": bester["source"],
            "political_leaning": bester["political_leaning"],
            "category": analyse.get("category", "Sonstiges"),
            "is_breaking": True,
            "breaking_sources": sorted(quellen),
            "relevance_score": analyse.get("relevance_score", 80),
            "is_top_story": analyse.get("is_top_story", True),
            "image_url": bild,
            "link": bester["link"],
            "timestamp": jetzt.isoformat(),
        })
        seen.add(fingerprint)
        logger.info(
            f"BREAKING NEWS: \"{bester['headline'][:80]}\" "
            f"({len(quellen)} Quellen: {quellen_str})"
        )

    if ergebnisse:
        dateiname = f"breaking_{jetzt.strftime('%Y%m%d_%H%M%S')}.json"
        with open(dateiname, "w", encoding="utf-8") as f:
            json.dump(ergebnisse, f, ensure_ascii=True, indent=2)
        print(f"\n  {len(ergebnisse)} Breaking News gespeichert in: {dateiname}")
        logger.info(
            f"BREAKING CHECK: {len(ergebnisse)} neue Stories gespeichert -> {dateiname}"
        )
        _zeige_naechsten_lauf()

    breaking_seen_speichern(seen)


# ─── Scheduling-Hilfsfunktion ────────────────────────────────────
def _zeige_naechsten_lauf():
    normal_jobs = schedule.get_jobs("normal")
    breaking_jobs = schedule.get_jobs("breaking")
    jetzt = datetime.now()
    print("\n" + "-" * 60)
    if breaking_jobs:
        naechster = min(j.next_run for j in breaking_jobs)
        diff_min = max(0, int((naechster - jetzt).total_seconds() / 60))
        print(f"  Breaking-News-Check: {naechster.strftime('%H:%M')} Uhr  (in {diff_min} Min.)")
    if normal_jobs:
        naechster = min(j.next_run for j in normal_jobs)
        diff_min = max(0, int((naechster - jetzt).total_seconds() / 60))
        print(f"  Normal-Durchlauf:    {naechster.strftime('%H:%M')} Uhr  (in {diff_min} Min.)")
    print("-" * 60)


# ─── Einstiegspunkt ─────────────────────────────────────────────
def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nFEHLER: Kein API-Key gefunden!")
        print("Bitte trage deinen Anthropic API-Key in die .env Datei ein.")
        print("Zeile in .env: ANTHROPIC_API_KEY=dein-key-hier\n")
        return

    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    client = anthropic.Anthropic(api_key=api_key)

    print("\n" + "=" * 60)
    print("  UNGEFAERBT NEWS AGENT  –  Scheduling aktiv")
    print(f"  Normal-Durchlauf:     {', '.join(NORMAL_ZEITEN)} Uhr")
    print(f"  Breaking-News-Check:  alle {BREAKING_INTERVALL_MIN} Minuten")
    print(f"  Unsplash-Fallback:    {'aktiv' if unsplash_key else 'inaktiv'}")
    print(f"  Log-Datei:            log.txt")
    print("=" * 60)
    logger.info("News Agent gestartet.")

    # Sofortiger erster Durchlauf zum Testen
    print("\nStarte initialen Durchlauf ...\n")
    normaler_durchlauf(client, unsplash_key)

    # # Schedules einrichten
    # for uhrzeit in NORMAL_ZEITEN:
    #     schedule.every().day.at(uhrzeit).do(
    #         normaler_durchlauf, client, unsplash_key
    #     ).tag("normal")

    # schedule.every(BREAKING_INTERVALL_MIN).minutes.do(
    #     breaking_news_check, client, unsplash_key
    # ).tag("breaking")

    # _zeige_naechsten_lauf()
    # print("  Agent laeuft im Hintergrund. Beenden mit Strg+C.\n")

    # letzter_status_ts = time.time()
    # try:
    #     while True:
    #         schedule.run_pending()
    #         # Alle 30 Minuten Status-Erinnerung
    #         if time.time() - letzter_status_ts >= 1800:
    #             _zeige_naechsten_lauf()
    #             letzter_status_ts = time.time()
    #         time.sleep(30)
    # except KeyboardInterrupt:
    #     print("\n\nAgent gestoppt (Strg+C).")
    #     logger.info("News Agent gestoppt.")


if __name__ == "__main__":
    main()
