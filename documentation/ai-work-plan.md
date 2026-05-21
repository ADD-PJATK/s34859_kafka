# AI-Assisted Work Plan — ADD Project

**Student ID:** s34859
**Student name:** William Baaklini
**Course:** Analysis of Large Data Sets (ADD), PJATK — Project-Based End-to-End Big Data
**Repository:** https://github.com/ADD-PJATK/s34859_kafka
**Document version:** 1.0
**Last updated:** 2026-05-21

---

## 3.1 Title block

This document is the operating manual for how I use AI coding assistants throughout the
ADD project. It applies to all additional assignments (AA1 anonymizer, AA2 Kafka/SSE
stocks, AA3 unified repository, AA4 this plan) and to any future Spark / streaming /
clustering tasks during Weeks 1–13. The repository above is the single source of truth
for graded deliverables.

---

## 3.2 Scope of AI use in this project

| Activity | Allowed? | Notes |
|---|---|---|
| Boilerplate code, CLI scaffolding (argparse, Flask routes, requirements.txt) | Yes | I review every generated line, name files myself, and pin versions when it matters. |
| PySpark transformations / Spark SQL queries | Yes | AI proposes; I run on a real sample before committing. Schema must come from real data, not invented columns. |
| Writing task reports (`documentation/taskNN_*.md`, READMEs) | Yes | AI drafts; I rewrite paragraphs about what I actually observed. |
| Debugging error messages and stack traces | Yes | I paste the *minimal* failing snippet and the literal error — never my whole repo or `.env`. |
| Designing architecture diagrams (Mermaid, ASCII) | Yes | AI proposes a layout; I check the boxes actually exist in the code. |
| Drafting commit messages and PR descriptions | Yes | I edit before pushing so the message reflects what *I* did, not “AI did everything”. |
| **Runtime anonymization (AA1 tool)** | **No** | Hard rule from AA1 spec — anonymizer must be pure stdlib, no HTTP, no LLM at runtime. |
| Pasting real personal data, credentials, or instructor’s API key into AI | **No** | Always use fictional or public samples; key stays in `.env` only. |
| Generating the final text of the AA4 disclosure (§3.8) without edits | **No** | The disclosure must be honest in my own words. |
| Submitting AI output unreviewed to grading | **No** | I am responsible for understanding and defending every line. |

---

## 3.3 Tools and models

- **Claude Code (CLI, Opus 4.7, 1M-context)** — primary agent for repo-wide refactors,
  multi-step automations (this AA3 merge, file renames, README rewrites), and
  branch/commit hygiene. Cloud-based; prompts and tool I/O leave my machine to
  Anthropic; I assume Anthropic’s data-handling policy applies (no training on API
  traffic by default for paid plans).
- **Claude.ai web** — ad-hoc Q&A, document outlining, and quick code review when I
  don’t need shell access. Same data-handling assumptions as above.
- **GitHub Copilot in editor** — inline suggestions for boilerplate (loop bodies,
  type hints, docstrings). Cloud-based; I disable it when editing `.env` or any file
  under `secrets/`.
- **No local models in this project.** I do not currently run Ollama / LM Studio,
  but I would consider it for tasks that involve sensitive sample data.

For each cloud tool I avoid pasting raw secrets, real personal data, or upstream
API keys. I read the per-tool privacy/training defaults at least once per semester.

---

## 3.4 Standard workflow (step-by-step)

The same loop applies whether I’m building a Flask endpoint or a PySpark job.

1. **Write a one-paragraph human spec** in plain English: goal, inputs, outputs,
   data path, constraints (e.g. “PySpark 3.5, read from `s3a://add-bucket/raw/`,
   write Parquet partitioned by `ds`”). No prompt to AI yet.
2. **Sketch the file map** in the repo (which files will change, in which folders).
   This forces me to think about blast radius before AI suggests churn.
3. **Paste only the minimum context** into AI: the spec, the relevant schema, the
   one or two files being edited. Never the whole repo, never `.env`.
4. **Ask for a plan first**, then code, then tests. The plan step catches
   misunderstandings cheaply. For non-trivial tasks I use Claude Code’s plan mode.
5. **Run the result locally** on a small real sample (or the AA1 example mapping).
   No commit until the script actually produces the expected output.
6. **Inspect every line** I’m about to commit. AI-generated imports, CLI flags, and
   API names get cross-checked against official docs. Hallucinated APIs are deleted.
7. **Document what changed** in the task report (`documentation/taskNN_*.md`) — what
   the task was, what I asked AI, what I edited, what I rejected.
8. **Commit with an honest message** (imperative, my words) and push. Co-authorship
   trailer is fine when AI did substantial drafting, but the message still describes
   *my* intent.

---

## 3.5 Prompting rules

- Always state the **language and stack version** (e.g. “Python 3.13, stdlib only”
  for AA1; “PySpark 3.5, Python 3.11” for Spark tasks).
- Always state the **exact file paths** I want changed (`anonymizer/anonymize.py`,
  not “the anonymizer file”).
- Demand **idempotent scripts** and explicit run instructions — every CLI must be
  re-runnable on the same input without side effects beyond the documented output.
- Require **error handling** for missing files, empty inputs, non-UTF-8 bytes, and
  rate-limit responses; no silent `except: pass`.
- Forbid **invented libraries or APIs** — if I haven’t seen the import in pip or
  the official docs, I delete it before committing.
- Ask for **diff-style / minimal changes** when editing existing files. Sweeping
  rewrites of files I didn’t mention are rejected.
- Always include the **acceptance criteria from the task spec** in the prompt so
  the model optimizes for the right target (e.g. AA3b: “must run from this exact
  command, examples must produce the expected output”).
- Always include **course constraints** (e.g. AA1: “no HTTP, no LLM at runtime”;
  AA2: “API key only via `.env`, never in code, never in browser”).
- End every non-trivial prompt with: **“If unsure, ask clarifying questions
  before writing code.”** This catches ambiguous requirements early.

---

## 3.6 Precautions and prohibited uses

1. **Secrets — never paste** API keys, passwords, `.env` contents, OAuth tokens, or
   cloud credentials into any AI tool. The `ADD_API_KEY` lives only in `.env`,
   which is gitignored.
2. **Personal data — never upload** real customer/PII data. AA1 development used
   only fictional sample CSVs/JSONs; any future Spark task uses public or
   synthetic datasets.
3. **Verification — never merge AI output without running it.** “Looks correct” is
   not enough. I run the script end-to-end on a clean path before commit.
4. **Hallucinations — verify every external API** (CLI flag, Spark function,
   library function) against the official docs. If the docs don’t describe the
   flag, I assume the model invented it.
5. **Licence and attribution** — substantial AI-generated blocks in reports
   include a sentence acknowledging AI assistance and how I edited it.
6. **Team consistency** — one style per repo (here: Black-style Python, 88 cols).
   AI must not rewrite unrelated files. If it tries, I revert those hunks.
7. **Scope creep** — AI must not add features outside the task spec. If a
   suggestion adds a “nice-to-have” logging framework I didn’t ask for, I cut it.
8. **Testing evidence** — every functional task keeps a log/screenshot/sample
   output committed (e.g. `anonymizer/screenshots/run_log.txt`, the `app2-history`
   downloaded CSVs).
9. **Academic integrity** — AI helps me learn; I remain responsible for
   understanding and orally defending every line. No copied plans, no AI text in
   places where the assignment asks for my own analysis.
10. **When to stop using AI** — if I’m debugging a subtle production-style incident
    (data leakage, schema drift on real data), I stop pasting context and switch
    to first principles. In exam conditions I follow course rules absolutely.
11. **Repo hygiene** — AI must not invent commits, branches, or tags. Force-push,
    `git reset --hard`, and `--no-verify` require my explicit instruction.
12. **Output destinations** — AI must not propose writes outside the project
    directory (no `C:\` paths, no `/etc/`). Output stays under the repo or under
    `examples/out/`.

---

## 3.7 Task-specific AI plans

### Task — AA1 Anonymizer (already complete)

- **What I asked AI to do**: scaffold an argparse CLI with `--mapping --input
  --output`, validate the mapping JSON, apply deterministic substitutions to
  `.json/.txt/.md/.csv`, print per-rule counts.
- **What I did myself without AI**: chose the supported extensions, designed the
  mapping schema (`find` as a list of synonyms, `replace` as a single string),
  decided on stdlib-only and the precise exit codes (`EXIT_USAGE=2`,
  `EXIT_MAPPING=3`, `EXIT_ENCODING=4`).
- **Definition of done**: `python anonymize.py --mapping examples/mapping.json
  --input examples/sample.csv --output examples/out/sample.anon.csv` runs and the
  output matches the committed `examples/out/sample.anon.csv`. Spec line “no
  HTTP/LLM at runtime” is satisfied — no `requests`/`urllib` imports, no AI calls.

### Task — AA2 Realtime Dashboard (already complete)

- **What I asked AI to do**: write a Flask SSE proxy that forwards `/api/stream`
  upstream with the `X-API-Key` header attached, and a Chart.js client that
  opens one EventSource per selected ticker.
- **What I did myself without AI**: chose to put one EventSource per ticker after
  noticing the upstream sends only one ticker per stream; designed the chart’s
  rolling 30-tick window; decided the API key is never sent to the browser.
- **Definition of done**: `python app.py` from `app1-dashboard/` serves the
  dashboard on `localhost:5000`; selecting two tickers produces live ticks
  within ~10 s; screenshot present in `screenshots/app1-dashboard.png`.

### Task — AA2 History Downloader (already complete)

- **What I asked AI to do**: a Flask proxy for `/api/latest`, browser-side polling
  every 10 s, a moving 1/2/5/10-minute window, CSV/JSON export via `Blob`.
- **What I did myself without AI**: matched the constraint that the upstream only
  retains ~10 min, so the window has to be *built forward*; chose the filename
  slug `stocks-YYYYMMDD-HHMMSS.{csv,json}`; decided exports happen entirely
  client-side so the API key never crosses the browser.
- **Definition of done**: `localhost:5001` shows the table after a few polls,
  CSV/JSON downloads contain real rows, screenshots in `screenshots/`.

### Task — AA3 Unified Repository (this submission)

- **What I asked AI to do**: design the merge of `s34859_anonymize` into
  `s34859_kafka` on `main` as a clean orphan-branch + `--allow-unrelated-histories`
  merge; rename `anonymize/` → `anonymizer/`; update the root README; draft this
  AA4 document.
- **What I did myself without AI**: decided to keep `app1-dashboard/` and
  `app2-history/` at repo root (spec allows it; less churn); chose the
  consolidation note path; reviewed every commit message; ran the anonymizer CLI
  myself to confirm AA3b before push.
- **Definition of done**: ACCEPTANCE.md A1–A4, B1–B5, C1–C4, D1–D9 all pass; one
  push to `origin/main` shows the new layout; the merge commit graph is intact.

### Task — Future Spark/clustering work (planned, e.g. ADD Task 07)

- **What I will ask AI to do**: write a PySpark pipeline that reads parquet
  partitions, computes k-means/spectral clustering features on a numeric subset,
  writes labels back partitioned by `ds`; draft the task report.
- **What I will do myself without AI**: choose the cluster count by inspecting
  the elbow plot on the real data; validate that the output partition count
  matches input; verify Spark’s `pyspark.ml.clustering` API in the official
  docs before accepting any import the model proposes.
- **Definition of done**: pipeline runs idempotently against a real sample;
  output parquet is readable by a follow-up notebook; task report under
  `documentation/task07_clustering.md`; AI usage logged in §3.8 disclosure.

---

## 3.8 Disclosure — how this document was produced with AI

This plan was drafted in a Claude Code (Opus 4.7) session on 2026-05-21 as part of
the same session that performed the AA3 merge. The high-level prompts I used
(paraphrased, not pasted secrets) were: “read the four Phase-2 spec documents
in the working directory; draft `documentation/ai-work-plan.md` that satisfies
sections 3.1 through 3.10, hits ≥10 precautions, ≥4 task-specific plans, and
≥150-word disclosure; use my actual AA1/AA2/AA3 work for the task-specific
plans; keep it 1,200–1,500 words.” I supplied my student ID, name, and the
absolute repo URL; I did not paste my `ADD_API_KEY`, the class password, the
contents of `.env`, or any real personal data into the model.

After the initial draft I rewrote the §3.2 scope table to remove rows the model
invented that did not apply to my repo (e.g. it had added “LangChain agents”
and “vector DBs” which I do not use). I also tightened §3.6 from 14 vague
bullets to 12 concrete must/must-not rules, dropping suggestions like “consider
running a security scanner” that were generic rather than actionable for ADD.
I edited §3.7 to reflect the actual decisions I made on AA1/AA2 — for example
the “one EventSource per ticker” call on AA1 was *mine*, not the model’s; the
model originally proposed a multiplexed single stream and I rejected that
suggestion when it produced flickering during testing. The revision log below
records this round. Final word count and English were my responsibility; the
model did not see my `.env` or the class password (which I always paste through
the redacted `[REDACTED]` placeholder in any committed file).

---

## 3.9 Review checklist before every commit

- [ ] I ran the script / app / notebook end-to-end on a clean path with the
      documented command.
- [ ] No secrets in the diff (`git grep -nE "ADD_API_KEY=[^[:space:]]"` returns
      nothing, `.env` is gitignored, no API keys in chat logs).
- [ ] No real personal data committed; only fictional or public samples.
- [ ] Task report under `documentation/` is updated in clear English.
- [ ] Screenshots / logs proving the run are committed where the spec asks.
- [ ] AI-generated blocks of substantial size are attributed in the report or in
      a code comment.
- [ ] Commit message describes *my* intent in imperative mood; AI co-authorship
      trailer added only when AI did substantial drafting.
- [ ] Pre-existing tests (where present) still pass; new tests added for new
      behaviour where reasonable.
- [ ] `.gitignore` still excludes `.venv/`, `.env`, `__pycache__/`, downloaded
      stock CSV/JSONs, and any temporary `examples/out/` overrides.

---

## 3.10 Revision log

| Date | Version | Change |
|------|---------|--------|
| 2026-05-21 | 0.1 | Initial draft in Claude Code session: sections 3.1–3.10 stub with placeholder task plans. |
| 2026-05-21 | 1.0 | Final pass: §3.2 scope trimmed to apply to this repo, §3.6 reduced from 14 vague to 12 concrete rules, §3.7 rewritten with the actual AA1/AA2/AA3 decisions, §3.8 disclosure rewritten to be honest about which suggestions I rejected. |
