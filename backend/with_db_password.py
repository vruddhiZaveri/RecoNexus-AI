import getpass
import os
from pathlib import Path
import runpy
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python backend/with_db_password.py SCRIPT")

    script = Path(sys.argv[1]).resolve()
    if not script.is_file():
        raise SystemExit("Script does not exist")

    previous = os.environ.get("PGPASSWORD")
    os.environ["PGPASSWORD"] = getpass.getpass("PostgreSQL password: ")

    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        if previous is None:
            os.environ.pop("PGPASSWORD", None)
        else:
            os.environ["PGPASSWORD"] = previous


if __name__ == "__main__":
    main()
