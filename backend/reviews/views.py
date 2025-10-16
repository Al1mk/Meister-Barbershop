import json
import os
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

CACHE_FILENAME = "google_reviews_cache.json"
CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours
GOOGLE_PLACES_ENDPOINT = "https://places.googleapis.com/v1"
GOOGLE_FIELD_MASK = ",".join(
    [
        "rating",
        "userRatingCount",
        "reviews.rating",
        "reviews.text",
        "reviews.publishTime",
        "reviews.authorAttribution.displayName",
        "reviews.authorAttribution.uri",
    ]
)


def _cache_path() -> Path:
    cache_dir = Path(settings.BASE_DIR) / "tmp"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / CACHE_FILENAME


def _load_cached() -> Dict[str, Any] | None:
    cache_file = _cache_path()
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if "payload" in data and "fetched_at" in data:
        return data
    # migrate legacy cache shape if present
    fetched_at = data.get("fetched_at")
    legacy_reviews = data.get("reviews") or []
    if fetched_at is None or not isinstance(legacy_reviews, list):
        return None
    migrated_reviews: List[Dict[str, Any]] = []
    for raw in legacy_reviews[:12]:
        raw = raw or {}
        timestamp = raw.get("time")
        iso_time = ""
        if isinstance(timestamp, (int, float)):
            try:
                if settings.USE_TZ:
                    dt = datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)
                    dt = dt.astimezone(timezone.get_default_timezone())
                else:
                    dt = datetime.fromtimestamp(timestamp)
                iso_time = dt.isoformat()
            except (OSError, OverflowError, ValueError):
                iso_time = ""
        migrated_reviews.append(
            {
                "authorName": raw.get("author_name") or "",
                "rating": raw.get("rating") or 0,
                "text": raw.get("text") or "",
                "time": iso_time,
                "sourceUrl": raw.get("author_url") or None,
            }
        )
    migrated = {
        "fetched_at": fetched_at,
        "payload": {
            "rating": data.get("rating") or 0,
            "userRatingCount": data.get("total_reviews") or 0,
            "reviews": migrated_reviews,
        },
    }
    return migrated


def _store_cache(payload: Dict[str, Any]) -> None:
    cache_file = _cache_path()
    cache_contents = {
        "fetched_at": timezone.now().isoformat(),
        "payload": payload,
    }
    cache_file.write_text(json.dumps(cache_contents))


def _sanitize_reviews(raw_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized: List[Dict[str, Any]] = []
    for item in (raw_reviews or [])[:12]:
        author = item.get("authorAttribution") or {}
        text_block = item.get("text") or {}
        uri = author.get("uri") or None
        sanitized.append(
            {
                "authorName": author.get("displayName") or "",
                "rating": item.get("rating") or 0,
                "text": text_block.get("text") or "",
                "time": item.get("publishTime") or "",
                "sourceUrl": uri,
            }
        )
    return sanitized


def _build_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    reviews = data.get("reviews") or []
    payload = {
        "rating": data.get("rating") or 0,
        "userRatingCount": data.get("userRatingCount") or 0,
        "reviews": _sanitize_reviews(reviews),
    }
    return payload


def _should_refresh(cache: Dict[str, Any] | None) -> bool:
    if not cache:
        return True
    fetched_at = cache.get("fetched_at")
    if not fetched_at:
        return True
    try:
        ts = datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    if settings.USE_TZ and ts.tzinfo is None:
        ts = timezone.make_aware(ts)
    elif settings.USE_TZ:
        ts = ts.astimezone(timezone.get_default_timezone())
    age = (timezone.now() - ts).total_seconds()
    return age > CACHE_TTL_SECONDS


def _fetch_from_google(place_id: str, api_key: str, language: str | None = None) -> Dict[str, Any] | None:
    url = f"{GOOGLE_PLACES_ENDPOINT}/places/{place_id}"
    params: Dict[str, Any] = {}
    if language:
        params["languageCode"] = language
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": GOOGLE_FIELD_MASK,
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return None
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("error"):
        return None
    return payload


@require_GET
def reviews_view(request):
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    place_id = os.getenv("GOOGLE_PLACE_ID")
    if not api_key or not place_id:
        return JsonResponse({"detail": "Google Places credentials missing."}, status=500)

    cached = _load_cached()
    if cached and not _should_refresh(cached):
        return JsonResponse(cached["payload"])

    language = request.GET.get("lang") or getattr(settings, "LANGUAGE_CODE", None)
    if language:
        language = language.replace("_", "-")
    google_data = _fetch_from_google(place_id, api_key, language=language)

    if google_data:
        payload = _build_payload(google_data)
        _store_cache(payload)
        return JsonResponse(payload)

    if cached:
        return JsonResponse(cached["payload"])

    return JsonResponse({"detail": "Unable to fetch reviews."}, status=502)
