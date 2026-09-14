-- Contract reference data needed to detect deviations (FR-07) and notify the
-- counterparty (FR-22). Values are loaded as reference data and are not
-- editable in the MVP interface, per the scope assumptions.

CREATE TABLE delivery_point (
    id                uuid        PRIMARY KEY,
    code              text        NOT NULL UNIQUE,
    name              text        NOT NULL,
    counterparty_name text        NOT NULL,
    notify_channel    text        NOT NULL,
    notify_address    text        NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now()
);

COMMENT ON COLUMN delivery_point.notify_channel IS
    'Notification channel agreed with the counterparty: email or sms (UC-13).';

CREATE TABLE node_delivery_link (
    node_id           uuid NOT NULL REFERENCES metering_node (id),
    delivery_point_id uuid NOT NULL REFERENCES delivery_point (id),

    PRIMARY KEY (node_id, delivery_point_id)
);

COMMENT ON TABLE node_delivery_link IS
    'Metering nodes to delivery points, many-to-many. This is why Deviation '
    'stores both ids explicitly instead of deriving one from the other.';

CREATE TABLE nomination (
    id                uuid           PRIMARY KEY,
    delivery_point_id uuid           NOT NULL REFERENCES delivery_point (id),
    gas_day           date           NOT NULL,
    planned_volume    numeric(14, 3) NOT NULL,
    threshold_pct     numeric(6, 2)  NOT NULL,
    created_at        timestamptz    NOT NULL DEFAULT now(),

    UNIQUE (delivery_point_id, gas_day)
);

COMMENT ON COLUMN nomination.gas_day IS
    'Gas day runs 10:00 to 10:00, not midnight to midnight (see glossary).';

COMMENT ON COLUMN nomination.threshold_pct IS
    'Materiality threshold from the contract reference data (FR-07). Held per '
    'nomination because it is agreed per delivery point and can differ.';

ALTER TABLE deviation
    ADD CONSTRAINT deviation_delivery_point_fk
    FOREIGN KEY (delivery_point_id) REFERENCES delivery_point (id);

INSERT INTO schema_migrations (version) VALUES ('0002_nominations');