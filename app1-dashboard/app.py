"""App #1 - Realtime Dashboard.

Flask backend that:
  - serves the dashboard page (index.html)
  - proxies GET /api/tickers   -> upstream /api/tickers
  - (added in next commit) proxies GET /api/stream as Server-Sent Events.

The upstream API key (ADD_API_KEY) is read from a local .env file via
python-dotenv and attached as the X-API-Key header. It never leaves the
server, so the browser never sees it.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

# Load .env from the repo root (one level up from this file's folder) so the
# same .env can serve both apps.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

UPSTREAM = "https://add.piotrkojalowicz.dev"
API_KEY = os.environ.get("ADD_API_KEY")

app = Flask(__name__)


def _headers():
    if not API_KEY:
        # Fail fast with a clear message rather than letting upstream 401 us.
        raise RuntimeError(
            "ADD_API_KEY is not set. Copy .env.example to .env and paste your key."
        )
    return {"X-API-Key": API_KEY}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tickers")
def tickers():
    r = requests.get(f"{UPSTREAM}/api/tickers", headers=_headers(), timeout=10)
    r.raise_for_status()
    return jsonify(r.json())


if __name__ == "__main__":
    # threaded=True is needed once we add the SSE endpoint, so the streaming
    # request doesn't block the rest of the server.
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
