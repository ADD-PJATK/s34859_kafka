"""Local data anonymizer: deterministic string substitution for text files.

Loads a JSON mapping of replacement rules and applies them to a UTF-8
source file (.json / .txt / .md / .csv), writing an anonymized copy to
a new path. Pure stdlib, no network, no AI.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_MAPPING = 3
EXIT_ENCODING = 4
EXIT_UNEXPECTED = 1

SUPPORTED_EXTENSIONS = {".json", ".txt", ".md", ".csv"}

log = logging.getLogger("anonymize")


@dataclass(frozen=True)
class Rule:
    find: tuple[str, ...]
    replace: str


@dataclass(frozen=True)
class Mapping:
    rules: tuple[Rule, ...]
    case_sensitive: bool


@dataclass(frozen=True)
class RuleStat:
    rule_index: int
    find_entry: str
    replace: str
    count: int


class MappingError(Exception):
    """Raised when the mapping file is missing, unreadable, or fails schema validation."""


class Utf8Error(Exception):
    """Raised when an input file is not valid UTF-8."""


def load_mapping(path: Path) -> Mapping:
    """Read and validate a mapping JSON file. Raises MappingError on any problem."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MappingError(f"Mapping file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise MappingError(f"Mapping file is not valid UTF-8: {path}") from exc

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise MappingError(f"Mapping is not valid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})") from exc

    if not isinstance(raw, dict):
        raise MappingError("Mapping root must be a JSON object")

    if "replacements" not in raw:
        raise MappingError("Mapping is missing required key 'replacements'")

    replacements = raw["replacements"]
    if not isinstance(replacements, list) or not replacements:
        raise MappingError("Mapping 'replacements' must be a non-empty array")

    rules: list[Rule] = []
    for idx, rule in enumerate(replacements):
        if not isinstance(rule, dict):
            raise MappingError(f"Mapping rule #{idx}: must be an object")
        if "find" not in rule:
            raise MappingError(f"Mapping rule #{idx}: missing 'find'")
        if "replace" not in rule:
            raise MappingError(f"Mapping rule #{idx}: missing 'replace'")

        find = rule["find"]
        if not isinstance(find, list) or not find:
            raise MappingError(
                f"Mapping rule #{idx}: 'find' must be a non-empty array of non-empty strings"
            )
        for j, entry in enumerate(find):
            if not isinstance(entry, str) or entry == "":
                raise MappingError(
                    f"Mapping rule #{idx}: 'find[{j}]' must be a non-empty string"
                )

        replace = rule["replace"]
        if not isinstance(replace, str):
            raise MappingError(f"Mapping rule #{idx}: 'replace' must be a string")

        rules.append(Rule(find=tuple(find), replace=replace))

    options = raw.get("options", {})
    if not isinstance(options, dict):
        raise MappingError("Mapping 'options' must be an object")
    case_sensitive = options.get("case_sensitive", False)
    if not isinstance(case_sensitive, bool):
        raise MappingError("Mapping options.case_sensitive must be a boolean")

    return Mapping(rules=tuple(rules), case_sensitive=case_sensitive)


def read_text_utf8(path: Path) -> str:
    """Read a file as strict UTF-8. Raises Utf8Error on bad bytes, FileNotFoundError if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise Utf8Error(
            f"Input file is not valid UTF-8 at byte offset {exc.start}: {path} ({exc.reason})"
        ) from exc


def write_text_utf8(path: Path, content: str) -> None:
    """Write UTF-8 text. Creates parent directory if missing. Preserves source newlines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(content)


def apply_rules(
    text: str, mapping: Mapping
) -> tuple[str, list[RuleStat]]:
    """Apply the mapping to the text and return the new text + per-find stats.

    Policy: rules are processed in array order. Within each rule, each `find`
    entry is processed in array order, doing a left-to-right non-overlapping
    pass. The `replace` string is inserted literally (no regex backref
    expansion). `options.case_sensitive` toggles re.IGNORECASE.
    """
    flags = 0 if mapping.case_sensitive else re.IGNORECASE
    stats: list[RuleStat] = []
    current = text
    for rule_index, rule in enumerate(mapping.rules):
        # Pre-bind the literal replacement so re.sub does not interpret
        # backrefs like \1 or \g<name>.
        literal_replace = rule.replace

        def _literal(_m, _r=literal_replace):
            return _r

        for find_entry in rule.find:
            pattern = re.compile(re.escape(find_entry), flags)
            new_text, count = pattern.subn(_literal, current)
            current = new_text
            stats.append(
                RuleStat(
                    rule_index=rule_index,
                    find_entry=find_entry,
                    replace=rule.replace,
                    count=count,
                )
            )
            log.info(
                "rule[%d] find=%r replace=%r -> %d replacement(s)",
                rule_index, find_entry, rule.replace, count,
            )
    return current, stats


def print_stats(stats: list[RuleStat], stream) -> None:
    """Human-readable per-rule replacement summary."""
    by_rule: dict[int, list[RuleStat]] = {}
    for s in stats:
        by_rule.setdefault(s.rule_index, []).append(s)
    total = 0
    for rule_index in sorted(by_rule):
        rule_total = sum(s.count for s in by_rule[rule_index])
        total += rule_total
        replace_value = by_rule[rule_index][0].replace
        print(f"rule #{rule_index} -> {replace_value!r}: {rule_total} replacement(s)", file=stream)
        for s in by_rule[rule_index]:
            print(f"    {s.find_entry!r}: {s.count}", file=stream)
    print(f"total: {total} replacement(s)", file=stream)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="anonymize.py",
        description=(
            "Apply deterministic string replacements from a JSON mapping "
            "to a UTF-8 text file (.json/.txt/.md/.csv)."
        ),
    )
    parser.add_argument(
        "--mapping",
        required=True,
        type=Path,
        help="Path to mapping JSON (schema: {replacements:[{find:[...],replace:'...'}], options:{case_sensitive:bool}}).",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Source file (.json, .txt, .md, or .csv). Read as UTF-8.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination file. Parent directory is created if missing. Required unless --dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report replacement counts to stdout without writing the output file.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Log progress to stderr.",
    )
    args = parser.parse_args(argv)
    if not args.dry_run and args.output is None:
        parser.error("--output is required unless --dry-run is set")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        mapping = load_mapping(args.mapping)
    except MappingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_MAPPING

    if not args.input.exists():
        print(f"error: Input file not found: {args.input}", file=sys.stderr)
        return EXIT_USAGE

    ext = args.input.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(
            f"error: Unsupported input extension {ext!r}. "
            f"Expected one of: {sorted(SUPPORTED_EXTENSIONS)}",
            file=sys.stderr,
        )
        return EXIT_USAGE

    log.info("loaded %d rule(s), case_sensitive=%s", len(mapping.rules), mapping.case_sensitive)

    try:
        source = read_text_utf8(args.input)
    except Utf8Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ENCODING

    log.info("read %d character(s) from %s", len(source), args.input)
    anonymized, stats = apply_rules(source, mapping)

    if args.dry_run:
        print(f"DRY RUN -- no output file written (would have written to {args.output or '<unset>'}).")
        print_stats(stats, sys.stdout)
        return EXIT_OK

    write_text_utf8(args.output, anonymized)
    total = sum(s.count for s in stats)
    print(f"wrote {len(anonymized)} character(s), {total} replacement(s) -> {args.output}", file=sys.stderr)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
