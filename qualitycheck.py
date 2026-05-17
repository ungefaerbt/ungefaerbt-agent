import json
import logging
import os
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("qualitycheck")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.propagate = False

# ── Konfigurierbare Schwellenwerte ──────────────────────────────────────────
SIMILARITY_THRESHOLD_IGNORE = 0.10
SIMILARITY_THRESHOLD_MARK   = 0.20
SIMILARITY_THRESHOLD_CLAUDE = 0.20
MAX_CLAUDE_CANDIDATES       = 20
DEFAULT_MERGE_MODE          = "keep_best"

# ── Wertende Wörter (einfacher Heuristik-Check) ─────────────────────────────
_OPINION_WORDS = {
    "skandalös", "skandal", "erschreckend", "inakzeptabel", "katastrophal",
    "bedauerlicherweise", "erfreulicherweise", "unglaublich", "endlich",
    "leider", "natürlich", "offensichtlich", "gefährlich", "notwendigerweise",
}

# ── TF-IDF oder Token-Overlap-Fallback ──────────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine_sim
    _SKLEARN = True
except ImportError:
    _SKLEARN = False


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _story_text(story):
    return " ".join(filter(None, [
        story.get("headline", ""),
        story.get("summary", ""),
        story.get("category", ""),
    ]))


def _aehnlichkeiten_tfidf(stories):
    texte = [_story_text(s) for s in stories]
    vec = TfidfVectorizer(min_df=1)
    matrix = vec.fit_transform(texte)
    sim = _cosine_sim(matrix)
    return {(i, j): float(sim[i, j]) for i, j in combinations(range(len(stories)), 2)}


def _aehnlichkeiten_token(stories):
    token_sets = [set(_story_text(s).lower().split()) for s in stories]
    ergebnis = {}
    for i, j in combinations(range(len(stories)), 2):
        a, b = token_sets[i], token_sets[j]
        union = a | b
        ergebnis[(i, j)] = len(a & b) / len(union) if union else 0.0
    return ergebnis


def aehnlichkeiten_berechnen(stories):
    if len(stories) < 2:
        return {}
    return _aehnlichkeiten_tfidf(stories) if _SKLEARN else _aehnlichkeiten_token(stories)


def stories_laden(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        roh = json.load(f)
    if isinstance(roh, list):
        return roh
    for key in ("stories", "articles", "news", "items"):
        if key in roh and isinstance(roh[key], list):
            return roh[key]
    raise ValueError(
        f"Keine bekannte Story-Struktur in '{pfad}' gefunden. "
        "Erwartet: Liste oder Dict mit Key 'stories', 'articles', 'news' oder 'items'."
    )


def pflichtfelder_pruefen(story):
    notes = []
    for feld in ("headline", "summary", "category", "relevance_score", "timestamp"):
        wert = story.get(feld)
        if wert is None or wert == "" or wert == []:
            notes.append(f"missing_{feld}")
    if not (story.get("sources") or story.get("source")):
        notes.append("missing_sources")
    return notes


def einfache_checks(story):
    notes = []
    headline = story.get("headline", "")
    summary = story.get("summary", "")
    if headline and len(headline.split()) < 4:
        notes.append("very_short_headline")
    if summary and len(summary.split()) < 10:
        notes.append("very_short_summary")
    if set(headline.lower().split()) & _OPINION_WORDS:
        notes.append("possibly_opinionated_headline")
    return notes


def _quellen_liste(story):
    q = story.get("sources") or story.get("source") or ""
    return [x.strip() for x in q.split(",") if x.strip()]


def _leanings_liste(story):
    l = story.get("political_leaning", "")
    return [x.strip() for x in l.split(",") if x.strip()]


def _story_rang(story):
    return (
        story.get("relevance_score", 0),
        int(bool(story.get("is_top_story", False))),
        story.get("cluster_size", 1),
        len(_quellen_liste(story)),
        len(story.get("summary", "")),
    )


def beste_story(a, b):
    return a if _story_rang(a) >= _story_rang(b) else b


def mergen(basis, andere, id_basis, id_andere):
    merged = dict(basis)

    alle_quellen = list(dict.fromkeys(_quellen_liste(basis) + _quellen_liste(andere)))
    merged["source"] = ", ".join(alle_quellen)

    alle_leanings = list(dict.fromkeys(_leanings_liste(basis) + _leanings_liste(andere)))
    merged["political_leaning"] = ", ".join(alle_leanings)

    merged["cluster_size"] = basis.get("cluster_size", 1) + andere.get("cluster_size", 1)
    merged["relevance_score"] = max(
        basis.get("relevance_score", 0),
        andere.get("relevance_score", 0),
    )
    merged["is_top_story"] = bool(basis.get("is_top_story")) or bool(andere.get("is_top_story"))
    merged["merged_from"] = [id_basis, id_andere]

    notizen = list(merged.get("quality_notes", []))
    if "merged_duplicate_story" not in notizen:
        notizen.append("merged_duplicate_story")
    merged["quality_notes"] = notizen
    merged["quality_status"] = "ready"

    return merged


def claude_paare_pruefen(kandidaten, stories):
    """
    Sendet alle Kandidatenpaare in einem einzigen Claude-Call.
    Gibt (dict pair_id→ergebnis, fehler_str_oder_None) zurück.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("Kein ANTHROPIC_API_KEY — Claude-Check übersprungen.")
        return {}, "kein_api_key"

    paare_json = []
    for idx, (i, j) in enumerate(kandidaten):
        sa, sb = stories[i], stories[j]
        paare_json.append({
            "pair_id": f"pair_{idx}",
            "story_a": {
                "headline": sa.get("headline", ""),
                "summary":  sa.get("summary", ""),
                "category": sa.get("category", ""),
            },
            "story_b": {
                "headline": sb.get("headline", ""),
                "summary":  sb.get("summary", ""),
                "category": sb.get("category", ""),
            },
        })

    prompt = (
        "Du bekommst Story-Paare. Entscheide für jedes Paar, ob beide Stories "
        "dasselbe konkrete Ereignis behandeln.\n\n"
        "Erlaubte decision-Werte: same_event | related_but_separate | different_event | uncertain\n\n"
        "Antworte NUR mit einem JSON-Array (kein weiterer Text):\n"
        "[{\"pair_id\": \"pair_0\", \"decision\": \"same_event\", "
        "\"confidence\": 0.91, \"reason\": \"...\"}]\n\n"
        f"Paare:\n{json.dumps(paare_json, ensure_ascii=False, indent=2)}"
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        antwort = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = antwort.content[0].text.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]
        ergebnisse = json.loads(text.strip())
        return {e["pair_id"]: e for e in ergebnisse}, None
    except Exception as e:
        logger.error("Claude-Call fehlgeschlagen: %s", e)
        return {}, str(e)


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def qualitycheck(input_pfad):
    logger.info("qualitycheck gestartet: %s", input_pfad)

    stories = stories_laden(input_pfad)
    stories_vorher = len(stories)
    logger.info("%s Stories geladen.", stories_vorher)

    ids = [f"story_{i}" for i in range(len(stories))]

    # Pflichtfelder + einfache Checks
    for story in stories:
        notizen = pflichtfelder_pruefen(story) + einfache_checks(story)
        story["quality_notes"] = notizen
        story["quality_status"] = "needs_review" if notizen else "ready"

    # Ähnlichkeit berechnen
    sim_map = aehnlichkeiten_berechnen(stories)

    kandidaten_claude = []
    markiert_related = []

    for (i, j), score in sim_map.items():
        if score >= SIMILARITY_THRESHOLD_CLAUDE:
            kandidaten_claude.append((i, j))
        elif score >= SIMILARITY_THRESHOLD_MARK:
            markiert_related.append((i, j))

    kandidaten_claude = kandidaten_claude[:MAX_CLAUDE_CANDIDATES]

    # Nur Paare mit identischer category an Claude — Rest als different_event verwerfen
    different_category = [
        (i, j) for (i, j) in kandidaten_claude
        if stories[i].get("category") != stories[j].get("category")
    ]
    kandidaten_claude = [
        (i, j) for (i, j) in kandidaten_claude
        if stories[i].get("category") == stories[j].get("category")
    ]

    logger.info(
        "%s Claude-Kandidaten, %s possible_related markiert, %s wegen different_category verworfen.",
        len(kandidaten_claude), len(markiert_related), len(different_category),
    )

    # possible_related markieren (kein Claude-Call)
    for i, j in markiert_related:
        for story_idx, other_idx in [(i, j), (j, i)]:
            related = stories[story_idx].setdefault("possible_related_stories", [])
            other_id = ids[other_idx]
            if other_id not in related:
                related.append(other_id)

    # Claude-Check
    claude_ergebnisse = {}
    claude_fehler = None
    claude_calls = 0

    if kandidaten_claude:
        claude_ergebnisse, claude_fehler = claude_paare_pruefen(kandidaten_claude, stories)
        if claude_ergebnisse:
            claude_calls = 1

    # Mergen
    merged_pairs = []
    zu_entfernen = set()

    for idx, (i, j) in enumerate(kandidaten_claude):
        pair_id = f"pair_{idx}"
        ergebnis = claude_ergebnisse.get(pair_id)

        if ergebnis is None:
            for k in (i, j):
                notizen = stories[k].setdefault("quality_notes", [])
                if "possible_duplicate" not in notizen:
                    notizen.append("possible_duplicate")
                stories[k]["quality_status"] = "needs_review"
            continue

        decision   = ergebnis.get("decision", "uncertain")
        confidence = float(ergebnis.get("confidence", 0.0))

        if decision == "same_event" and confidence >= 0.80:
            if i in zu_entfernen or j in zu_entfernen:
                continue
            basis = beste_story(stories[i], stories[j])
            basis_idx  = i if basis is stories[i] else j
            andere_idx = j if basis_idx == i else i
            stories[basis_idx] = mergen(
                stories[basis_idx], stories[andere_idx],
                ids[basis_idx], ids[andere_idx],
            )
            zu_entfernen.add(andere_idx)
            merged_pairs.append({
                "pair_id":    pair_id,
                "merged_into": ids[basis_idx],
                "removed":     ids[andere_idx],
                "confidence":  confidence,
                "reason":      ergebnis.get("reason", ""),
            })

        elif decision == "uncertain":
            for k in (i, j):
                notizen = stories[k].setdefault("quality_notes", [])
                if "uncertain_duplicate" not in notizen:
                    notizen.append("uncertain_duplicate")
                stories[k]["quality_status"] = "needs_review"

        elif decision == "related_but_separate":
            for story_idx, other_idx in [(i, j), (j, i)]:
                related = stories[story_idx].setdefault("possible_related_stories", [])
                other_id = ids[other_idx]
                if other_id not in related:
                    related.append(other_id)

    finale_stories = [s for idx, s in enumerate(stories) if idx not in zu_entfernen]

    needs_review_count = sum(1 for s in finale_stories if s.get("quality_status") == "needs_review")

    logger.info(
        "Merges: %s | Stories vorher: %s, nachher: %s | needs_review: %s",
        len(merged_pairs), stories_vorher, len(finale_stories), needs_review_count,
    )

    # Output schreiben
    with open(OUTPUT_DIR / "final_news_checked.json", "w", encoding="utf-8") as f:
        json.dump(finale_stories, f, ensure_ascii=False, indent=2)

    warnings = []
    if claude_fehler == "kein_api_key":
        warnings.append("Kein ANTHROPIC_API_KEY — Claude-Check wurde übersprungen.")
    elif claude_fehler:
        warnings.append(f"Claude-Call fehlgeschlagen: {claude_fehler}")

    report = {
        "timestamp":               datetime.now().isoformat(),
        "input_file":              input_pfad,
        "sklearn_used":            _SKLEARN,
        "stories_before":          stories_vorher,
        "stories_after":           len(finale_stories),
        "technical_candidates_total": len(kandidaten_claude) + len(markiert_related) + len(different_category),
        "marked_possible_related": len(markiert_related),
        "different_category_filtered": len(different_category),
        "claude_candidates_total": len(kandidaten_claude),
        "claude_calls":            claude_calls,
        "confirmed_merges":        len(merged_pairs),
        "needs_review_count":      needs_review_count,
        "merged_pairs":            merged_pairs,
        "warnings":                warnings,
        "errors":                  [],
    }

    with open(OUTPUT_DIR / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("qualitycheck abgeschlossen → final_news_checked.json, quality_report.json")
    return finale_stories, report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python qualitycheck.py input_file.json")
        sys.exit(1)
    qualitycheck(sys.argv[1])
