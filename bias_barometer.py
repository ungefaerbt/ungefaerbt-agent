import json
import logging
import sys
from datetime import datetime

logger = logging.getLogger("bias_barometer")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.propagate = False

ALLE_SPEKTREN = ["Links", "Mitte-Links", "Mitte", "Mitte-Rechts", "Rechts"]


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


def normalisiere_liste(wert):
    """Wandelt kommaseparierten String oder Liste in bereinigte Liste um."""
    if isinstance(wert, list):
        return [x.strip() for x in wert if str(x).strip()]
    if isinstance(wert, str):
        return [x.strip() for x in wert.split(",") if x.strip()]
    return []


def spektren_normalisieren(story):
    """Gibt bereinigte Liste gültiger Spektren zurück (Duplikate erhalten)."""
    roh = normalisiere_liste(story.get("political_leaning", ""))
    return [s for s in roh if s in ALLE_SPEKTREN]


def quellen_normalisieren(story):
    """Gibt bereinigte Quellenliste zurück."""
    if story.get("sources"):
        return normalisiere_liste(story["sources"])
    return normalisiere_liste(story.get("source", ""))


def barometer_berechnen(story):
    spektren = spektren_normalisieren(story)
    quellen  = quellen_normalisieren(story)

    source_count = len(quellen)
    cluster_size = story.get("cluster_size", 1)

    # Fallback: keine gültigen Spektren
    if not spektren:
        notizen = list(story.get("quality_notes", []))
        if "missing_valid_political_leaning" not in notizen:
            notizen.append("missing_valid_political_leaning")
        story["quality_notes"]        = notizen
        story["source_count"]         = source_count
        story["spectrum_distribution"] = {s: 0 for s in ALLE_SPEKTREN}
        story["spectrum_count"]       = 0
        story["silent_spectrums"]     = list(ALLE_SPEKTREN)
        story["blindspot_score"]      = 100
        story["blindspot_label"]      = "Unklar"
        return story

    # spectrum_distribution (Duplikate zählen)
    distribution = {s: 0 for s in ALLE_SPEKTREN}
    for s in spektren:
        distribution[s] += 1

    unique_spektren   = [s for s in ALLE_SPEKTREN if distribution[s] > 0]
    spectrum_count    = len(unique_spektren)
    silent_spectrums  = [s for s in ALLE_SPEKTREN if distribution[s] == 0]

    # Einzelmeldung
    ist_einzelmeldung = cluster_size <= 1 or source_count <= 1

    if ist_einzelmeldung:
        blindspot_score = 100
        blindspot_label = "Einzelmeldung"
    else:
        blindspot_score = round((len(silent_spectrums) / len(ALLE_SPEKTREN)) * 100)
        if spectrum_count == 1:
            blindspot_label = "Einseitig berichtet"
        elif spectrum_count == 2:
            blindspot_label = "Schmal berichtet"
        elif spectrum_count == 3:
            blindspot_label = "Mehrere Perspektiven"
        elif spectrum_count == 4:
            blindspot_label = "Breit berichtet"
        else:
            blindspot_label = "Sehr breit berichtet"

    story["source_count"]          = source_count
    story["spectrum_distribution"] = distribution
    story["spectrum_count"]        = spectrum_count
    story["silent_spectrums"]      = silent_spectrums
    story["blindspot_score"]       = blindspot_score
    story["blindspot_label"]       = blindspot_label

    return story


def bias_barometer(input_pfad):
    logger.info("bias_barometer gestartet: %s", input_pfad)

    stories = stories_laden(input_pfad)
    logger.info("%s Stories geladen.", len(stories))

    label_counts = {}
    unclear_count = 0
    warnings = []
    errors = []
    verarbeitet = 0

    for story in stories:
        try:
            barometer_berechnen(story)
            label = story.get("blindspot_label", "Unklar")
            label_counts[label] = label_counts.get(label, 0) + 1
            if label == "Unklar":
                unclear_count += 1
            verarbeitet += 1
        except Exception as e:
            headline = story.get("headline", "–")[:60]
            errors.append(f"Fehler bei '{headline}': {e}")

    logger.info("%s/%s Stories verarbeitet.", verarbeitet, len(stories))

    with open("final_news_with_barometer.json", "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)

    report = {
        "timestamp":        datetime.now().isoformat(),
        "input_file":       input_pfad,
        "stories_total":    len(stories),
        "stories_processed": verarbeitet,
        "label_counts":     label_counts,
        "unclear_count":    unclear_count,
        "warnings":         warnings,
        "errors":           errors,
    }

    with open("bias_barometer_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(
        "bias_barometer abgeschlossen → final_news_with_barometer.json, bias_barometer_report.json"
    )
    return stories, report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python bias_barometer.py input.json")
        sys.exit(1)
    bias_barometer(sys.argv[1])
