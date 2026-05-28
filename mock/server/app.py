"""Mock stock-feed server (offline substitute for the instructor API).

Endpoints:
  GET /api/tickers                -> list of synthetic tickers
  GET /api/latest?ticker=SYMBOL   -> most recent fixture tick for a symbol
  GET /api/stream?ticker=SYMBOL   -> SSE stream of synthetic ticks for one
                                     or more symbols (repeat the query
                                     param: ?ticker=ACME&ticker=GLOBEX)

The stream emits standards-compliant SSE frames:

    event: tick
    data: {"ticker":"ACME","price":142.55,...}
    \n

(blank line terminates each frame). A keep-alive comment line ":\n\n" is
written every ~5s of idle so proxies do not close the connection.

No external network. All data is read from ../fixtures/*.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, stream_with_context

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"

app = Flask(__name__)


def _load_tickers() -> dict:
    return json.loads((FIXTURES / "tickers.json").read_text(encoding="utf-8"))


def _load_ticks() -> list[dict]:
    payload = json.loads((FIXTURES / "ticks.json").read_text(encoding="utf-8"))
    return payload["ticks"]


@app.route("/api/health")
def health():
    return jsonify({"ok": True})


@app.route("/api/tickers")
def tickers():
    return jsonify(_load_tickers())


@app.route("/api/latest")
def latest():
    symbol = request.args.get("ticker")
    if not symbol:
        return ("ticker query param required", 400)
    matches = [t for t in _load_ticks() if t["ticker"].upper() == symbol.upper()]
    if not matches:
        return (f"no ticks for ticker {symbol!r}", 404)
    return jsonify(matches[-1])


@app.route("/api/stream")
def stream():
    selected = [s.upper() for s in request.args.getlist("ticker")]
    if not selected:
        return ("ticker query param required", 400)

    pool = [t for t in _load_ticks() if t["ticker"].upper() in selected]
    if not pool:
        return (f"no ticks for selected tickers: {selected}", 404)

    def emit():
        # Cycle through the fixture ticks forever, with a small delay
        # between frames, so the consumer sees a continuous SSE stream.
        idx = 0
        while True:
            tick = pool[idx % len(pool)]
            payload = json.dumps(tick, ensure_ascii=False)
            yield f"event: tick\n"
            yield f"data: {payload}\n\n"
            idx += 1
            time.sleep(0.2)

    return Response(
        stream_with_context(emit()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    # threaded=True so the SSE generator doesn't block other requests
    # (health probe, /api/tickers) while a stream is open.
    app.run(host="127.0.0.1", port=5050, threaded=True)
