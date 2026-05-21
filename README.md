# s34859_kafka — ADD Phase 2 Submission

**Student:** s34859 — William Baaklini
**Course:** Analysis of Large Data Sets (ADD), PJATK

This single repository holds all Phase 2 deliverables on `main`:

- **AA1** — Local Data Anonymizer (CLI, stdlib-only, no AI/HTTP at runtime).
- **AA2** — Real-time Stock Data: two Flask/SSE apps consuming the instructor's
  HTTP/SSE facade in front of a Kafka broker at **`https://add.piotrkojalowicz.dev`**.
- **AA3** — Unified repository (this layout + working anonymizer).
- **AA4** — AI-Assisted Work Plan document.

---

## Repo map

| Path | What it is |
|---|---|
| [`anonymizer/`](anonymizer/) | **AA1** — anonymizer CLI, sample mapping, sample inputs/outputs, screenshots, AA1 build chat. |
| [`app1-dashboard/`](app1-dashboard/) | **AA2 App #1** — realtime dashboard (SSE proxy + Chart.js client). |
| [`app2-history/`](app2-history/) | **AA2 App #2** — history downloader / viewer (10 s polling, CSV/JSON export). |
| [`screenshots/`](screenshots/) | AA2 screenshots (App #1 and App #2). |
| [`documentation/ai-work-plan.md`](documentation/ai-work-plan.md) | **AA4** — AI-Assisted Work Plan. |
| [`consolidation/CONSOLIDATION.md`](consolidation/CONSOLIDATION.md) | **AA3** — note explaining the merge of `s34859_anonymize` into this repo. |
| [`consolidation/AA3_PLAN.md`](consolidation/AA3_PLAN.md) | Plan-mode plan for the AA3 merge (transparency). |
| [`chat-transcript.md`](chat-transcript.md) | AA2 Claude Code session transcript. |
| `scripts/` | Helper that produced `chat-transcript.md`. |

---

## Quick start

### AA1 — Anonymizer

Pure Python 3.9+, **no third-party packages**, **no network / LLM at runtime**.

```powershell
cd anonymizer
python anonymize.py --mapping examples\mapping.json --input examples\sample.csv --output examples\out\sample.anon.csv
```

Supports `.json`, `.txt`, `.md`, `.csv`. Full usage / flags / error table in
[`anonymizer/USAGE.md`](anonymizer/USAGE.md). The committed
`anonymizer/examples/out/sample.anon.*` files are the expected outputs.

### AA2 — Both Flask apps

Both apps read `ADD_API_KEY` from a shared `.env` at the **repo root**. Create
it once:

```powershell
Copy-Item .env.example .env
notepad .env   # paste your key in place of "paste_your_key_here"
```

Get a key at <https://add.piotrkojalowicz.dev/> (class password held by the
instructor). `.env` is gitignored — the key is never committed.

**App #1 — Realtime dashboard** (port 5000):

```powershell
cd app1-dashboard
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>. Full instructions in
[`app1-dashboard/README.md`](app1-dashboard/README.md).

**App #2 — History downloader** (port 5001, so both apps can run together):

```powershell
cd app2-history
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5001>. Full instructions in
[`app2-history/README.md`](app2-history/README.md).

### AA4 — Work plan

See [`documentation/ai-work-plan.md`](documentation/ai-work-plan.md).

---

## Screenshots

In [`screenshots/`](screenshots/):

- `app1-dashboard.png` — App #1 with live updates for ≥2 tickers and the chart.
- `app2-history-table.png` — App #2 showing the populated table for a chosen range.
- `app2-history-download.png` — a downloaded CSV with real rows.

Anonymizer screenshots and a captured terminal run-log live in
[`anonymizer/screenshots/`](anonymizer/screenshots/).

---

## Conversation transcripts

- [`chat-transcript.md`](chat-transcript.md) — full Claude Code session for AA2.
- [`anonymizer/CHAT_HISTORY.md`](anonymizer/CHAT_HISTORY.md) — Claude session for AA1.
- AA3 merge + AA4 drafting: this Claude Code plan-mode session; plan is archived
  at [`consolidation/AA3_PLAN.md`](consolidation/AA3_PLAN.md) and disclosed in
  [`documentation/ai-work-plan.md`](documentation/ai-work-plan.md) §3.8.
