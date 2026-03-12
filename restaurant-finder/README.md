# Restaurant Reservation Finder

Paste a Google Maps restaurant list URL (or restaurant names) and find available reservations on **Resy** and **OpenTable**.

## Setup

```bash
cd restaurant-finder

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure Resy API key
cp .env.example .env
# Edit .env and add your RESY_API_KEY

# Run the app
python app.py
```

Then open [http://localhost:5000](http://localhost:5000).

## Getting a Resy API Key

OpenTable works out of the box. For Resy:

1. Go to [resy.com](https://resy.com) and open browser DevTools (F12)
2. Go to the Network tab, search for any restaurant
3. Find a request to `api.resy.com` and copy the `authorization` header value
4. It looks like: `ResyAPI api_key="YOUR_KEY_HERE"`
5. Put just the key part in your `.env` file

## How It Works

1. **Paste your Google Maps list URL** — the app extracts restaurant names from the shared list page
2. **Or type restaurant names** — one per line in the "Paste Names" tab
3. **Set your date, time, and party size**
4. **Hit "Find Reservations"** — the app checks Resy and OpenTable concurrently
5. **See results** — available time slots are shown with links to book

## Architecture

```
app.py                  — Flask server with API routes
maps_parser.py          — Google Maps shared list URL parser
resy_checker.py         — Resy API search + availability checker
opentable_checker.py    — OpenTable API search + availability checker
templates/index.html    — Single-page frontend
```

## Notes

- Google Maps list parsing relies on extracting data from the page HTML. If Google changes their page structure, the parser may need updating. The "Paste Names" tab is a reliable fallback.
- Resy and OpenTable APIs are unofficial/public-facing. Rate limiting may apply.
- All availability checks run concurrently (max 5 at a time) for speed.
