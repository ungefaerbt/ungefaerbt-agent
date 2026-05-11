import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


IMAGE_MODE = "stock_search_first"
USAGE_LABEL = "Symbolbild"
UNSPLASH_ORIENTATION = "squarish"
MAX_ANCHORS_PER_STORY = 6
MAX_PHOTOS_PER_ANCHOR = 3
MAX_CANDIDATES_FOR_CLAUDE = 18
REQUEST_RETRIES = 3
REQUEST_TIMEOUT = 10
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"


STOP_WORDS = {
    "aber",
    "alle",
    "auch",
    "auf",
    "aus",
    "bei",
    "bis",
    "das",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "fuer",
    "hat",
    "mit",
    "nach",
    "nicht",
    "oder",
    "sich",
    "und",
    "von",
    "vor",
    "was",
    "wegen",
    "wie",
    "wird",
    "zu",
    "zum",
    "zur",
}


CATEGORY_ANCHORS = {
    "politik": ["Bundestag", "Berlin", "parliament", "government"],
    "wirtschaft": ["euro", "business", "factory", "bank", "supermarket"],
    "international": ["diplomacy", "flag", "conference", "border"],
    "krieg": ["diplomacy", "flag", "conference", "border"],
    "umwelt": ["climate", "drought", "flood", "wind turbine"],
    "klima": ["climate", "drought", "flood", "wind turbine"],
    "kriminalitaet": ["police", "emergency", "street"],
    "unfall": ["police", "emergency", "street"],
    "sport": ["stadium", "football", "trophy"],
    "technologie": ["data center", "smartphone", "artificial intelligence"],
    "kultur": ["museum", "theater", "concert"],
    "gesellschaft": ["city street", "community", "public square"],
    "gesundheit": ["hospital", "medicine", "doctor"],
    "sonstiges": ["news", "city", "public"],
}


KNOWN_ENTITY_ANCHORS = {
    "bundesregierung": "Bundesregierung",
    "bundestag": "Bundestag",
    "bundesrat": "Bundesrat",
    "berlin": "Berlin",
    "euro": "euro",
    "commerzbank": "Commerzbank",
    "deutsche bank": "Deutsche Bank",
    "volkswagen": "Volkswagen",
    "bmw": "BMW",
    "mercedes": "Mercedes",
    "siemens": "Siemens",
    "sap": "SAP",
    "panini": "Panini",
    "wien": "Wien",
    "ukraine": "Ukraine flag",
    "russland": "Russia flag",
    "russia": "Russia flag",
    "iran": "Iran flag",
    "usa": "USA flag",
    "vereinigte staaten": "USA flag",
    "eu": "EU flag",
    "nato": "NATO flag",
    "un": "United Nations",
    "uno": "United Nations",
    "labour": "Labour",
    "reform uk": "Reform UK",
    "apple": "Apple",
    "google": "Google",
    "microsoft": "Microsoft",
    "openai": "OpenAI",
}


HARD_NEWS_TERMS = {
    "angriff",
    "anschlag",
    "bombe",
    "drohne",
    "explosion",
    "feuer",
    "gefecht",
    "gewalt",
    "krieg",
    "kriminalitaet",
    "luftalarm",
    "mord",
    "opfer",
    "rakete",
    "schuss",
    "terror",
    "tot",
    "tote",
    "unfall",
    "waffenruhe",
}


HIGH_RISK_TERMS = {
    "battle",
    "battlefield",
    "blood",
    "bloody",
    "bomb",
    "crash",
    "dead",
    "explosion",
    "fire",
    "missile",
    "soldier",
    "weapon",
    "war",
}


PERSON_HINTS = {
    "praesident",
    "premierminister",
    "kanzler",
    "minister",
    "chef",
    "parteichef",
    "sprecher",
}


def _log(message: str) -> None:
    print(f"[IMAGE_AGENT] {message}")


def _normalize(value: Any) -> str:
    text = str(value or "").lower()
    text = (
        text.replace("ae", "ae")
        .replace("oe", "oe")
        .replace("ue", "ue")
        .replace("ss", "ss")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def _clean_anchor(anchor: str) -> str:
    anchor = re.sub(r"[^\w\s.-]", " ", str(anchor or ""), flags=re.UNICODE)
    anchor = re.sub(r"\s+", " ", anchor).strip()
    parts = anchor.split()
    if len(parts) > 2:
        anchor = " ".join(parts[:2])
    return anchor


def _add_unique(target: list[str], anchor: str, max_items: int = MAX_ANCHORS_PER_STORY) -> None:
    anchor = _clean_anchor(anchor)
    if not anchor:
        return
    key = _normalize(anchor)
    if key in {_normalize(item) for item in target}:
        return
    if len(target) < max_items:
        target.append(anchor)


def _story_text(story: dict[str, Any]) -> str:
    return " ".join(
        str(story.get(key, ""))
        for key in ("headline", "title", "summary", "description", "category", "source")
        if story.get(key)
    )


def _story_headline(story: dict[str, Any]) -> str:
    return str(story.get("headline") or story.get("title") or "").strip()


def _story_summary(story: dict[str, Any]) -> str:
    return str(story.get("summary") or story.get("description") or "").strip()


def _story_category(story: dict[str, Any]) -> str:
    return str(story.get("category") or story.get("kategorie") or story.get("ressort") or "Sonstiges").strip()


def _is_hard_news(story: dict[str, Any]) -> bool:
    text = _normalize(_story_text(story))
    return any(term in text for term in HARD_NEWS_TERMS)


def _misleading_risk(story: dict[str, Any]) -> str:
    text = _normalize(_story_text(story))
    matches = sum(1 for term in HARD_NEWS_TERMS if term in text)
    if matches >= 3:
        return "high"
    if matches >= 1 or bool(story.get("is_breaking")):
        return "medium"
    return "low"


def _avoid_terms_for_story(story: dict[str, Any]) -> list[str]:
    avoid = ["recognizable faces", "clickbait", "sensational scenes"]
    if _is_hard_news(story):
        avoid.extend(
            [
                "fake battlefield",
                "blood",
                "weapons",
                "explosions",
                "dramatic accident scenes",
                "graphic suffering",
                "real victims",
            ]
        )
    return avoid


def _extract_known_entities(text: str) -> list[str]:
    normalized = _normalize(text)
    found: list[str] = []
    for needle, anchor in KNOWN_ENTITY_ANCHORS.items():
        pattern = r"(?<!\w)" + re.escape(needle) + r"(?!\w)"
        if re.search(pattern, normalized):
            _add_unique(found, anchor, max_items=4)
    return found


def _extract_specific_terms(text: str) -> list[str]:
    found: list[str] = []

    # Acronyms and mixed-case brands are useful on Unsplash, but person names are not.
    for match in re.finditer(r"\b[A-ZÄÖÜ]{2,8}\b", text):
        term = match.group(0)
        if _normalize(term) not in STOP_WORDS:
            _add_unique(found, term, max_items=3)

    for match in re.finditer(r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9.-]{3,}\b", text):
        term = match.group(0)
        normalized = _normalize(term)
        if normalized in STOP_WORDS:
            continue
        if any(hint in normalized for hint in PERSON_HINTS):
            continue
        if normalized.startswith("bundes") or normalized.endswith(
            ("bank", "rat", "tag", "stadt", "werke", "konzern")
        ):
            _add_unique(found, term, max_items=3)

    return found


def _category_anchor_key(category: str, story: dict[str, Any]) -> str:
    normalized_category = _normalize(category)
    normalized_text = _normalize(_story_text(story))

    if any(term in normalized_text for term in ("krieg", "waffenruhe", "militaer", "angriff")):
        return "krieg"
    if any(term in normalized_text for term in ("kriminal", "mord", "polizei", "terror")):
        return "kriminalitaet"
    if any(term in normalized_text for term in ("unfall", "crash", "kollision")):
        return "unfall"
    if any(term in normalized_text for term in ("klima", "duerre", "trockenheit", "flut", "hochwasser")):
        return "klima"

    for key in CATEGORY_ANCHORS:
        if key in normalized_category:
            return key
    return "sonstiges"


def load_stories(input_path: str | Path) -> list[dict[str, Any]]:
    path = Path(input_path)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("stories", "items", "articles", "data"):
            if isinstance(data.get(key), list):
                return data[key]

    raise ValueError("Input JSON must be a list of stories or an object with a stories/items/articles/data list.")


def save_stories(stories: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(stories, file, ensure_ascii=False, indent=2)
        file.write("\n")


def build_visual_anchors(story: dict[str, Any]) -> dict[str, Any]:
    headline = _story_headline(story)
    summary = _story_summary(story)
    category = _story_category(story)
    text = f"{headline} {summary}"
    category_key = _category_anchor_key(category, story)

    anchors: list[str] = []
    for anchor in _extract_known_entities(text):
        _add_unique(anchors, anchor)

    if not _is_hard_news(story):
        for anchor in _extract_specific_terms(text):
            _add_unique(anchors, anchor)

    for anchor in CATEGORY_ANCHORS.get(category_key, CATEGORY_ANCHORS["sonstiges"]):
        _add_unique(anchors, anchor)

    risk = _misleading_risk(story)
    if _is_hard_news(story) and risk == "low":
        risk = "medium"

    return {
        "visual_category": category_key,
        "image_mode": IMAGE_MODE,
        "preferred_subjects": anchors,
        "avoid": _avoid_terms_for_story(story),
        "search_queries": anchors,
        "misleading_risk": risk,
        "usage_label": USAGE_LABEL,
    }


def _unsplash_search_url(query: str, access_key: str, per_page: int) -> str:
    params = urllib.parse.urlencode(
        {
            "query": query,
            "per_page": per_page,
            "orientation": UNSPLASH_ORIENTATION,
            "order_by": "relevant",
            "content_filter": "high",
            "client_id": access_key,
        }
    )
    return f"https://api.unsplash.com/search/photos?{params}"


def _candidate_from_unsplash_result(result: dict[str, Any], anchor: str, rank: int) -> dict[str, Any] | None:
    urls = result.get("urls") or {}
    links = result.get("links") or {}
    user = result.get("user") or {}
    user_links = user.get("links") or {}
    image_url = urls.get("regular")

    if not image_url:
        return None

    description = result.get("description") or result.get("alt_description") or ""
    return {
        "id": result.get("id"),
        "url": image_url,
        "source": "unsplash",
        "photographer": user.get("name"),
        "photographer_url": user_links.get("html"),
        "unsplash_url": links.get("html"),
        "download_location": links.get("download_location"),
        "description": description,
        "alt_text": result.get("alt_description") or description,
        "usage_label": USAGE_LABEL,
        "width": result.get("width"),
        "height": result.get("height"),
        "color": result.get("color"),
        "likes": result.get("likes"),
        "created_at": result.get("created_at"),
        "anchor": anchor,
        "anchor_rank": rank,
        "final_score": None,
    }


def search_unsplash_candidates(
    anchors: list[str],
    access_key: str,
    photos_per_anchor: int = MAX_PHOTOS_PER_ANCHOR,
) -> list[dict[str, Any]]:
    if not access_key:
        _log("No UNSPLASH_ACCESS_KEY found. Skipping stock search.")
        return []

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for rank, anchor in enumerate(anchors, start=1):
        url = _unsplash_search_url(anchor, access_key, photos_per_anchor)
        for attempt in range(REQUEST_RETRIES):
            try:
                with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
                    data = json.loads(response.read().decode("utf-8"))
                results = data.get("results", [])
                _log(f"Anchor '{anchor}' returned {len(results)} photo(s).")
                for result in results[:photos_per_anchor]:
                    candidate = _candidate_from_unsplash_result(result, anchor, rank)
                    if not candidate:
                        continue
                    dedupe_key = candidate.get("id") or candidate["url"]
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    candidates.append(candidate)
                break
            except Exception as exc:
                wait_seconds = 2**attempt
                _log(f"Unsplash attempt {attempt + 1} failed for '{anchor}': {exc}. Waiting {wait_seconds}s.")
                time.sleep(wait_seconds)

    return candidates


def _candidate_identity_keys(candidate: dict[str, Any]) -> set[str]:
    keys = set()
    for field in ("id", "url", "unsplash_url"):
        value = candidate.get(field)
        if value:
            keys.add(str(value))

    url = str(candidate.get("url") or "")
    if "?" in url:
        keys.add(url.split("?", 1)[0])

    return keys


def _primary_image_identity_keys(primary_image: dict[str, Any]) -> set[str]:
    keys = set()
    for field in ("url", "unsplash_url"):
        value = primary_image.get(field)
        if value:
            keys.add(str(value))

    url = str(primary_image.get("url") or "")
    if "?" in url:
        keys.add(url.split("?", 1)[0])

    return keys


def _filter_previously_selected_candidates(
    candidates: list[dict[str, Any]],
    used_image_keys: set[str],
) -> list[dict[str, Any]]:
    if not used_image_keys:
        return candidates
    return [
        candidate
        for candidate in candidates
        if _candidate_identity_keys(candidate).isdisjoint(used_image_keys)
    ]


def score_image_candidate(candidate: dict[str, Any], story: dict[str, Any], visual_brief: dict[str, Any]) -> int:
    score = 50

    if candidate.get("description") or candidate.get("alt_text"):
        score += 8
    if candidate.get("photographer") and candidate.get("unsplash_url") and candidate.get("download_location"):
        score += 10
    if candidate.get("width") and candidate.get("height"):
        width = int(candidate["width"])
        height = int(candidate["height"])
        if width and height:
            ratio = width / height
            if 0.75 <= ratio <= 1.35:
                score += 8

    anchor_rank = int(candidate.get("anchor_rank") or 99)
    score += max(0, 8 - anchor_rank)

    text = _normalize(
        " ".join(
            str(candidate.get(key, ""))
            for key in ("description", "alt_text", "anchor", "unsplash_url")
        )
    )
    if any(term in text for term in HIGH_RISK_TERMS):
        score -= 25 if _is_hard_news(story) else 12

    if visual_brief.get("misleading_risk") == "high":
        score -= 5

    return max(0, min(100, score))


def _primary_image_from_candidate(
    candidate: dict[str, Any] | None,
    confidence: str,
    reason: str | None,
    final_score: int | None,
    selection_method: str,
    needs_review: bool,
) -> dict[str, Any]:
    if not candidate:
        return {
            "url": None,
            "source": "unsplash",
            "photographer": None,
            "photographer_url": None,
            "unsplash_url": None,
            "download_location": None,
            "description": None,
            "alt_text": None,
            "usage_label": USAGE_LABEL,
            "confidence": "low",
            "reason": reason,
            "final_score": None,
            "selection_method": selection_method,
            "needs_review": True,
        }

    return {
        "url": candidate.get("url"),
        "source": candidate.get("source", "unsplash"),
        "photographer": candidate.get("photographer"),
        "photographer_url": candidate.get("photographer_url"),
        "unsplash_url": candidate.get("unsplash_url"),
        "download_location": candidate.get("download_location"),
        "description": candidate.get("description"),
        "alt_text": candidate.get("alt_text"),
        "usage_label": USAGE_LABEL,
        "confidence": confidence,
        "reason": reason,
        "final_score": final_score,
        "selection_method": selection_method,
        "needs_review": needs_review,
    }


def _parse_model_json(text: str) -> dict[str, Any]:
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def select_best_image_with_claude(
    client: Any,
    story: dict[str, Any],
    visual_brief: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not client or not candidates:
        return None

    headline = _story_headline(story)
    summary = _story_summary(story)
    category = _story_category(story)
    compact_candidates = candidates[:MAX_CANDIDATES_FOR_CLAUDE]
    candidate_lines = []
    for index, candidate in enumerate(compact_candidates, start=1):
        candidate_lines.append(
            "\n".join(
                [
                    f"{index}. url: {candidate.get('url')}",
                    f"   anchor: {candidate.get('anchor')}",
                    f"   description: {candidate.get('description') or candidate.get('alt_text') or ''}",
                    f"   photographer: {candidate.get('photographer') or ''}",
                    f"   unsplash_url: {candidate.get('unsplash_url') or ''}",
                ]
            )
        )

    prompt = (
        "Du bist Bildredakteur fuer die News-Marke 'ungefaerbt'. "
        "Die Marke ist neutral, ruhig, faktenorientiert und nicht clickbaitig.\n\n"
        "Waehle aus den Unsplash-Kandidaten genau ein Bild fuer diese Story. "
        "Bevorzuge ein neutrales Symbolbild, das nicht irrefuehrt. "
        "Bei Krieg, Terror, Unfall, Mord, Kriminalitaet, Katastrophen oder realen Personen "
        "muss die Auswahl besonders konservativ sein: keine Fake-Battlefield-Bilder, kein Blut, "
        "keine dramatischen Unfallbilder, keine erkennbaren Opfer, keine sensationsheischende Emotionalisierung.\n\n"
        f"Headline: {headline}\n"
        f"Summary: {summary}\n"
        f"Category: {category}\n"
        f"Visual brief: {json.dumps(visual_brief, ensure_ascii=False)}\n\n"
        "Kandidaten:\n"
        f"{chr(10).join(candidate_lines)}\n\n"
        "Antworte nur mit validem JSON:\n"
        "{"
        '"candidate_index": 1, '
        '"confidence": "low|medium|high", '
        '"reason": "kurze Begruendung", '
        '"alt_text": "neutraler deutscher Alt-Text", '
        '"final_score": 0'
        "}"
    )

    model = os.getenv("IMAGE_AGENT_CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL)

    for attempt in range(REQUEST_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=350,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            data = _parse_model_json(text)
            index = int(data.get("candidate_index", 0))
            if not 1 <= index <= len(compact_candidates):
                raise ValueError(f"Claude returned invalid candidate_index: {index}")

            confidence = str(data.get("confidence") or "medium").lower()
            if confidence not in {"low", "medium", "high"}:
                confidence = "medium"

            candidate = dict(compact_candidates[index - 1])
            if data.get("alt_text"):
                candidate["alt_text"] = str(data["alt_text"])

            final_score = data.get("final_score")
            try:
                final_score_int = max(0, min(100, int(final_score)))
            except Exception:
                final_score_int = score_image_candidate(candidate, story, visual_brief)

            return _primary_image_from_candidate(
                candidate=candidate,
                confidence=confidence,
                reason=str(data.get("reason") or "Claude selected this candidate."),
                final_score=final_score_int,
                selection_method="claude",
                needs_review=confidence == "low" or visual_brief.get("misleading_risk") == "high",
            )
        except Exception as exc:
            wait_seconds = 2**attempt
            _log(f"Claude selection attempt {attempt + 1} failed: {exc}. Waiting {wait_seconds}s.")
            time.sleep(wait_seconds)

    return None


def select_best_image_fallback(
    story: dict[str, Any],
    visual_brief: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if not candidates:
        return _primary_image_from_candidate(
            candidate=None,
            confidence="low",
            reason="No Unsplash candidates found.",
            final_score=None,
            selection_method="fallback_no_candidates",
            needs_review=True,
        )

    scored_candidates = []
    for candidate in candidates:
        score = score_image_candidate(candidate, story, visual_brief)
        candidate["final_score"] = score
        scored_candidates.append(candidate)

    best = max(scored_candidates, key=lambda item: int(item.get("final_score") or 0))
    return _primary_image_from_candidate(
        candidate=best,
        confidence="low",
        reason="Local fallback selected the best available Unsplash candidate. Manual review recommended.",
        final_score=int(best.get("final_score") or 0),
        selection_method="fallback_no_claude",
        needs_review=True,
    )


def build_image_package(
    visual_brief: dict[str, Any],
    primary_image: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "visual_brief": visual_brief,
        "primary_image": primary_image,
        "candidates": candidates,
    }


def enrich_story_with_images(
    client: Any,
    story: dict[str, Any],
    access_key: str,
    photos_per_anchor: int = MAX_PHOTOS_PER_ANCHOR,
    used_image_keys: set[str] | None = None,
) -> dict[str, Any]:
    enriched = dict(story)
    visual_brief = build_visual_anchors(story)
    anchors = visual_brief.get("search_queries") or []
    _log(f"Story: {_story_headline(story)[:70]}")
    _log(f"Anchors: {', '.join(anchors)}")

    candidates = search_unsplash_candidates(anchors, access_key, photos_per_anchor=photos_per_anchor)
    selectable_candidates = _filter_previously_selected_candidates(candidates, used_image_keys or set())
    removed_count = len(candidates) - len(selectable_candidates)
    if removed_count:
        _log(f"Skipped {removed_count} candidate(s) already selected earlier in this run.")

    primary_image = select_best_image_with_claude(client, story, visual_brief, selectable_candidates)
    if not primary_image:
        primary_image = select_best_image_fallback(story, visual_brief, selectable_candidates)

    enriched["image_package"] = build_image_package(visual_brief, primary_image, candidates)
    return enriched


def enrich_stories_with_images(
    client: Any,
    stories: list[dict[str, Any]],
    access_key: str,
    photos_per_anchor: int = MAX_PHOTOS_PER_ANCHOR,
    limit: int | None = None,
    sync_image_url: bool = False,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    selected_stories = stories[:limit] if limit else stories
    used_image_keys: set[str] = set()

    for index, story in enumerate(selected_stories, start=1):
        if not isinstance(story, dict):
            _log(f"Skipping non-object story at index {index}.")
            continue
        _log(f"Processing {index}/{len(selected_stories)}")
        enriched = enrich_story_with_images(
            client,
            story,
            access_key,
            photos_per_anchor=photos_per_anchor,
            used_image_keys=used_image_keys,
        )
        primary_image = enriched.get("image_package", {}).get("primary_image", {})
        used_image_keys.update(_primary_image_identity_keys(primary_image))
        if sync_image_url:
            selected_url = primary_image.get("url")
            if selected_url:
                enriched["image_url"] = selected_url
        output.append(enriched)

    if limit and len(stories) > limit:
        output.extend(stories[limit:])

    return output


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _load_nearby_env_files() -> None:
    for path in (Path(".env"), Path("..") / ".env"):
        _load_env_file(path)


def _create_anthropic_client(api_key: str | None, disabled: bool = False) -> Any:
    if disabled or not api_key:
        return None
    try:
        import anthropic  # type: ignore

        return anthropic.Anthropic(api_key=api_key)
    except Exception as exc:
        _log(f"Claude client unavailable: {exc}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich news stories with neutral Unsplash image packages.")
    parser.add_argument("--input", required=True, help="Input JSON file with stories.")
    parser.add_argument("--output", required=True, help="Output JSON file to write.")
    parser.add_argument("--unsplash-key", default=None, help="Unsplash API key. Defaults to UNSPLASH_ACCESS_KEY.")
    parser.add_argument("--anthropic-key", default=None, help="Anthropic API key. Defaults to ANTHROPIC_API_KEY.")
    parser.add_argument("--no-claude", action="store_true", help="Skip Claude and use local fallback selection.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N stories for testing.")
    parser.add_argument(
        "--photos-per-anchor",
        type=int,
        default=MAX_PHOTOS_PER_ANCHOR,
        help="How many Unsplash photos to fetch per anchor.",
    )
    parser.add_argument(
        "--sync-image-url",
        action="store_true",
        help="Also copy the selected primary image URL into the story's image_url field.",
    )
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _load_nearby_env_files()

    unsplash_key = args.unsplash_key or os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
    anthropic_key = args.anthropic_key or os.getenv("ANTHROPIC_API_KEY", "").strip()
    client = _create_anthropic_client(anthropic_key, disabled=args.no_claude)

    stories = load_stories(args.input)
    _log(f"Loaded {len(stories)} story/stories.")
    if not client:
        _log("Claude is not active. Fallback selections will be marked for review.")

    enriched = enrich_stories_with_images(
        client=client,
        stories=stories,
        access_key=unsplash_key,
        photos_per_anchor=max(1, min(10, args.photos_per_anchor)),
        limit=args.limit,
        sync_image_url=args.sync_image_url,
    )
    save_stories(enriched, args.output)
    _log(f"Wrote output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
