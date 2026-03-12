"""
Resy Availability Checker

Uses the Resy public API to search for restaurants and check reservation availability.
"""

import requests
from datetime import datetime


RESY_API_BASE = "https://api.resy.com"

# Default headers for Resy API requests
DEFAULT_HEADERS = {
    "Authorization": 'ResyAPI api_key="{api_key}"',
    "Origin": "https://resy.com",
    "Referer": "https://resy.com/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _get_headers(api_key: str) -> dict:
    """Build request headers with the provided API key."""
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f'ResyAPI api_key="{api_key}"'
    return headers


def search_venue(name: str, location: str, api_key: str) -> list[dict]:
    """
    Search for a restaurant on Resy by name and location.

    Args:
        name: Restaurant name
        location: City or address for context
        api_key: Resy API key

    Returns:
        List of matching venues with id, name, and location info
    """
    headers = _get_headers(api_key)

    # Use the venue search endpoint
    params = {
        "per_page": 5,
        "query": name,
        "types": ["venue"],
    }

    if location:
        params["query"] = f"{name} {location}"

    try:
        resp = requests.get(
            f"{RESY_API_BASE}/3/venuesearch/search",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        venues = []
        search_results = data.get("search", {}).get("hits", [])
        for hit in search_results:
            venue = hit.get("_source", hit)
            venues.append({
                "id": venue.get("id", {}).get("resy") if isinstance(venue.get("id"), dict) else venue.get("id"),
                "name": venue.get("name", ""),
                "location": {
                    "city": venue.get("location", {}).get("city", ""),
                    "neighborhood": venue.get("location", {}).get("neighborhood", ""),
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
    Check reservation availability at a Resy venue.

    Args:
        venue_id: Resy venue ID
        date: Date string in YYYY-MM-DD format
        party_size: Number of guests
        api_key: Resy API key

    Returns:
        Dict with 'available' bool and 'slots' list of available times
    """
    headers = _get_headers(api_key)

    params = {
        "day": date,
        "party_size": party_size,
        "venue_id": venue_id,
    }

    try:
        resp = requests.get(
            f"{RESY_API_BASE}/4/find",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", {})
        venues = results.get("venues", [])

        slots = []
        if venues:
            venue_data = venues[0]
            for slot in venue_data.get("slots", []):
                config = slot.get("config", {})
                date_info = slot.get("date", {})
                slots.append({
                    "time": date_info.get("start", ""),
                    "end": date_info.get("end", ""),
                    "type": config.get("type", ""),
                    "token": config.get("token", ""),
                })

        return {
            "available": len(slots) > 0,
            "slots": slots,
            "venue_id": venue_id,
        }

    except requests.RequestException as e:
        return {"available": False, "slots": [], "error": str(e)}


def find_and_check(
    restaurant_name: str,
    location: str,
    date: str,
    party_size: int,
    api_key: str,
) -> dict:
    """
    Search for a restaurant on Resy and check its availability.

    Args:
        restaurant_name: Name of the restaurant
        location: City or neighborhood
        date: Date in YYYY-MM-DD format
        party_size: Number of guests
        api_key: Resy API key

    Returns:
        Dict with venue info and availability
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

    # Use the best match (first result)
    best = venues[0]
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
    city = best.get("location", {}).get("city", "").lower().replace(" ", "-")
    resy_url = f"https://resy.com/cities/{city}/{url_slug}" if url_slug and city else ""

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
