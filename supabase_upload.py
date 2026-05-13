"""
supabase_upload.py
------------------
Letzter Pipeline-Schritt: Laedt Stories aus einer JSON-Datei in Supabase hoch.

Ausfuehren:
    python supabase_upload.py final_news_social.json
    python supabase_upload.py final_news_social.json --dry-run
"""

import argparse
import hashlib
import json
import logging
import os
import sys

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("supabase_upload")

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

BATCH_SIZE = 20

TABELLEN_FELDER = [
    "story_id",
    "headline",
    "summary",
    "category",
    "source",
    "political_leaning",
    "source_count",
    "source_articles",
    "links",
    "link",
    "relevance_score",
    "is_top_story",
    "is_breaking",
    "quality_status",
    "quality_notes",
    "merged_from",
    "blindspot_label",
    "blindspot_score",
    "spectrum_count",
    "silent_spectrums",
    "spectrum_distribution",
    "social_post_worthy",
    "social_post_score",
    "suggested_social_format",
    "social_angle",
    "social_reason",
    "social_risk",
    "social_status",
    "timestamp",
    "cluster_id",
    "cluster_size",
    "cluster_article_count",
    "image_url",
]

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _story_id_erzeugen(story: dict) -> str:
    headline = story.get("headline", "")
    timestamp = story.get("timestamp", "")
    rohtext = f"{headline}|{timestamp}"
    return hashlib.sha256(rohtext.encode("utf-8")).hexdigest()


def _story_mappen(story: dict) -> dict:
    if not story.get("story_id"):
        story["story_id"] = _story_id_erzeugen(story)

    return {feld: story.get(feld, None) for feld in TABELLEN_FELDER}


def _stories_laden(pfad: str) -> list[dict]:
    with open(pfad, "r", encoding="utf-8") as f:
        daten = json.load(f)

    if isinstance(daten, list):
        return daten

    if isinstance(daten, dict):
        for key in ("stories", "articles", "news", "items"):
            if key in daten and isinstance(daten[key], list):
                return daten[key]

    raise ValueError(
        f"Unbekanntes JSON-Format in '{pfad}'. "
        "Erwartet: Liste oder Dict mit Key 'stories', 'articles', 'news' oder 'items'."
    )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def _batch_hochladen(client, batch: list[dict]) -> tuple[int, int]:
    """Versucht einen Batch hochzuladen. Bei Fehler: einzeln retry."""
    try:
        client.table("stories").upsert(batch, on_conflict="story_id").execute()
        return len(batch), 0
    except Exception as e:
        log.warning(f"Batch-Upload fehlgeschlagen ({len(batch)} Stories) — retry einzeln: {e}")

    erfolge = 0
    fehler = 0
    for row in batch:
        try:
            client.table("stories").upsert([row], on_conflict="story_id").execute()
            erfolge += 1
        except Exception as e2:
            log.error(f"Story fehlgeschlagen [{row.get('story_id', '?')}]: {e2}")
            fehler += 1

    return erfolge, fehler


def hochladen(client, stories: list[dict], dry_run: bool = False) -> None:
    gesamt = len(stories)
    log.info(f"{gesamt} Stories geladen.")

    if dry_run:
        log.info(f"[DRY-RUN] Wuerden {gesamt} Stories in {-(-gesamt // BATCH_SIZE)} Batches hochgeladen.")
        return

    log.info(
        f"Starte Upload in Batches von {BATCH_SIZE} "
        f"({-(-gesamt // BATCH_SIZE)} Batches gesamt) ..."
    )

    gesamt_erfolg = 0
    gesamt_fehler = 0

    for i in range(0, gesamt, BATCH_SIZE):
        batch_roh = stories[i: i + BATCH_SIZE]
        batch = [_story_mappen(s) for s in batch_roh]
        batch_nr = i // BATCH_SIZE + 1

        erfolg, fehler = _batch_hochladen(client, batch)
        gesamt_erfolg += erfolg
        gesamt_fehler += fehler

        log.info(
            f"Batch {batch_nr}: {erfolg} OK, {fehler} Fehler "
            f"[{min(i + BATCH_SIZE, gesamt)}/{gesamt}]"
        )

    log.info("=" * 50)
    log.info(f"Upload abgeschlossen.")
    log.info(f"  Gesamt:       {gesamt}")
    log.info(f"  Erfolgreich:  {gesamt_erfolg}")
    log.info(f"  Fehlgeschlagen: {gesamt_fehler}")
    log.info("=" * 50)


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Stories in Supabase hochladen.")
    parser.add_argument("input", help="Pfad zur JSON-Datei (z.B. final_news_social.json)")
    parser.add_argument("--dry-run", action="store_true", help="Nur zaehlen, nicht hochladen.")
    args = parser.parse_args()

    log.info(f"Input: {args.input}")
    if args.dry_run:
        log.info("[DRY-RUN] Kein echter Upload.")

    # .env laden
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        if not supabase_url:
            log.error("SUPABASE_URL ist nicht gesetzt.")
        if not supabase_key:
            log.error("SUPABASE_KEY ist nicht gesetzt.")
        sys.exit(1)

    # Hinweis: UNIQUE INDEX
    print(
        "\nHinweis: Fuer den Upsert wird folgender UNIQUE INDEX benoetigt.\n"
        "Falls noch nicht vorhanden, im Supabase SQL Editor ausfuehren:\n\n"
        "  CREATE UNIQUE INDEX IF NOT EXISTS idx_stories_story_id ON stories (story_id);\n"
    )

    # Stories laden
    try:
        stories = _stories_laden(args.input)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        log.error(f"Fehler beim Laden der Input-Datei: {e}")
        sys.exit(1)

    # Supabase-Client
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        log.info("Supabase-Verbindung hergestellt.")
    except Exception as e:
        log.error(f"Supabase-Verbindung fehlgeschlagen: {e}")
        sys.exit(1)

    hochladen(client, stories, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
