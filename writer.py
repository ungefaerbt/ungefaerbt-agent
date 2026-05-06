import json
import re

from config import SYSTEM_PROMPT


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

Falls der Artikel kein seriöser Nachrichtenartikel ist (Satire, Werbung, fiktiver Inhalt, kein journalistischer Nachrichtenwert), antworte NUR mit:
{{"summary": "KEIN_ARTIKEL"}}

Andernfalls schreibe eine eigene sachliche Headline auf Deutsch in max. 10 Wörtern. Keine Meinung, keine Wertung, keine Ausrufezeichen, kein Clickbait. Nur belegbare Fakten.

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


def analyse_mit_claude(client, schlagzeile):
    klassifikation = klassifizieren_mit_haiku(client, schlagzeile)
    zusammenfassung = zusammenfassen_mit_sonnet(client, schlagzeile)
    return {**klassifikation, **zusammenfassung}
