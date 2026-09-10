-- Core schema for the asynchronous ingestion and deviation flow.
-- Covers FR-08 (telemetry intake), FR-16 (controller archive re-read),
-- FR-07 / FR-22 (deviation detection and counterparty notification),
-- NFR-6 (no loss, no duplicates), NFR-11 (append-only accounting data).

CREATE TABLE schema_migrations (
    version     text        PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now()
);

-- Reference data -----------------------------------------------------------

CREATE TABLE metering_node (
    id          uuid        PRIMARY KEY,
    code        text        NOT NULL UNIQUE,
    name        text        NOT NULL,
    line_name   text        NOT NULL,
    is_active   boolean     NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON COLUMN metering_node.line_name IS
    'Pipeline line; monitoring and accounting are kept per line.';

-- Operational layer (ADR-001) ----------------------------------------------

CREATE TYPE measurement_source  AS ENUM ('telemetry', 'archive');
CREATE TYPE measurement_quality AS ENUM ('valid', 'suspect');

CREATE TABLE measurement (
    id           uuid                PRIMARY KEY,
    node_id      uuid                NOT NULL REFERENCES metering_node (id),
    measured_at  timestamptz         NOT NULL,
    flow_rate    numeric(14, 3)      NOT NULL,
    pressure     numeric(14, 3)      NOT NULL,
    temperature  numeric(14, 3)      NOT NULL,
    source       measurement_source  NOT NULL,
    quality      measurement_quality NOT NULL DEFAULT 'valid',
    reject_reason text,
    received_at  timestamptz         NOT NULL DEFAULT now(),

    CONSTRAINT measurement_natural_key UNIQUE (node_id, measured_at)
);

COMMENT ON CONSTRAINT measurement_natural_key ON measurement IS
    'A node produces one measurement per timestamp. Re-reading the controller '
    'archive after a connection loss (FR-16) must not create duplicates, so '
    'inserts use ON CONFLICT DO NOTHING against this key.';

CREATE INDEX measurement_node_time_idx ON measurement (node_id, measured_at DESC);

CREATE TABLE hourly_aggregate (
    id                uuid           PRIMARY KEY,
    node_id           uuid           NOT NULL REFERENCES metering_node (id),
    hour_start        timestamptz    NOT NULL,
    volume            numeric(14, 3) NOT NULL,
    avg_pressure      numeric(14, 3) NOT NULL,
    avg_temperature   numeric(14, 3) NOT NULL,
    measurement_count integer        NOT NULL,
    is_complete       boolean        NOT NULL,
    computed_at       timestamptz    NOT NULL DEFAULT now(),

    UNIQUE (node_id, hour_start)
);

COMMENT ON COLUMN hourly_aggregate.is_complete IS
    'False when fewer measurements arrived than the sampling rate implies '
    '(NFR-9: one measurement per minute).';

-- Deviations and notifications ---------------------------------------------

CREATE TYPE deviation_status AS ENUM ('open', 'resolved');

CREATE TABLE deviation (
    id                uuid             PRIMARY KEY,
    node_id           uuid             NOT NULL REFERENCES metering_node (id),
    delivery_point_id uuid,
    detected_at       timestamptz      NOT NULL DEFAULT now(),
    measured_at       timestamptz      NOT NULL,
    nominated_value   numeric(14, 3)   NOT NULL,
    actual_value      numeric(14, 3)   NOT NULL,
    deviation_pct     numeric(6, 2)    NOT NULL,
    threshold_pct     numeric(6, 2)    NOT NULL,
    status            deviation_status NOT NULL DEFAULT 'open'
);

COMMENT ON COLUMN deviation.delivery_point_id IS
    'Held explicitly: NodeDeliveryLink is M:N, so the delivery point cannot be '
    'derived from the node. Nullable here because contracts are out of scope '
    'for this implementation slice.';

CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'dead');

CREATE TABLE notification (
    id            uuid                PRIMARY KEY,
    deviation_id  uuid                NOT NULL REFERENCES deviation (id),
    channel       text                NOT NULL,
    recipient     text                NOT NULL,
    status        notification_status NOT NULL DEFAULT 'pending',
    attempts      integer             NOT NULL DEFAULT 0,
    last_error    text,
    created_at    timestamptz         NOT NULL DEFAULT now(),
    sent_at       timestamptz
);

COMMENT ON TABLE notification IS
    'NFR-5: delivered within three minutes of the deviation being recorded. '
    'Status dead means the retry budget was exhausted and the message went to '
    'the dead-letter queue for manual handling.';

-- Implementation support tables --------------------------------------------

CREATE TABLE outbox (
    id             bigserial   PRIMARY KEY,
    aggregate_type text        NOT NULL,
    aggregate_id   uuid        NOT NULL,
    event_type     text        NOT NULL,
    partition_key  text        NOT NULL,
    payload        jsonb       NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    published_at   timestamptz,
    attempts       integer     NOT NULL DEFAULT 0,
    last_error     text
);

CREATE INDEX outbox_unpublished_idx
    ON outbox (created_at)
    WHERE published_at IS NULL;

COMMENT ON TABLE outbox IS
    'Transactional outbox. A database write and a Kafka publish cannot share '
    'one transaction, so the event is written here in the same transaction as '
    'the business row and published afterwards by a relay process.';

CREATE TABLE processed_message (
    consumer      text        NOT NULL,
    message_key   text        NOT NULL,
    processed_at  timestamptz NOT NULL DEFAULT now(),

    PRIMARY KEY (consumer, message_key)
);

COMMENT ON TABLE processed_message IS
    'Consumer-side deduplication. Kafka delivery is at-least-once, so each '
    'consumer records what it has already handled (NFR-6: no duplicates).';

INSERT INTO schema_migrations (version) VALUES ('0001_core_schema');