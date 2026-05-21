# Acceptance criteria & Grading rubric — Local Data Anonymizer

## Grading — 0 to 4 points

| # | Criterion | Points |
|---|-----------|--------|
| 1 | **Git repository** — created in the ADD GitHub organisation, named `sXXXXX_anonymize` (your student ID) | 1 pt |
| 2 | **README** — prerequisites, installation, how to run, full mapping JSON contract, documented policy for overlaps / rule order | 1 pt |
| 3 | **Evidence of execution** — screenshots or equivalent showing successful runs on **at least two** of: `.json`, `.txt`, `.md`, `.csv` | 1 pt |
| 4 | **Git & examples** — ≥3 meaningful commits, `.gitignore` suited to the project, `examples/` with valid `mapping.json` and sample inputs | 1 pt |

**Total: 4 points**

---

## 1. Git repository (1 pt)

- [ ] Repository created under the **ADD GitHub organisation**
- [ ] Repository name: `sXXXXX_anonymize` (replace `XXXXX` with your student ID, e.g. `s12345_anonymize`)
- [ ] Repository is **public** or accessible to the instructor
- [ ] No real personal data committed — use fictional samples only

---

## 2. README requirements (1 pt)

The root `README.md` must include **all** of the following:

- [ ] **Prerequisites** — runtime / language version (e.g. Python 3.11+, Node 20+, JDK 21, etc.)
- [ ] **Installation** — clone repo, install dependencies (exact commands)
- [ ] **How to run** — copy-pasteable CLI example using `--mapping`, `--input`, `--output` (or your documented equivalent)
- [ ] **Mapping format** — document the required `replacements` + `options.case_sensitive` schema from the assignment `README.md`
- [ ] **Behavioural edge cases** — how ordered rules interact with overlapping `find` strings, and how **multiple `find` entries in one rule** interact with each other (must match actual code)
- [ ] **Encoding** — state that input/output is UTF-8
- [ ] **Prohibitions** — one short paragraph confirming the tool does **not** use HTTP APIs or AI/LLM services at runtime

> A good README means someone who has never seen your code can run a sample from `examples/` in under 5 minutes.

---

## 3. Screenshots / proof of runs (1 pt)

Include images in `screenshots/` or embed them in the README:

- [ ] At least **two** different source extensions among `.json`, `.txt`, `.md`, `.csv` are processed successfully
- [ ] Evidence shows the **command used** and the **result** (output path, file excerpt, or diff-style view)
- [ ] Content is clearly **anonymized** vs. the sample “before” state (side-by-side or before/after in README is fine)

---

## 4. Git usage & examples (1 pt)

- [ ] At least **3 commits** with meaningful messages (e.g. `"Add CLI flags for mapping/input/output"`, `"Handle UTF-8 decode errors"`)
- [ ] Avoid a single “initial dump” commit with the entire project and no history
- [ ] `.gitignore` present and sensible for the chosen technology
- [ ] `examples/` contains a valid **`mapping.json`** and at least one sample input file; README references how to run against these files

---

## Functional requirements checklist

### Core behaviour

- [ ] Loads mapping from JSON file matching the **required** schema (`replacements`, optional `options.case_sensitive`); each rule has **`find` as an array of strings** and **`replace` as a single string**
- [ ] Rejects invalid mapping (e.g. empty `find` array, empty string inside `find`, missing `replace`) with a non-zero exit / clear error message
- [ ] Reads source file as **UTF-8 text**
- [ ] Writes anonymized content to the **output** path specified by the user
- [ ] Supports extensions: `.json`, `.txt`, `.md`, `.csv` (all treated as UTF-8 text unless you document and implement optional structured handling)

### Constraints (must hold for full credit)

- [ ] **No** runtime dependency on external anonymization APIs (no HTTP calls for masking)
- [ ] **No** LLM / AI inference (local or remote) used to decide replacements
- [ ] Deterministic output for the same inputs and mapping

### Optional extras (not required)

- [ ] `--dry-run` or statistics per rule (e.g. counts per `find` entry)
- [ ] JSON-aware replacement by key paths (only if fully documented and tested)
