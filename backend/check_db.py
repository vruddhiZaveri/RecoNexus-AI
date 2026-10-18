import getpass
import os
import psycopg

previous = os.environ.get("PGPASSWORD")
os.environ["PGPASSWORD"] = getpass.getpass("PostgreSQL password: ")

try:
    with psycopg.connect(
        host="127.0.0.1",
        port=5434,
        dbname="reconexus",
        user="reconexus",
        connect_timeout=5,
    ) as conn:
        result = conn.execute(
            "SELECT current_database(), current_user"
        ).fetchone()
        print("Connection successful:", result)
finally:
    if previous is None:
        os.environ.pop("PGPASSWORD", None)
    else:
        os.environ["PGPASSWORD"] = previous
