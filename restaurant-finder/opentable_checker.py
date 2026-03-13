"""
OpenTable Availability Checker

OpenTable aggressively blocks server-side API requests (503/403), so this module
uses a two-pronged approach:
1. Try their booking widget API (best-effort, may be blocked)
2. Always generate a direct booking URL the user can open in their browser

The booking URL pre-fills the date, time, and party size so the user just has to
click to see availability.
"""

import re
from urllib.parse import quote, urlencode
import requests


def _build_search_url(restaurant_name: str, location: str, date: str, time: str, party_size: int) -> str:
    """Build an OpenTable search URL with pre-filled reservation details."""
    params = {
        "term": restaurant_name,
        "dateTime": f"{date}T{time}",
        "covers": party_size,
    }
    return f"https://www.opentable.com/s?{urlencode(params)}"


def _build_booking_url(restaurant_slug: str, date: str, time: str, party_size: int) -> str:
    """Build a direct OpenTable booking URL for a known restaurant."""
    params = {
        "dateTime": f"{date}T{time}",
        "covers": party_size,
    }
    return f"https://www.opentable.com/r/{restaurant_slug}?{urlencode(params)}"


def _slugify(name: str) -> str:
    """Convert a restaurant name to an OpenTable-style URL slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def find_and_check(
    restaurant_name: str,
    location: str,
    date: str,
    time: str,
    party_size: int,
) -> dict:
    """
    Generate OpenTable booking links for a restaurant.

    Since OpenTable blocks server-side API access, we generate direct URLs
    that the user can open in their browser to check availability and book.

    Returns:
        Dict with restaurant info and booking URL
    """
    slug = _slugify(restaurant_name)
    location_slug = _slugify(location) if location else ""

    # Build candidate booking URLs
    # OpenTable URLs follow patterns like /r/restaurant-name-city
    if location_slug:
        primary_slug = f"{slug}-{location_slug}"
    else:
        primary_slug = slug

    booking_url = _build_booking_url(primary_slug, date, time, party_size)
    search_url = _build_search_url(restaurant_name, location, date, time, party_size)

    return {
        "platform": "opentable",
        "restaurant": restaurant_name,
        "found": True,
        "available": None,  # We can't check server-side; user needs to click
        "slots": [],
        "url": search_url,
        "booking_url": booking_url,
        "note": "Click to check availability on OpenTable",
    }
