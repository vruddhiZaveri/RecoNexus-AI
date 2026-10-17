# Sprint 1 — trustworthy ingestion foundation
Proposed duration: 10 working days. Priority order is dependency-driven, estimates are planning assumptions. Sprint goal: authenticated, persistent ingestion with observable lineage and repeat-safe behavior. Exact matching domain code can be developed early, but is not exposed as a persistent reconciliation run until integrity controls exist.

| Order | Story | Points | Dependency | Done when |
|---|---|---:|---|---|
| P0-1 | Confirm conventions and golden fixtures | 2 | None | Direction/date/reference decisions and expected outcomes reviewed |
| P0-2 | Repository, Python environment, FastAPI health and CI | 2 | None | Documented commands; health smoke and test job pass |
| P0-3 | PostgreSQL migrations and least-privilege roles | 3 | P0-1 | Fresh migration and rollback/reapply tested locally |
| P0-4 | Strict CSV parser and monetary domain | 3 | P0-1 | Invalid rows reject atomic batch; float/excess precision rejected |
| P0-5 | Idempotent persistent ingestion | 5 | P0-3,4 | Retry returns same batch; changed replay and concurrent duplicates conflict safely |
| P0-6 | Authenticated actor and audit transaction | 3 | P0-3 | No actor spoofing; denial and rollback tests pass |
| P1-7 | Upload UI with preview/errors/receipt | 3 | P0-5,6 | Keyboard accessible upload against real API; safe error messages |
| P1-8 | Sprint demo and runbook | 2 | All P0 | Reproduce from empty DB, retry import, inspect lineage and audit |
Total: 23 points. If capacity is lower, move upload UI and documentation polish; do not remove integrity controls. Sprint 2: persist sealed exact-match runs and exception creation. Sprint 3: case/review UX and analytics. Later: tolerance, AI, Jira.

## Current implementation checkpoint
Created in this handoff: product/architecture specifications; proposed SQL schema; strict domain parser; pure exact matcher; regression tests; optional FastAPI health scaffold; synthetic fixtures. Not yet implemented: PostgreSQL integration/migrations, auth, upload API, frontend, persistent runs or audit enforcement. Do not treat SQL design as a deployed database.

## Learning sequence
1. Business: wrong financial matches hide discrepancies. Requirement: only unique evidence qualifies. UX: explain ambiguous cases. Architecture: pure domain function enables reproducible tests. APM relevance: trade precision against automation with a measurable acceptance gate.
2. Business: file retries must not duplicate exposure. Requirement: identity and payload must agree. UX: show original batch receipt on replay. Architecture: unique DB constraints plus transactional writes. Tests: simultaneous uploads, changed payload, mid-commit failure. Metric: replay creates zero extra records. APM relevance: reliable operations and reduced support burden.
3. Business: decisions need accountability. Requirement: maker-checker and evidence. UX: versioned proposal and explicit review. Architecture: optimistic case version, role checks and same-transaction audit. Tests: self-approval, stale proposal, rollback. Metric: 100% controlled mutation coverage. APM relevance: stakeholder controls and release readiness.

## Windows setup and next implementation step
This package was created in a Linux workspace. It does not create or verify your Windows directory.
PowerShell:
```powershell
New-Item -ItemType Directory -Force 'C:\1_PLACEMENT\FINAL PROJECTS\RECONEXUS'
Set-Location 'C:\1_PLACEMENT\FINAL PROJECTS\RECONEXUS'
# Extract the ZIP contents here; ensure backend and docs are directly beneath this folder.
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m unittest discover -s backend\tests -v
python -m uvicorn backend.app.main:app --reload
```
Open http://127.0.0.1:8000/health and /docs. Requirements are bounded candidates, not an installed lockfile. Resolve in your environment, run dependency/security checks, and commit an exact lock before release. Next build task: turn schema into migrations and implement transactional batch repository, then POST /batches; do not start AI before this path works.
