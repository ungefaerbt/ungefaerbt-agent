"""
supabase_setup.py
-----------------
Einmaliges Setup-Tool fuer die Supabase-Datenbank.

Gibt den SQL-Befehl fuer die "stories"-Tabelle aus und
testet optional die Verbindung zu Supabase.

Ausfuehren:
    python supabase_setup.py
"""

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
log = logging.getLogger("supabase_setup")

# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS stories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    story_id text,
    headline text,
    summary text,
    category text,

    source text,
    political_leaning text,
    source_count integer,
    source_articles jsonb,
    links jsonb,
    link text,

    relevance_score integer,
    is_top_story boolean,
    is_breaking boolean,

    quality_status text,
    quality_notes jsonb,
    merged_from jsonb,

    blindspot_label text,
    blindspot_score integer,
    spectrum_count integer,
    silent_spectrums jsonb,
    spectrum_distribution jsonb,

    social_post_worthy boolean,
    social_post_score integer,
    suggested_social_format text,
    social_angle text,
    social_reason text,
    social_risk text,
    social_status text,

    timestamp timestamptz,
    cluster_id integer,
    cluster_size integer,
    cluster_article_count integer,

    image_url text,

    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stories_timestamp ON stories (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stories_category ON stories (category);
CREATE INDEX IF NOT EXISTS idx_stories_relevance_score ON stories (relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_stories_social_post_worthy ON stories (social_post_worthy);
CREATE INDEX IF NOT EXISTS idx_stories_blindspot_label ON stories (blindspot_label);
CREATE INDEX IF NOT EXISTS idx_stories_quality_status ON stories (quality_status);
""".strip()

# ---------------------------------------------------------------------------
# Umgebungsvariablen laden
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    log.warning("python-dotenv nicht installiert – .env wird nicht geladen.")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ---------------------------------------------------------------------------
# SQL ausgeben
# ---------------------------------------------------------------------------

print("\n" + "=" * 70)
print("SUPABASE SQL – in den SQL-Editor einfuegen und auf Run klicken:")
print("=" * 70)
print(CREATE_SQL)
print("=" * 70 + "\n")

log.info("Anleitung:")
log.info("  1. Oeffne dein Supabase Dashboard")
log.info("  2. Navigiere zu: SQL Editor")
log.info("  3. Fuege den SQL-Code oben ein")
log.info("  4. Klicke auf 'Run'")
log.info("")
log.info("Das Script fuehrt keinen SQL selbst aus – du hast die volle Kontrolle.")

# ---------------------------------------------------------------------------
# Verbindungstest
# ---------------------------------------------------------------------------

if not SUPABASE_URL or not SUPABASE_KEY:
    log.error("Umgebungsvariablen fehlen:")
    if not SUPABASE_URL:
        log.error("  SUPABASE_URL ist nicht gesetzt")
    if not SUPABASE_KEY:
        log.error("  SUPABASE_KEY ist nicht gesetzt")
    log.error("Lege eine .env-Datei an oder setze die Variablen in deiner Shell.")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    log.warning("supabase-Paket nicht installiert – Verbindungstest uebersprungen.")
    log.warning("Installieren mit:  pip install supabase")
    sys.exit(0)

log.info("Verbinde mit Supabase ...")
try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    log.info("Client erstellt.")
except Exception as e:
    log.error(f"Verbindung fehlgeschlagen: {e}")
    sys.exit(1)

log.info("Teste Lesezugriff auf Tabelle 'stories' ...")
try:
    client.table("stories").select("id").limit(1).execute()
    log.info("Verbindung OK – Tabelle 'stories' ist erreichbar.")
except Exception as e:
    fehlermeldung = str(e)
    fehler_code = e.get("code") if isinstance(e, dict) else ""
    fehler_str = str(e)

    if "does not exist" in fehler_str or "relation" in fehler_str:
        log.warning(
            "Tabelle 'stories' existiert noch nicht. "
            "Fuehre zuerst den SQL-Code oben im Supabase SQL-Editor aus."
        )
    elif "42501" in fehler_str or "permission denied" in fehler_str:
        log.warning(
            "Tabelle 'stories' existiert, aber der verwendete Key hat keinen Lesezugriff. "
            "Nutze den service_role Key (nicht den anon Key) fuer dieses Setup-Script."
        )
    else:
        log.error(f"Unerwarteter Fehler beim Verbindungstest: {e}")
        sys.exit(1)
