import logging
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

logger = logging.getLogger(__name__)

_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}


def ist_zu_vage(headline):
    if not headline or not headline.strip():
        return True
    woerter = headline.split()
    if len(woerter) < 5:
        return True
    stripped = headline.strip()
    if (stripped[0] in ('„', '"', '"', "'") and
            stripped[-1] in ('"', '"', '"', "'") and
            len(woerter) < 8):
        return True
    return False


def _normalize_url(url):
    parsed = urlparse(url.strip())
    params = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k not in _TRACKING_PARAMS and v
    ]
    params.sort()
    return urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, urlencode(params), ""
    ))


def dedupe_by_url(artikel_liste):
    try:
        from cluster import _artikel_staerke
    except ImportError:
        _artikel_staerke = None

    vorher = len(artikel_liste)

    # Determine the strongest article per normalized URL (first seen wins on ties)
    best = {}
    for artikel in artikel_liste:
        link = artikel.get("link", "")
        if not link or not link.strip():
            continue
        norm = _normalize_url(link)
        if norm not in best:
            best[norm] = artikel
        elif _artikel_staerke is not None and _artikel_staerke(artikel) > _artikel_staerke(best[norm]):
            best[norm] = artikel

    # Rebuild list: keep winners, mark losers
    result = []
    seen_norms = set()
    removed = 0
    for artikel in artikel_liste:
        link = artikel.get("link", "")
        if not link or not link.strip():
            result.append(artikel)
            continue
        norm = _normalize_url(link)
        if norm not in seen_norms and best.get(norm) is artikel:
            seen_norms.add(norm)
            result.append(artikel)
        else:
            artikel["filter_reason"] = "duplicate_url"
            removed += 1

    logger.info("dedupe_by_url: %d Artikel vorher", vorher)
    logger.info("dedupe_by_url: %d Artikel nach Deduplizierung", len(result))
    logger.info("dedupe_by_url: %d entfernt wegen duplicate_url", removed)
    return result
