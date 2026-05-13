import argparse
import glob
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)

logger.propagate = False

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def schritt_ausfuehren(name, args, dry_run=False):
    logger.info("Starte: %s", name)
    if dry_run:
        logger.info("[DRY-RUN] Würde ausführen: %s", " ".join(args))
        return
    start = time.monotonic()
    result = subprocess.run(args, cwd=PROJECT_DIR)
    dauer = time.monotonic() - start
    if result.returncode != 0:
        logger.error("Schritt fehlgeschlagen: %s (exit code %s)", name, result.returncode)
        sys.exit(1)
    logger.info("Fertig: %s (%.1fs)", name, dauer)


def neue_news_datei_finden(nach_zeitpunkt):
    muster = os.path.join(PROJECT_DIR, "news_*.json")
    kandidaten = [
        p for p in glob.glob(muster)
        if os.path.getmtime(p) >= nach_zeitpunkt
    ]
    if not kandidaten:
        return None
    return max(kandidaten, key=os.path.getmtime)


def zwischendatei_pruefen(pfad, schritt_name):
    if not os.path.isfile(pfad):
        logger.error("Zwischendatei fehlt nach Schritt '%s': %s", schritt_name, pfad)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ungefärbt Pipeline Runner")
    parser.add_argument("--dry-run", action="store_true", help="Zeigt Schritte ohne Ausführung")
    args = parser.parse_args()

    dry_run = args.dry_run
    pipeline_start = time.monotonic()
    news_such_zeitpunkt = time.time()

    logger.info("Pipeline gestartet%s", " [DRY-RUN]" if dry_run else "")

    # Schritt 1: main.py
    schritt_ausfuehren("main.py", [sys.executable, "main.py"], dry_run)

    # news_*.json mit Änderungszeit nach Startzeitpunkt finden
    if dry_run:
        news_datei = "news_DATUM.json (Platzhalter)"
    else:
        news_datei = neue_news_datei_finden(news_such_zeitpunkt)
        if not news_datei:
            logger.error(
                "Kein news_*.json mit Änderungszeit nach Pipelinestart gefunden. "
                "main.py hat möglicherweise keine Datei erzeugt."
            )
            sys.exit(1)
        logger.info("news-Datei gefunden: %s", os.path.basename(news_datei))

    # Schritt 2: qualitycheck.py
    schritt_ausfuehren(
        "qualitycheck.py",
        [sys.executable, "qualitycheck.py", news_datei if not dry_run else "news_DATUM.json"],
        dry_run,
    )
    if not dry_run:
        zwischendatei_pruefen(
            os.path.join(PROJECT_DIR, "final_news_checked.json"), "qualitycheck.py"
        )

    # Schritt 3: bias_barometer.py
    schritt_ausfuehren(
        "bias_barometer.py",
        [sys.executable, "bias_barometer.py", "final_news_checked.json"],
        dry_run,
    )
    if not dry_run:
        zwischendatei_pruefen(
            os.path.join(PROJECT_DIR, "final_news_with_barometer.json"), "bias_barometer.py"
        )

    # Schritt 4: social_eval.py
    schritt_ausfuehren(
        "social_eval.py",
        [sys.executable, "social_eval.py", "final_news_with_barometer.json"],
        dry_run,
    )
    if not dry_run:
        zwischendatei_pruefen(
            os.path.join(PROJECT_DIR, "final_news_social.json"), "social_eval.py"
        )

    # Schritt 5: supabase_upload.py
    schritt_ausfuehren(
        "supabase_upload.py",
        [sys.executable, "supabase_upload.py", "final_news_social.json"],
        dry_run,
    )
    if not dry_run:
        zwischendatei_pruefen(
            os.path.join(PROJECT_DIR, "final_news_social.json"), "supabase_upload.py"
        )

    gesamtdauer = time.monotonic() - pipeline_start
    logger.info(
        "Pipeline abgeschlossen%s — Gesamtdauer: %.0fm %.0fs",
        " [DRY-RUN]" if dry_run else "",
        gesamtdauer // 60,
        gesamtdauer % 60,
    )


if __name__ == "__main__":
    main()
