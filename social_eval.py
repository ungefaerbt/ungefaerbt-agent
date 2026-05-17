import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("social_eval")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.propagate = False

# ---------------------------------------------------------------------------
# Kontrast-Check Konfiguration
# ---------------------------------------------------------------------------

ENABLE_CONTRAST_CHECK = True
CONTRAST_BONUS_HIGH = 20
CONTRAST_BONUS_LOW = 10
CONTRAST_THRESHOLD_HIGH = 70
CONTRAST_THRESHOLD_LOW = 50
CONTRAST_MODEL = os.getenv("CONTRAST_MODEL", "claude-sonnet-4-6")

# FIX: Scoring-Schwellen angepasst an realistisch erreichbare Scores
# Vorher: social_post_worthy = score >= 70 → nie erreichbar (max ~60 ohne breaking)
# Jetzt:  candidate >= 55, needs_review >= 42
SOCIAL_THRESHOLD_CANDIDATE    = 55   # vorher implizit 70
SOCIAL_THRESHOLD_NEEDS_REVIEW = 42   # vorher implizit 60

CONTRAST_SYSTEM_PROMPT = """\
Du analysierst Nachrichtenheadlines verschiedener Medien zur selben Geschichte.
Bewerte ob die Headlines semantisch unterschiedlich framen — also ob sie unterschiedliche \
Schwerpunkte setzen, unterschiedliche Begriffe verwenden oder das Ereignis unterschiedlich darstellen.

Antworte AUSSCHLIESSLICH mit einem JSON-Objekt. Kein erklärender Text, keine Markdown-Backticks, kein Preamble.
Wenn kein Kontrast erkennbar ist, antworte mit einem leeren contrast_pairs Array.\
"""


# ---------------------------------------------------------------------------
# Kontrast-Check Hilfsfunktionen
# ---------------------------------------------------------------------------

def _kontrast_fallback():
    return {
        "has_contrast": False,
        "contrast_score": 0,
        "contrast_type": "no_contrast",
        "contrast_pairs": [],
        "recommended_social_format": "keep_existing_format",
    }


def _parse_contrast_json(text):
    # FIX: robusteres Parsing — mehrere Backtick-Formate abfangen
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        # nimm den ersten nicht-leeren Block nach einem Backtick
        for part in parts[1:]:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned:
                text = cleaned
                break
    return json.loads(text)


def kontrast_bonus_berechnen(contrast_score):
    if contrast_score >= CONTRAST_THRESHOLD_HIGH:
        return CONTRAST_BONUS_HIGH
    if contrast_score >= CONTRAST_THRESHOLD_LOW:
        return CONTRAST_BONUS_LOW
    return 0


def kontrast_check_ausfuehren(client, story):
    source_articles = story.get("source_articles")
    if not source_articles or len(source_articles) < 2:
        return _kontrast_fallback()

    artikel_input = [
        {
            "source": a.get("source", ""),
            "political_leaning": a.get("political_leaning", ""),
            "headline": a.get("headline", ""),
            "link": a.get("link", ""),
        }
        for a in source_articles
    ]

    payload = {
        "story_id": story.get("story_id", ""),
        "headline": story.get("headline", ""),
        "summary": story.get("summary", ""),
        "category": story.get("category", ""),
        "source_articles": artikel_input,
    }

    try:
        antwort = client.messages.create(
            model=CONTRAST_MODEL,
            max_tokens=1000,
            system=CONTRAST_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        raw_text = antwort.content[0].text
        ergebnis = _parse_contrast_json(raw_text)
        return {
            "has_contrast": bool(ergebnis.get("has_contrast", False)),
            "contrast_score": int(ergebnis.get("contrast_score", 0)),
            "contrast_type": ergebnis.get("contrast_type", "no_contrast"),
            "contrast_pairs": ergebnis.get("contrast_pairs", []),
            "recommended_social_format": ergebnis.get("recommended_social_format", "keep_existing_format"),
        }
    except json.JSONDecodeError as e:
        logger.warning(
            "Kontrast-Check JSON-Parse-Fehler für '%s': %s | Raw: %s",
            story.get("headline", "?")[:60], e,
            antwort.content[0].text[:200] if antwort and antwort.content else "no response",
        )
        return _kontrast_fallback()
    except Exception as e:
        logger.warning(
            "Kontrast-Check fehlgeschlagen für '%s': %s",
            story.get("headline", "?")[:60], e,
        )
        return _kontrast_fallback()


# ---------------------------------------------------------------------------
# Story-Laden
# ---------------------------------------------------------------------------

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


def source_count_bestimmen(story):
    sc = story.get("source_count")
    if sc is not None and sc != "":
        return int(sc)
    sources = story.get("sources")
    if isinstance(sources, list) and sources:
        return len(sources)
    source = story.get("source", "")
    if isinstance(source, str) and source.strip():
        return len([x for x in source.split(",") if x.strip()])
    cluster_size = story.get("cluster_size")
    if cluster_size:
        return int(cluster_size)
    # FIX: source_articles als letzter Fallback
    sa = story.get("source_articles")
    if isinstance(sa, list):
        return len(sa)
    return 1


def score_berechnen(story, source_count):
    score = 0
    relevance = story.get("relevance_score", 0)
    cluster_size = story.get("cluster_size", 1)
    spectrum_count = story.get("spectrum_count", 0)
    blindspot_score = story.get("blindspot_score", 100)
    blindspot_label = story.get("blindspot_label", "")
    quality_status = story.get("quality_status", "needs_review")
    headline = story.get("headline", "")
    summary = story.get("summary", "")

    # 1. Relevanz — FIX: Schwellen angepasst, mehr Punkte für mittlere Relevanz
    if relevance >= 90:
        score += 30
    elif relevance >= 80:
        score += 25
    elif relevance >= 70:
        score += 20   # vorher 16
    elif relevance >= 60:
        score += 14   # vorher 8
    elif relevance >= 50:
        score += 8    # neu: auch 50-60 kriegt Punkte

    # 2. Top Story
    if story.get("is_top_story"):
        score += 15

    # 3. Breaking
    if story.get("is_breaking"):
        score += 10

    # 4. Quellen / Cluster
    if source_count >= 5 or cluster_size >= 5:
        score += 12   # vorher 10
    elif source_count >= 3 or cluster_size >= 3:
        score += 9    # vorher 7
    elif source_count >= 2 or cluster_size >= 2:
        score += 5    # vorher 4

    # 5. Barometer-Interesse — FIX: niedrigere Schwellen, mehr Punkte
    if blindspot_score >= 80:
        score += 16   # vorher 18
    elif blindspot_score >= 60:
        score += 12   # vorher 14
    elif blindspot_score >= 40:
        score += 8    # unverändert
    elif blindspot_score >= 20:
        score += 4    # neu: auch moderate Blindspot-Scores belohnen

    # 6. Spektren-Verteilung
    if spectrum_count >= 5:
        score += 15
    elif spectrum_count == 4:
        score += 12
    elif spectrum_count == 3:
        score += 9    # vorher 8
    elif spectrum_count == 2:
        score += 6
    elif spectrum_count == 1 and source_count > 1:
        score += 12   # vorher 14 — leicht reduziert

    # 7. Abzüge
    if blindspot_label == "Einzelmeldung":
        score -= 20
    if blindspot_label == "Unklar":
        score -= 15
    if quality_status != "ready":
        score -= 25
    if not headline or not summary:
        score -= 30

    return max(0, min(100, score))


def social_risk_bestimmen(story, source_count):
    quality_status = story.get("quality_status", "needs_review")
    blindspot_label = story.get("blindspot_label", "")
    cluster_size = story.get("cluster_size", 1)
    blindspot_score = story.get("blindspot_score", 100)
    spectrum_count = story.get("spectrum_count", 0)

    # 1. High
    if (quality_status != "ready"
            or blindspot_label == "Unklar"
            or source_count <= 1
            or cluster_size <= 1):
        return "high"

    # 2. Medium
    if (blindspot_score >= 80
            or spectrum_count <= 1
            or story.get("is_breaking")):
        return "medium"

    return "low"


def suggested_format_bestimmen(story, source_count, social_post_worthy, social_status,
                                recommended_social_format=None):
    blindspot_label = story.get("blindspot_label", "")
    blindspot_score = story.get("blindspot_score", 0)
    spectrum_count = story.get("spectrum_count", 0)
    relevance_score = story.get("relevance_score", 0)

    # 1. Nicht empfohlen
    if not social_post_worthy and social_status == "not_recommended":
        return "no_post"

    # FIX: Kontrast-Format von Claude berücksichtigen
    # Vorher: recommended_social_format wurde komplett ignoriert
    if recommended_social_format and recommended_social_format not in (
        "keep_existing_format", "no_post", ""
    ):
        # Kontrast-Format hat Vorrang wenn Story worthy ist
        if social_post_worthy:
            return recommended_social_format

    # 2. Breaking
    if story.get("is_breaking") and source_count >= 2:
        return "breaking_post"

    # 3. Blindspot-Carousel
    if blindspot_label == "Einseitig berichtet" or blindspot_score >= 60:
        return "blindspot_carousel"

    # 4. Breite Abdeckung
    if spectrum_count >= 4:
        return "broad_coverage_carousel"

    # 5. Bias-Barometer-Carousel
    if spectrum_count >= 3 and source_count >= 3:
        return "bias_barometer_carousel"

    # 6. Explainer
    if relevance_score >= 70:   # vorher 80 — etwas gesenkt
        return "explainer_carousel"

    return "no_post"


def social_angle_bestimmen(story, social_post_worthy, social_status, source_count):
    blindspot_score = story.get("blindspot_score", 0)
    spectrum_count = story.get("spectrum_count", 0)
    silent = story.get("silent_spectrums", [])
    relevance_score = story.get("relevance_score", 0)

    if not social_post_worthy and social_status == "not_recommended":
        return "Nicht empfohlen: zu wenige Quellen oder unsichere Qualität."
    if story.get("is_breaking") and source_count >= 2:
        return "Breaking-Thema mit mehreren Quellen."
    if silent and blindspot_score >= 60:
        return "Auffällige Verteilung: Mehrere Spektren fehlen in der Berichterstattung."
    if spectrum_count >= 4:
        return "Breit berichtete Story mit mehreren politischen Spektren."
    if relevance_score >= 70:
        return "Hohe Relevanz und mehrere Quellen machen die Story erklärenswert."
    if spectrum_count >= 3:
        return "Mehrere politische Perspektiven vertreten."
    return "Nicht empfohlen: zu wenige Quellen oder unsichere Qualität."


def social_reason_bestimmen(story, social_post_worthy, social_status, source_count):
    blindspot_score = story.get("blindspot_score", 0)
    spectrum_count = story.get("spectrum_count", 0)
    blindspot_label = story.get("blindspot_label", "")
    relevance_score = story.get("relevance_score", 0)

    if not social_post_worthy and social_status == "not_recommended":
        return "Nicht empfohlen wegen Einzelmeldung oder fehlender Qualität."
    if blindspot_score >= 60 and story.get("silent_spectrums"):
        return "Hoher Blindspot-Score und fehlende Spektren machen die Story interessant."
    if spectrum_count >= 4:
        return "Breite Berichterstattung über mehrere Spektren."
    if relevance_score >= 70 and source_count >= 3:
        return "Hohe Relevanz, mehrere Quellen und klares Bias-Barometer."
    if spectrum_count >= 3:
        return "Mehrere Spektren und ausreichende Quellenbreite."
    return "Nicht empfohlen wegen Einzelmeldung oder fehlender Qualität."


def story_evaluieren(story, contrast_score=0, recommended_social_format=None):
    source_count = source_count_bestimmen(story)
    if story.get("source_count") is None:
        story["source_count"] = source_count

    social_post_score = score_berechnen(story, source_count)
    social_risk = social_risk_bestimmen(story, source_count)
    quality_status = story.get("quality_status", "needs_review")

    bonus = kontrast_bonus_berechnen(contrast_score)
    social_priority_score = min(100, max(0, social_post_score + bonus))

    # FIX: Schwelle von 70 auf SOCIAL_THRESHOLD_CANDIDATE (55) gesenkt
    social_post_worthy = (
        social_priority_score >= SOCIAL_THRESHOLD_CANDIDATE
        and quality_status == "ready"
        and social_risk != "high"
    )

    if social_post_worthy:
        social_status = "candidate"
    elif social_priority_score >= SOCIAL_THRESHOLD_NEEDS_REVIEW:
        social_status = "needs_review"
    else:
        social_status = "not_recommended"

    suggested_format = suggested_format_bestimmen(
        story, source_count, social_post_worthy, social_status,
        recommended_social_format=recommended_social_format,  # FIX: jetzt übergeben
    )
    social_angle = social_angle_bestimmen(
        story, social_post_worthy, social_status, source_count
    )
    social_reason = social_reason_bestimmen(
        story, social_post_worthy, social_status, source_count
    )

    story["social_post_worthy"]      = social_post_worthy
    story["social_post_score"]       = social_post_score
    story["social_priority_score"]   = social_priority_score
    story["suggested_social_format"] = suggested_format
    story["social_angle"]            = social_angle
    story["social_reason"]           = social_reason
    story["social_risk"]             = social_risk
    story["social_status"]           = social_status

    return story


def social_eval(input_pfad):
    logger.info("social_eval gestartet: %s", input_pfad)

    stories = stories_laden(input_pfad)
    logger.info("%s Stories geladen.", len(stories))

    # ---------------------------------------------------------------------------
    # Kontrast-Check vorbereiten
    # ---------------------------------------------------------------------------
    contrast_client = None
    contrast_check_ran = False
    contrast_skipped_reason = None

    if ENABLE_CONTRAST_CHECK:
        logger.info("Kontrast-Check aktiviert (Modell: %s).", CONTRAST_MODEL)
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            contrast_skipped_reason = "ANTHROPIC_API_KEY nicht gesetzt"
            logger.warning("Kontrast-Check übersprungen: %s", contrast_skipped_reason)
        else:
            try:
                import anthropic
                contrast_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                contrast_skipped_reason = "anthropic-Paket nicht installiert"
                logger.warning("Kontrast-Check übersprungen: %s", contrast_skipped_reason)
    else:
        contrast_skipped_reason = "ENABLE_CONTRAST_CHECK == False"
        logger.info("Kontrast-Check deaktiviert.")

    # ---------------------------------------------------------------------------
    # Kontrast-Checks ausführen
    # ---------------------------------------------------------------------------
    contrast_results = {}
    stories_geprueft = 0

    if contrast_client is not None:
        for i, story in enumerate(stories):
            source_articles = story.get("source_articles")
            if isinstance(source_articles, list) and len(source_articles) >= 2:
                contrast_results[i] = kontrast_check_ausfuehren(contrast_client, story)
                stories_geprueft += 1
            else:
                contrast_results[i] = _kontrast_fallback()
        contrast_check_ran = True
        logger.info("Kontrast-Check: %s/%s Stories geprüft.", stories_geprueft, len(stories))
    else:
        for i in range(len(stories)):
            contrast_results[i] = _kontrast_fallback()

    # ---------------------------------------------------------------------------
    # Stories evaluieren
    # ---------------------------------------------------------------------------
    format_counts = {}
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    candidate_count = 0
    needs_review_count = 0
    not_recommended_count = 0
    score_summe = 0
    top_candidates = []
    errors = []
    stories_with_contrast = 0
    contrast_score_summe = 0
    worthy_durch_bonus = 0

    for i, story in enumerate(stories):
        try:
            kontrast = contrast_results[i]
            contrast_score = kontrast["contrast_score"]

            # Kontrast-Felder in Story schreiben
            story["has_contrast"]              = kontrast["has_contrast"]
            story["contrast_score"]            = contrast_score
            story["contrast_type"]             = kontrast["contrast_type"]
            story["contrast_pairs"]            = kontrast["contrast_pairs"]
            story["recommended_social_format"] = kontrast["recommended_social_format"]

            if kontrast["has_contrast"]:
                stories_with_contrast += 1
            contrast_score_summe += contrast_score

            # Score ohne Bonus — um "worthy durch Bonus" zu erkennen
            score_ohne_bonus = score_berechnen(story, source_count_bestimmen(story))

            # FIX: recommended_social_format jetzt an story_evaluieren weitergeben
            story_evaluieren(
                story,
                contrast_score=contrast_score,
                recommended_social_format=kontrast["recommended_social_format"],
            )

            if (story["social_post_worthy"]
                    and kontrast_bonus_berechnen(contrast_score) > 0
                    and score_ohne_bonus < SOCIAL_THRESHOLD_CANDIDATE):
                worthy_durch_bonus += 1

            status = story["social_status"]
            fmt = story["suggested_social_format"]
            risk = story["social_risk"]

            format_counts[fmt] = format_counts.get(fmt, 0) + 1
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            score_summe += story["social_post_score"]

            if status == "candidate":
                candidate_count += 1
            elif status == "needs_review":
                needs_review_count += 1
            else:
                not_recommended_count += 1

            if story.get("social_post_worthy"):
                top_candidates.append({
                    "headline":                story.get("headline", ""),
                    "social_post_score":       story["social_post_score"],
                    "social_priority_score":   story["social_priority_score"],
                    "suggested_social_format": story["suggested_social_format"],
                    "social_reason":           story["social_reason"],
                })
        except Exception as e:
            headline = story.get("headline", "–")[:60]
            errors.append(f"Fehler bei '{headline}': {e}")
            logger.error("Fehler bei Story '%s': %s", headline, e)

    social_post_worthy_count = candidate_count
    avg_score = round(score_summe / len(stories), 1) if stories else 0.0
    avg_contrast = round(contrast_score_summe / len(stories), 1) if stories else 0.0
    top_candidates.sort(key=lambda x: x["social_priority_score"], reverse=True)

    logger.info(
        "%s/%s Stories als social_post_worthy markiert (Schwelle: %s).",
        social_post_worthy_count, len(stories), SOCIAL_THRESHOLD_CANDIDATE,
    )
    if contrast_check_ran:
        logger.info(
            "%s/%s Stories mit has_contrast == true.",
            stories_with_contrast, stories_geprueft,
        )
        logger.info(
            "%s neue social_post_worthy durch Kontrast-Bonus.",
            worthy_durch_bonus,
        )

    # ---------------------------------------------------------------------------
    # final_news_social.json
    # ---------------------------------------------------------------------------
    with open(OUTPUT_DIR / "final_news_social.json", "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------------------------
    # final_social_candidates.json
    # ---------------------------------------------------------------------------
    candidates = [
        s for s in stories
        if s.get("social_post_worthy") or s.get("social_status") == "candidate"
    ]
    candidates.sort(key=lambda x: x.get("social_priority_score", 0), reverse=True)

    with open(OUTPUT_DIR / "final_social_candidates.json", "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    logger.info("%s Stories in final_social_candidates.json.", len(candidates))

    # ---------------------------------------------------------------------------
    # social_eval_report.json
    # ---------------------------------------------------------------------------
    report = {
        "timestamp":                     datetime.now().isoformat(),
        "input_file":                    input_pfad,
        "stories_total":                 len(stories),
        "social_post_worthy_count":      social_post_worthy_count,
        "candidate_count":               candidate_count,
        "needs_review_count":            needs_review_count,
        "not_recommended_count":         not_recommended_count,
        "average_social_post_score":     avg_score,
        "format_counts":                 format_counts,
        "risk_counts":                   risk_counts,
        "top_candidates":                top_candidates,
        "contrast_check_enabled":        ENABLE_CONTRAST_CHECK,
        "contrast_check_ran":            contrast_check_ran,
        "stories_with_contrast":         stories_with_contrast,
        "average_contrast_score":        avg_contrast,
        "social_threshold_candidate":    SOCIAL_THRESHOLD_CANDIDATE,
        "social_threshold_needs_review": SOCIAL_THRESHOLD_NEEDS_REVIEW,
        "contrast_check_skipped_reason": contrast_skipped_reason,
        "warnings":                      [],
        "errors":                        errors,
    }

    with open(OUTPUT_DIR / "social_eval_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(
        "social_eval abgeschlossen → final_news_social.json, "
        "final_social_candidates.json, social_eval_report.json"
    )
    return stories, report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python social_eval.py input.json")
        sys.exit(1)
    social_eval(sys.argv[1])
