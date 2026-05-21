# AA3 + AA4 — Unified `sXXXXX_kafka` Repository on `main`

## Context

The PJATK ADD Phase-2 spec (README.md, ACCEPTANCE.md, AA3-unified-repository.md, AA4-ai-work-plan.md in the working directory) requires that AA1 (anonymizer), AA2 (Kafka/SSE stocks), and a new AA4 work-plan document all live on `main` of a single repo `sXXXXX_kafka`. Currently:

- `s34859_kafka/main` has the AA2 apps (`app1-dashboard/`, `app2-history/`), screenshots, `chat-transcript.md`, `.env.example`, root README, etc.
- The AA1 source (from the legacy `s34859_anonymize` repo) was just landed as a clean **orphan branch** `anonymize` with a single root commit putting the AA1 tree under `anonymize/`.
- No `documentation/` and no `consolidation/` directories exist yet on `main`.
- The anonymize folder is misspelled vs. spec (`anonymize/` vs spec's `anonymizer/`).

Goal: merge the orphan branch into `main`, restructure to match the spec exactly, add the required AA4 document and a consolidation note, update the root README, then push to origin.

User decisions captured:
- **AA2 layout:** keep `app1-dashboard/` and `app2-history/` at repo root (spec allows this; just document in root README).
- **Anonymizer folder name:** rename `anonymize/` → `anonymizer/` to match the spec.
- **AA4 draft:** full ~1,200–1,500-word draft, all 10 mandatory sections, with student-specific content.
- **Push:** push `main` (and `anonymize` history branch) to `origin` at the end.

---

## Approach

Five clear, atomic commits on top of `main`, in this order:

1. Rename on the orphan branch so the merge brings in the correct folder name.
2. Merge `anonymize` into `main` with `--allow-unrelated-histories` (preserves AA1 commit + history).
3. Restructure: add `documentation/ai-work-plan.md` (AA4) and `consolidation/CONSOLIDATION.md`.
4. Update root `README.md` so it satisfies AA3a (map, quick-starts for anonymizer + both apps, AA4 link, student ID).
5. Push.

`.gitignore` already on root is a superset of the anonymizer's; no union needed. Per-folder `.gitignore` stays inside `anonymizer/`.

---

## Detailed steps

### 1. Rename on the orphan branch
```
cd s34859_kafka
git checkout anonymize
git mv anonymize anonymizer
git commit -m "Rename anonymize/ to anonymizer/ to match AA3 spec"
```

### 2. Merge into main
```
git checkout main
git merge anonymize --allow-unrelated-histories -m "Merge AA1 anonymizer tree into unified repo (AA3a)"
```
Result: `anonymizer/` appears on `main` with its full history reachable via the merge commit.

### 3. Create AA4 + consolidation files

**`documentation/ai-work-plan.md`** — full draft per AA4 §3.1–3.10. Required content:
- §3.1 Title block: `AI-Assisted Work Plan — ADD Project`, student ID `s34859`, name `William Baaklini`, today's date, course, repo URL.
- §3.2 Scope-of-AI table (≥6 rows; explicit "No" for AA1 runtime).
- §3.3 Tools: Claude Code (this session), Claude.ai, GitHub Copilot if used; with cloud/data notes.
- §3.4 Workflow: ≥6 ordered, data-eng-specific steps.
- §3.5 Prompting rules: ≥8 bullets.
- §3.6 Precautions: ≥10 distinct must/must-not rules covering all themes (secrets, PII, verification, hallucinations, licence, team consistency, scope creep, evidence, integrity, when-to-stop).
- §3.7 Task-specific plans: ≥4 subsections — pick from anonymizer build, Kafka SSE proxy, history downloader/charts, AA4 doc itself, and a hypothetical Spark/clustering task from the wider ADD timeline.
- §3.8 Disclosure: ≥150 words, honest, names sections AI drafted vs. hand-edited, mentions edits made and rejected suggestions.
- §3.9 Pre-commit checklist: ≥8 items.
- §3.10 Revision log: ≥2 rows.
- Target: 1,200–1,500 words excluding tables.

**`consolidation/CONSOLIDATION.md`** — short note: previously two repos (`s34859_anonymize`, `s34859_kafka`); merged on YYYY-MM-DD via orphan-branch + `--allow-unrelated-histories`; folder renamed to `anonymizer/`; AA1 history preserved as branch `anonymize`; no API keys/PII brought across; pointers to per-app READMEs.

```
git add documentation/ai-work-plan.md consolidation/CONSOLIDATION.md
git commit -m "AA4: add AI work plan; AA3: add consolidation note"
```

### 4. Update root README.md

Modify the existing `s34859_kafka/README.md` (don't rewrite from scratch — preserve the AA2 tone) to add:
- Student ID + name line.
- **Repo map** section listing: `anonymizer/`, `app1-dashboard/`, `app2-history/`, `screenshots/`, `documentation/ai-work-plan.md`, `consolidation/CONSOLIDATION.md`, `chat-transcript.md`.
- **Quick start** subsections:
  - Anonymizer: `cd anonymizer && python anonymize.py --in examples/sample.csv --map examples/mapping.json --out out/` (verify exact command in `anonymizer/README.md` first).
  - App #1 and App #2: link to their per-app READMEs and the existing `.env`/`ADD_API_KEY` paragraph.
- **AA4** link to `documentation/ai-work-plan.md`.
- Keep the existing screenshots and chat-transcript references.

```
git add README.md
git commit -m "AA3a: root README maps anonymizer + both Kafka apps + AA4 plan"
```

### 5. Push
```
git push origin main
git push origin anonymize    # optional but tidy; preserves AA1 import history
```

---

## Files to create / modify

**Create**
- `s34859_kafka/documentation/ai-work-plan.md` — the AA4 deliverable.
- `s34859_kafka/consolidation/CONSOLIDATION.md` — merge note.

**Modify**
- `s34859_kafka/README.md` — repo map, quick starts, AA4 link, student-ID block.

**Rename (via merge)**
- `anonymize/**` (on orphan branch) → `anonymizer/**` (on `main`).

**Untouched**
- `app1-dashboard/`, `app2-history/`, root `screenshots/`, `scripts/`, `chat-transcript.md`, `.env.example`, root `.gitignore`.
- All files inside `anonymizer/` (including its own README, USAGE, ACCEPTANCE, CHAT_HISTORY, examples, screenshots).

---

## Chat / plan saving

The spec does not explicitly require an AA3 merge-chat transcript. AA1's `CHAT_HISTORY.md` (inside `anonymizer/`) and AA2's `chat-transcript.md` are already preserved. AA4 §3.8 covers AI-disclosure inside the work-plan document itself. **Decision:** save this plan as `consolidation/AA3_PLAN.md` for transparency (copy of this file), and let the AA4 disclosure section carry the narrative. No separate chat dump needed.

```
cp <plan-file> s34859_kafka/consolidation/AA3_PLAN.md
git add consolidation/AA3_PLAN.md
git amend or new commit
```

---

## Verification

Run before push:

1. `git log --oneline --graph --all -15` — confirm 4 new commits on `main` plus a merge commit linking to the orphan branch.
2. `tree -L 2 s34859_kafka` — confirm layout matches spec §3:
   - `anonymizer/`, `app1-dashboard/`, `app2-history/`, `documentation/ai-work-plan.md`, `consolidation/CONSOLIDATION.md`, root `README.md`, `.env.example`, `.gitignore`, `screenshots/`, `chat-transcript.md`, `scripts/`.
3. **AA3b functional check** — actually run the anonymizer to verify the +1 point:
   ```
   cd anonymizer
   python -m venv .venv && .venv\Scripts\activate
   pip install -r requirements.txt   # if present; else stdlib only
   python anonymize.py --in examples/sample.csv --map examples/mapping.json --out examples/out/
   ```
   Confirm output files appear and match `examples/out/sample.anon.*`.
4. **AA2 smoke** — start each Flask app briefly to confirm `.env`-based key still works (don't commit `.env`).
5. Grep for secrets pre-push:
   ```
   git grep -nE "ADD_API_KEY=[^[:space:]]" || echo "clean"
   git grep -niE "(password|api[_-]?key|token)[^a-z0-9]" -- ':(exclude)anonymizer/CHAT_HISTORY.md' ':(exclude)chat-transcript.md'
   ```
6. Word-count check on AA4:
   ```
   wc -w documentation/ai-work-plan.md   # expect ≥1200
   ```
7. ACCEPTANCE.md checklist (A1–A4, B1–B5, C1–C4, D1–D9) — walk it mentally; every box must pass.
8. After `git push`: open the GitHub repo in browser, confirm `main` shows the new layout and the merge commit graph.

---

## Out of scope

- Re-grading AA1 or AA2 (Phase 1 grades stand).
- Rewriting per-app READMEs inside `app1-dashboard/`, `app2-history/`, `anonymizer/` — they already meet their respective specs.
- Adding new functionality to the anonymizer or stock apps.
