from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.ingestion import ingest_csv


def main():
    root = Path(__file__).resolve().parents[1]
    content = (root / "data" / "source_a.csv").read_bytes()

    arguments = {
        "source_id": UUID("20000000-0000-4000-8000-000000000001"),
        "actor_id": UUID("10000000-0000-4000-8000-000000000001"),
        "idempotency_key": "demo-source-a-v1",
    }

    first = ingest_csv(content, **arguments)
    second = ingest_csv(content, **arguments)

    if first.batch_id != second.batch_id or not second.replayed:
        raise AssertionError("Replay did not return the original batch")

    print("First receipt:", first)
    print("Second receipt:", second)
    print("PASS: replay returned the original batch")


if __name__ == "__main__":
    main()
