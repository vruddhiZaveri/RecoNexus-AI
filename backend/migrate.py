from pathlib import Path
import getpass
import hashlib

import psycopg

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def migrate():
    password = getpass.getpass("PostgreSQL password: ")

    with psycopg.connect(
        host="127.0.0.1",
        port=5434,
        dbname="reconexus",
        user="reconexus",
        password=password,
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET LOCAL lock_timeout = '10s'")
            cursor.execute("SET LOCAL statement_timeout = '60s'")

            # Serialize concurrent migration attempts.
            cursor.execute(
                "SELECT pg_advisory_xact_lock(726301001)"
            )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version text PRIMARY KEY,
                    checksum text NOT NULL,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
            """)

            for path in sorted(MIGRATIONS.glob("*.sql")):
                content = path.read_bytes()
                checksum = hashlib.sha256(content).hexdigest()

                cursor.execute(
                    "SELECT checksum FROM schema_migrations WHERE version = %s",
                    (path.name,),
                )
                existing = cursor.fetchone()

                if existing:
                    if existing[0] != checksum:
                        raise RuntimeError(
                            f"Applied migration was modified: {path.name}"
                        )
                    print(f"Already applied: {path.name}")
                    continue

                cursor.execute(content.decode("utf-8-sig"))
                cursor.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum)
                    VALUES (%s, %s)
                    """,
                    (path.name, checksum),
                )
                print(f"Prepared: {path.name}")

        # SQL changes and migration history commit together.
    print("Migrations committed successfully.")


if __name__ == "__main__":
    migrate()
