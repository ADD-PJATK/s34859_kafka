"""End-to-end pipeline test.

Drives the client to fetch ticks, runs the pipeline to anonymize them,
and asserts the anonymized output:

  1. exists,
  2. does not contain any original sensitive strings,
  3. has the trader_email field replaced by a PERSON_* placeholder.

The pipeline is invoked from a tmp directory with an explicit --input
so the run is reproducible regardless of where pytest is launched.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT = REPO_ROOT / "mock" / "client-dashboard" / "client.py"
PIPELINE = REPO_ROOT / "integration" / "pipeline" / "run_pipeline.py"

SENSITIVE_STRINGS = [
    "Anna Kowalska",
    "Marek Nowak",
    "Olek Zielinski",
    "anna.kowalska@brokerage.test",
    "marek.nowak@brokerage.test",
    "olek.zielinski@brokerage.test",
]


def _run_client(mock_server: str, out: Path, buffer: int = 6) -> None:
    rc = subprocess.call(
        [
            sys.executable,
            str(CLIENT),
            "--server", mock_server,
            "--tickers", "ACME,GLOBEX,INITECH",
            "--buffer", str(buffer),
            "--out", str(out),
            "--format", "json",
        ],
        timeout=30,
    )
    assert rc == 0, "client subprocess should exit 0"


def _run_pipeline(input_path: Path, out_dir: Path, cwd: Path) -> Path:
    rc = subprocess.call(
        [
            sys.executable,
            str(PIPELINE),
            "--input", str(input_path),
            "--out-dir", str(out_dir),
        ],
        cwd=str(cwd),
        timeout=60,
    )
    assert rc == 0, f"pipeline subprocess exited with {rc}"
    return out_dir / "ticks.anon.json"


def test_pipeline_anonymizes_sensitive_fields(mock_server, tmp_path):
    raw = tmp_path / "ticks.raw.json"
    out_dir = tmp_path / "out"
    _run_client(mock_server, raw, buffer=6)

    # Invoke the pipeline from a neutral cwd (NOT the repo root) so that
    # we catch any path bugs in the pipeline itself.
    anon = _run_pipeline(raw, out_dir, cwd=tmp_path)

    assert anon.exists(), "anonymized output file should exist"
    anon_text = anon.read_text(encoding="utf-8")

    # 1. None of the raw sensitive strings should appear anywhere in the
    #    anonymized output.
    for needle in SENSITIVE_STRINGS:
        assert needle not in anon_text, (
            f"sensitive string {needle!r} still present in anonymized output"
        )

    # 2. Every tick's email field should be a placeholder token.
    ticks = json.loads(anon_text)
    assert isinstance(ticks, list) and ticks, "expected a non-empty list of ticks"
    for tick in ticks:
        email = tick["email"]
        assert email.startswith("PERSON_"), (
            f"email field should be a PERSON_* placeholder, got {email!r}"
        )
