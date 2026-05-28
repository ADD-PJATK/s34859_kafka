"""Mock client / CLI consumer.

Connects to the mock SSE stream, buffers the last N ticks, and exports
the buffer to JSON or CSV.

Usage:
    python client.py --tickers ACME,GLOBEX --buffer 8 --out out/ticks.json
    python client.py --tickers ACME --buffer 5 --out out/ticks.csv --format csv

By default the client stops after the buffer is full. Use --duration to
keep reading for N seconds instead (still capped by the buffer size).

This is the consumer side that the integration pipeline feeds into. It
is intentionally minimal — it is meant to be reproducible and easy to
test, not pretty.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import deque
from pathlib import Path

import requests

DEFAULT_SERVER = "http://127.0.0.1:5050"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mock SSE consumer / exporter")
    p.add_argument("--server", default=DEFAULT_SERVER, help="Base URL of the mock server")
    p.add_argument(
        "--tickers",
        required=True,
        help="Comma-separated list of ticker symbols (e.g. ACME,GLOBEX)",
    )
    p.add_argument(
        "--buffer",
        type=int,
        default=10,
        help="Number of most recent ticks to keep in the rolling buffer",
    )
    p.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="If > 0, read for this many seconds instead of stopping when buffer is full",
    )
    p.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output file path (.json or .csv depending on --format)",
    )
    p.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format",
    )
    return p.parse_args(argv)


def stream_ticks(server: str, symbols: list[str]):
    """Yield decoded tick dicts from the mock SSE stream.

    NOTE: This is a hand-rolled SSE consumer (no sseclient dep). The
    server emits frames of the form:

        event: tick
        data: {"ticker":...}
        <blank line>

    so we iterate lines and decode every non-empty payload as JSON.
    """
    params = [("ticker", s) for s in symbols]
    with requests.get(
        f"{server}/api/stream",
        params=params,
        stream=True,
        timeout=(5, None),
        headers={"Accept": "text/event-stream"},
    ) as resp:
        resp.raise_for_status()
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            # INTENTIONAL BUG: this strips an optional "data: " prefix and
            # then assumes whatever's left is JSON. SSE control lines like
            # "event: tick" pass through unchanged and crash json.loads.
            payload = raw.split("data: ", 1)[-1]
            yield json.loads(payload)


def export_json(ticks: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ticks, ensure_ascii=False, indent=2), encoding="utf-8")


def export_csv(ticks: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["ticker", "price", "ts", "trader_email", "operator_name", "comment"]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for t in ticks:
            w.writerow({k: t.get(k, "") for k in fields})


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    symbols = [s.strip() for s in args.tickers.split(",") if s.strip()]
    if not symbols:
        print("error: --tickers must list at least one symbol", file=sys.stderr)
        return 2

    buf: deque[dict] = deque(maxlen=args.buffer)
    started = time.monotonic()

    for tick in stream_ticks(args.server, symbols):
        buf.append(tick)
        if args.duration > 0:
            if time.monotonic() - started >= args.duration:
                break
        else:
            if len(buf) >= args.buffer:
                break

    ticks = list(buf)
    if args.format == "json":
        export_json(ticks, args.out)
    else:
        export_csv(ticks, args.out)

    print(f"wrote {len(ticks)} tick(s) -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
