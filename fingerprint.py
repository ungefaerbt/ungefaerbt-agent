import json
import logging
import time

FINGERPRINT_MODEL = "claude-haiku-4-5-20251001"
FINGERPRINT_MAX_TOKENS = 150

ANTHROPIC_CALL_DELAY_SECONDS = 1.3
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 10

logger = logging.getLogger("fingerprint")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.propagate = False

_LEER = {
    "event_who": [],
    "event_what": "",
    "event_where": None,
    "event_when": None,
}

_PROMPT = (
    'Analysiere diese Nachricht und antworte NUR mit diesem JSON:\n'
    '{\n'
    '  "event_who": ["Person oder Organisation"],\n'
    '  "event_what": "Ereignis in max. 5 Wörtern",\n'
    '  "event_where": "Ort oder null",\n'
    '  "event_when": "YYYY-MM-DD oder null"\n'
    '}\n'
    'Headline: "__HEADLINE__"\n'
    'Zusammenfassung: "__SUMMARY__"'
)


def _null(val):
    if val is None or val == "null" or val == "":
        return None
    return val


def _parse_json(text):
    if "```" in text:
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except Exception:
        return None


def _ist_rate_limit(e):
    s = str(e).lower()
    return "429" in s or "rate_limit" in s or "rate limit" in s


def _fallback_fingerprint(artikel):
    woerter = artikel.get("headline", "").split()
    return {
        "event_who": [],
        "event_what": " ".join(woerter[:5]),
        "event_where": None,
        "event_when": None,
    }


def _einzeln(client, artikel, stats):
    headline = artikel.get("headline", "").replace('"', '\\"')
    summary  = artikel.get("summary",  "").replace('"', '\\"')
    prompt   = _PROMPT.replace("__HEADLINE__", headline).replace("__SUMMARY__", summary)

    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(ANTHROPIC_CALL_DELAY_SECONDS)
        try:
            resp = client.messages.create(
                model=FINGERPRINT_MODEL,
                max_tokens=FINGERPRINT_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            data = _parse_json(resp.content[0].text)
            if data is None:
                raise ValueError("Ungültige JSON-Antwort")
            stats["erfolg"] += 1
            return {
                "event_who":   data.get("event_who") or [],
                "event_what":  data.get("event_what") or "",
                "event_where": _null(data.get("event_where")),
                "event_when":  _null(data.get("event_when")),
            }
        except Exception as e:
            if _ist_rate_limit(e) and attempt < MAX_RETRIES:
                warte = RETRY_BACKOFF_SECONDS * attempt
                stats["retries"] += 1
                logger.warning(
                    "Rate Limit '%s' (Versuch %s/%s) — warte %ss",
                    artikel.get("headline", "")[:50], attempt, MAX_RETRIES, warte,
                )
                time.sleep(warte)
            else:
                logger.warning(
                    "Fingerprint fehlgeschlagen '%s': %s",
                    artikel.get("headline", "")[:50], str(e)[:100],
                )
                stats["fallback"] += 1
                return _fallback_fingerprint(artikel)

    stats["fallback"] += 1
    return _fallback_fingerprint(artikel)


def fingerprint_erstellen(artikel_liste, client):
    n = len(artikel_liste)
    logger.info("Fingerprinting gestartet: %s Artikel", n)

    stats = {"erfolg": 0, "fallback": 0, "retries": 0}

    for i, artikel in enumerate(artikel_liste, 1):
        fp = _einzeln(client, artikel, stats)
        artikel.update(fp)
        print(f"\r  Fingerprint: {i}/{n}", end="", flush=True)

    print()

    logger.info(
        "Fingerprinting abgeschlossen: %s erfolgreich, %s Fallback, %s Retries",
        stats["erfolg"], stats["fallback"], stats["retries"],
    )

    return artikel_liste
