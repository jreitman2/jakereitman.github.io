"""
OpenTable Availability Checker

Uses OpenTable's public-facing API to search for restaurants and check
reservation availability.
"""

import requests


OPENTABLE_BASE = "https://www.opentable.com"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://www.opentable.com",
    "Referer": "https://www.opentable.com/",
}


def search_restaurant(name: str, location: str) -> list[dict]:
    """
    Search for a restaurant on OpenTable.

    Args:
        name: Restaurant name
        location: City or area

    Returns:
        List of matching restaurants with id, name, and profile URL
    """
    headers = DEFAULT_HEADERS.copy()

    query = f"{name} {location}" if location else name

    params = {
        "term": query,
        "latitude": 0,
        "longitude": 0,
    }

    try:
        resp = requests.get(
            f"{OPENTABLE_BASE}/dapi/fe/search",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        restaurants = []
        for r in data.get("restaurants", [])[:5]:
            restaurants.append({
                "id": r.get("rid", r.get("restaurantId", "")),
                "name": r.get("name", ""),
                "neighborhood": r.get("neighborhood", ""),
                "cuisine": r.get("primaryCuisine", ""),
                "price_range": r.get("priceBand", ""),
                "profile_url": r.get("profileLink", ""),
                "photos": r.get("photos", {}).get("small", ""),
            })
        return restaurants

    except requests.RequestException as e:
        return [{"error": str(e)}]


def check_availability(
    restaurant_id: int,
    date: str,
    time: str,
    party_size: int,
) -> dict:
    """
    Check reservation availability at an OpenTable restaurant.

    Args:
        restaurant_id: OpenTable restaurant ID
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24h)
        party_size: Number of guests

    Returns:
        Dict with availability info and time slots
    """
    headers = DEFAULT_HEADERS.copy()
    headers["Content-Type"] = "application/json"

    # OpenTable availability endpoint
    datetime_str = f"{date}T{time}"

    params = {
        "rid": restaurant_id,
        "partySize": party_size,
        "dateTime": datetime_str,
        "enableFindNextAvailable": True,
        "includeNextAvailable": True,
    }

    try:
        resp = requests.get(
            f"{OPENTABLE_BASE}/dapi/fe/gql/GetRestaurantAvailability",
            params=params,
            headers=headers,
            timeout=10,
        )

        # If the GQL endpoint doesn't work, try the REST endpoint
        if resp.status_code != 200:
            return _check_availability_rest(restaurant_id, date, time, party_size)

        data = resp.json()

        slots = []
        availability = data.get("availability", data.get("data", {}).get("availability", {}))
        time_slots = availability.get("timeSlots", availability.get("slots", []))

        for slot in time_slots:
            slots.append({
                "time": slot.get("dateTime", slot.get("time", "")),
                "type": slot.get("tableType", slot.get("type", "standard")),
            })

        return {
            "available": len(slots) > 0,
            "slots": slots,
            "restaurant_id": restaurant_id,
        }

    except requests.RequestException as e:
        return _check_availability_rest(restaurant_id, date, time, party_size)


def _check_availability_rest(
    restaurant_id: int,
    date: str,
    time: str,
    party_size: int,
) -> dict:
    """Fallback: check availability using the REST API endpoint."""
    headers = DEFAULT_HEADERS.copy()

    datetime_str = f"{date}T{time}:00"

    try:
        resp = requests.get(
            f"{OPENTABLE_BASE}/restref/api/availability",
            params={
                "rid": restaurant_id,
                "dateTime": datetime_str,
                "partySize": party_size,
                "enableFindNextAvailable": "true",
            },
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        slots = []
        for slot in data.get("availability", []):
            slots.append({
                "time": slot.get("dateTime", ""),
                "type": slot.get("tableType", "standard"),
            })

        return {
            "available": len(slots) > 0,
            "slots": slots,
            "restaurant_id": restaurant_id,
        }

    except requests.RequestException as e:
        return {"available": False, "slots": [], "error": str(e)}


def find_and_check(
    restaurant_name: str,
    location: str,
    date: str,
    time: str,
    party_size: int,
) -> dict:
    """
    Search for a restaurant on OpenTable and check its availability.

    Args:
        restaurant_name: Name of the restaurant
        location: City or neighborhood
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24h)
        party_size: Number of guests

    Returns:
        Dict with restaurant info and availability
    """
    restaurants = search_restaurant(restaurant_name, location)

    if not restaurants:
        return {
            "platform": "opentable",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "url": "",
        }

    if "error" in restaurants[0]:
        return {
            "platform": "opentable",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "error": restaurants[0]["error"],
            "url": "",
        }

    best = restaurants[0]
    restaurant_id = best.get("id")

    if not restaurant_id:
        return {
            "platform": "opentable",
            "restaurant": restaurant_name,
            "found": False,
            "available": False,
            "slots": [],
            "url": "",
        }

    availability = check_availability(restaurant_id, date, time, party_size)

    profile_url = best.get("profile_url", "")
    if profile_url and not profile_url.startswith("http"):
        profile_url = f"https://www.opentable.com{profile_url}"

    return {
        "platform": "opentable",
        "restaurant": best.get("name", restaurant_name),
        "found": True,
        "available": availability["available"],
        "slots": availability["slots"],
        "restaurant_id": restaurant_id,
        "url": profile_url,
        "error": availability.get("error"),
    }
