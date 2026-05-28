# s34859_kafka — AA4 (Secure AI Prompt + Mock Integration)

**Student:** s34859 — William Baaklini
**Course:** Analysis of Large Data Sets (ADD), PJATK

Single repository, graded branch **`main`**. Pre-AA4 work (AA1/AA2/Phase 2)
is preserved on the **`backup/pre-aa4-2026-05-28`** branch.

---

## Quick start (offline mock pipeline)

Prerequisites: **Python 3.11+**, Windows + PowerShell.

```powershell
# 1. (one-time) prepare venvs and dependencies
powershell -File scripts\run_mock.ps1     # boots the server (Ctrl+C to stop)
# in a second terminal:
powershell -File scripts\run_tests.ps1    # runs pytest against the mock
# or, all-in-one demo:
powershell -File scripts\demo.ps1         # boots server, drains client, anonymizes
```

The demo writes `integration/out/ticks.anon.json` — the end-to-end
proof that the mock SSE stream was consumed, exported, and run through
the AA1 anonymizer **without leaving 127.0.0.1**.

---

## Repository layout

| Path | What it is |
|---|---|
| [`anonymizer/`](anonymizer/) | AA1 — frozen anonymizer CLI. Pure stdlib, no AI / no HTTP. |
| [`mock/server/`](mock/server/) | Flask SSE mock server (`/api/tickers`, `/api/latest`, `/api/stream`) on `127.0.0.1:5050`. |
| [`mock/client-dashboard/`](mock/client-dashboard/) | CLI consumer — connects to the mock stream, buffers last *N* ticks, exports JSON/CSV. |
| [`mock/fixtures/`](mock/fixtures/) | Synthetic ticker list, synthetic ticks (with fictional sensitive fields), anonymizer mapping. |
| [`integration/pipeline/`](integration/pipeline/) | `run_pipeline.py` — exported ticks → AA1 anonymizer → `integration/out/`. |
| [`integration/tests/`](integration/tests/) | `pytest` suite — server smoke tests, client round-trip, end-to-end anonymization assertions. |
| [`scripts/`](scripts/) | PowerShell helpers: `run_mock.ps1`, `run_tests.ps1`, `demo.ps1`. |
| [`documentation/plan-from-grading.md`](documentation/plan-from-grading.md) | Plan derived from my Phase 2 feedback (anticipated failure modes). |
| [`documentation/prompt.md`](documentation/prompt.md) | Phase B one-shot AI agent prompt (added at start of Phase B). |
| [`documentation/ai-fix-log.md`](documentation/ai-fix-log.md) | Phase B/C — evidence of failures, fixes, final passing state. |
| [`documentation/ai-chat/`](documentation/ai-chat/) | Full AI conversation export(s). |

---

## Safety

- No real personal data. Every name and email under `mock/fixtures/` is fictional.
- No external network. Mock server binds to `127.0.0.1:5050`; client only talks to that URL.
- No `.env`, no API keys on `main`.
- Anonymizer is deterministic and offline — `anonymize.py` is stdlib-only and is treated as frozen.

---

## Troubleshooting

| Symptom | Likely cause | Try |
|---|---|---|
| `requests.exceptions.ConnectionError` from the client or demo | Server hasn't finished binding to port 5050 yet | Wait for `GET /api/health` to return `{"ok": true}` before running the client; in scripts, poll the endpoint instead of sleeping. |
| `json.JSONDecodeError` in `client.py` | SSE consumer is parsing control lines (`event: ...`) as JSON | Skip lines that don't start with `data: ` in `stream_ticks()`. |
| `error: Mapping file not found: mock/fixtures/mapping.json` | Pipeline is being invoked from a directory other than the repo root, and the default mapping path is relative | Pass `--mapping <absolute_path>` or anchor the default to `Path(__file__).resolve().parents[2] / "mock" / "fixtures" / "mapping.json"`. |
| `integration/out/ticks.anon.json` still contains a raw `@brokerage.test` address | A `find` entry in `mock/fixtures/mapping.json` is misspelled and never matches | Diff the mapping `find` arrays against the fixture values in `ticks.json`. |
| `scripts\demo.ps1` succeeds on a second run but fails on the first | Race between Flask startup and the client connect | Add a readiness loop in `demo.ps1` that polls `http://127.0.0.1:5050/api/health` before launching the client. |

---

## AA1, AA2 (pre-AA4 work)

Preserved at:
[`backup/pre-aa4-2026-05-28`](https://github.com/ADD-PJATK/s34859_kafka/tree/backup/pre-aa4-2026-05-28).

The AA1 anonymizer is still on `main` under [`anonymizer/`](anonymizer/)
because AA4 depends on it. AA2 apps (`app1-dashboard/`, `app2-history/`)
remain on `main` for transparency but are **not** the focus of grading
for AA4 — grading evaluates the offline mock pipeline.
