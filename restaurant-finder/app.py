"""
Restaurant Reservation Finder

A Flask web app that takes a Google Maps restaurant list and finds
available reservations on Resy.
"""

import os
import concurrent.futures
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from maps_parser import parse_google_maps_list, parse_manual_list
from resy_checker import find_and_check as resy_find, DEFAULT_API_KEY as RESY_DEFAULT_KEY

load_dotenv()

app = Flask(__name__)

RESY_API_KEY = os.environ.get("RESY_API_KEY", RESY_DEFAULT_KEY)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse-list", methods=["POST"])
def parse_list():
    """Parse a Google Maps list URL or manual text input."""
    data = request.get_json()
    input_type = data.get("type", "url")  # "url" or "manual"
    value = data.get("value", "").strip()

    if not value:
        return jsonify({"error": "No input provided"}), 400

    if input_type == "url":
        try:
            restaurants = parse_google_maps_list(value)
        except Exception as e:
            return jsonify({"error": f"Failed to parse list: {str(e)}"}), 400
    else:
        restaurants = parse_manual_list(value)

    if not restaurants:
        return jsonify({
            "error": "No restaurants found. Try pasting restaurant names manually.",
            "restaurants": [],
        }), 200

    return jsonify({"restaurants": restaurants})


@app.route("/api/check-availability", methods=["POST"])
def check_availability():
    """
    Check reservation availability for a list of restaurants on Resy.

    Expects JSON:
    {
        "restaurants": [{"name": "...", "address": "..."}],
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "party_size": 2,
        "location": "New York"
    }
    """
    data = request.get_json()
    restaurants = data.get("restaurants", [])
    date = data.get("date", "")
    party_size = data.get("party_size", 2)
    location = data.get("location", "")

    if not restaurants:
        return jsonify({"error": "No restaurants provided"}), 400
    if not date:
        return jsonify({"error": "No date provided"}), 400

    results = []

    def check_restaurant(restaurant):
        name = restaurant.get("name", "")
        addr = restaurant.get("address", "") or location
        resy_result = resy_find(name, addr, date, party_size, RESY_API_KEY)
        return {"name": name, "result": resy_result}

    # Check all restaurants concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_restaurant = {
            executor.submit(check_restaurant, r): r for r in restaurants
        }
        for future in concurrent.futures.as_completed(future_to_restaurant):
            try:
                results.append(future.result(timeout=30))
            except Exception as e:
                restaurant = future_to_restaurant[future]
                results.append({
                    "name": restaurant.get("name", "Unknown"),
                    "result": {"found": False, "available": False, "slots": [], "error": str(e)},
                })

    # Sort results: available first, then by name
    results.sort(key=lambda r: (
        not r.get("result", {}).get("available", False),
        r.get("name", ""),
    ))

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
