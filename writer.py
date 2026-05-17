import json
import re

from config import SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# Hilfsfunktion: JSON sauber parsen
# ---------------------------------------------------------------------------

def _parse_json(text: str, pflichtfelder: list[str]) -> dict:
    """
    Parst JSON aus dem Modell-Output.
    Entfernt Markdown-Blöcke falls vorhanden.
    Fällt auf Regex zurück wenn JSON ungültig ist.
    Wirft einen Fehler wenn Pflichtfelder fehlen.
    """
    # Markdown-Blöcke entfernen
    if "```" in text:
        parts = text.split("```")
        # Nimm den ersten Block nach dem ersten ```
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    # Direktes Parsen versuchen
    try:
        ergebnis = json.loads(text)
    except json.JSONDecodeError:
        # Regex-Fallback: alle bekannten Felder extrahieren
        ergebnis = {}
        for feld in pflichtfelder:
            # Strings
            match = re.search(
                rf'"{feld}"\s*:\s*"(.*?)"(?=\s*[,}}])', text, re.DOTALL
            )
            if match:
                ergebnis[feld] = match.group(1).replace('\\"', '"')
                continue
            # Booleans
            match = re.search(rf'"{feld}"\s*:\s*(true|false)', text)
            if match:
                ergebnis[feld] = match.group(1) == "true"
                continue
            # Zahlen
            match = re.search(rf'"{feld}"\s*:\s*(\d+)', text)
            if match:
                ergebnis[feld] = int(match.group(1))

    # Prüfen ob alle Pflichtfelder vorhanden sind
    fehlend = [f for f in pflichtfelder if f not in ergebnis]
    if fehlend:
        raise ValueError(
            f"Modell-Antwort enthält nicht alle Pflichtfelder. "
            f"Fehlend: {fehlend}. Rohtext: {text[:300]}"
        )

    return ergebnis


# ---------------------------------------------------------------------------
# Klassifizierung (Haiku) — schnell & günstig, nur Metadaten
# ---------------------------------------------------------------------------

def klassifizieren_mit_haiku(client, artikel: dict) -> dict:
    """
    Klassifiziert einen Artikel nach Kategorie, Relevanz und Breaking-Status.
    Wird für ALLE Artikel aufgerufen — auch für spätere Cluster-Artikel.
    Kein Sonnet, kein Summary hier.
    """
    teaser_block = ""
    if artikel.get("teaser"):
        teaser_block = f'\nBeschreibung: "{artikel["teaser"]}"\n'

    prompt = f"""Klassifiziere diesen Nachrichtenartikel:

Headline: "{artikel['headline']}"{teaser_block}

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
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    text = antwort.content[0].text.strip()

    try:
        return _parse_json(text, ["category", "is_breaking", "relevance_score", "is_top_story"])
    except (ValueError, Exception):
        # Sicherer Fallback — Klassifizierung ist nie ein Blocker
        return {
            "category": "Sonstiges",
            "is_breaking": False,
            "relevance_score": 50,
            "is_top_story": False,
        }


# ---------------------------------------------------------------------------
# Cluster-Synthese (Sonnet) — das Herzstück
# ---------------------------------------------------------------------------

SYNTHESE_PROMPT = """\
Du bist Redakteur bei "ungefärbt" — einem Nachrichtenmedium das ausschließlich \
faktenbasiert berichtet. Deine Aufgabe: Mehrere Berichte über dasselbe Ereignis \
zu einer einzigen klaren, neutralen Story zusammenfassen.

Deine Grundsätze:
- Nur belegbare Fakten. Keine Meinung, keine Wertung, keine Interpretation.
- Keine politische Färbung in keine Richtung.
- Verweise NIE auf andere Quellen. Kein "laut Spiegel", kein "wie berichtet wird", \
kein "einem Bericht zufolge". Du bist der Journalist — du kennst die Fakten.
- Übernimm nie Formulierungen 1:1 aus den Quellen. Schreibe alles neu in deiner eigenen Sprache.
- Schreibe klar und direkt — verständlich für jeden, aber nicht monoton. \
Informativ und trotzdem angenehm zu lesen.
- Keine Ausrufezeichen, kein Clickbait, keine reißerischen Formulierungen.
"""

def cluster_synthese_mit_sonnet(client, cluster_artikel: list[dict]) -> dict:
    """
    Synthetisiert 2+ Artikel desselben Clusters zu einer einzigen ungefärbten Story.
    
    Gibt zurück:
        {"headline": str, "summary": str}
    oder:
        {"summary": "KEIN_CLUSTER"} wenn die Artikel nicht dasselbe Ereignis beschreiben.
    
    Wirft eine Exception bei API-Fehler (Aufrufer soll entscheiden wie er damit umgeht).
    """
    if len(cluster_artikel) < 2:
        raise ValueError(
            f"cluster_synthese_mit_sonnet erwartet mindestens 2 Artikel, "
            f"bekommen: {len(cluster_artikel)}"
        )

    # Artikel-Texte aufbereiten — ohne political_leaning, nur Inhalt zählt
    artikel_texte = []
    for i, a in enumerate(cluster_artikel, 1):
        zeilen = [f"Bericht {i}:"]
        zeilen.append(f'Headline: "{a["headline"]}"')
        if a.get("teaser"):
            zeilen.append(f'Beschreibung: "{a["teaser"]}"')
        if a.get("summary"):
            zeilen.append(f'Zusammenfassung: {a["summary"]}')
        artikel_texte.append("\n".join(zeilen))

    anzahl = len(cluster_artikel)
    artikel_block = "\n\n".join(artikel_texte)

    prompt = f"""Hier sind {anzahl} Berichte. Prüfe zuerst: Beschreiben sie dasselbe konkrete Ereignis?

{artikel_block}

Falls NEIN — die Artikel haben thematisch nichts miteinander zu tun \
(komplett unterschiedliche Ereignisse, Personen und Orte) — \
antworte ausschließlich mit:
{{"summary": "KEIN_CLUSTER"}}

Wichtig: Antworte NICHT mit KEIN_CLUSTER wenn die Artikel dasselbe \
Thema aus verschiedenen Winkeln beleuchten, verschiedene Aspekte \
desselben Ereignisses zeigen, oder zeitlich zusammenhängende \
Entwicklungen derselben Geschichte beschreiben. \
Diese sollen synthetisiert werden.

Falls JA — schreibe:
1. Eine eigene Headline auf Deutsch (max. 10 Wörter). \
Sachlich, klar, kein Clickbait, keine Meinung.
2. Eine Zusammenfassung in 2–3 Sätzen. \
Nur Fakten. Keine Quellenverweise. Deine eigene Sprache.

Antworte NUR mit diesem JSON (kein weiterer Text):
{{
  "headline": "Deine neutrale Headline",
  "summary": "Deine neutrale Zusammenfassung in 2–3 Sätzen."
}}"""

    antwort = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=[{
            "type": "text",
            "text": f"{SYSTEM_PROMPT}\n\n{SYNTHESE_PROMPT}",
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    text = antwort.content[0].text.strip()

    # KEIN_CLUSTER früh erkennen — vor dem JSON-Parsing
    if "KEIN_CLUSTER" in text:
        return {"summary": "KEIN_CLUSTER"}

    return _parse_json(text, ["headline", "summary"])


def analyse_mit_claude(client, artikel):
    return klassifizieren_mit_haiku(client, artikel)
