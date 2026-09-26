# ChangeGuard — Hackathon Implementation Plan

## Top-Level Overview

**Goal:** Build a working hackathon prototype of ChangeGuard, an AI-powered developer workflow assistant.  
A developer selects or pastes a code diff from a synthetic sample project, then Bob performs parallel
analysis across four dimensions (impact, code/security, testing gaps, test generation) and assembles
a Release Readiness Report visible in a React dashboard.

**Core technology:** React + Vite + Tailwind CSS (frontend) · Python FastAPI (backend) · IBM Bob (AI analysis orchestration) · pytest (test execution) · JSON file persistence.

**IBM Bob role:** Bob is the orchestration brain — it runs in Plan mode to design each analysis session,
then spawns four focused subagents in Agent mode to perform parallel analysis, then assembles the
final report. Bob is not a coding assistant here; it is the runtime workflow engine.

**Scope boundary (hackathon):** One synthetic sample project, one analysis workflow, one dashboard view.
No auth, no multi-user, no cloud deployment required.

**Status legend:** `[ ] pending` · `[-] in progress` · `[x] done`

---

## Architecture

```
Developer (browser)
  │
  ▼
React Dashboard  ──── REST ────▶  FastAPI Backend
                                      │
                              Orchestrator Service
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼           ▼
                     Impact       Code/Sec    Test-Gap    Test-Gen
                     Subagent     Subagent    Subagent    Subagent
                       (Bob)       (Bob)       (Bob)       (Bob)
                          └───────────┼───────────┘
                                      ▼
                              Report Assembler
                                      │
                              JSON result store
```

Bob subagents are invoked via the Bob CLI / API from inside the FastAPI backend.
Each subagent is a focused Bob session with its own skill and context.

---

## Folder Structure (target)

```
ibm-bob-2-hackathon/
├── README.md
├── changeguard-plan.md             ← this file
│
├── frontend/                       ← React + Vite + Tailwind
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── client.js           ← axios wrapper for backend
│   │   ├── components/
│   │   │   ├── DiffSelector.jsx    ← pick/paste a diff
│   │   │   ├── AnalysisRunner.jsx  ← trigger analysis, show progress
│   │   │   ├── ReportDashboard.jsx ← tabbed results view
│   │   │   ├── ImpactPanel.jsx
│   │   │   ├── CodeReviewPanel.jsx
│   │   │   ├── SecurityPanel.jsx
│   │   │   ├── TestGapPanel.jsx
│   │   │   ├── TestGenPanel.jsx
│   │   │   ├── TestResultsPanel.jsx
│   │   │   └── ReleaseBadge.jsx    ← GO / CAUTION / BLOCK verdict
│   │   └── hooks/
│   │       └── useAnalysis.js      ← polling hook for job status
│   └── public/
│
├── backend/
│   ├── requirements.txt
│   ├── main.py                     ← FastAPI app entry point
│   ├── routers/
│   │   ├── analysis.py             ← POST /analysis, GET /analysis/{id}
│   │   └── reports.py              ← GET /reports, GET /reports/{id}
│   ├── services/
│   │   ├── orchestrator.py         ← runs Bob subagents in parallel
│   │   ├── diff_parser.py          ← parses unified diff into structured data
│   │   ├── test_runner.py          ← executes pytest on sample project
│   │   └── report_assembler.py     ← merges subagent outputs → report JSON
│   ├── bob_agents/
│   │   ├── impact_agent.md         ← Bob skill/prompt for impact analysis
│   │   ├── code_review_agent.md    ← Bob skill/prompt for code + security
│   │   ├── test_gap_agent.md       ← Bob skill/prompt for test gap analysis
│   │   └── test_gen_agent.md       ← Bob skill/prompt for test generation
│   ├── models/
│   │   └── schemas.py              ← Pydantic models
│   └── data/
│       └── results/                ← JSON result files (one per analysis run)
│
├── sample_project/                 ← synthetic intentionally-flawed Python app
│   ├── README.md
│   ├── app/
│   │   ├── auth.py                 ← contains auth bugs + security issues
│   │   ├── calculator.py           ← arithmetic logic with edge-case bugs
│   │   ├── data_processor.py       ← SQL injection risk, missing validation
│   │   └── user_manager.py         ← logic bugs, missing tests
│   ├── tests/
│   │   ├── test_calculator.py      ← partial coverage only
│   │   └── test_auth.py            ← thin, missing negative paths
│   └── diffs/
│       ├── diff_001_add_discount.patch   ← sample diff 1: feature addition
│       ├── diff_002_fix_login.patch      ← sample diff 2: security fix
│       └── diff_003_refactor_data.patch  ← sample diff 3: risky refactor
│
├── tests/                          ← integration/e2e tests for ChangeGuard itself
│   ├── test_diff_parser.py
│   ├── test_orchestrator.py
│   └── test_report_assembler.py
│
├── docs/
│   ├── architecture.md
│   └── demo-script.md              ← step-by-step hackathon demo walkthrough
│
└── bob_sessions/                   ← saved Bob session logs for demo replay
    ├── session_impact.md
    ├── session_code_review.md
    ├── session_test_gap.md
    └── session_test_gen.md
```

---

## Sub-Tasks

---

### ST-01 · Sample Project Creation
**Status:** [ ] pending

**Intent:**  
Create the synthetic sample Python project that all ChangeGuard analysis will target.
It must contain realistic but intentionally flawed code — bugs, security issues, missing tests —
so that every analysis stage produces meaningful, visible output during the demo.

**Expected Outcomes:**
- `sample_project/app/` contains four Python modules with documented flaws.
- `sample_project/tests/` contains partial tests (some coverage, obvious gaps).
- `sample_project/diffs/` contains three `.patch` files representing realistic developer changes.
- The project is runnable with `pytest` and produces pass/fail results.
- No personal, confidential, or proprietary data anywhere.

**Todo List:**
1. Create `sample_project/app/calculator.py` — division-by-zero, off-by-one edge cases.
2. Create `sample_project/app/auth.py` — hardcoded secret, timing-attack-vulnerable comparison, plaintext password logging.
3. Create `sample_project/app/data_processor.py` — SQL injection via f-string query, missing input validation.
4. Create `sample_project/app/user_manager.py` — missing null checks, logic bug in role assignment.
5. Create `sample_project/tests/test_calculator.py` — covers happy path only (gaps visible to Bob).
6. Create `sample_project/tests/test_auth.py` — only tests successful login, misses failure paths.
7. Create three `.patch` files in `sample_project/diffs/` representing real-looking unified diffs.
8. Add `sample_project/README.md` describing the project and its known flaws.
9. Verify `pytest sample_project/tests/` runs cleanly.

**Relevant Context:**
- All code is fictional and safe for public demo.
- Flaws must be obvious enough for Bob to detect but realistic enough to be instructive.

---

### ST-02 · Backend Foundation
**Status:** [ ] pending

**Intent:**  
Scaffold the FastAPI backend with routing, Pydantic schemas, and the diff-parsing service.
This is pure application code — no Bob involvement yet.

**Expected Outcomes:**
- `backend/main.py` starts a FastAPI server on port 8000.
- `POST /analysis` accepts a diff (string or file) and a diff_id, returns a job `id`.
- `GET /analysis/{id}` returns current job status and partial/complete results.
- `GET /reports` returns a list of completed reports.
- `GET /reports/{id}` returns a full report JSON.
- `backend/services/diff_parser.py` correctly parses a unified diff into changed-file/changed-function structures.
- Unit tests for `diff_parser` pass.

**Todo List:**
1. Create `backend/requirements.txt` (fastapi, uvicorn, pydantic, pytest, httpx, python-multipart).
2. Create `backend/models/schemas.py` with Pydantic models: `AnalysisRequest`, `AnalysisJob`, `AnalysisResult`, `ReleaseReport`.
3. Create `backend/main.py` with FastAPI app, CORS, and router inclusion.
4. Create `backend/routers/analysis.py` with POST and GET endpoints.
5. Create `backend/routers/reports.py` with GET endpoints.
6. Create `backend/services/diff_parser.py` parsing unified diff → `{file, added_lines, removed_lines, changed_functions}`.
7. Create `backend/data/results/` directory and a JSON store helper.
8. Write `tests/test_diff_parser.py` against all three sample diffs.
9. Verify `uvicorn backend.main:app` starts without errors.

**Relevant Context:**
- Jobs are stored as JSON files in `backend/data/results/`.
- No database needed; file-based store keeps setup simple.
- CORS must allow `localhost:5173` (Vite dev server default).

---

### ST-03 · Bob Agent Definitions
**Status:** [ ] pending

**Intent:**  
Define the four Bob subagent roles as structured prompt/skill files.
These are the core IBM Bob artefacts — they demonstrate Bob running focused, parallel,
context-aware AI analysis rather than being used as a generic coding assistant.

**Expected Outcomes:**
- Four `backend/bob_agents/*.md` files, each defining a focused Bob analysis role.
- Each file contains: role description, input format, output format (JSON schema), analysis checklist, and output constraints.
- The files are self-contained enough for a Bob Agent session to follow without additional context.

**Todo List:**
1. Create `backend/bob_agents/impact_agent.md`:
   - Role: Identify changed files and functions, map call-graph dependencies, flag ripple-risk areas.
   - Input: parsed diff JSON.
   - Output: `{changed_files[], changed_functions[], dependency_map{}, ripple_risk_areas[]}`.
2. Create `backend/bob_agents/code_review_agent.md`:
   - Role: Detect bugs, code-quality issues, and security vulnerabilities in changed code.
   - Input: diff + changed-function context.
   - Output: `{bugs[], quality_issues[], security_issues[], severity_counts{}}`.
3. Create `backend/bob_agents/test_gap_agent.md`:
   - Role: Analyse existing tests vs changed functions, identify untested paths and edge cases.
   - Input: changed functions + existing test file list.
   - Output: `{covered_functions[], uncovered_functions[], missing_edge_cases[], gap_score}`.
4. Create `backend/bob_agents/test_gen_agent.md`:
   - Role: Generate pytest test cases for the identified gaps.
   - Input: gap analysis output + source function signatures.
   - Output: `{generated_tests: [{function, test_code, rationale}]}`.
5. Review all four files for consistency of input/output contract.

**Relevant Context:**
- These files are both Bob session starters AND documentation of the AI workflow.
- The orchestrator service (ST-04) will pass these files as system prompts to Bob CLI invocations.
- Bob subagents should be invoked in Plan mode first to confirm strategy, then Agent mode for execution.

---

### ST-04 · Orchestrator and Report Assembler
**Status:** [ ] pending

**Intent:**  
Build the Python service that invokes the four Bob subagents concurrently, collects their outputs,
runs pytest on any generated tests, and assembles the final Release Readiness Report.
This is where IBM Bob's subagent + parallel capability is demonstrated.

**Expected Outcomes:**
- `backend/services/orchestrator.py` launches all four Bob subagents concurrently (using `asyncio` or `concurrent.futures`).
- Each subagent call writes a structured JSON result file.
- `backend/services/test_runner.py` appends generated test code to the sample project and runs `pytest`, capturing pass/fail/error.
- `backend/services/report_assembler.py` merges all four results + test run output into a final `ReleaseReport` JSON.
- The release verdict logic: BLOCK if any critical security issue; CAUTION if bugs or test gaps above threshold; GO otherwise.
- `tests/test_orchestrator.py` and `tests/test_report_assembler.py` pass with mocked Bob outputs.

**Todo List:**
1. Create `backend/services/orchestrator.py`:
   - Accept parsed diff + analysis job id.
   - Invoke `impact_agent`, `code_review_agent`, `test_gap_agent` concurrently.
   - After gap analysis, invoke `test_gen_agent` sequentially (depends on gap output).
   - Persist partial results to JSON after each agent completes.
   - Update job status to `running → partial → complete`.
2. Create `backend/services/test_runner.py`:
   - Write generated test code to a temp file in `sample_project/tests/`.
   - Execute `pytest` via subprocess, capture stdout/stderr/exit code.
   - Parse pytest output into `{passed, failed, errors, test_lines[]}`.
3. Create `backend/services/report_assembler.py`:
   - Merge all subagent JSON outputs into `ReleaseReport` schema.
   - Compute `release_verdict`: GO / CAUTION / BLOCK.
   - Compute summary counts for dashboard badges.
4. Write unit tests with mocked Bob outputs for orchestrator and assembler.
5. Verify end-to-end: submit a sample diff, get a complete report JSON.

**Relevant Context:**
- Bob CLI invocation pattern: `bob --skill backend/bob_agents/<agent>.md --input <input.json> --output <output.json>`.
- If Bob CLI invocation details change, the orchestrator must be updated accordingly.
- The `test_gen_agent` depends on `test_gap_agent` output — do not run it in the parallel batch.

---

### ST-05 · Frontend Dashboard
**Status:** [ ] pending

**Intent:**  
Build the React dashboard that lets a developer select a pre-made diff or paste their own,
trigger the analysis, watch live progress, and view all results in a tabbed report view.
This is standard application code; Bob does not build the frontend.

**Expected Outcomes:**
- `frontend/` is a working Vite + React + Tailwind app.
- `DiffSelector` component allows choosing one of the three sample diffs or pasting a custom diff.
- `AnalysisRunner` component submits the diff, then polls `GET /analysis/{id}` and shows a progress indicator per subagent.
- `ReportDashboard` shows a tabbed layout with: Impact · Code Review · Security · Test Gaps · Generated Tests · Test Results · Release Verdict.
- `ReleaseBadge` shows GO (green) / CAUTION (amber) / BLOCK (red) with summary counts.
- Frontend communicates with backend via `frontend/src/api/client.js`.
- Application runs on `localhost:5173` with `npm run dev`.

**Todo List:**
1. Scaffold Vite + React project in `frontend/` with Tailwind CSS configured.
2. Create `frontend/src/api/client.js` wrapping fetch/axios for all backend calls.
3. Create `frontend/src/hooks/useAnalysis.js` — polls `/analysis/{id}` every 2 s until status is `complete`.
4. Create `DiffSelector.jsx` — dropdown of sample diffs + textarea for custom paste.
5. Create `AnalysisRunner.jsx` — submit button, four progress indicators (one per subagent), status text.
6. Create `ImpactPanel.jsx` — lists changed files, functions, and ripple-risk areas.
7. Create `CodeReviewPanel.jsx` — lists bugs and quality issues with severity badges.
8. Create `SecurityPanel.jsx` — lists security issues; critical issues highlighted prominently.
9. Create `TestGapPanel.jsx` — shows gap score, covered vs uncovered function lists.
10. Create `TestGenPanel.jsx` — shows generated test code in a syntax-highlighted block.
11. Create `TestResultsPanel.jsx` — shows pytest pass/fail counts, error messages.
12. Create `ReleaseBadge.jsx` — large GO/CAUTION/BLOCK badge with counts.
13. Create `ReportDashboard.jsx` — assembles all panels into tabbed layout.
14. Create `App.jsx` — top-level layout wiring `DiffSelector` → `AnalysisRunner` → `ReportDashboard`.
15. Verify `npm run dev` starts and the full flow renders with a sample report.

**Relevant Context:**
- Tailwind utility classes keep styling self-contained; no separate CSS files needed.
- Use React state for tab selection and analysis job tracking.
- The polling hook must handle `error` status from the backend gracefully.

---

### ST-06 · Bob Workflow Demonstration Artefacts
**Status:** [ ] pending

**Intent:**  
Create the Bob session logs, demo script, and supporting files that make IBM Bob's role
visible and reproducible during the hackathon presentation.
These artefacts prove that Bob is part of the runtime workflow, not just used to write code.

**Expected Outcomes:**
- `bob_sessions/` contains four markdown files, one per subagent, showing a real Bob session transcript.
- `docs/demo-script.md` provides a step-by-step walkthrough a presenter can follow live.
- `docs/architecture.md` describes the full system with Bob's role called out explicitly.
- The repo README is updated to describe ChangeGuard, setup instructions, and how Bob fits in.

**Todo List:**
1. Run a real Bob session for each of the four analysis agents against `diff_001_add_discount.patch`.
2. Save each session transcript to `bob_sessions/session_<agent>.md`.
3. Write `docs/demo-script.md`: steps from "open dashboard" to "read release report", highlighting each Bob call.
4. Write `docs/architecture.md`: system overview, Bob integration points, data flow.
5. Update `README.md`: project description, quickstart (backend + frontend), Bob workflow explanation.

**Relevant Context:**
- Session transcripts must show Bob in Plan mode (analysis strategy) and Agent mode (execution).
- The demo script should be usable even if live internet is unreliable — outputs should be pre-cached.

---

### ST-07 · Integration Testing and Hardening
**Status:** [ ] pending

**Intent:**  
Verify the complete end-to-end flow works reliably before the hackathon demo.
Fix any integration breaks and ensure the demo can be repeated multiple times without state issues.

**Expected Outcomes:**
- Full flow (diff selection → analysis → report) completes for all three sample diffs.
- All `pytest tests/` tests pass.
- Frontend shows no console errors for the happy path.
- Re-running an analysis on the same diff produces consistent results (idempotency check).
- A reset script or instructions clear prior results for a fresh demo run.

**Todo List:**
1. Run `pytest tests/` and fix any failures.
2. Run the full frontend flow for each of the three sample diffs; record any UI bugs.
3. Fix any issues found.
4. Add a `scripts/reset_demo.sh` (or `.ps1`) that deletes `backend/data/results/*` and any temp test files.
5. Verify the reset script leaves the repo in a clean demo-ready state.
6. Do a final end-to-end rehearsal of the demo script.

**Relevant Context:**
- The demo script from ST-06 should be used as the test specification here.
- Any Bob session caching should be verified — stale cache must not corrupt a fresh run.

---

## Data Structures

### AnalysisRequest
```json
{
  "diff_id": "diff_001_add_discount",
  "diff_text": "<unified diff string>",
  "label": "Add discount feature"
}
```

### AnalysisJob
```json
{
  "id": "uuid",
  "status": "queued | running | partial | complete | error",
  "diff_id": "diff_001_add_discount",
  "created_at": "ISO8601",
  "subagent_status": {
    "impact": "pending | running | done | error",
    "code_review": "pending | running | done | error",
    "test_gap": "pending | running | done | error",
    "test_gen": "pending | running | done | error",
    "test_run": "pending | running | done | error"
  },
  "report_id": "uuid | null"
}
```

### ReleaseReport
```json
{
  "id": "uuid",
  "job_id": "uuid",
  "diff_id": "string",
  "created_at": "ISO8601",
  "release_verdict": "GO | CAUTION | BLOCK",
  "impact": { "changed_files": [], "changed_functions": [], "ripple_risk_areas": [] },
  "code_review": { "bugs": [], "quality_issues": [], "security_issues": [], "severity_counts": {} },
  "test_gap": { "covered_functions": [], "uncovered_functions": [], "missing_edge_cases": [], "gap_score": 0.0 },
  "test_gen": { "generated_tests": [{ "function": "", "test_code": "", "rationale": "" }] },
  "test_run": { "passed": 0, "failed": 0, "errors": 0, "output": "" }
}
```

---

## IBM Bob Workflow

Bob is invoked at **runtime** by the FastAPI orchestrator, not only during development.

| Stage | Bob Mode | Bob Role |
|---|---|---|
| Analysis session start | Plan | Bob plans analysis strategy for the given diff |
| Impact analysis | Agent + Subagent | Focused agent maps changed files/functions and call graph |
| Code & security review | Agent + Subagent | Focused agent reviews code and flags bugs/security issues |
| Test gap analysis | Agent + Subagent | Focused agent compares changed functions to existing tests |
| Test generation | Agent + Subagent | Focused agent generates pytest test cases for gaps |
| Report assembly | Agent | Bob assembles all subagent outputs into final report |

All four analysis subagents run concurrently (impact, code review, test gap).
Test generation runs after test gap analysis completes (sequential dependency).

---

## Deployment Approach

**Hackathon demo (local):**
1. `cd backend && uvicorn main:app --reload` — runs on port 8000.
2. `cd frontend && npm run dev` — runs on port 5173.
3. Both processes run on the presenter's laptop.
4. No Docker, no cloud needed for the demo.

**If a public URL is needed:**
- Backend: deploy to Railway or Render (free tier, zero-config Python).
- Frontend: deploy to Vercel or Netlify (free tier, zero-config Vite).
- No environment variables or secrets needed for the demo.

---

## Risks and Scope-Control

| Risk | Mitigation |
|---|---|
| Bob CLI invocation is slow per call | Pre-cache Bob outputs for the three sample diffs; show live only for the custom-diff path |
| Bob output format is inconsistent | Define strict JSON output schemas in each agent .md; add a validation/fallback layer in the assembler |
| Test generation produces non-runnable code | Cap test-gen output to simple assertions; validate syntax before writing to disk |
| Frontend polish takes too long | Use Tailwind utility classes only; no custom CSS; prioritise data visibility over aesthetics |
| Four people stepping on each other | ST-01 and ST-02 can be done in parallel; ST-03 and ST-04 unblock ST-05; assign one owner per sub-task |
| Demo environment unreliable | Pre-save all Bob session outputs; demo can run fully offline from cached results |
| Scope creep | No auth, no multi-user, no history UI beyond the last run, no cloud infra |

---

## Development Sequence

```
Day 1:
  ST-01 Sample Project         (person A)
  ST-02 Backend Foundation     (person B)

Day 1 afternoon / Day 2 morning:
  ST-03 Bob Agent Definitions  (person C — unblocks ST-04)
  ST-05 Frontend scaffold      (person D — start with static mock data)

Day 2:
  ST-04 Orchestrator           (person B, after ST-02 and ST-03)
  ST-05 Frontend (wire up)     (person D, after ST-04 API is live)

Day 2 afternoon:
  ST-06 Bob Demo Artefacts     (person C, run real Bob sessions)
  ST-07 Integration + Hardening (all four together)
```
