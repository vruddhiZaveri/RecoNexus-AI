import getpass
import psycopg

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
        cursor.execute("SELECT current_database(), current_user")
        print("Connection successful:", cursor.fetchone())

