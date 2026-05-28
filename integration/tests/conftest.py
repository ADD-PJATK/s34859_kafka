"""Pytest fixtures: spin up the mock server as a subprocess for tests.

The server is launched once per pytest session on 127.0.0.1:5050 and
torn down at the end. We wait for /api/health to respond before yielding
to test cases — no fixed sleep.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_DIR = REPO_ROOT / "mock" / "server"
SERVER_URL = "http://127.0.0.1:5050"
HEALTH_URL = f"{SERVER_URL}/api/health"


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_health(timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = requests.get(HEALTH_URL, timeout=1.0)
            if r.status_code == 200 and r.json().get("ok") is True:
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.2)
    raise RuntimeError(
        f"mock server did not become healthy within {timeout}s "
        f"(last error: {last_err!r})"
    )


@pytest.fixture(scope="session")
def mock_server():
    """Start the Flask mock server on port 5050 for the test session."""
    if _port_open("127.0.0.1", 5050):
        # Someone is already running it — use it as-is.
        yield SERVER_URL
        return

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(SERVER_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_health()
        yield SERVER_URL
    finally:
        if proc.poll() is None:
            try:
                if sys.platform == "win32":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                else:
                    proc.terminate()
            except Exception:  # noqa: BLE001
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
