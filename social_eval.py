import json
import logging
import sys
from datetime import datetime

logger = logging.getLogger("social_eval")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.propagate = False


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

    # 1. Relevanz
    if relevance >= 90:
        score += 30
    elif relevance >= 80:
        score += 24
    elif relevance >= 70:
        score += 16
    elif relevance >= 60:
        score += 8

    # 2. Top Story
    if story.get("is_top_story"):
        score += 15

    # 3. Breaking
    if story.get("is_breaking"):
        score += 10

    # 4. Quellen / Cluster
    if source_count >= 5 or cluster_size >= 5:
        score += 10
    elif source_count >= 3 or cluster_size >= 3:
        score += 7
    elif source_count >= 2 or cluster_size >= 2:
        score += 4

    # 5. Barometer-Interesse
    if blindspot_score >= 80:
        score += 18
    elif blindspot_score >= 60:
        score += 14
    elif blindspot_score >= 40:
        score += 8

    # 6. Spektren-Verteilung
    if spectrum_count >= 5:
        score += 15
    elif spectrum_count == 4:
        score += 12
    elif spectrum_count == 3:
        score += 8
    elif spectrum_count == 2:
        score += 6
    elif spectrum_count == 1 and source_count > 1:
        score += 14

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


def suggested_format_bestimmen(story, source_count, social_post_worthy, social_status):
    blindspot_label = story.get("blindspot_label", "")
    blindspot_score = story.get("blindspot_score", 0)
    spectrum_count = story.get("spectrum_count", 0)
    relevance_score = story.get("relevance_score", 0)

    # 1. Nicht empfohlen und kein needs_review
    if not social_post_worthy and social_status != "needs_review":
        return "no_post"

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
    if relevance_score >= 80:
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
    if relevance_score >= 80:
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
    if relevance_score >= 80 and source_count >= 3:
        return "Hohe Relevanz, mehrere Quellen und klares Bias-Barometer."
    if spectrum_count >= 3:
        return "Mehrere Spektren und ausreichende Quellenbreite."
    return "Nicht empfohlen wegen Einzelmeldung oder fehlender Qualität."


def story_evaluieren(story):
    source_count = source_count_bestimmen(story)
    if story.get("source_count") is None:
        story["source_count"] = source_count

    social_post_score = score_berechnen(story, source_count)
    social_risk = social_risk_bestimmen(story, source_count)
    quality_status = story.get("quality_status", "needs_review")

    social_post_worthy = (
        social_post_score >= 70
        and quality_status == "ready"
        and social_risk != "high"
    )

    if social_post_worthy:
        social_status = "candidate"
    elif social_post_score >= 60:
        social_status = "needs_review"
    else:
        social_status = "not_recommended"

    suggested_format = suggested_format_bestimmen(
        story, source_count, social_post_worthy, social_status
    )
    social_angle = social_angle_bestimmen(
        story, social_post_worthy, social_status, source_count
    )
    social_reason = social_reason_bestimmen(
        story, social_post_worthy, social_status, source_count
    )

    story["social_post_worthy"]      = social_post_worthy
    story["social_post_score"]       = social_post_score
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

    format_counts = {}
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    candidate_count = 0
    needs_review_count = 0
    not_recommended_count = 0
    score_summe = 0
    top_candidates = []
    errors = []

    for story in stories:
        try:
            story_evaluieren(story)
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
                    "headline":              story.get("headline", ""),
                    "social_post_score":     story["social_post_score"],
                    "suggested_social_format": story["suggested_social_format"],
                    "social_reason":         story["social_reason"],
                })
        except Exception as e:
            headline = story.get("headline", "–")[:60]
            errors.append(f"Fehler bei '{headline}': {e}")

    social_post_worthy_count = candidate_count
    avg_score = round(score_summe / len(stories), 1) if stories else 0.0
    top_candidates.sort(key=lambda x: x["social_post_score"], reverse=True)

    logger.info(
        "%s/%s Stories als social_post_worthy markiert.",
        social_post_worthy_count, len(stories),
    )

    with open("final_news_social.json", "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)

    report = {
        "timestamp":               datetime.now().isoformat(),
        "input_file":              input_pfad,
        "stories_total":           len(stories),
        "social_post_worthy_count": social_post_worthy_count,
        "candidate_count":         candidate_count,
        "needs_review_count":      needs_review_count,
        "not_recommended_count":   not_recommended_count,
        "average_social_post_score": avg_score,
        "format_counts":           format_counts,
        "risk_counts":             risk_counts,
        "top_candidates":          top_candidates,
        "warnings":                [],
        "errors":                  errors,
    }

    with open("social_eval_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("social_eval abgeschlossen → final_news_social.json, social_eval_report.json")
    return stories, report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python social_eval.py input.json")
        sys.exit(1)
    social_eval(sys.argv[1])
