"""End-to-end pipeline: tick export -> anonymizer -> out/.

Reads the JSON file produced by ``mock/client-dashboard/client.py`` (a
list of tick dicts), serializes it to a text format the AA1 anonymizer
can process (UTF-8 JSON), invokes ``anonymizer/anonymize.py`` with the
project mapping, and writes the anonymized payload to ``out/``.

The output preserves the same JSON shape as the input — only the
sensitive string values (trader_email, operator_name, references inside
comment) are replaced according to the mapping.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ANONYMIZER = REPO_ROOT / "anonymizer" / "anonymize.py"

# INTENTIONAL BUG: this path is resolved against the *current working
# directory*, not against REPO_ROOT. The pipeline therefore only finds
# the mapping when it is invoked from the repo root. Running it from
# scripts/ or integration/pipeline/ fails with "Mapping file not found".
DEFAULT_MAPPING = Path("mock/fixtures/mapping.json")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Anonymize an exported tick file")
    p.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the tick export (JSON list produced by client.py)",
    )
    p.add_argument(
        "--mapping",
        type=Path,
        default=DEFAULT_MAPPING,
        help="Path to the anonymizer mapping JSON",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "integration" / "out",
        help="Directory where the anonymized JSON is written",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 2
    if not args.mapping.exists():
        print(f"error: mapping file not found: {args.mapping}", file=sys.stderr)
        return 2

    # Stage 1: copy the raw export into a staging file that the
    # anonymizer can read. We use .json so the anonymizer's extension
    # check accepts it; the anonymizer does NOT structurally parse JSON,
    # it just does deterministic string replacement on UTF-8 text.
    stage_dir = args.out_dir
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_file = stage_dir / "ticks.stage.json"
    out_file = stage_dir / "ticks.anon.json"

    # Re-serialize so we get stable, pretty formatting regardless of
    # what the client wrote.
    ticks = json.loads(args.input.read_text(encoding="utf-8"))
    stage_file.write_text(
        json.dumps(ticks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Stage 2: invoke the AA1 anonymizer as a subprocess.
    cmd = [
        sys.executable,
        str(ANONYMIZER),
        "--mapping", str(args.mapping),
        "--input", str(stage_file),
        "--output", str(out_file),
        "--verbose",
    ]
    print("running:", " ".join(cmd), file=sys.stderr)
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"error: anonymizer exited with code {rc}", file=sys.stderr)
        return rc

    print(f"anonymized output -> {out_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
