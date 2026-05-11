import json
import logging
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from config import (
    ALLE_AUSRICHTUNGEN,
    BREAKING_QUELLEN_SCHWELLE,
    BREAKING_SEEN_DATEI,
)
from cluster import _cluster_fingerprint, schlagzeilen_clustern
from fetcher import schlagzeilen_abrufen
from filter import ist_zu_vage
from writer import analyse_mit_claude

logger = logging.getLogger("news_agent")


def breaking_bilder_anreichern(input_datei):
    """Reichert eine Breaking-JSON mit dem separaten Image-Agent an."""
    image_agent = Path(__file__).resolve().parent / "image-agent" / "image_agent.py"
    if not image_agent.exists():
        print("  Warnung: image-agent/image_agent.py nicht gefunden. Bildanreicherung übersprungen.")
        logger.warning("Breaking-Bildanreicherung übersprungen: image_agent.py nicht gefunden.")
        return None

    input_path = Path(input_datei)
    output_path = input_path.with_name(f"{input_path.stem}_with_images{input_path.suffix}")
    befehl = [
        sys.executable,
        str(image_agent),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--sync-image-url",
    ]

    try:
        subprocess.run(befehl, check=True)
        print(f"  Breaking-Bilder gespeichert in: {output_path.name}")
        logger.info(f"BREAKING IMAGE AGENT: {input_path.name} -> {output_path.name}")
        return str(output_path)
    except Exception as e:
        print(f"  Warnung: Image-Agent konnte Breaking-Datei nicht anreichern: {e}")
        logger.warning(f"Breaking-Bildanreicherung fehlgeschlagen: {e}")
        return None


def breaking_seen_laden():
    """Lädt Fingerprints bekannter Breaking News (max. 24h alt)."""
    if not os.path.exists(BREAKING_SEEN_DATEI):
        return set()
    try:
        with open(BREAKING_SEEN_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
        grenze = time.time() - 86400
        return {fp for fp, ts in daten.items() if ts > grenze}
    except Exception:
        return set()


def breaking_seen_speichern(seen):
    """Speichert Fingerprints mit Zeitstempel, löscht Einträge älter als 24h."""
    try:
        vorherige = {}
        if os.path.exists(BREAKING_SEEN_DATEI):
            with open(BREAKING_SEEN_DATEI, "r", encoding="utf-8") as f:
                vorherige = json.load(f)
        jetzt = time.time()
        grenze = jetzt - 86400
        aktuell = {fp: ts for fp, ts in vorherige.items() if ts > grenze}
        for fp in seen:
            if fp not in aktuell:
                aktuell[fp] = jetzt
        with open(BREAKING_SEEN_DATEI, "w", encoding="utf-8") as f:
            json.dump(aktuell, f, ensure_ascii=True)
    except Exception as e:
        print(f"  Warnung: {BREAKING_SEEN_DATEI} konnte nicht gespeichert werden: {e}")


def breaking_news_check(client, on_complete=None):
    jetzt = datetime.now()
    print(f"\n[{jetzt.strftime('%H:%M')}] Breaking-News-Check ...", end="", flush=True)

    alle = schlagzeilen_abrufen(max_pro_quelle=5, gesamt_limit=None, verbose=False)
    artikel = [a for a in alle if not ist_zu_vage(a["headline"])]

    if not artikel:
        print(" Keine Artikel abrufbar.")
        logger.info("BREAKING CHECK: Keine Artikel abgerufen.")
        return

    schlagzeilen_clustern(artikel)

    cluster_quellen = defaultdict(set)
    cluster_artikel = defaultdict(list)
    for a in artikel:
        cid = a["cluster_id"]
        cluster_quellen[cid].add(a["source"])
        cluster_artikel[cid].append(a)

    kandidaten = [
        cid for cid, quellen in cluster_quellen.items()
        if len(quellen) >= BREAKING_QUELLEN_SCHWELLE
    ]

    if not kandidaten:
        print(f" Alles ruhig. ({len(artikel)} Artikel gecheckt)")
        logger.info(f"BREAKING CHECK: Keine Kandidaten. {len(artikel)} Artikel gecheckt.")
        return

    print(f"\n  {len(kandidaten)} Kandidat(en) mit {BREAKING_QUELLEN_SCHWELLE}+ Quellen gefunden!")

    seen = breaking_seen_laden()
    neu = []
    for cid in kandidaten:
        fingerprint = _cluster_fingerprint(cluster_artikel[cid])
        if fingerprint not in seen:
            neu.append((cid, fingerprint, cluster_artikel[cid], cluster_quellen[cid]))

    if not neu:
        print(f"  Alle {len(kandidaten)} Kandidaten bereits bekannt.")
        logger.info(f"BREAKING CHECK: {len(kandidaten)} Kandidaten, alle bereits bekannt.")
        return

    print(f"  {len(neu)} neue Breaking News! Rufe Claude auf ...")
    ergebnisse = []

    for cid, fingerprint, arts, quellen in neu:
        bester = arts[0]
        quellen_str = ", ".join(sorted(quellen))
        print(f"\n  *** BREAKING: \"{bester['headline'][:65]}\"")
        print(f"      Quellen ({len(quellen)}): {quellen_str}")

        try:
            analyse = analyse_mit_claude(client, bester)
        except Exception as e:
            print(f"      Claude-Fehler: {e}")
            continue

        ergebnisse.append({
            "headline": bester["headline"],
            "summary": analyse.get("summary", ""),
            "source": bester["source"],
            "political_leaning": bester["political_leaning"],
            "category": analyse.get("category", "Sonstiges"),
            "is_breaking": True,
            "breaking_sources": sorted(quellen),
            "relevance_score": analyse.get("relevance_score", 80),
            "is_top_story": analyse.get("is_top_story", True),
            "image_url": "",
            "link": bester["link"],
            "timestamp": jetzt.isoformat(),
        })
        seen.add(fingerprint)
        logger.info(
            f"BREAKING NEWS: \"{bester['headline'][:80]}\" "
            f"({len(quellen)} Quellen: {quellen_str})"
        )

    if ergebnisse:
        dateiname = f"breaking_{jetzt.strftime('%Y%m%d_%H%M%S')}.json"
        with open(dateiname, "w", encoding="utf-8") as f:
            json.dump(ergebnisse, f, ensure_ascii=True, indent=2)
        print(f"\n  {len(ergebnisse)} Breaking News gespeichert in: {dateiname}")
        breaking_bilder_anreichern(dateiname)
        logger.info(
            f"BREAKING CHECK: {len(ergebnisse)} neue Stories gespeichert -> {dateiname}"
        )
        if on_complete:
            on_complete()

    breaking_seen_speichern(seen)
