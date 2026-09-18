-- Align the schema with the ER model in docs/data-model.
--
-- Four changes, each closing a gap found when the diagrams were transcribed:
--   1. Contract parameters are valid over an interval, not for a single gas day.
--   2. A deviation records which version of those parameters it was judged
--      against, without which a later change of nomination makes past
--      deviations unexplainable.
--   3. Field names follow the model.
--   4. The hourly aggregate stores the mean of the raw readings, which is what
--      avg_volume means and what an incomplete hour needs.

-- 1. Contract parameters --------------------------------------------------

CREATE TABLE contract_parameter (
    id                              uuid           PRIMARY KEY,
    delivery_point_id               uuid           NOT NULL REFERENCES delivery_point (id),
    valid_from                      timestamptz    NOT NULL,
    valid_to                        timestamptz,
    daily_nomination                numeric(14, 3) NOT NULL,
    deviation_threshold             numeric(6, 2)  NOT NULL,
    accumulated_deviation_threshold numeric(6, 2)  NOT NULL,

    CONSTRAINT contract_parameter_interval CHECK (valid_to IS NULL OR valid_to > valid_from)
);

COMMENT ON TABLE contract_parameter IS
    'Contract reference data per delivery point (FR-07, FR-30). A change of '
    'nomination closes the current row and opens a new one, so the parameters '
    'in force at any past moment stay recoverable.';

COMMENT ON COLUMN contract_parameter.valid_to IS
    'NULL on the row currently in force. Mirrors MethodVersion.active_to.';

COMMENT ON COLUMN contract_parameter.deviation_threshold IS
    'Instantaneous threshold: flow against the hourly share of the plan. '
    'Drives the dispatcher alarm (FR-07).';

COMMENT ON COLUMN contract_parameter.accumulated_deviation_threshold IS
    'Accumulated threshold: volume since the start of the gas day against the '
    'plan pro-rated to now. Drives the counterparty notification (FR-22). The '
    'specification names one threshold; two comparisons need two.';

-- The ER model states that exactly one version is in force at any moment but
-- notes the constraint is not expressible in the schema. For a single open
-- interval per delivery point it is.
CREATE UNIQUE INDEX contract_parameter_one_in_force_idx
    ON contract_parameter (delivery_point_id)
    WHERE valid_to IS NULL;

INSERT INTO contract_parameter (
    id, delivery_point_id, valid_from, valid_to,
    daily_nomination, deviation_threshold, accumulated_deviation_threshold
)
SELECT gen_random_uuid(), delivery_point_id, '2026-01-01T00:00:00+00', NULL,
       planned_volume, threshold_pct, accumulated_threshold_pct
FROM nomination n
WHERE n.gas_day = (SELECT max(gas_day) FROM nomination WHERE delivery_point_id = n.delivery_point_id);

DROP TABLE nomination;

-- 2. Deviation ------------------------------------------------------------

ALTER TABLE deviation
    ADD COLUMN contract_parameter_id uuid REFERENCES contract_parameter (id);

COMMENT ON COLUMN deviation.contract_parameter_id IS
    'Which version of the contract parameters this deviation was judged '
    'against. The planned value is not stored: it is derived from this row, '
    'which keeps the two from drifting apart.';

ALTER TABLE deviation RENAME COLUMN threshold_pct TO threshold_value;
ALTER TABLE deviation RENAME COLUMN deviation_pct TO deviation_value;
ALTER TABLE deviation DROP COLUMN nominated_value;

-- 3. Measurement and aggregate names --------------------------------------

ALTER TABLE measurement RENAME COLUMN flow_rate TO volume_raw;
ALTER TABLE measurement ADD COLUMN packet_id uuid;

COMMENT ON COLUMN measurement.packet_id IS
    'The telemetry packet this reading arrived in, so a packet rejected by '
    'validation (FR-08) can be traced to every reading it carried.';

COMMENT ON COLUMN measurement.quality IS
    'Deliberate divergence from the ER model, which carries is_valid and '
    'is_suspicious as separate booleans. FR-08 describes one state — a packet '
    'that fails validation is marked suspect — so two booleans allow a '
    'combination with no meaning. An enum makes that state unrepresentable.';

ALTER TABLE hourly_aggregate RENAME COLUMN volume TO avg_volume;

COMMENT ON COLUMN hourly_aggregate.avg_volume IS
    'Mean of the raw readings in the hour, per the ER model. The hourly volume '
    'is this multiplied by the hour; storing the mean keeps an incomplete hour '
    'honest, where a sum divided by a fixed 60 would under-report it.';

INSERT INTO schema_migrations (version) VALUES ('0007_align_with_er_model');
