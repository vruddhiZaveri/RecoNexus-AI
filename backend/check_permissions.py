from pathlib import Path
import sys
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db import connect_db


def main():
    checks = (
        ("Transaction updates", "UPDATE transactions SET amount = amount WHERE false"),
        ("Transaction deletion", "DELETE FROM transactions WHERE false"),
        ("Audit updates", "UPDATE audit_logs SET reason = reason WHERE false"),
        ("Audit deletion", "DELETE FROM audit_logs WHERE false"),
        ("User creation", """
            INSERT INTO users (id, subject, display_name, role)
            SELECT NULL::uuid, 'test', 'test', 'ADMIN' WHERE false
        """),
        ("Migration history access", "SELECT * FROM schema_migrations WHERE false"),
    )

    with connect_db(autocommit=True) as conn:
        role = conn.execute("SELECT current_user").fetchone()[0]
        if role != "reconexus_app":
            raise RuntimeError("Run this check as reconexus_app")

        for label, statement in checks:
            try:
                with conn.transaction():
                    conn.execute(statement)
            except psycopg.errors.InsufficientPrivilege:
                print(f"PASS: {label} denied")
            else:
                raise AssertionError(f"{label} unexpectedly permitted")

    print("PASS: all 6 permission checks")


if __name__ == "__main__":
    main()
