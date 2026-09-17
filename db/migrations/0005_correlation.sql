-- A correlation id is generated when a request enters the system and travels
-- with it through every service and both brokers, so one search reconstructs
-- the whole path of a single measurement.

ALTER TABLE measurement ADD COLUMN correlation_id uuid;
ALTER TABLE outbox      ADD COLUMN correlation_id uuid;
ALTER TABLE deviation   ADD COLUMN correlation_id uuid;

CREATE INDEX measurement_correlation_idx ON measurement (correlation_id);
CREATE INDEX deviation_correlation_idx   ON deviation (correlation_id);

INSERT INTO schema_migrations (version) VALUES ('0005_correlation');