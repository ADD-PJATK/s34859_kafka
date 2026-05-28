# AA4 Phase B — One-Shot Repair Prompt

> This is the **exact text** I will paste into the AI coding agent at the
> start of Phase B. It is meant to be self-contained: an agent receiving
> only this prompt, with no prior conversation, should be able to bring
> the repository from its deliberately broken Phase A baseline to a
> fully working end-to-end state.

---

## 1. Mission

You are working in a freshly cloned copy of
`https://github.com/ADD-PJATK/s34859_kafka` at commit
`23723ef…` (the **Phase A baseline** — intentionally broken). Your job
is to make the offline mock SSE pipeline pass its automated test suite
and produce a correctly anonymized output file, with **minimal,
focused** changes.

The application under repair is an **offline** stand-in for a real-time
stock feed:

1. A Flask **mock server** (`mock/server/app.py`) emits SSE frames of
   synthetic ticks on `http://127.0.0.1:5050`.
2. A CLI **client** (`mock/client-dashboard/client.py`) connects to the
   stream, buffers the last *N* ticks, and exports them as JSON.
3. An **integration pipeline**
   (`integration/pipeline/run_pipeline.py`) feeds the exported ticks
   through the AA1 anonymizer (`anonymizer/anonymize.py`) and writes
   the result to `integration/out/ticks.anon.json`.

Each layer has **at least one deliberate defect** introduced during
Phase A. Tests under `integration/tests/` fail today. After your run,
they must pass.

---

## 2. Stack and prerequisites

- **Python 3.11+** (the test machine has 3.11 or 3.12 installed and on PATH).
- **Windows + PowerShell** is the primary shell. All scripts under
  `scripts/` are `.ps1`. POSIX equivalents are not required.
- **Dependencies** are pinned per-component:
  - `mock/server/requirements.txt` → `Flask==3.0.3`
  - `mock/client-dashboard/requirements.txt` → `requests==2.32.3`
  - `integration/tests/requirements.txt` → `pytest==8.3.2`, `requests`, `Flask`
- **No external network** is allowed at any point — only `127.0.0.1`.
- **No `.env`, no API key** is needed or permitted; the mock replaces
  the real instructor API.

---

## 3. Repository layout (only the parts you should touch)

| Path | Role |
|---|---|
| `mock/server/app.py` | Flask SSE mock server. Emits `event: tick\ndata: <json>\n\n` frames. Considered **structurally correct** — do not change its SSE wire format. |
| `mock/fixtures/tickers.json` | Synthetic ticker list. |
| `mock/fixtures/ticks.json` | Synthetic ticks with fictional sensitive fields (`trader_email`, `operator_name`, `comment`). Fictional people: `Anna Kowalska`, `Marek Nowak`, `Olek Zielinski`. Fictional emails under `@brokerage.test`. |
| `mock/fixtures/mapping.json` | AA1 anonymizer mapping that maps the three fictional people (each with their email) onto `PERSON_A`, `PERSON_B`, `PERSON_C`. |
| `mock/client-dashboard/client.py` | CLI consumer / exporter. |
| `integration/pipeline/run_pipeline.py` | Glue: tick JSON → staging → AA1 anonymizer → `integration/out/ticks.anon.json`. |
| `integration/tests/conftest.py` | Spawns the mock server as a subprocess and waits on `/api/health` before yielding. |
| `integration/tests/test_mock_server.py` | Smoke tests for the three HTTP endpoints. |
| `integration/tests/test_client.py` | Drives `client.py` as a subprocess and validates its JSON output. |
| `integration/tests/test_pipeline.py` | End-to-end: client → pipeline → anonymized JSON; asserts no raw PII strings remain. |
| `scripts/run_mock.ps1` | Boots the server in venv. |
| `scripts/run_tests.ps1` | Installs test deps in venv and runs `pytest -v`. |
| `scripts/demo.ps1` | All-in-one: server (background) + client + pipeline. |

**Off-limits — do not edit:**

- `anonymizer/anonymize.py` and anything else under `anonymizer/`. AA1
  is frozen and considered correct. If a behavior of the anonymizer
  bothers you, the fix is in the inputs you give it (mapping, file
  paths), not in the anonymizer itself.
- `app1-dashboard/`, `app2-history/`, `chat-transcript.md`,
  `consolidation/`, `screenshots/`, `documentation/ai-work-plan.md`,
  the existing `backup/pre-aa4-2026-05-28` branch. These are AA1/AA2
  history kept for transparency.

---

## 4. Read these before changing anything

In this order:

1. `README.md` — top-level quick-start and troubleshooting table.
2. `documentation/plan-from-grading.md` — the **anticipated failure
   modes** section is your diagnostic checklist (categories of bugs,
   not bug locations).
3. `mock/server/README.md` — exact SSE frame format.
4. `mock/client-dashboard/README.md` — client CLI surface.
5. `anonymizer/USAGE.md` — mapping schema, exit codes, what the
   anonymizer guarantees.
6. Every file under `integration/tests/` — the tests **are the spec**
   for what "done" means.

---

## 5. Phase B procedure (do this in order)

### 5.1 Prepare environments

From the repo root, in PowerShell:

```powershell
# Server venv + deps
cd mock\server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\..

# Client venv + deps
cd mock\client-dashboard
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\..

# Test venv + deps
cd integration\tests
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\..
```

### 5.2 Capture the baseline failure (must do FIRST, before any edits)

```powershell
powershell -File scripts\run_tests.ps1 *>&1 | Tee-Object -FilePath baseline-tests.log
```

Save `baseline-tests.log` for the fix log. **Do not edit any source
file until you have this baseline.**

### 5.3 Diagnose, fix, re-run — iterate

For each failing test:

1. Read the **full traceback** end-to-end. Identify the first thing
   that goes wrong, not the last symptom.
2. Map the symptom to one of the failure categories in §6 below.
3. Open the production file at the indicated layer and form a
   hypothesis. State the hypothesis (one sentence) before editing.
4. Make the **minimum** change that closes the hypothesis. Do not
   refactor surrounding code; do not "improve" naming; do not add
   defensive `try/except` that just swallows the symptom.
5. Re-run `scripts\run_tests.ps1`. Confirm the targeted failure is
   gone and **no previously-passing test has regressed**.
6. Move on to the next failing test.

### 5.4 Run the end-to-end demo

When `pytest` is green:

```powershell
powershell -File scripts\demo.ps1
```

This must exit 0, leave `integration/out/ticks.anon.json` on disk, and
the file must satisfy the acceptance checklist in §7.

### 5.5 Update the fix log

Open `documentation/ai-fix-log.md` and append:

- The verbatim baseline `pytest` output (from §5.2).
- One short paragraph per fix: **file**, **what changed**, **why** (one
  sentence linking it to a failing test).
- The verbatim final `pytest` output (all green).
- Verbatim `demo.ps1` output and the first 30 lines of
  `integration/out/ticks.anon.json`.
- A 5-to-10-sentence reflection on what made debugging tractable
  (what the failure messages told you, what the test design
  surfaced, what you would do differently).

---

## 6. Failure-mode playbook (categories, not locations)

When a test fails, classify it into one of these categories and search
the codebase for that *kind* of mistake. Do not search for the specific
bugs by name — the prompt does not list them.

| Category | What it looks like at the surface | Where to investigate |
|---|---|---|
| **SSE wire-format mishandling** | `json.JSONDecodeError` on a line that obviously is not JSON (e.g. starts with `event: `), or a stream consumer that exits non-zero before the expected number of frames arrives. | Any code that calls `iter_lines()` on an SSE response. The server side is correct; consumer logic is not. |
| **Path resolution drift** | `Mapping file not found` / `No such file or directory` for a file that is clearly committed and present. The error reproduces when the script is invoked from a directory that is not the repo root. | Any module-level `Path("...")` literal. Convert to `Path(__file__).resolve().parents[N] / ...` so the path is anchored, not cwd-relative. |
| **Data-vs-test-spec drift** | `KeyError` in a test assertion, or an `assert` that compares two values neither of which is wrong individually — the test just expects a different schema than the fixture provides. | The test source itself. Cross-check the asserted key against `mock/fixtures/ticks.json` and the client's export shape. Fix the test if and only if the production data is the authoritative shape. |
| **Mapping miss** | `pytest` reports a sensitive string still present in the anonymized output, even though every layer above seemed to work. | `mock/fixtures/mapping.json`. Diff every entry of every `find` array character-by-character against the corresponding value in `mock/fixtures/ticks.json`. A single missing letter in a domain or surname is enough to slip a record through. |
| **Cold-start race** | A script (not a pytest run) intermittently fails on first invocation with `ConnectionRefusedError` or `Connection refused`, then succeeds on the second run because the process started during the failed run is still listening. | Any launcher script that starts a server and a client in sequence without first polling for readiness. Replace fixed sleeps (or, worse, no wait at all) with a `GET /api/health` poll. |

If a failure does **not** fit any of these categories, write a one-line
note explaining what category you think it belongs to and proceed
cautiously — do not invent a sixth category to justify a sweeping
refactor.

---

## 7. Acceptance — "done" is **all** of these

1. `powershell -File scripts\run_tests.ps1` (from the repo root) exits
   0 and reports all tests in `integration/tests/` as **passed**. No
   tests skipped, no tests marked `xfail` to hide problems.
2. `powershell -File scripts\demo.ps1` (from the repo root) exits 0 on
   both a cold first run and a warm second run on the same shell.
3. `integration/out/ticks.anon.json` exists, parses as a JSON array of
   tick objects, and contains **none** of the following raw strings:
   - `Anna Kowalska`
   - `Marek Nowak`
   - `Olek Zielinski`
   - `anna.kowalska@brokerage.test`
   - `marek.nowak@brokerage.test`
   - `olek.zielinski@brokerage.test`
4. Every tick object in that file has a `trader_email` value that
   matches the regex `^PERSON_[A-Z]+$`.
5. The repository tree on disk shows **no** new `.env` file, no API
   key in any file, no new third-party package added to any
   `requirements.txt`, and no network destination other than
   `127.0.0.1` (or `localhost`) in any source file.
6. `documentation/ai-fix-log.md` is populated per §5.5.

---

## 8. Hard constraints (scope and safety)

- **Do not edit `anonymizer/`**. AA1 is frozen.
- **Do not add new top-level dependencies.** If a fix tempts you to
  `pip install` something new, the fix is wrong.
- **Do not change SSE wire format on the server.** The server emits
  `event: tick\ndata: <json>\n\n`; that is correct.
- **Do not add `try / except` blocks that catch and ignore.** Catching
  `JSONDecodeError` to "skip" the offending line is treating the
  symptom, not the cause. Filter what you parse instead.
- **Do not introduce backwards-compatibility shims** (renamed
  parameters that alias old names, `# removed` comments, etc.). Delete
  what is wrong, write what is right.
- **Do not call external services**, do not introduce HTTP clients
  that point anywhere other than `http://127.0.0.1:5050`, do not read
  any `.env`, do not write any secret to disk.
- **Do not commit or push.** Leave changes in the working tree. The
  human will review the diff before any commit.

---

## 9. When you are done

Print, in a single final message:

1. The list of files you modified, one per line.
2. The one-paragraph summary that will go into the commit message.
3. The exit code and last 10 lines of `scripts\run_tests.ps1`.
4. The exit code and last 10 lines of `scripts\demo.ps1`.
5. The first 30 lines of `integration/out/ticks.anon.json`.

Then stop. Do not push, do not open a PR, do not run further commands
unsolicited.
