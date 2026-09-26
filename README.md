# ChangeGuard MVP

**Code Change Risk & Release Readiness Analysis**

ChangeGuard analyses a code diff and produces a developer-facing risk report in seconds — no AI service required, no accounts, no cloud.

---

## What it does

1. **Select a code change** — choose one of three synthetic sample diffs or paste your own unified diff
2. **Analyse the change** — the backend runs five analysis stages:
   - Impact analysis (changed files, functions, ripple-risk areas)
   - Code & bug review (logic errors, edge cases)
   - Security review (injection, hardcoded secrets, weak crypto)
   - Test gap analysis (uncovered functions, missing edge cases)
   - Test generation & execution (targeted pytest cases run against the real sample project)
3. **Read the report** — a tabbed dashboard shows all findings with severity badges
4. **Release verdict** — `GO` / `CAUTION` / `BLOCK` based on what was found

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Start the API server (port 8000)
python -m uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # opens on http://localhost:5173
```

### Run tests

```bash
python -m pytest tests/ sample_project/tests/ -v
```

---

## Project Structure

```
ibm-bob-2-hackathon/
├── backend/
│   ├── main.py                  ← FastAPI entry point (port 8000)
│   ├── models/schemas.py        ← Pydantic models
│   ├── routers/                 ← REST endpoints
│   ├── services/
│   │   ├── diff_parser.py       ← Unified diff → structured data
│   │   ├── analyzer.py          ← Static analysis engine (bugs, security, gaps)
│   │   ├── test_runner.py       ← Runs generated pytest tests
│   │   ├── report_assembler.py  ← Merges results → ReleaseReport + verdict
│   │   ├── orchestrator.py      ← Drives the 5-stage pipeline
│   │   └── store.py             ← JSON file persistence
│   └── data/results/            ← Job + report JSON files
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              ← Top-level layout
│   │   ├── api/client.js        ← Backend API calls
│   │   ├── hooks/useAnalysis.js ← Polling hook
│   │   ├── data/sampleDiffs.js  ← Bundled sample diffs
│   │   └── components/          ← Dashboard panels
│   └── vite.config.js           ← Proxies /analysis and /reports to :8000
│
├── sample_project/              ← Synthetic intentionally-flawed Python app
│   ├── app/
│   │   ├── calculator.py        ← Division-by-zero, wrong formula
│   │   ├── auth.py              ← Hardcoded key, plaintext password log, weak token
│   │   ├── data_processor.py    ← SQL injection, path traversal
│   │   └── user_manager.py      ← Role logic bug, NoneType crash
│   ├── tests/                   ← Partial tests (intentional gaps)
│   └── diffs/                   ← Three sample .patch files
│
└── tests/                       ← ChangeGuard backend tests (24 passing)
    ├── test_diff_parser.py
    ├── test_orchestrator.py
    └── test_report_assembler.py
```

---

## Sample Diffs

| Diff | Description | Expected Verdict |
|------|-------------|-----------------|
| `diff_001_add_discount` | Adds calculator functions — division-by-zero, wrong formula | CAUTION |
| `diff_002_fix_login` | Auth module — hardcoded secret, plaintext password log, weak MD5 token | BLOCK |
| `diff_003_refactor_data` | Data processor — SQL injection, path traversal | BLOCK |

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analysis` | Start analysis job |
| `GET`  | `/analysis/{id}` | Poll job status |
| `GET`  | `/reports` | List completed reports |
| `GET`  | `/reports/{id}` | Get full report |
| `GET`  | `/health` | Health check |

---

## Reset demo state

```powershell
Remove-Item backend\data\results\* -Force
```

---

## Stack

- **Frontend:** React 18 + Vite 5 + Tailwind CSS 3
- **Backend:** Python 3.11+ + FastAPI + Pydantic v2 + pytest
- **Persistence:** JSON files (no database)
- **Auth:** None
