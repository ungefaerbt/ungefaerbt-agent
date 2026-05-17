"""
social_pack.py
--------------
Baut fertige Social-Media-Posts aus final_social_candidates.json.

Für Stories mit has_contrast == true und nicht-leeren contrast_pairs:
    Kontrast-Post mit zwei gegenübergestellten Headlines.

Für Stories ohne Kontrast aber social_post_worthy == true:
    Standard-Post mit Headline und Summary (max. 2 Sätze).

Output: output/social_pack_output.json
"""

import json
import logging
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("social_pack")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.propagate = False


_SPEKTRUM_PRIORITAET = ["Links", "Rechts", "Mitte-Links", "Mitte-Rechts", "Mitte"]


def _source_headlines_extrahieren(story: dict, max_quellen: int = 5) -> list:
    artikel = story.get("source_articles") or []
    if not artikel:
        return []

    nach_leaning: dict = {}
    for a in artikel:
        leaning = (a.get("political_leaning") or "Unbekannt").strip()
        nach_leaning.setdefault(leaning, []).append(a)

    ausgewaehlt = []
    gesehen_leanings: set = set()

    # Zuerst je eine Quelle pro Spektrum, Enden zuerst
    for leaning in _SPEKTRUM_PRIORITAET:
        if len(ausgewaehlt) >= max_quellen:
            break
        if leaning in nach_leaning and leaning not in gesehen_leanings:
            a = nach_leaning[leaning][0]
            ausgewaehlt.append({
                "source":   a.get("source", ""),
                "headline": a.get("headline", ""),
                "leaning":  leaning,
            })
            gesehen_leanings.add(leaning)

    # Auffüllen mit noch nicht enthaltenen Artikeln (original Reihenfolge)
    schon_drin = {(e["source"], e["headline"]) for e in ausgewaehlt}
    for a in artikel:
        if len(ausgewaehlt) >= max_quellen:
            break
        key = (a.get("source", ""), a.get("headline", ""))
        if key not in schon_drin:
            ausgewaehlt.append({
                "source":   a.get("source", ""),
                "headline": a.get("headline", ""),
                "leaning":  (a.get("political_leaning") or "Unbekannt").strip(),
            })
            schon_drin.add(key)

    return ausgewaehlt


def _summary_kuerzen(summary: str, max_saetze: int = 2) -> str:
    if not summary:
        return ""
    saetze = [s.strip() for s in summary.split(".") if s.strip()]
    return ". ".join(saetze[:max_saetze]) + "." if saetze else summary


def _kontrast_post(story: dict) -> dict:
    pairs = story["contrast_pairs"]
    pair = pairs[0]
    quelle_a = pair.get("source_a") or pair.get("source_1", "Quelle A")
    quelle_b = pair.get("source_b") or pair.get("source_2", "Quelle B")
    headline_a = pair.get("headline_a") or pair.get("headline_1", "")
    headline_b = pair.get("headline_b") or pair.get("headline_2", "")
    thema = story.get("headline", "")

    post_text = (
        f"📰 {thema}\n\n"
        f"{quelle_a} sagt: '{headline_a}'\n"
        f"{quelle_b} sagt: '{headline_b}'\n\n"
        f"➡️ Was steckt dahinter? Link in Bio."
    )

    return {
        "post_text":             post_text,
        "post_type":             "contrast",
        "story_id":              story.get("story_id", ""),
        "headline":              thema,
        "social_priority_score": story.get("social_priority_score", 0),
        "suggested_format":      story.get("suggested_social_format", ""),
        "source_headlines":      _source_headlines_extrahieren(story),
    }


def _standard_post(story: dict) -> dict:
    headline = story.get("headline", "")
    summary = _summary_kuerzen(story.get("summary", ""), max_saetze=2)

    post_text = f"📰 {headline}"
    if summary:
        post_text += f"\n\n{summary}"
    post_text += "\n\n➡️ Link in Bio."

    return {
        "post_text":             post_text,
        "post_type":             "standard",
        "story_id":              story.get("story_id", ""),
        "headline":              headline,
        "social_priority_score": story.get("social_priority_score", 0),
        "suggested_format":      story.get("suggested_social_format", ""),
        "source_headlines":      _source_headlines_extrahieren(story),
    }


def social_pack_erstellen(input_pfad: str) -> list:
    with open(input_pfad, "r", encoding="utf-8") as f:
        kandidaten = json.load(f)

    posts = []
    kontrast_count = 0
    standard_count = 0

    for story in kandidaten:
        hat_kontrast = story.get("has_contrast", False)
        contrast_pairs = story.get("contrast_pairs") or []
        social_post_worthy = story.get("social_post_worthy", False)

        if hat_kontrast and contrast_pairs:
            posts.append(_kontrast_post(story))
            kontrast_count += 1
        elif social_post_worthy:
            posts.append(_standard_post(story))
            standard_count += 1

    posts.sort(key=lambda p: p["social_priority_score"], reverse=True)

    out_pfad = OUTPUT_DIR / "social_pack_output.json"
    with open(out_pfad, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    logger.info(
        "social_pack abgeschlossen — %s Posts (%s Kontrast, %s Standard) → social_pack_output.json",
        len(posts), kontrast_count, standard_count,
    )
    return posts


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 social_pack.py output/final_social_candidates.json")
        sys.exit(1)
    social_pack_erstellen(sys.argv[1])
