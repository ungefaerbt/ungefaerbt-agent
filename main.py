import sys
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime

import anthropic
import schedule
from dotenv import load_dotenv

from config import (
    ALLE_AUSRICHTUNGEN,
    BREAKING_INTERVALL_MIN,
    KATEGORIE_FALLBACK_BILDER,
    NORMAL_ZEITEN,
)
from breaking import breaking_news_check
from cluster import schlagzeilen_clustern
from fetcher import schlagzeilen_abrufen
from filter import ist_zu_vage
from images import unsplash_bild_suchen
from sorter import feed_sortieren
from writer import analyse_mit_claude, cluster_synthese_mit_sonnet

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

_log_handler = logging.FileHandler("log.txt", encoding="utf-8")
_log_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger = logging.getLogger("news_agent")
logger.addHandler(_log_handler)
logger.setLevel(logging.INFO)


def _zeige_naechsten_lauf():
    normal_jobs = schedule.get_jobs("normal")
    breaking_jobs = schedule.get_jobs("breaking")
    jetzt = datetime.now()
    print("\n" + "-" * 60)
    if breaking_jobs:
        naechster = min(j.next_run for j in breaking_jobs)
        diff_min = max(0, int((naechster - jetzt).total_seconds() / 60))
        print(f"  Breaking-News-Check: {naechster.strftime('%H:%M')} Uhr  (in {diff_min} Min.)")
    if normal_jobs:
        naechster = min(j.next_run for j in normal_jobs)
        diff_min = max(0, int((naechster - jetzt).total_seconds() / 60))
        print(f"  Normal-Durchlauf:    {naechster.strftime('%H:%M')} Uhr  (in {diff_min} Min.)")
    print("-" * 60)


def normaler_durchlauf(client, unsplash_key):
    jetzt_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n{'=' * 60}")
    print(f"  NORMALER DURCHLAUF -- {jetzt_str}")
    print(f"{'=' * 60}")

    alle = schlagzeilen_abrufen()

    if not alle:
        print("\nKeine Schlagzeilen gefunden. Bitte Internetverbindung prüfen.")
        logger.info("NORMAL DURCHLAUF: Keine Schlagzeilen gefunden.")
        return

    # Schritt 1: Vage Headlines vorfiltern
    gefiltert = [a for a in alle if not ist_zu_vage(a["headline"])]
    uebersprungen = len(alle) - len(gefiltert)
    if uebersprungen:
        print(f"\n  {uebersprungen} Artikel wegen zu vager Headline übersprungen.")

    # Schritt 2: Clustering VOR der API-Analyse
    print(f"\nClustere {len(gefiltert)} Artikel ...")
    schlagzeilen_clustern(gefiltert)
    synthetisierte_cluster = len({
        a["cluster_id"] for a in gefiltert if a.get("cluster_size", 1) > 1
    })
    print(f"  {synthetisierte_cluster} Cluster mit 2+ Quellen erkannt.")

    # Schritt 3: Claude-Analyse
    print(f"\nAnalysiere {len(gefiltert)} Schlagzeilen mit Claude ...\n")
    ergebnisse = []

    for i, artikel in enumerate(gefiltert, 1):
        print(f"  [{i}/{len(gefiltert)}] {artikel['headline'][:70]}...")
        try:
            analyse = analyse_mit_claude(client, artikel)
            if analyse.get("summary") == "KEIN_ARTIKEL":
                print(f"    ↳ Kein seriöser Artikel – verworfen.")
                uebersprungen += 1
                continue
            kategorie = analyse.get("category", "Sonstiges")
            image_url = unsplash_bild_suchen(client, artikel["headline"], kategorie, unsplash_key)
            if image_url:
                print(f"    Unsplash-Bild gefunden.")
            if not image_url:
                image_url = KATEGORIE_FALLBACK_BILDER.get(kategorie, "")
            ergebnisse.append({
                "headline": analyse.get("headline") or artikel["headline"],
                "summary": analyse.get("summary", ""),
                "source": artikel["source"],
                "political_leaning": artikel["political_leaning"],
                "category": kategorie,
                "is_breaking": analyse.get("is_breaking", False),
                "relevance_score": analyse.get("relevance_score", 50),
                "is_top_story": analyse.get("is_top_story", False),
                "image_url": image_url,
                "link": artikel["link"],
                "timestamp": datetime.now().isoformat(),
                "cluster_id": artikel["cluster_id"],
                "cluster_size": artikel["cluster_size"],
                "blindspot_label": artikel.get("blindspot_label", "Einzelmeldung"),
                "blindspot_score": artikel.get("blindspot_score", 100),
                "silent_spectrums": artikel.get("silent_spectrums", []),
                "spectrum_count": artikel.get("spectrum_count", 0),
            })
            time.sleep(0.5)
        except Exception as fehler:
            print(f"    Fehler bei Analyse: {fehler}")

    # Schritt 4: Cluster-Synthese
    print(f"\nSynthetisiere Cluster ...")
    nach_cluster = defaultdict(list)
    for a in ergebnisse:
        nach_cluster[a["cluster_id"]].append(a)

    finale_artikel = []
    cluster_synthetisiert = 0

    for cid, gruppe in nach_cluster.items():
        if len(gruppe) == 1:
            finale_artikel.append(gruppe[0])
            continue

        bester = max(gruppe, key=lambda x: x.get("relevance_score", 0))

        try:
            synthese = cluster_synthese_mit_sonnet(client, gruppe)
            summary = synthese.get("summary", bester.get("summary", ""))
            cluster_headline = synthese.get("headline") or bester["headline"]
            if summary == "KEIN_CLUSTER":
                for a in gruppe:
                    a["cluster_size"] = 1
                finale_artikel.extend(gruppe)
                print(f"    ↳ Kein echter Cluster – {len(gruppe)} Artikel als Einzelmeldungen")
                continue
        except Exception as e:
            print(f"    Synthese-Fehler Cluster {cid}: {e}")
            summary = bester.get("summary", "")
            cluster_headline = bester["headline"]

        alle_quellen = ", ".join(dict.fromkeys(a["source"] for a in gruppe))
        vorhandene_spektren = [s for s in ALLE_AUSRICHTUNGEN if any(a["political_leaning"] == s for a in gruppe)]
        alle_spektren = ", ".join(vorhandene_spektren)
        image_url = unsplash_bild_suchen(client, cluster_headline, bester["category"], unsplash_key)
        if not image_url:
            image_url = KATEGORIE_FALLBACK_BILDER.get(bester["category"], "")

        finale_artikel.append({
            "headline": cluster_headline,
            "summary": summary,
            "source": alle_quellen,
            "political_leaning": alle_spektren,
            "category": bester["category"],
            "is_breaking": bester.get("is_breaking", False),
            "relevance_score": bester.get("relevance_score", 50),
            "is_top_story": bester.get("is_top_story", False),
            "image_url": image_url,
            "link": bester["link"],
            "timestamp": bester["timestamp"],
            "cluster_id": cid,
            "cluster_size": bester["cluster_size"],
            "blindspot_label": bester.get("blindspot_label", "Einzelmeldung"),
            "blindspot_score": bester.get("blindspot_score", 100),
            "silent_spectrums": bester.get("silent_spectrums", []),
            "spectrum_count": len(vorhandene_spektren),
        })
        cluster_synthetisiert += 1
        print(f"  ✓ Cluster: {len(gruppe)} Artikel → 1 Story  [{alle_quellen[:55]}]")

    ergebnisse = feed_sortieren(finale_artikel)

    # Sicherheitsnetz: Einzelartikel dürfen nie spectrum_count > 1 oder falsches Label haben
    for a in ergebnisse:
        if a.get("cluster_size", 1) == 1:
            a["spectrum_count"] = 1
            a["blindspot_label"] = "Einzelmeldung"

    dateiname = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dateiname, "w", encoding="utf-8") as f:
        json.dump(ergebnisse, f, ensure_ascii=True, indent=2)

    breaking_count = sum(1 for a in ergebnisse if a.get("is_breaking", False))
    top_story_count = sum(1 for a in ergebnisse if a.get("is_top_story", False))
    normal_count = len(ergebnisse) - breaking_count
    scores = [a.get("relevance_score", 0) for a in ergebnisse]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    print(f"\n Fertig! {len(ergebnisse)} Stories gespeichert in: {dateiname}")
    print(f" ({breaking_count} Breaking, {normal_count} Normal, {cluster_synthetisiert} Cluster synthetisiert)")
    if uebersprungen:
        print(f" ({uebersprungen} Artikel wegen zu vager Headline übersprungen)")

    print(f"\n{'─' * 60}")
    print(f"  LAUF-STATISTIK")
    print(f"{'─' * 60}")
    print(f"  Gesamtanzahl Stories:        {len(ergebnisse)}")
    print(f"  Cluster synthetisiert:       {cluster_synthetisiert}")
    print(f"  is_top_story = true:         {top_story_count}")
    print(f"  Durchschnittlicher Score:    {avg_score}")

    top_beispiel = next((a for a in ergebnisse if a.get("is_top_story")), None)
    if top_beispiel:
        print(f"\n  Beispiel Top Story:")
        print(f"    Headline:   {top_beispiel['headline'][:65]}")
        print(f"    Kategorie:  {top_beispiel['category']}")
        print(f"    Score:      {top_beispiel.get('relevance_score', '–')}")
        print(f"    Blindspot:  {top_beispiel.get('blindspot_label', '–')}")
        print(f"    Cluster:    {top_beispiel.get('cluster_size', 1)} Quelle(n)")
        print(f"    Bild:       {'ja' if top_beispiel.get('image_url') else 'nein'}")
    print(f"{'─' * 60}\n")

    print("-" * 60)

    breaking_artikel = [a for a in ergebnisse if a.get("is_breaking", False)]
    multi_artikel = [a for a in ergebnisse if not a.get("is_breaking", False) and a["cluster_size"] > 1]
    einzel_artikel = [a for a in ergebnisse if not a.get("is_breaking", False) and a["cluster_size"] == 1]

    def _zeige_artikel(artikel, breaking=False):
        leaning = artikel["political_leaning"].ljust(12)
        kategorie = artikel["category"].ljust(15)
        breaking_label = " *** BREAKING ***" if breaking else ""
        print(f"[{leaning}] [{kategorie}]{breaking_label}")
        print(f"  {artikel['headline']}")
        print(f"  {artikel['source']}")
        print()

    if breaking_artikel:
        print("\n" + "*" * 60)
        print("  *** BREAKING NEWS ***")
        print("*" * 60)
        letzter_cluster_id = None
        for artikel in breaking_artikel:
            cluster_id = artikel["cluster_id"]
            cluster_size = artikel["cluster_size"]
            if cluster_size > 1 and cluster_id != letzter_cluster_id:
                fueller = "-" * (44 - len(str(cluster_size)))
                print(f"\n-- {cluster_size} Quellen berichten {fueller}")
            letzter_cluster_id = cluster_id
            _zeige_artikel(artikel, breaking=True)

    if multi_artikel:
        letzter_cluster_id = None
        for artikel in multi_artikel:
            cluster_id = artikel["cluster_id"]
            cluster_size = artikel["cluster_size"]
            if cluster_id != letzter_cluster_id:
                fueller = "-" * (44 - len(str(cluster_size)))
                print(f"\n-- {cluster_size} Quellen berichten {fueller}")
            letzter_cluster_id = cluster_id
            _zeige_artikel(artikel)

    if einzel_artikel:
        print("\n-- Einzelmeldungen " + "-" * 41)
        for artikel in einzel_artikel:
            _zeige_artikel(artikel)

    logger.info(
        f"NORMAL DURCHLAUF: {len(ergebnisse)} Stories, "
        f"{cluster_synthetisiert} Cluster synthetisiert, "
        f"{uebersprungen} uebersprungen -> {dateiname}"
    )
    _zeige_naechsten_lauf()


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nFEHLER: Kein API-Key gefunden!")
        print("Bitte trage deinen Anthropic API-Key in die .env Datei ein.")
        print("Zeile in .env: ANTHROPIC_API_KEY=dein-key-hier\n")
        return

    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    client = anthropic.Anthropic(api_key=api_key)

    print("\n" + "=" * 60)
    print("  UNGEFAERBT NEWS AGENT  –  Scheduling aktiv")
    print(f"  Normal-Durchlauf:     {', '.join(NORMAL_ZEITEN)} Uhr")
    print(f"  Breaking-News-Check:  alle {BREAKING_INTERVALL_MIN} Minuten")
    print(f"  Unsplash-Fallback:    {'aktiv' if unsplash_key else 'inaktiv'}")
    print(f"  Log-Datei:            log.txt")
    print("=" * 60)
    logger.info("News Agent gestartet.")

    print("\nStarte initialen Durchlauf ...\n")
    normaler_durchlauf(client, unsplash_key)

    # # Schedules einrichten
    # for uhrzeit in NORMAL_ZEITEN:
    #     schedule.every().day.at(uhrzeit).do(
    #         normaler_durchlauf, client, unsplash_key
    #     ).tag("normal")

    # schedule.every(BREAKING_INTERVALL_MIN).minutes.do(
    #     breaking_news_check, client, unsplash_key, _zeige_naechsten_lauf
    # ).tag("breaking")

    # _zeige_naechsten_lauf()
    # print("  Agent laeuft im Hintergrund. Beenden mit Strg+C.\n")

    # letzter_status_ts = time.time()
    # try:
    #     while True:
    #         schedule.run_pending()
    #         if time.time() - letzter_status_ts >= 1800:
    #             _zeige_naechsten_lauf()
    #             letzter_status_ts = time.time()
    #         time.sleep(30)
    # except KeyboardInterrupt:
    #     print("\n\nAgent gestoppt (Strg+C).")
    #     logger.info("News Agent gestoppt.")


if __name__ == "__main__":
    main()
