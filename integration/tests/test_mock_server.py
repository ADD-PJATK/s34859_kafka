"""Smoke tests for the mock server's three endpoints."""

from __future__ import annotations

import json

import requests


def test_tickers_endpoint_returns_synthetic_list(mock_server):
    r = requests.get(f"{mock_server}/api/tickers", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert "tickers" in body
    symbols = {t["symbol"] for t in body["tickers"]}
    assert {"ACME", "GLOBEX", "INITECH"}.issubset(symbols)


def test_latest_endpoint_returns_a_tick(mock_server):
    r = requests.get(f"{mock_server}/api/latest", params={"ticker": "ACME"}, timeout=5)
    assert r.status_code == 200
    tick = r.json()
    assert tick["ticker"] == "ACME"
    assert isinstance(tick["price"], (int, float))
    # Sensitive fields must be present in the fixture (they get
    # anonymized downstream).
    assert "trader_email" in tick
    assert "operator_name" in tick
    assert "comment" in tick


def test_latest_endpoint_requires_ticker(mock_server):
    r = requests.get(f"{mock_server}/api/latest", timeout=5)
    assert r.status_code == 400


def test_stream_endpoint_emits_at_least_two_tick_frames(mock_server):
    """Read a few raw SSE lines and confirm we get 'event: tick' + 'data: {json}' pairs."""
    with requests.get(
        f"{mock_server}/api/stream",
        params={"ticker": "ACME"},
        stream=True,
        timeout=(5, 10),
        headers={"Accept": "text/event-stream"},
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("Content-Type", "")

        seen_events = 0
        last_data: dict | None = None
        for raw in resp.iter_lines(decode_unicode=True):
            if raw is None:
                continue
            if raw.startswith("event: tick"):
                seen_events += 1
            elif raw.startswith("data: "):
                last_data = json.loads(raw[len("data: "):])
            if seen_events >= 2 and last_data is not None:
                break

    assert seen_events >= 2
    assert last_data is not None
    assert last_data["ticker"] == "ACME"
