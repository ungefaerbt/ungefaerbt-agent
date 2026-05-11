import json
import concurrent.futures

FINGERPRINT_MODEL = "claude-haiku-4-5-20251001"
FINGERPRINT_MAX_TOKENS = 150
FINGERPRINT_BATCH_SIZE = 10

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


def _einzeln(client, artikel):
    headline = artikel.get("headline", "").replace('"', '\\"')
    summary = artikel.get("summary", "").replace('"', '\\"')
    prompt = _PROMPT.replace("__HEADLINE__", headline).replace("__SUMMARY__", summary)
    try:
        resp = client.messages.create(
            model=FINGERPRINT_MODEL,
            max_tokens=FINGERPRINT_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(resp.content[0].text.strip())
        return {
            "event_who": data.get("event_who") or [],
            "event_what": data.get("event_what") or "",
            "event_where": _null(data.get("event_where")),
            "event_when": _null(data.get("event_when")),
        }
    except Exception as e:
        print(f"\n  [FP-Fehler] {artikel.get('headline', '')[:60]} → {e}")
        return dict(_LEER)


def fingerprint_erstellen(artikel_liste, client):
    n = len(artikel_liste)
    ergebnisse = [None] * n

    with concurrent.futures.ThreadPoolExecutor(max_workers=FINGERPRINT_BATCH_SIZE) as pool:
        future_to_idx = {
            pool.submit(_einzeln, client, a): i
            for i, a in enumerate(artikel_liste)
        }
        fertig = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            ergebnisse[idx] = future.result()
            fertig += 1
            print(f"\r  Fingerprint: {fertig}/{n}", end="", flush=True)

    print()

    for i, artikel in enumerate(artikel_liste):
        artikel.update(ergebnisse[i] or dict(_LEER))

    return artikel_liste
