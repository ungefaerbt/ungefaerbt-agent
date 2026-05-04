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

sys.stdout.reconfigure(encoding="utf-8")
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

SYSTEM_PROMPT = """Du bist ein neutraler Nachrichtenanalyst für das Projekt "ungefärbt".
Deine Aufgabe: Nachrichtenüberschriften sachlich und ohne Wertung zusammenfassen.
Regeln:
- Nur belegbare Fakten, keine Meinungen oder Spekulationen
- Klare, einfache Sprache auf Deutsch
- 2–3 Sätze pro Zusammenfassung
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

    def keywords(headline):
        return {
            w.strip(sonderzeichen).lower()
            for w in headline.split()
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

    kw_liste = [keywords(a["headline"]) for a in artikel_liste]
    for i in range(n):
        for j in range(i + 1, n):
            if len(kw_liste[i] & kw_liste[j]) >= 2:
                eltern[find(i)] = find(j)

    wurzeln = [find(i) for i in range(n)]
    groessen = Counter(wurzeln)

    for i, artikel in enumerate(artikel_liste):
        artikel["cluster_id"] = wurzeln[i]
        artikel["cluster_size"] = groessen[wurzeln[i]]

    artikel_liste.sort(
        key=lambda a: (a["cluster_size"], a.get("is_breaking", False)),
        reverse=True,
    )
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
def schlagzeilen_abrufen(max_pro_quelle=2, gesamt_limit=10, verbose=True):
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
def analyse_mit_claude(client, schlagzeile):
    teaser_block = ""
    if schlagzeile.get("teaser"):
        teaser_block = f'\nBeschreibung: "{schlagzeile["teaser"]}"\n'

    nutzer_nachricht = f"""Analysiere diesen Nachrichtenartikel von {schlagzeile['source']}:

Headline: "{schlagzeile['headline']}"{teaser_block}

Antworte NUR mit diesem JSON (kein weiterer Text):
{{
  "summary": "Neutrale Zusammenfassung in 2–3 Sätzen.",
  "category": "Eines von: Politik / Wirtschaft / Gesellschaft / Technologie / Sport / Kultur / Umwelt",
  "is_breaking": false
}}"""

    antwort = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
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
        summary_match = re.search(r'"summary"\s*:\s*"(.*?)"(?=\s*,\s*"|\s*\})', text, re.DOTALL)
        category_match = re.search(r'"category"\s*:\s*"([^"]+)"', text)
        breaking_match = re.search(r'"is_breaking"\s*:\s*(true|false)', text)
        if not summary_match:
            raise
        return {
            "summary": summary_match.group(1).replace('\\"', '"'),
            "category": category_match.group(1) if category_match else "Sonstiges",
            "is_breaking": breaking_match.group(1) == "true" if breaking_match else False,
        }


# ─── Durchläufe ─────────────────────────────────────────────────
def normaler_durchlauf(client, unsplash_key):
    jetzt_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n{'═' * 60}")
    print(f"  NORMALER DURCHLAUF – {jetzt_str}")
    print(f"{'═' * 60}")

    schlagzeilen = schlagzeilen_abrufen()

    if not schlagzeilen:
        print("\nKeine Schlagzeilen gefunden. Bitte Internetverbindung prüfen.")
        logger.info("NORMAL DURCHLAUF: Keine Schlagzeilen gefunden.")
        return

    print(f"\nAnalysiere {len(schlagzeilen)} Schlagzeilen mit Claude ...\n")
    ergebnisse = []
    uebersprungen = 0

    for i, artikel in enumerate(schlagzeilen, 1):
        if ist_zu_vage(artikel["headline"]):
            print(f"  [{i}/{len(schlagzeilen)}] ÜBERSPRUNGEN (zu vage): {artikel['headline'][:70]}")
            uebersprungen += 1
            continue
        print(f"  [{i}/{len(schlagzeilen)}] {artikel['headline'][:70]}...")
        try:
            analyse = analyse_mit_claude(client, artikel)
            kategorie = analyse.get("category", "Sonstiges")
            image_url = artikel["image_url"]
            if not image_url:
                image_url = unsplash_bild_suchen(artikel["headline"], kategorie, unsplash_key)
                if image_url:
                    print(f"    Unsplash-Bild gefunden.")
            ergebnisse.append({
                "headline": artikel["headline"],
                "summary": analyse.get("summary", ""),
                "source": artikel["source"],
                "political_leaning": artikel["political_leaning"],
                "category": kategorie,
                "is_breaking": analyse.get("is_breaking", False),
                "image_url": image_url,
                "link": artikel["link"],
                "timestamp": datetime.now().isoformat(),
            })
            time.sleep(0.5)
        except Exception as fehler:
            print(f"    Fehler bei Analyse: {fehler}")

    schlagzeilen_clustern(ergebnisse)

    dateiname = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dateiname, "w", encoding="utf-8") as f:
        json.dump(ergebnisse, f, ensure_ascii=True, indent=2)

    print(f"\n Fertig! {len(ergebnisse)} Artikel gespeichert in: {dateiname}")
    if uebersprungen:
        print(f" ({uebersprungen} Artikel wegen zu vager Headline übersprungen)\n")
    else:
        print()

    print("─" * 60)
    letzter_cluster_id = None
    einzelmeldungen_gezeigt = False
    for artikel in ergebnisse:
        cluster_id = artikel["cluster_id"]
        cluster_size = artikel["cluster_size"]
        if cluster_size > 1:
            if cluster_id != letzter_cluster_id:
                fueller = "─" * (44 - len(str(cluster_size)))
                print(f"\n── {cluster_size} Quellen berichten {fueller}")
            letzter_cluster_id = cluster_id
        else:
            if not einzelmeldungen_gezeigt:
                print("\n── Einzelmeldungen " + "─" * 41)
                einzelmeldungen_gezeigt = True
        leaning = artikel["political_leaning"].ljust(12)
        kategorie = artikel["category"].ljust(15)
        breaking = " *** BREAKING ***" if artikel["is_breaking"] else ""
        print(f"[{leaning}] [{kategorie}]{breaking}")
        print(f"  {artikel['headline']}")
        print(f"  {artikel['source']}")
        print()

    logger.info(
        f"NORMAL DURCHLAUF: {len(ergebnisse)} Artikel analysiert, "
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

        ergebnisse.append({
            "headline": bester["headline"],
            "summary": analyse.get("summary", ""),
            "source": bester["source"],
            "political_leaning": bester["political_leaning"],
            "category": analyse.get("category", "Sonstiges"),
            "is_breaking": True,
            "breaking_sources": sorted(quellen),
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
    print("\n" + "─" * 60)
    if breaking_jobs:
        naechster = min(j.next_run for j in breaking_jobs)
        diff_min = max(0, int((naechster - jetzt).total_seconds() / 60))
        print(f"  Breaking-News-Check: {naechster.strftime('%H:%M')} Uhr  (in {diff_min} Min.)")
    if normal_jobs:
        naechster = min(j.next_run for j in normal_jobs)
        diff_min = max(0, int((naechster - jetzt).total_seconds() / 60))
        print(f"  Normal-Durchlauf:    {naechster.strftime('%H:%M')} Uhr  (in {diff_min} Min.)")
    print("─" * 60)


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

    # Schedules einrichten
    for uhrzeit in NORMAL_ZEITEN:
        schedule.every().day.at(uhrzeit).do(
            normaler_durchlauf, client, unsplash_key
        ).tag("normal")

    schedule.every(BREAKING_INTERVALL_MIN).minutes.do(
        breaking_news_check, client, unsplash_key
    ).tag("breaking")

    _zeige_naechsten_lauf()
    print("  Agent laeuft im Hintergrund. Beenden mit Strg+C.\n")

    letzter_status_ts = time.time()
    try:
        while True:
            schedule.run_pending()
            # Alle 30 Minuten Status-Erinnerung
            if time.time() - letzter_status_ts >= 1800:
                _zeige_naechsten_lauf()
                letzter_status_ts = time.time()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nAgent gestoppt (Strg+C).")
        logger.info("News Agent gestoppt.")


if __name__ == "__main__":
    main()
