import getpass
from uuid import uuid4

import psycopg


def main():

    with psycopg.connect(
        host="127.0.0.1",
        port=5434,
        dbname="reconexus",
        user="reconexus",
        connect_timeout=5,
        autocommit=True,
    ) as conn:
        actor, source, batch = uuid4(), uuid4(), uuid4()
        checks = 0

        try:
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO users
                        (id, subject, display_name, role)
                    VALUES (%s, %s, 'Constraint Test', 'ANALYST')
                    """,
                    (actor, f"test-{actor}"),
                )
                conn.execute(
                    """
                    INSERT INTO sources
                        (id, name, perspective, timezone, mapping_version)
                    VALUES (%s, %s, 'COMMON_ACCOUNT', 'Asia/Kolkata', 'v1')
                    """,
                    (source, f"test-{source}"),
                )
                conn.execute(
                    """
                    INSERT INTO batches
                        (id, source_id, idempotency_key, file_sha256,
                         raw_object_key, created_by)
                    VALUES (%s, %s, 'test-key', %s, 'test-only', %s)
                    """,
                    (batch, source, "a" * 64, actor),
                )

                def expect_rejection(label, error_type, query, params):
                    nonlocal checks
                    try:
                        # Nested transaction creates a savepoint.
                        with conn.transaction():
                            conn.execute(query, params)
                    except error_type:
                        checks += 1
                        print(f"PASS: {label}")
                    else:
                        raise AssertionError(f"Constraint failed: {label}")

                insert_batch = """
                    INSERT INTO batches
                        (id, source_id, idempotency_key, file_sha256,
                         raw_object_key, created_by)
                    VALUES (%s, %s, %s, %s, 'test-only', %s)
                """

                expect_rejection(
                    "Duplicate idempotency key rejected",
                    psycopg.errors.UniqueViolation,
                    insert_batch,
                    (uuid4(), source, "test-key", "b" * 64, actor),
                )
                expect_rejection(
                    "Duplicate file hash rejected",
                    psycopg.errors.UniqueViolation,
                    insert_batch,
                    (uuid4(), source, "different-key", "a" * 64, actor),
                )

                insert_transaction = """
                    INSERT INTO transactions
                        (id, source_id, batch_id, source_record_id,
                         row_number, reference_raw, reference_normalized,
                         business_date, amount, currency, direction,
                         payload_sha256)
                    VALUES
                        (%s, %s, %s, %s, %s, 'REF', 'REF',
                         '2026-10-01', %s, 'INR', 'CREDIT', %s)
                """

                def transaction_params(
                    amount, record_id="record-1", row=2, batch_id=batch
                ):
                    return (
                        uuid4(), source, batch_id, record_id,
                        row, amount, "c" * 64,
                    )

                conn.execute(insert_transaction, transaction_params("100.00"))

                expect_rejection(
                    "Duplicate source record rejected",
                    psycopg.errors.UniqueViolation,
                    insert_transaction,
                    transaction_params("100.00", row=3),
                )

                for amount in ("-1", "0", "1.001", "10000000000000000"):
                    expect_rejection(
                        f"Invalid monetary amount rejected: {amount}",
                        psycopg.errors.CheckViolation,
                        insert_transaction,
                        transaction_params(amount, record_id=str(uuid4()), row=4),
                    )

                expect_rejection(
                    "Unknown batch rejected",
                    psycopg.errors.ForeignKeyViolation,
                    insert_transaction,
                    transaction_params(
                        "10.00", record_id="unknown-batch",
                        row=5, batch_id=uuid4(),
                    ),
                )

                # A deliberate failure verifies outer transaction rollback.
                raise RuntimeError("ROLLBACK_TEST")

        except RuntimeError as exc:
            if str(exc) != "ROLLBACK_TEST":
                raise

        for table, identity in (
            ("users", actor), ("sources", source), ("batches", batch)
        ):
            # Table names come only from this fixed internal list.
            count = conn.execute(
                f"SELECT count(*) FROM {table} WHERE id = %s",
                (identity,),
            ).fetchone()[0]
            assert count == 0, f"Rollback failed for {table}"

        remaining = conn.execute(
            "SELECT count(*) FROM transactions WHERE batch_id = %s",
            (batch,),
        ).fetchone()[0]
        assert remaining == 0, "Rollback failed for transactions"

        print(f"PASS: {checks} constraint checks")
        print("PASS: transaction rollback; no test records retained")


if __name__ == "__main__":
    main()
