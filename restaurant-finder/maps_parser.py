"""
Google Maps List Parser

Extracts restaurant names and addresses from a shared Google Maps list URL.
Google Maps lists are heavily JS-rendered, so we parse the embedded data
from the page source.
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def resolve_short_url(url: str) -> str:
    """Resolve shortened Google Maps URLs (maps.app.goo.gl) to full URLs."""
    if "goo.gl" in url or "maps.app" in url:
        resp = requests.head(url, allow_redirects=True, timeout=10)
        return resp.url
    return url


def parse_google_maps_list(url: str) -> list[dict]:
    """
    Parse a shared Google Maps list URL and extract restaurant info.

    Args:
        url: A Google Maps shared list URL

    Returns:
        List of dicts with 'name', 'address', and 'lat'/'lng' if available
    """
    url = resolve_short_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    html = resp.text

    restaurants = []

    # Google Maps embeds place data in the page source in various formats.
    # We try multiple extraction strategies.

    # Strategy 1: Look for place names in the structured data embedded in scripts
    # Google Maps pages contain data in window.APP_INITIALIZATION_STATE or
    # similar JS variables with arrays of place information.
    restaurants = _extract_from_page_data(html)

    if not restaurants:
        # Strategy 2: Parse meta tags and visible text as fallback
        restaurants = _extract_from_meta_and_text(html)

    return restaurants


def _extract_from_page_data(html: str) -> list[dict]:
    """Extract restaurant data from embedded JavaScript data in the page."""
    restaurants = []

    # Google Maps embeds data as nested arrays in script tags.
    # Place names typically appear near coordinates and addresses.
    # Pattern: looks for quoted strings that appear to be place names
    # near address-like strings.

    # Find all script content
    soup = BeautifulSoup(html, "lxml")

    # Look for the data payload - Google stores list items in a specific format
    # The data often appears in patterns like: [null,"Place Name",null,[null,null,lat,lng]...]
    # or as ["Place Name","address string",...]

    scripts = soup.find_all("script")
    all_script_text = " ".join(s.string or "" for s in scripts)

    # Extract place names - they often appear in a pattern with specific markers
    # Pattern: ,[\"PlaceName\",\" or similar in the serialized data
    # Look for patterns like: "name\\",null,null,null,\\"address\\"
    # In practice the data is in Protocol Buffer-like nested arrays

    # Try to find entries that look like: [null,"Restaurant Name",...]
    # followed by address data
    name_pattern = re.findall(
        r'\[null,"([^"]{3,60})"(?:,null)*,(?:null,)*"([^"]{10,120})"',
        all_script_text,
    )
    for name, address in name_pattern:
        if _looks_like_restaurant_entry(name, address):
            restaurants.append({"name": name, "address": address})

    # Also try: ["0x...:0x...",lat,lng,"Place Name"]
    coord_pattern = re.findall(
        r'"0x[0-9a-f]+:0x[0-9a-f]+",([-\d.]+),([-\d.]+),"([^"]{3,60})"',
        all_script_text,
    )
    seen_names = {r["name"] for r in restaurants}
    for lat, lng, name in coord_pattern:
        if name not in seen_names:
            restaurants.append({
                "name": name,
                "address": "",
                "lat": float(lat),
                "lng": float(lng),
            })
            seen_names.add(name)

    # Try another common pattern where names appear in title-like contexts
    title_pattern = re.findall(
        r'\\\"([^\\\"]{3,60})\\\"[,\]]*\\\"([^\\\"]*(?:St|Ave|Blvd|Rd|Dr|Way|Pl|Ct|Ln|Pkwy|Hwy|Broadway|Street|Avenue|Road|Drive|Place|Court)[^\\\"]*?)\\\"',
        all_script_text,
    )
    for name, address in title_pattern:
        if name not in seen_names and _looks_like_restaurant_entry(name, address):
            restaurants.append({"name": name, "address": address})
            seen_names.add(name)

    return restaurants


def _extract_from_meta_and_text(html: str) -> list[dict]:
    """Fallback: extract from meta tags and page title."""
    soup = BeautifulSoup(html, "lxml")
    restaurants = []

    # Check og:title or page title for list info
    title_tag = soup.find("meta", property="og:title")
    if title_tag:
        title = title_tag.get("content", "")
        # Sometimes the title contains useful info about the list

    # Look for aria-label attributes that contain place names
    # Google Maps uses these extensively
    place_elements = soup.find_all(attrs={"aria-label": True})
    seen = set()
    for el in place_elements:
        label = el.get("aria-label", "")
        # Filter for likely restaurant/place names (not UI elements)
        if (
            len(label) > 3
            and label not in seen
            and not _is_ui_label(label)
        ):
            restaurants.append({"name": label, "address": ""})
            seen.add(label)

    return restaurants


def _looks_like_restaurant_entry(name: str, address: str) -> bool:
    """Heuristic check if a name/address pair looks like a real place."""
    # Filter out things that are clearly not restaurant names
    skip_words = [
        "google", "maps", "null", "undefined", "true", "false",
        "http", "www", "javascript", "function", "return",
    ]
    name_lower = name.lower()
    if any(w in name_lower for w in skip_words):
        return False
    if len(name) < 3 or len(name) > 60:
        return False
    # Name should contain at least one letter
    if not re.search(r"[a-zA-Z]", name):
        return False
    return True


def _is_ui_label(label: str) -> bool:
    """Check if an aria-label is likely a UI element, not a place name."""
    ui_words = [
        "close", "menu", "search", "back", "zoom", "directions",
        "share", "save", "send", "navigate", "more", "options",
        "collapse", "expand", "toggle", "button", "click",
    ]
    label_lower = label.lower().strip()
    return any(label_lower == w or label_lower.startswith(w + " ") for w in ui_words)


def parse_manual_list(text: str) -> list[dict]:
    """
    Parse a manually entered list of restaurant names (one per line).

    Args:
        text: Newline-separated restaurant names

    Returns:
        List of dicts with 'name' key
    """
    restaurants = []
    for line in text.strip().splitlines():
        name = line.strip().strip("-•*").strip()
        if name:
            restaurants.append({"name": name, "address": ""})
    return restaurants
