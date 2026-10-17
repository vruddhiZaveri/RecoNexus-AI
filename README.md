# RecoNexus
Financial reconciliation and exception management — initial foundation.

Start with docs/PRODUCT_REQUIREMENTS.md, docs/WORKFLOW_ARCHITECTURE.md, docs/SCHEMA.sql and docs/SPRINT_1.md.

From this directory, run `python -m unittest discover -s backend/tests -v` (Python 3.11+; domain tests use standard library only).
Optional API: install backend/requirements.txt then `python -m uvicorn backend.app.main:app --reload`. Only /health is implemented; it explicitly does not assert database readiness. FastAPI dependency installation and HTTP smoke testing are pending.

Sample source_a/source_b files should yield one matched pair and two source-side field-discrepancy records. Domain output is a per-record diagnostic, not yet consolidated business exception cases. Future service groups related discrepancies into one case to avoid double-counted exposure. No persistent ingestion, authentication, frontend, AI or Jira is implemented yet.

Run tests before adding persistent services. Windows instructions and next steps are in Sprint 1. Do not use real financial data. All performance figures in docs are targets, not results.
