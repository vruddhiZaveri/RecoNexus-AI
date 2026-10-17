CREATE TABLE users (
    id uuid PRIMARY KEY,
    subject text UNIQUE NOT NULL,
    display_name text NOT NULL,
    role text NOT NULL CHECK (
        role IN ('ANALYST', 'REVIEWER', 'MANAGER', 'AUDITOR', 'ADMIN')
    ),
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE sources (
    id uuid PRIMARY KEY,
    name text UNIQUE NOT NULL,
    perspective text NOT NULL,
    timezone text NOT NULL,
    mapping_version text NOT NULL
);

CREATE TABLE batches (
    id uuid PRIMARY KEY,
    source_id uuid NOT NULL REFERENCES sources(id),
    idempotency_key text NOT NULL,
    file_sha256 text NOT NULL CHECK (
        file_sha256 ~ '^[0-9a-f]{64}$'
    ),
    raw_object_key text NOT NULL,
    created_by uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_id, idempotency_key),
    UNIQUE (source_id, file_sha256),
    UNIQUE (id, source_id)
);

CREATE TABLE transactions (
    id uuid PRIMARY KEY,
    source_id uuid NOT NULL REFERENCES sources(id),
    batch_id uuid NOT NULL,
    source_record_id text NOT NULL CHECK (btrim(source_record_id) <> ''),
    row_number integer NOT NULL CHECK (row_number >= 2),
    reference_raw text NOT NULL,
    reference_normalized text NOT NULL,
    business_date date NOT NULL,
    amount numeric NOT NULL CHECK (
        amount > 0
        AND amount < 10000000000000000
        AND amount = trunc(amount, 2)
    ),
    currency text NOT NULL CHECK (currency = 'INR'),
    direction text NOT NULL CHECK (direction IN ('CREDIT', 'DEBIT')),
    payload_sha256 text NOT NULL CHECK (
        payload_sha256 ~ '^[0-9a-f]{64}$'
    ),
    FOREIGN KEY (batch_id, source_id)
        REFERENCES batches(id, source_id),
    UNIQUE (source_id, source_record_id),
    UNIQUE (batch_id, row_number)
);

CREATE TABLE audit_logs (
    id uuid PRIMARY KEY,
    actor_id uuid REFERENCES users(id),
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id uuid NOT NULL,
    request_id text NOT NULL,
    before_state jsonb,
    after_state jsonb,
    reason text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX transactions_candidate_lookup
    ON transactions (
        source_id, reference_normalized, business_date,
        currency, direction, amount
    );

CREATE INDEX audit_entity_history
    ON audit_logs (entity_type, entity_id, created_at);
