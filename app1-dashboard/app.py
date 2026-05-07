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
import sseclient
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

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


@app.route("/api/stream")
def stream():
    """Proxy upstream SSE to the browser.

    Opens a streaming GET against /api/stream upstream (with the API key
    attached) and re-emits every "tick" event verbatim to the browser. The
    browser's EventSource therefore never sees the API key.
    """
    selected = request.args.getlist("ticker")
    if not selected:
        return ("ticker query param required", 400)

    upstream_params = [("ticker", t) for t in selected]
    upstream_resp = requests.get(
        f"{UPSTREAM}/api/stream",
        params=upstream_params,
        headers=_headers(),
        stream=True,
        timeout=(10, None),  # connect timeout 10s, no read timeout
    )

    def relay():
        client = sseclient.SSEClient(upstream_resp)
        try:
            for ev in client.events():
                # Re-emit as SSE. EventSource on the browser will dispatch
                # this with the matching event name (e.g. "tick").
                if ev.event:
                    yield f"event: {ev.event}\n"
                yield f"data: {ev.data}\n\n"
        finally:
            upstream_resp.close()

    return Response(
        stream_with_context(relay()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    # threaded=True is needed once we add the SSE endpoint, so the streaming
    # request doesn't block the rest of the server.
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
