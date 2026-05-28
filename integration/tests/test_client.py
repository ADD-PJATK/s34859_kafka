"""Tests the client's SSE consumer can round-trip ticks from the mock server."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT = REPO_ROOT / "mock" / "client-dashboard" / "client.py"


def test_client_collects_ticks_to_json(mock_server, tmp_path):
    """Run the client as a subprocess and confirm it writes a valid JSON list."""
    out = tmp_path / "ticks.json"
    rc = subprocess.call(
        [
            sys.executable,
            str(CLIENT),
            "--server", mock_server,
            "--tickers", "ACME,GLOBEX",
            "--buffer", "4",
            "--out", str(out),
            "--format", "json",
        ],
        timeout=30,
    )
    assert rc == 0, "client should exit 0 after collecting --buffer ticks"
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 4
    for tick in data:
        # Every record must have the full sensitive payload the
        # downstream anonymizer expects to scrub.
        assert tick["ticker"] in {"ACME", "GLOBEX"}
        assert "trader_email" in tick
        assert "operator_name" in tick
        assert "comment" in tick
