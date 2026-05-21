# `anonymize.py` — Usage Guide

A standalone how-to for the CLI. See `README.md` for a one-paragraph
project overview.

---

## Quick start

```powershell
# Anonymize a CSV file
python anonymize.py --mapping examples\mapping.json --input examples\sample.csv --output examples\out\sample.anon.csv
```

Open `examples\out\sample.anon.csv` to see the result.

---

## Command-line interface

```
python anonymize.py --mapping <PATH> --input <PATH> --output <PATH> [--dry-run] [--verbose]
```

| Flag | Required? | Meaning |
|------|-----------|---------|
| `--mapping <path>` | yes | Path to the mapping JSON. |
| `--input <path>` | yes | Source file. Must exist and have one of the supported extensions. |
| `--output <path>` | yes (unless `--dry-run`) | Destination file. Parent directory is created automatically. |
| `--dry-run` | no | Print per-rule and per-`find` replacement counts to stdout. No output file is written. |
| `-v`, `--verbose` | no | Log progress (one line per `find` entry) to stderr. |
| `-h`, `--help` | no | Show the auto-generated help text and exit. |

### Supported input extensions

`.json`, `.txt`, `.md`, `.csv` — all treated as UTF-8 text. The tool
does not parse JSON or CSV structurally; it just does deterministic
string replacement.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success. |
| `1` | Unexpected internal error. |
| `2` | Invalid CLI usage, missing input file, or unsupported extension. |
| `3` | Mapping file missing, unreadable, or fails schema validation. |
| `4` | Input file is not valid UTF-8. |

---

## Mapping file format

The mapping is a JSON object with one required key, `replacements`, and
one optional `options` object.

```json
{
  "replacements": [
    {
      "find": ["Anna Nowak", "A. Nowak", "NOWAK, Anna"],
      "replace": "PERSON_A"
    },
    {
      "find": ["anna@firma.test", "contact@firma.test"],
      "replace": "EMAIL_A"
    },
    {
      "find": ["+48 500 100 200", "500-100-200"],
      "replace": "PHONE_A"
    }
  ],
  "options": {
    "case_sensitive": false
  }
}
```

### Per-rule schema

- `find` — JSON array of **one or more non-empty strings**. Every
  string in the array is replaced by the same `replace` token.
- `replace` — single string. May be empty (treated as full redaction).

### Options

- `options.case_sensitive` — boolean. Default `false`
  (case-insensitive matching). When `true`, matching is exact.

### What the validator rejects

A mapping fails validation (exit code 3, message printed to stderr) if:

- the root is not a JSON object;
- `replacements` is missing or empty;
- a rule is not an object;
- a rule is missing `find` or `replace`;
- `find` is not an array, or is empty, or contains a non-string or an
  empty string;
- `replace` is not a string;
- `options.case_sensitive` is not a boolean.

---

## Replacement policy and edge cases

The engine is intentionally simple and deterministic:

1. **Rules run in array order.** Rule `0` rewrites the text, then rule
   `1` sees the rewritten text, and so on. Choose token names like
   `PERSON_A` that don't accidentally match a later rule's `find`
   entry.
2. **Within a rule, `find` entries also run in array order.** Each
   entry triggers a single left-to-right, non-overlapping pass over
   the current text.
3. **Overlap policy.** If two `find` entries in the same rule could
   overlap on the same substring (e.g. `"abc"` and `"bcd"` in
   `"abcd"`), the earlier entry wins, because it runs first and
   consumes its match. Re-order entries if you want a different
   precedence.
4. **`replace` is treated literally.** Regex back-references such as
   `\1` or `\g<name>` inside `replace` are **not** expanded — the
   string is inserted exactly as written.
5. **Case sensitivity.** When `options.case_sensitive` is `false`
   (the default), matching uses `re.IGNORECASE`, so `Anna`, `ANNA`,
   and `anna` all match a `find` of `Anna`. The replacement token is
   inserted with its original casing from the mapping.

---

## Encoding

- Input is read as **strict UTF-8**. If the file contains bytes that
  are not valid UTF-8, the tool exits with code `4` and prints the
  offending byte offset on stderr — it does not silently re-decode
  with another codec.
- Output is written as **UTF-8** with the source string's line
  endings preserved.

---

## Worked examples

These four runs against the supplied fixtures show what every
extension looks like before and after.

### Markdown — `examples/sample.md`

**Before:**

```markdown
# Weekly note

Contact **Anna Nowak** for access.

- Email: anna@firma.test
- Phone: +48 500 100 200
```

**After (`examples/out/sample.anon.md`):**

```markdown
# Weekly note

Contact **PERSON_A** for access.

- Email: EMAIL_A
- Phone: PHONE_A
```

### CSV — `examples/sample.csv`

**Before:**

```csv
id,name,email,phone
1,Anna Nowak,anna@firma.test,+48 500 100 200
2,A. Nowak,contact@firma.test,500-100-200
```

**After (`examples/out/sample.anon.csv`):**

```csv
id,name,email,phone
1,PERSON_A,EMAIL_A,PHONE_A
2,PERSON_A,EMAIL_A,PHONE_A
```

### JSON — `examples/sample.json`

**Before:**

```json
{
  "project": "Demo",
  "owner": "Anna Nowak",
  "contact": "anna@firma.test",
  "meta": { "phone": "+48 500 100 200" }
}
```

**After (`examples/out/sample.anon.json`):**

```json
{
  "project": "Demo",
  "owner": "PERSON_A",
  "contact": "EMAIL_A",
  "meta": { "phone": "PHONE_A" }
}
```

### Plain text — `examples/sample.txt`

**Before:**

```
Line 1: Owner A. Nowak
Line 2: Also: NOWAK, Anna
Line 3: Email contact@firma.test
Line 4: Alt phone 500-100-200
```

**After (`examples/out/sample.anon.txt`):**

```
Line 1: Owner PERSON_A
Line 2: Also: PERSON_A
Line 3: Email EMAIL_A
Line 4: Alt phone PHONE_A
```

---

## Dry-run

`--dry-run` reports counts to stdout and writes nothing:

```powershell
python anonymize.py --mapping examples\mapping.json --input examples\sample.txt --dry-run
```

Output:

```
DRY RUN -- no output file written (would have written to <unset>).
rule #0 -> 'PERSON_A': 2 replacement(s)
    'Anna Nowak': 0
    'A. Nowak': 1
    'NOWAK, Anna': 1
rule #1 -> 'EMAIL_A': 1 replacement(s)
    'anna@firma.test': 0
    'contact@firma.test': 1
rule #2 -> 'PHONE_A': 1 replacement(s)
    '+48 500 100 200': 0
    '500-100-200': 1
total: 4 replacement(s)
```

> The `0` next to some entries is **not** an error — it just means that
> particular spelling variant from the mapping does not appear in this
> file. The mapping defines several variants per rule so the same
> mapping works across all sample files.

---

## Verbose logs

`--verbose` (or `-v`) enables `INFO`-level logging to stderr:

```powershell
python anonymize.py --mapping examples\mapping.json --input examples\sample.md --output examples\out\sample.anon.md --verbose
```

Stderr trace:

```
INFO anonymize: loaded 3 rule(s), case_sensitive=False
INFO anonymize: read 101 character(s) from examples\sample.md
INFO anonymize: rule[0] find='Anna Nowak' replace='PERSON_A' -> 1 replacement(s)
INFO anonymize: rule[0] find='A. Nowak' replace='PERSON_A' -> 0 replacement(s)
...
wrote 83 character(s), 3 replacement(s) -> examples\out\sample.anon.md
```

`INFO` is a normal log level — these lines are **not** errors.

---

## Error scenarios

| What you do | What happens |
|-------------|--------------|
| Pass a mapping with `"find": []` | Exit 3, `error: Mapping rule #0: 'find' must be a non-empty array of non-empty strings` |
| Pass a mapping with a non-string `replace` | Exit 3, `error: Mapping rule #N: 'replace' must be a string` |
| Pass a non-existent `--input` | Exit 2, `error: Input file not found: <path>` |
| Pass an unsupported extension (e.g. `.bin`) | Exit 2, `error: Unsupported input extension '.bin'. Expected one of: ['.csv', '.json', '.md', '.txt']` |
| Pass a file containing non-UTF-8 bytes | Exit 4, `error: Input file is not valid UTF-8 at byte offset N: <path> (...)` |
| Omit `--output` without `--dry-run` | Exit 2, `anonymize.py: error: --output is required unless --dry-run is set` |

All errors are written to stderr, leaving stdout clean.
