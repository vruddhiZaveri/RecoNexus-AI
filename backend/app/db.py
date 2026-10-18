import os
import psycopg


def connect_db(*, autocommit=False):
    if not os.environ.get("PGPASSWORD"):
        raise RuntimeError(
            "Database password missing. Run through backend/with_db_password.py."
        )

    return psycopg.connect(
        host=os.environ.get("RECONEXUS_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("RECONEXUS_DB_PORT", "5434")),
        dbname=os.environ.get("RECONEXUS_DB_NAME", "reconexus"),
        user=os.environ.get("RECONEXUS_DB_USER", "reconexus"),
        connect_timeout=5,
        autocommit=autocommit,
    )
