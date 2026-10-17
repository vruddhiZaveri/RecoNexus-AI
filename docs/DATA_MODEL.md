# Database relationships and implementation notes
SCHEMA.sql contains proposed executable DDL, not an applied migration. UUID primary keys are generated server-side. Records have stable source identities; changed source payloads create an ingestion conflict, never an overwrite. Run inputs seal the evaluated population. Match membership uniqueness prevents reuse inside scope; overlapping scopes require an explicit source-pair policy and lock before any write.

```mermaid
erDiagram
    SOURCES ||--o{ BATCHES : delivers
    BATCHES ||--o{ TRANSACTIONS : contains
    SCOPES ||--o{ RUNS : owns
    MATCHING_RULES ||--o{ RUNS : governs
    RUNS ||--o{ RUN_INPUTS : seals
    TRANSACTIONS ||--o{ RUN_INPUTS : participates
    RUNS ||--o{ MATCH_GROUPS : produces
    MATCH_GROUPS ||--o{ MATCH_MEMBERS : contains
    TRANSACTIONS ||--o{ MATCH_MEMBERS : consumes
    RUNS ||--o{ EXCEPTIONS : raises
    EXCEPTIONS ||--o{ EXCEPTION_TRANSACTIONS : references
    TRANSACTIONS ||--o{ EXCEPTION_TRANSACTIONS : explains
    EXCEPTIONS ||--o{ INVESTIGATIONS : records
    EXCEPTIONS ||--o{ EVIDENCE : collects
    EXCEPTIONS ||--o{ RECOMMENDATIONS : suggests
    EXCEPTIONS ||--o{ PROPOSALS : proposes
    PROPOSALS ||--o| REVIEW_DECISIONS : receives
    EXCEPTIONS ||--o{ JIRA_TICKETS : escalates
```
Audit logs point to affected resource IDs polymorphically; service validation establishes valid references. The outbox records external delivery intent within the originating transaction. Foreign keys establish identity, not authorization. Application checks must verify that evidence, proposals and recommendations belong to the same case; deploy DB triggers or constrained procedures as defense in depth.

Exact-v1 accepts one record from each side. Later one-to-many needs explicit bounded group rules, shared reference, currency/direction agreement, exact Decimal totals and unique consumption; no unrestricted subset search. Tolerance rules need approved fee policy and business-calendar date interpretation. They are intentionally absent from the initial engine.
