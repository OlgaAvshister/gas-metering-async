-- FR-07 names a single materiality threshold, but the dispatcher signal and
-- the counterparty notification compare different things: an instantaneous
-- flow rate against the hourly plan, and the volume accumulated since the
-- start of the gas day against the plan for that point in the day. A shared
-- threshold cannot serve both, so the accumulated one is held separately.

ALTER TABLE nomination
    ADD COLUMN accumulated_threshold_pct numeric(6, 2) NOT NULL DEFAULT 2.00;

COMMENT ON COLUMN nomination.threshold_pct IS
    'Instantaneous threshold: flow rate against the hourly share of the plan. '
    'Drives the dispatcher alarm (FR-07).';

COMMENT ON COLUMN nomination.accumulated_threshold_pct IS
    'Accumulated threshold: volume since the start of the gas day against the '
    'plan for that point in the day. Drives the counterparty notification '
    '(FR-22). Lower than the instantaneous one because accumulated drift moves '
    'slowly and is already serious by the time it reaches the larger figure.';

ALTER TABLE deviation
    ADD COLUMN kind text NOT NULL DEFAULT 'instantaneous';

ALTER TABLE deviation
    ADD CONSTRAINT deviation_kind_check
    CHECK (kind IN ('instantaneous', 'accumulated'));

COMMENT ON COLUMN deviation.kind IS
    'Which comparison produced this record. Only accumulated deviations '
    'trigger a notification command.';

INSERT INTO schema_migrations (version) VALUES ('0003_thresholds');