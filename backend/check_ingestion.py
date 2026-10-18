from pathlib import Path
import sys
from unittest.mock import patch
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db import connect_db
from backend.app.ingestion import ingest_csv, IngestionConflict


ACTOR = UUID("10000000-0000-4000-8000-000000000001")
SOURCE = UUID("20000000-0000-4000-8000-000000000001")


def counts():
    with connect_db() as conn:
        return tuple(
            conn.execute(query).fetchone()[0]
            for query in (
                "SELECT count(*) FROM batches",
                "SELECT count(*) FROM batch_files",
                "SELECT count(*) FROM transactions",
                "SELECT count(*) FROM audit_logs",
            )
        )


def expect_failure(label, error_type, action):
    before = counts()
    try:
        action()
    except error_type:
        pass
    else:
        raise AssertionError(f"{label}: expected rejection")

    if counts() != before:
        raise AssertionError(f"{label}: database counts changed")
    print(f"PASS: {label}; no records added")


def main():
    root = Path(__file__).resolve().parents[1]
    original = (root / "data/source_a.csv").read_bytes()
    common = {"source_id": SOURCE, "actor_id": ACTOR}

    # Different valid bytes, same key.
    changed = original + b"\n"

    expect_failure(
        "Same key with changed file rejected",
        IngestionConflict,
        lambda: ingest_csv(
            changed, **common, idempotency_key="demo-source-a-v1"
        ),
    )

    expect_failure(
        "Same file with a different key rejected",
        IngestionConflict,
        lambda: ingest_csv(
            original, **common, idempotency_key=str(uuid4())
        ),
    )

    expect_failure(
        "Existing source record identities rejected",
        IngestionConflict,
        lambda: ingest_csv(
            changed, **common, idempotency_key=str(uuid4())
        ),
    )

    header = (
        "record_id,reference,business_date,amount,currency,direction\n"
    )

    expect_failure(
        "Fractional paise rejected",
        ValueError,
        lambda: ingest_csv(
            (header + "bad,R,2026-10-01,1.001,INR,CREDIT\n").encode(),
            **common,
            idempotency_key=str(uuid4()),
        ),
    )

    fresh = (
        header
        + f"{uuid4()},ROLLBACK,2026-10-01,10.00,INR,CREDIT\n"
    ).encode()

    # Jsonb is constructed at the audit-write stage, after inserting
    # the batch, original file and transaction.
    def failed_audit_payload(*args, **kwargs):
        raise RuntimeError("Injected audit-stage failure")

    with patch(
        "backend.app.ingestion.Jsonb",
        side_effect=failed_audit_payload,
    ):
        expect_failure(
            "Audit-stage failure rolls back the entire import",
            RuntimeError,
            lambda: ingest_csv(
                fresh, **common, idempotency_key=str(uuid4())
            ),
        )

    print("PASS: all 5 ingestion checks")


if __name__ == "__main__":
    main()
