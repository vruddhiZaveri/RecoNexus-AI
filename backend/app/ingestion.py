import csv
from dataclasses import dataclass
import hashlib
import io
import json
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from backend.app.db import connect_db
from backend.app.domain import parse_csv


class IngestionConflict(ValueError):
    pass


@dataclass(frozen=True)
class Receipt:
    batch_id: UUID
    transaction_count: int
    replayed: bool


def ingest_csv(
    content: bytes,
    *,
    source_id: UUID,
    actor_id: UUID,
    idempotency_key: str,
) -> Receipt:
    """Local service entrypoint; actor identity is not HTTP authentication."""

    if not idempotency_key.strip() or len(idempotency_key) > 200:
        raise ValueError("Provide an idempotency key of 1–200 characters")

    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError("File must contain 1 byte to 10 MiB")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must use UTF-8 encoding") from exc

    # Complete validation before any database writes.
    try:
        records = parse_csv(text)
        raw_rows = list(csv.DictReader(io.StringIO(text), strict=True))
    except csv.Error as exc:
        raise ValueError("Malformed CSV") from exc

    if len(raw_rows) != len(records):
        raise ValueError("Parsed row counts disagree")

    file_hash = hashlib.sha256(content).hexdigest()
    request_id = str(uuid4())

    with connect_db() as conn:
        conn.execute("SET LOCAL lock_timeout = '10s'")
        conn.execute("SET LOCAL statement_timeout = '60s'")

        actor = conn.execute(
            """
            SELECT role, active FROM users
            WHERE id = %s
            """,
            (actor_id,),
        ).fetchone()

        if actor is None or not actor[1] or actor[0] not in (
            "ANALYST", "MANAGER", "ADMIN"
        ):
            raise PermissionError("Active ingestion-authorized user required")

        # Stable source-specific lock, released automatically on commit/rollback.
        lock_key = int.from_bytes(
            hashlib.sha256(source_id.bytes).digest()[:8],
            byteorder="big",
            signed=True,
        )
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))

        # Serialize imports for this source to prevent concurrent duplicates.
        source = conn.execute(
            "SELECT id FROM sources WHERE id = %s",
            (source_id,),
        ).fetchone()
        if source is None:
            raise ValueError("Unknown data source")

        existing = conn.execute(
            """
            SELECT id, file_sha256 FROM batches
            WHERE source_id = %s AND idempotency_key = %s
            """,
            (source_id, idempotency_key),
        ).fetchone()

        if existing:
            if existing[1] != file_hash:
                raise IngestionConflict(
                    "This idempotency key belongs to different file content"
                )
            count = conn.execute(
                "SELECT count(*) FROM transactions WHERE batch_id = %s",
                (existing[0],),
            ).fetchone()[0]
            return Receipt(existing[0], count, True)

        duplicate_file = conn.execute(
            """
            SELECT id FROM batches
            WHERE source_id = %s AND file_sha256 = %s
            """,
            (source_id, file_hash),
        ).fetchone()
        if duplicate_file:
            raise IngestionConflict(
                "File already imported; retry using its original idempotency key"
            )

        source_record_ids = [record.record_id for record in records]
        duplicate_record = conn.execute(
            """
            SELECT source_record_id FROM transactions
            WHERE source_id = %s AND source_record_id = ANY(%s)
            LIMIT 1
            """,
            (source_id, source_record_ids),
        ).fetchone()
        if duplicate_record:
            raise IngestionConflict(
                "At least one source record identity was already imported"
            )

        batch_id = uuid4()
        conn.execute(
            """
            INSERT INTO batches
                (id, source_id, idempotency_key, file_sha256,
                 raw_object_key, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                batch_id, source_id, idempotency_key, file_hash,
                f"postgres:batch_files/{batch_id}", actor_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO batch_files (batch_id, content, size_bytes)
            VALUES (%s, %s, %s)
            """,
            (batch_id, content, len(content)),
        )

        rows = []
        for ordinal, (record, raw) in enumerate(
            zip(records, raw_rows), start=2
        ):
            # Hash a canonical representation of the original parsed fields.
            payload = json.dumps(
                raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")

            rows.append((
                uuid4(), source_id, batch_id, record.record_id, ordinal,
                raw["reference"], record.reference, record.business_date,
                record.amount, record.currency, record.direction,
                hashlib.sha256(payload).hexdigest(),
            ))

        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO transactions
                    (id, source_id, batch_id, source_record_id, row_number,
                     reference_raw, reference_normalized, business_date,
                     amount, currency, direction, payload_sha256)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )

        conn.execute(
            """
            INSERT INTO audit_logs
                (id, actor_id, action, entity_type, entity_id,
                 request_id, after_state, reason)
            VALUES (%s, %s, 'BATCH_IMPORTED', 'batch', %s, %s, %s, %s)
            """,
            (
                uuid4(), actor_id, batch_id, request_id,
                Jsonb({
                    "source_id": str(source_id),
                    "file_sha256": file_hash,
                    "transaction_count": len(records),
                }),
                "Validated synthetic CSV ingestion",
            ),
        )

    # Return success only after the connection context commits.
    return Receipt(batch_id, len(records), False)
