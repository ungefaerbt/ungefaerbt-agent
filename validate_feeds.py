import json
import logging
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime

import feedparser

from config import QUELLEN

sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("validate_feeds")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)

logger.propagate = False


def feeds_aus_quelle(name, daten):
    if "feeds" in daten:
        return [
            (eintrag.get("ressort", "allgemein"), eintrag["rss"])
            for eintrag in daten.get("feeds", [])
            if "rss" in eintrag
        ]
    if "rss" in daten:
        return [(None, daten["rss"])]
    return []


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def feed_laden(rss_url, timeout=10):
    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            inhalt = response.read()
        return feedparser.parse(inhalt), None, None
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None, "BLOCKED_403", str(e)
        return None, "ERROR", str(e)
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", None)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return None, "ERROR", "timeout"
        return None, "ERROR", str(e)
    except (socket.timeout, TimeoutError):
        return None, "ERROR", "timeout"
    except Exception as e:
        return None, "ERROR", str(e)


def feed_pruefen(source, ausrichtung, ressort, rss_url):
    ergebnis = {
        "source": source,
        "ausrichtung": ausrichtung,
        "rss_url": rss_url,
    }
    if ressort is not None:
        ergebnis["ressort"] = ressort

    feed, status_fehler, fehler_msg = feed_laden(rss_url)

    if status_fehler == "BLOCKED_403":
        logger.warning("Feed blockiert (403) — möglicherweise User-Agent-Filter: %s", rss_url)
        ergebnis["status"] = "BLOCKED_403"
        ergebnis["error_message"] = fehler_msg
        ergebnis["number_of_entries"] = 0
        return ergebnis

    if status_fehler == "ERROR":
        ergebnis["status"] = "ERROR"
        ergebnis["error_message"] = fehler_msg
        ergebnis["number_of_entries"] = 0
        return ergebnis

    entries = feed.get("entries", [])
    anzahl = len(entries)
    ergebnis["number_of_entries"] = anzahl

    feed_info = feed.get("feed", {})
    if feed_info.get("title"):
        ergebnis["feed_title"] = feed_info["title"]

    if entries:
        neuester = entries[0]
        ergebnis["newest_entry_title"] = neuester.get("title", "")
        ergebnis["newest_entry_link"] = neuester.get("link", "")
        datum = neuester.get("published") or neuester.get("updated")
        if datum:
            ergebnis["newest_entry_date"] = datum

    if anzahl >= 3:
        ergebnis["status"] = "OK"
    elif anzahl >= 1:
        ergebnis["status"] = "WARN"
    else:
        ergebnis["status"] = "ERROR"

    return ergebnis


def ergebnis_ausgeben(ergebnis):
    source = ergebnis["source"]
    ressort = ergebnis.get("ressort")
    label = f"{source} / {ressort}" if ressort else source
    status = ergebnis["status"]
    fehler = ergebnis.get("error_message", "")
    anzahl = ergebnis.get("number_of_entries", 0)

    if fehler:
        print(f"{status:<6} {label:<40} {fehler}")
    else:
        print(f"{status:<6} {label:<40} {anzahl} Artikel")


def main():
    logger.info("validate_feeds gestartet")

    alle_ergebnisse = []

    for name, daten in QUELLEN.items():
        ausrichtung = daten.get("ausrichtung", "")
        feeds = feeds_aus_quelle(name, daten)

        if not feeds:
            logger.warning("Keine RSS-URL für %s", name)
            continue

        for ressort, rss_url in feeds:
            ergebnis = feed_pruefen(name, ausrichtung, ressort, rss_url)
            alle_ergebnisse.append(ergebnis)
            ergebnis_ausgeben(ergebnis)

    gesamt       = len(alle_ergebnisse)
    ok           = sum(1 for e in alle_ergebnisse if e["status"] == "OK")
    warn         = sum(1 for e in alle_ergebnisse if e["status"] == "WARN")
    error        = sum(1 for e in alle_ergebnisse if e["status"] == "ERROR")
    blocked_403  = sum(1 for e in alle_ergebnisse if e["status"] == "BLOCKED_403")

    print()
    print(f"Gesamt: {gesamt}  |  OK: {ok}  |  WARN: {warn}  |  ERROR: {error}  |  BLOCKED_403: {blocked_403}")

    jetzt = datetime.now()
    report = {
        "timestamp": jetzt.isoformat(),
        "gesamt": gesamt,
        "ok": ok,
        "warn": warn,
        "error": error,
        "blocked_403_count": blocked_403,
        "ergebnisse": alle_ergebnisse,
    }

    datei_timestamp = f"feed_validation_report_{jetzt.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    datei_latest = "feed_validation_report_latest.json"

    with open(datei_timestamp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(datei_latest, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(
        "validate_feeds abgeschlossen: %s/%s OK, %s WARN, %s ERROR, %s BLOCKED_403 — %s, %s",
        ok, gesamt, warn, error, blocked_403, datei_timestamp, datei_latest,
    )


if __name__ == "__main__":
    main()
