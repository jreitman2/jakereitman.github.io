"""
Resy Availability Checker

Uses the Resy public API to search for restaurants and check reservation availability.
"""

import json
import requests


RESY_API_BASE = "https://api.resy.com"

# Public API key extracted from Resy's client-side JavaScript
DEFAULT_API_KEY = "VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"


def _get_headers(api_key: str) -> dict:
    """Build request headers with the provided API key."""
    return {
        "Authorization": f'ResyAPI api_key="{api_key}"',
        "Origin": "https://resy.com",
        "Referer": "https://resy.com/",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def search_venue(name: str, location: str, api_key: str) -> list[dict]:
    """
    Search for a restaurant on Resy by name and location.

    Returns:
        List of matching venues with id, name, and location info
    """
    headers = _get_headers(api_key)

    geo = {}
    # Common city coordinates for better search results
    city_coords = {
        "new york": {"latitude": 40.7128, "longitude": -74.0060},
        "los angeles": {"latitude": 34.0522, "longitude": -118.2437},
        "san francisco": {"latitude": 37.7749, "longitude": -122.4194},
        "chicago": {"latitude": 41.8781, "longitude": -87.6298},
        "miami": {"latitude": 25.7617, "longitude": -80.1918},
    }
    for city, coords in city_coords.items():
        if city in location.lower():
            geo = coords
            break

    # Use only restaurant name in query — geo handles location filtering.
    # Appending location to the query confuses Resy's search.
    struct_data = json.dumps({
        "query": name,
        "per_page": 10,
        "types": ["venue"],
        **({"geo": geo} if geo else {}),
    })

    try:
        resp = requests.post(
            f"{RESY_API_BASE}/3/venuesearch/search",
            data={"struct_data": struct_data},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        venues = []
        for hit in data.get("search", {}).get("hits", []):
            venue = hit.get("_source", hit)
            venue_id = venue.get("id", {})
            if isinstance(venue_id, dict):
                venue_id = venue_id.get("resy")

            location_data = venue.get("location", {})
            venues.append({
                "id": venue_id,
                "name": venue.get("name", ""),
                "location": {
                    "city": location_data.get("name", ""),
                    "neighborhood": location_data.get("neighborhood", ""),
                    "url_slug": location_data.get("url_slug", ""),
                },
                "cuisine": venue.get("cuisine", []),
                "price_range": venue.get("price_range", 0),
                "url_slug": venue.get("url_slug", ""),
            })
        return venues

    except requests.RequestException as e:
        return [{"error": str(e)}]


def check_availability(
    venue_id: int,
    date: str,
    party_size: int,
    api_key: str,
) -> dict:
    """
    Check reservation availability at a Resy venue using /3/find.

    Returns:
        Dict with 'available' bool and 'slots' list of available times
    """
    headers = _get_headers(api_key)

    params = {
        "day": date,
        "party_size": party_size,
        "venue_id": venue_id,
        "lat": "0",
        "long": "0",
    }

    try:
        resp = requests.get(
            f"{RESY_API_BASE}/3/find",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        slots = []
        results = data.get("results", [])

        # Results can be a list of venue result objects
        if isinstance(results, list):
            for venue_result in results:
                if not isinstance(venue_result, dict):
                    continue
                for slot in venue_result.get("slots", []):
                    config = slot.get("config", {})
                    date_info = slot.get("date", {})
                    slots.append({
                        "time": date_info.get("start", ""),
                        "end": date_info.get("end", ""),
                        "type": config.get("type", ""),
                    })
        elif isinstance(results, dict):
            # Results might also be a dict with a venues key
            for venue_data in results.get("venues", []):
                for slot in venue_data.get("slots", []):
                    config = slot.get("config", {})
                    date_info = slot.get("date", {})
                    slots.append({
                        "time": date_info.get("start", ""),
                        "end": date_info.get("end", ""),
                        "type": config.get("type", ""),
                    })

        return {
            "available": len(slots) > 0,
            "slots": slots,
            "venue_id": venue_id,
        }

    except requests.RequestException as e:
        return {"available": False, "slots": [], "error": str(e)}


def _name_similarity(query: str, candidate: str) -> float:
    """Simple name similarity score. Higher is better."""
    q = query.lower().strip()
    c = candidate.lower().strip()
    if q == c:
        return 1.0
    if q in c or c in q:
        return 0.8
    # Check word overlap
    q_words = set(q.split())
    c_words = set(c.split())
    if not q_words:
        return 0.0
    overlap = len(q_words & c_words)
    return overlap / max(len(q_words), len(c_words))


def find_and_check(
    restaurant_name: str,
    location: str,
    date: str,
    party_size: int,
    api_key: str,
) -> dict:
    """
    Search for a restaurant on Resy and check its availability.
    """
    venues = search_venue(restaurant_name, location, api_key)

    if not venues:
        return {
            "platform": "resy",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "url": "",
        }

    if "error" in venues[0]:
        return {
            "platform": "resy",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "error": venues[0]["error"],
            "url": "",
        }

    # Pick the best matching venue by name similarity
    scored = [(v, _name_similarity(restaurant_name, v.get("name", ""))) for v in venues]
    scored.sort(key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    # If the best match is too poor, mark as not found
    if best_score <= 0.5:
        return {
            "platform": "resy",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "url": "",
        }

    venue_id = best.get("id")

    if not venue_id:
        return {
            "platform": "resy",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "url": "",
        }

    availability = check_availability(venue_id, date, party_size, api_key)

    url_slug = best.get("url_slug", "")
    location_slug = best.get("location", {}).get("url_slug", "")
    resy_url = f"https://resy.com/cities/{location_slug}/{url_slug}" if url_slug and location_slug else ""

    return {
        "platform": "resy",
        "restaurant": best.get("name", restaurant_name),
        "found": True,
        "available": availability["available"],
        "slots": availability["slots"],
        "venue_id": venue_id,
        "url": resy_url,
        "error": availability.get("error"),
    }
