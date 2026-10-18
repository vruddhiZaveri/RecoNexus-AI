from pathlib import Path
import sys
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db import connect_db


ANALYST_ID = UUID("10000000-0000-4000-8000-000000000001")
SOURCE_A_ID = UUID("20000000-0000-4000-8000-000000000001")
SOURCE_B_ID = UUID("20000000-0000-4000-8000-000000000002")


def main():
    request_id = str(uuid4())
    created = 0

    with connect_db() as conn:
        # Serialize concurrent demo setup attempts.
        conn.execute("SELECT pg_advisory_xact_lock(726301002)")

        existing = conn.execute(
            """
            SELECT subject, display_name, role, active
            FROM users WHERE id = %s
            """,
            (ANALYST_ID,),
        ).fetchone()

        expected = ("demo:analyst", "Demo Analyst", "ANALYST", True)

        if existing is None:
            conn.execute(
                """
                INSERT INTO users
                    (id, subject, display_name, role, active)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (ANALYST_ID, *expected),
            )
            conn.execute(
                """
                INSERT INTO audit_logs
                    (id, action, entity_type, entity_id,
                     request_id, after_state, reason)
                VALUES
                    (%s, 'DEMO_USER_CREATED', 'user', %s, %s, %s, %s)
                """,
                (
                    uuid4(), ANALYST_ID, request_id,
                    Jsonb({"subject": expected[0], "role": expected[2]}),
                    "Explicit local synthetic demo setup",
                ),
            )
            created += 1
        elif existing != expected:
            raise RuntimeError("Demo analyst differs from expected setup")

        for source_id, name in (
            (SOURCE_A_ID, "Demo Internal Ledger"),
            (SOURCE_B_ID, "Demo Payment Processor"),
        ):
            expected_source = (
                name,
                "COMMON_ACCOUNT",
                "Asia/Kolkata",
                "csv-v1",
            )
            existing = conn.execute(
                """
                SELECT name, perspective, timezone, mapping_version
                FROM sources WHERE id = %s
                """,
                (source_id,),
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO sources
                        (id, name, perspective, timezone, mapping_version)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (source_id, *expected_source),
                )
                conn.execute(
                    """
                    INSERT INTO audit_logs
                        (id, action, entity_type, entity_id,
                         request_id, after_state, reason)
                    VALUES
                        (%s, 'DEMO_SOURCE_CREATED', 'source', %s, %s, %s, %s)
                    """,
                    (
                        uuid4(), source_id, request_id,
                        Jsonb({"name": name, "mapping_version": "csv-v1"}),
                        "Explicit local synthetic demo setup",
                    ),
                )
                created += 1
            elif existing != expected_source:
                raise RuntimeError(f"Demo source configuration differs: {name}")

    print(f"Demo setup committed. Created {created} entities.")
    print("Analyst:", ANALYST_ID)
    print("Source A:", SOURCE_A_ID)
    print("Source B:", SOURCE_B_ID)


if __name__ == "__main__":
    main()
