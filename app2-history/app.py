"""App #2 - History Downloader / Viewer.

Flask backend that:
  - serves the history page (index.html)
  - proxies GET /api/tickers      -> upstream /api/tickers
  - proxies GET /api/latest       -> upstream /api/latest (with the API key
                                     attached server-side)
  - (added in next commit) /export?format=csv|json downloads the accumulated
    window as a file.

Polling and the table/chart UI live entirely on the client; this commit only
gives the page a working ticker list and a way to fetch the latest tick.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

UPSTREAM = "https://add.piotrkojalowicz.dev"
API_KEY = os.environ.get("ADD_API_KEY")

app = Flask(__name__)


def _headers():
    if not API_KEY:
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


@app.route("/api/latest")
def latest():
    selected = request.args.getlist("ticker")
    if not selected:
        return ("ticker query param required", 400)
    params = [("ticker", t) for t in selected]
    r = requests.get(
        f"{UPSTREAM}/api/latest", params=params, headers=_headers(), timeout=10
    )
    r.raise_for_status()
    return jsonify(r.json())


if __name__ == "__main__":
    # Different port from App #1 so both can run at the same time.
    app.run(host="127.0.0.1", port=5001, debug=True)
