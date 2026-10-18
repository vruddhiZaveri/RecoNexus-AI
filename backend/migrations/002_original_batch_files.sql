CREATE TABLE batch_files (
    batch_id uuid PRIMARY KEY REFERENCES batches(id),
    content bytea NOT NULL,
    size_bytes integer NOT NULL CHECK (
        size_bytes > 0 AND size_bytes <= 10485760
    ),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (octet_length(content) = size_bytes)
);
