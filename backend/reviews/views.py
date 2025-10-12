import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

CACHE_FILENAME = "google_reviews_cache.json"
CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours
GOOGLE_PLACES_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json"


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
    return data


def _store_cache(payload: Dict[str, Any]) -> None:
    cache_file = _cache_path()
    cache_file.write_text(json.dumps(payload))


def _sanitize_reviews(raw_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized: List[Dict[str, Any]] = []
    for item in raw_reviews[:12]:
        sanitized.append(
            {
                "author_name": item.get("author_name"),
                "profile_photo_url": item.get("profile_photo_url"),
                "rating": item.get("rating"),
                "text": item.get("text"),
                "time": item.get("time"),
                "relative_time_description": item.get("relative_time_description"),
                "author_url": item.get("author_url"),
                "language": item.get("language"),
            }
        )
    return sanitized


def _build_payload(data: Dict[str, Any], place_id: str) -> Dict[str, Any]:
    result = data.get("result", {})
    reviews = result.get("reviews") or []
    payload = {
        "rating": result.get("rating"),
        "total_reviews": result.get("user_ratings_total"),
        "fetched_at": timezone.now().isoformat(),
        "reviews": _sanitize_reviews(reviews),
        "place_url": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
    }
    return payload


def _should_refresh(cache: Dict[str, Any] | None) -> bool:
    if not cache:
        return True
    fetched_at = cache.get("fetched_at")
    if not fetched_at:
        return True
    try:
        ts = timezone.datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    if settings.USE_TZ and ts.tzinfo is None:
        ts = timezone.make_aware(ts)
    age = (timezone.now() - ts).total_seconds()
    return age > CACHE_TTL_SECONDS


def _fetch_from_google(place_id: str, api_key: str, language: str | None = None) -> Dict[str, Any] | None:
    params = {
        "place_id": place_id,
        "fields": "rating,user_ratings_total,reviews",
        "reviews_sort": "newest",
        "key": api_key,
    }
    if language:
        params["language"] = language
    try:
        response = requests.get(GOOGLE_PLACES_ENDPOINT, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return None
    payload = response.json()
    if payload.get("status") != "OK":
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
        return JsonResponse(cached)

    language = request.GET.get("lang")
    google_data = _fetch_from_google(place_id, api_key, language=language)

    if google_data:
        payload = _build_payload(google_data, place_id)
        _store_cache(payload)
        return JsonResponse(payload)

    if cached:
        return JsonResponse(cached)

    return JsonResponse({"detail": "Unable to fetch reviews."}, status=502)
