# RecoNexus — Product Requirements Document
Version 0.1 • 18 October 2026 • Status: proposed baseline

## 1. Product outcome and problem
Financial operations staff compare independently generated transaction records, investigate differences and maintain evidence of resolution. Spreadsheet comparison separates matching, ownership and evidence, making it difficult to establish what was reconciled, which rules were used, and why a case was closed.
RecoNexus will provide a reproducible reconciliation run and a traceable exception workspace. It is a synthetic-data portfolio application, with simulated source integrations, not a banking system or an accounting ledger.

## 2. Hypotheses and discovery
Hypothesis H1: deterministic exact matching reduces repetitive comparison work. H2: consolidated evidence reduces investigation time. H3: review gates improve traceability. These are unvalidated hypotheses, not measured business benefits.
Interview 3–5 operations users or use explicitly labeled proxy interviews. Ask about volumes, source cutoffs, reference quality, correction procedures, case ownership, and approval thresholds. Record observed workflows separately from assumptions. Validate whether source records represent posted transactions or settlement aggregates before adding aggregation rules.
Sponsor: portfolio product owner; operational owner: reconciliation manager; technical owner: developer; control owner: reviewer. In a demo one person may simulate multiple users, but maker and checker identities must differ.

## 3. Personas and jobs
| Persona | Job | Main pain | Product outcome |
|---|---|---|---|
| Analyst | Compare sources and investigate exceptions | Repeated spreadsheet work | Evidence and clear case ownership |
| Operations manager | Prioritize work and monitor cutoffs | Hidden backlog | Exposure and SLA visibility |
| Reviewer | Approve justified resolutions | Missing rationale | Evidence-backed decision history |
| Auditor | Reconstruct decisions | Fragmented history | Read-only export and lineage |
| Product manager | Evaluate workflow effectiveness | Unclear denominators | Versioned, comparable metrics |

## 4. Scope and releases
### MVP (first functioning release)
Single demo organization; two configured sources; INR only; UTF-8 CSV with fixed template; atomic batch validation; immutable imported records; exact reference/date/amount/direction matching; candidate ambiguity detection; unmatched and duplicate exceptions; persistent PostgreSQL runs; analyst and reviewer roles; authenticated case actions; review workflow; append-only application audit; operational dashboard; labeled fixtures and regression tests.
### Next release
Configurable source mappings, Excel adapters, business-calendar tolerance, controlled one-to-many matching, notification/SLA worker, evidence-grounded AI investigation, approved Jira escalation and status sync.
### Excluded
Real bank connectivity, payments, journal posting, ledger corrections, FX conversion, real KYC/PII, autonomous closure, automatic monetary write-offs, universal accounting compliance claims, multi-tenant production deployment.

## 5. Functional requirements and acceptance criteria
| ID / priority | Requirement | Acceptance criteria |
|---|---|---|
| ING-01 P0 | Validate imports | Reject entire batch on bad headers, dates, IDs, currency, direction or amounts; return row/field errors; no partial transactions |
| ING-02 P0 | Idempotent ingestion | Same source + file SHA-256 returns original batch; same key with changed payload returns conflict; unique source record ID prevents reinsertion |
| ING-03 P0 | Preserve lineage | Every accepted transaction links source, batch, row, raw-file hash and original reference |
| REC-01 P0 | Exact matching | Unique reference, currency, signed amount and date on each side yield one group with recorded rule version |
| REC-02 P0 | Avoid double use | A transaction belongs to at most one committed group in its reconciliation scope; overlapping runs serialize or conflict |
| REC-03 P0 | Handle uncertainty | Multiple candidates yield ambiguity; reused references are not silently paired; missing side becomes exception |
| REC-04 P0 | Reproducibility | Sealed input membership and rule version produce identical canonical output hash |
| EXC-01 P0 | Investigate | Analyst sees both source records, rule, reason, exposure, history and evidence; can claim and propose resolution |
| EXC-02 P0 | Review | Separate reviewer accepts/rejects a versioned proposal; rejected proposals return to investigation; stale updates return 409 |
| AUD-01 P0 | Audit | Data mutation and event commit in same DB transaction; failure rolls back both |
| IAM-01 P0 | Authorize | API enforces role/object access; denied actions return 403 without mutations |
| ANA-01 P1 | Measure | Display metric period, currency, denominator and last successful run; no fabricated improvements |
| AI-01 P2 | Assist | Read-only tools; every factual claim cites allowed evidence IDs; invalid citations fail verification; no closure capability |
| JIR-01 P2 | Escalate | Approved escalation uses stable external key and outbox; retries never create duplicate tickets |

## 6. UX requirements
Primary navigation: Overview, Imports, Runs, Exceptions, Audit, Settings. Imports shows template, preview, validation errors and explicit commit. Runs shows sources, cutoff, immutable rule version and count conservation. Exception list filters by status, owner, severity and age. Detail screen has side-by-side records, differences, evidence, timeline, proposal and reviewer panel. Confirmation includes concrete action and rationale. Empty/error/loading states are explicit; keyboard navigation, labeled inputs and responsive layouts are required. Financial values always display currency and two decimal places. AI output is labeled as a suggestion and remains distinct from source evidence.

## 7. Business conventions
Scope = organization + source pair + reconciliation period + currency. Amount is a positive decimal magnitude; direction CREDIT/DEBIT is relative to a documented common account perspective. Adapters map source signs; no implicit absolute-value conversion. MVP dates are ISO business dates agreed by both sources; UTC timestamps record system actions. Reference normalization trims surrounding whitespace only, remains case-sensitive, preserves raw text; blank reference never auto-matches. INR has two fractional digits; reject excess precision rather than round. Fees, reversals, net settlement and cross-currency records remain exceptions until explicit rules exist.
An exception is a workflow object, not proof of financial loss. Exposure is an operational unmatched amount, reported by currency and side; do not sum both legs of the same discrepancy or imply it is a ledger balance.

## 8. Nonfunctional requirements
Proposed targets, not achieved: 10,000 rows per source under 10 seconds for reconciliation on a documented 2-vCPU/4-GB environment; upload limit 10 MB and 100,000 rows; bounded parsing; paginated APIs; no sensitive raw payloads in logs. Correctness gates: zero false-positive matches on golden fixtures; zero transaction reuse; 100% accepted mutations have an audit event. Use DB constraints, request IDs, timeouts and structured error codes. Secrets remain server-side. Raw files are private and hashed. Retention default for synthetic demo is 30 days, configurable; deletion records a tombstone and respects evidence references. Backup/restore drill required before deployment.

## 9. Metrics and evaluation
| Metric | Definition | Initial target |
|---|---|---|
| Automatic match rate | Auto-matched eligible records / eligible records in sealed run | Report observed; dataset-dependent |
| Precision | Correct predicted pair edges / all predicted edges | 100% on golden fixtures |
| Recall | Correct predicted edges / all labeled true edges | Report per rule; no forced matching |
| Completeness | Input rows accounted as matched, excepted or explicitly excluded / total rows | 100% |
| Resolution time | Closed_at − opened_at, median and p90 | Baseline first |
| Manual investigation time | Active analyst time from measured sessions | Compare paired tasks |
| Exposure | Unresolved source-side magnitude, currency separated | Reconciles to exception drilldown |
| SLA breach rate | Cases overdue as of cutoff / cases with due date | Report baseline |
| AI acceptance | Accepted verified suggestions / reviewed suggestions | Track with rejection reasons |
| Audit coverage | Committed controlled mutations with valid event / controlled mutations | 100% |
Benchmark with seeded labeled datasets including clean pairs, duplicates, missing sides, reused references, wrong amounts/dates, blank references and adversarial AI evidence. Keep training/demo fixtures separate from held-out evaluation. Publish environment, seed, dataset hash, rules, counts, timing and failures.

## 10. Risks and decisions
False matches outweigh higher automation rate: route ambiguity for review. Duplicate source record IDs may be upstream corrections: quarantine conflict and require a new version, never overwrite. Calendar differences require source-specific cutoff policy. AI hallucination is controlled through read-only evidence and verification. Jira outages require retryable outbox. Production immutability requires DB privilege separation and external audit retention; an append-only UI alone is insufficient.

## 11. Release gate
Persistent ingest→run→exception→proposal→independent review→audit flow passes integration tests; authorization and concurrency tests pass; counts conserve; recovery and export demonstrated; no critical security defects; README can reproduce locally. Frontend mockups, AI demos or this foundation alone do not satisfy the release gate.
