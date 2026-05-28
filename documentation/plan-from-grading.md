# Plan from Phase 2 Grading Feedback (AA4)

> Source: my **own** Phase 2 grading feedback (returned report + in-class
> comments). Sanitized — no instructor URLs or private grading artifacts
> are reproduced here, only my own paraphrase of what the feedback said
> and how it shapes the AA4 mock.

---

## 1. Sanitized summary of my Phase 2 outcome

What worked in Phase 2:

- AA1 anonymizer was correct, deterministic, and dependency-free.
- AA2 dashboard and history apps connected to the instructor's API and
  showed live updates / downloads end to end.
- The repository was consolidated into a single `sXXXXX_kafka` repo on
  `main` with clear per-component READMEs.

Where the feedback flagged weaknesses (paraphrased from my notes):

- **AA3 integration was thin.** AA1 was present and AA2 was present, but
  the bridge between them (stream → exportable record → anonymizer)
  was implicit. Nothing tied them end to end.
- **Reproducibility was fragile.** Several quick-start commands assumed
  the reader was already `cd`'d into a specific subdirectory; running
  them verbatim from the repo root broke.
- **No offline test path.** All checks went through the instructor's
  live API. There was no way to demonstrate the pipeline on a machine
  without a key or without internet.
- **Anonymizer coverage was hand-verified only.** I never wrote an
  automated test that re-anonymized a fixture and asserted that no raw
  PII strings remained.
- **README troubleshooting was thin.** The "what to do if it doesn't
  work" section was missing common failure modes (SSE buffering,
  missing `.env`, server-not-ready races).

These items are exactly what AA4 is asking me to fix in a mock world.

---

## 2. What I will mock in AA4 (mapped to the feedback)

| Phase 2 weakness | What I mock in AA4 |
|---|---|
| Thin AA3 integration | A real `integration/pipeline/run_pipeline.py` that walks the full chain: SSE stream → JSON export → AA1 anonymizer → `integration/out/`. |
| Reproducibility fragile | `scripts/demo.ps1` runs the whole thing from the repo root in one command; conftest fixtures spin the server up and tear it down deterministically. |
| No offline test path | All endpoints are reimplemented as a local Flask mock on `127.0.0.1:5050`; no external network, no API key. Fixtures live in `mock/fixtures/`. |
| Anonymizer coverage hand-verified only | `integration/tests/test_pipeline.py` asserts that none of the original sensitive strings appear in the anonymized output. |
| Thin README troubleshooting | Top-level `README.md` documents the three common failure modes (server boot race, SSE parsing, mapping mismatches). |

---

## 3. What "done" means for AA4

After the Phase B agent run, the following must be true:

1. `powershell -File scripts\demo.ps1` (run from repo root) exits 0 and
   leaves `integration/out/ticks.anon.json` on disk.
2. `powershell -File scripts\run_tests.ps1` (run from repo root) is
   green — all tests in `integration/tests/` pass.
3. `integration/out/ticks.anon.json` contains **no** original sensitive
   strings: `Anna Kowalska`, `Marek Nowak`, `Olek Zielinski`, and the
   three `*@brokerage.test` emails are all replaced by `PERSON_*`
   placeholders.
4. No `.env`, no API key, no calls outside `127.0.0.1`.

---

## 4. Anticipated failure modes and how each one is detected

Concrete list with detection method — these are the categories of
breakage I expect the AI agent to find in `main` during Phase B.

| # | Failure mode | Where it can hide | How a test or run surfaces it |
|---|---|---|---|
| 1 | **SSE field parsing** — consumer treats every non-empty line as JSON, so SSE control lines like `event: tick` crash `json.loads`. | `mock/client-dashboard/client.py`, `stream_ticks()`. | `test_client_collects_ticks_to_json` — client subprocess exits non-zero; stderr shows `JSONDecodeError`. |
| 2 | **Mapping typo** — a misspelled domain or name in `mock/fixtures/mapping.json` means a sensitive value never matches and slips through to the output. | `mock/fixtures/mapping.json`, `find` arrays. | `test_pipeline_anonymizes_sensitive_fields` — asserts no raw PII string remains; one of the `*@brokerage.test` addresses survives. |
| 3 | **cwd-relative paths** — pipeline (or scripts) compute paths against the current working directory, so they work from one folder but fail from another. | `integration/pipeline/run_pipeline.py` defaults; demo / test invocations from `tmp_path`. | Pipeline subprocess exits 2 with `Mapping file not found`, even though the file is committed. |
| 4 | **Wrong schema field in tests** — a test asserts on `tick["email"]` but the actual export uses `tick["trader_email"]`. The bug is in the test, not the code. | `integration/tests/test_pipeline.py`. | `KeyError: 'email'` in the test report; production output is actually correct. |
| 5 | **Server-boot race** — demo script launches the Flask server and immediately calls the client; on a cold machine the client races the bind and gets `ConnectionRefused`. | `scripts/demo.ps1`. | `demo.ps1` flakes on first run after reboot; client subprocess exits non-zero with `requests.exceptions.ConnectionError`. |
| 6 | **CSV quoting** — exporting a tick whose `comment` field contains a comma breaks the row when later re-read without `csv` module quoting. | `mock/client-dashboard/client.py` `export_csv`. | Bonus check: round-trip CSV → reader → record count mismatches the buffer size. |
| 7 | **README quick-start drifts from reality** — instructions say `python app.py` but the venv lives in a sibling folder, or the command must be run from a different cwd. | `README.md`, `mock/server/README.md`. | A reader following the README literally from the repo root hits "No such file" or "module not found". |

The Phase B prompt (`documentation/prompt.md`) points the agent at this
file as its diagnostic checklist — not as a list of bug locations
("cheat sheet"), but as the **categories** of failure to consider when
tests fail.

---

## 5. Safety constraints I will enforce in the prompt

- No real PII — every name and email in fixtures is fictional.
- No `.env`, no API keys, no calls beyond `127.0.0.1`.
- The anonymizer stays deterministic and offline (`anonymize.py` is
  stdlib-only by construction; we do not introduce any AI/HTTP call).
- The agent is told explicitly: do **not** edit `anonymizer/` — AA1 is
  considered frozen and correct.
