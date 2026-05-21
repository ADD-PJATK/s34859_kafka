# s34859_anonymize

A small command-line tool that reads a JSON **mapping file** and a UTF-8
**source file** (`.json`, `.txt`, `.md`, or `.csv`) and writes an
anonymized copy. All replacements are deterministic and based solely on
the mapping you load from disk — the tool makes **no network calls** and
uses **no AI / LLM services** at runtime.

```powershell
python anonymize.py --mapping examples\mapping.json --input examples\sample.csv --output examples\out\sample.anon.csv
```

For complete documentation — flags, mapping schema, replacement policy,
encoding rules, before/after examples, dry-run, verbose logs, and the
full error-scenario table — see **[USAGE.md](USAGE.md)**.

---

## Prerequisites

- **Python 3.9 or newer** (developed and tested on Python 3.13.5).
- No third-party packages. Only the Python standard library
  (`argparse`, `json`, `re`, `logging`, `pathlib`, `dataclasses`).
- Tested on Windows 11 with PowerShell. Works unchanged on macOS and
  Linux.

```powershell
python --version
```

---

## Installation

```powershell
git clone https://github.com/ADD-PJATK/s34859_anonymize.git
cd s34859_anonymize
```

There is nothing else to install.

---

## Project layout

```
s34859_anonymize/
├── anonymize.py            # the CLI tool (stdlib only)
├── README.md               # this file
├── USAGE.md                # full usage documentation
├── ACCEPTANCE.md           # assignment grading rubric (unmodified)
├── CHAT_HISTORY.md         # chronological record of this build session
├── .gitignore
├── examples/
│   ├── mapping.json        # sample mapping
│   ├── sample.csv          # sample inputs (one per supported extension)
│   ├── sample.json
│   ├── sample.md
│   ├── sample.txt
│   └── out/                # anonymized outputs produced by the tool
│       ├── sample.anon.csv
│       ├── sample.anon.json
│       ├── sample.anon.md
│       └── sample.anon.txt
└── screenshots/
    └── run_log.txt         # captured terminal session (before/after evidence)
```

---

## Privacy and dependencies

- No HTTP / HTTPS calls.
- No LLM / AI inference, local or remote.
- No file contents are sent anywhere.
- Standard-library imports only.

The example data is fictional.
