-- A correlation id can originate in another system with its own id format, so
-- the column accepts any string rather than only a UUID. The value is opaque
-- here: it is carried and matched, never parsed.

ALTER TABLE measurement ALTER COLUMN correlation_id TYPE text;
ALTER TABLE outbox      ALTER COLUMN correlation_id TYPE text;
ALTER TABLE deviation   ALTER COLUMN correlation_id TYPE text;

INSERT INTO schema_migrations (version) VALUES ('0006_correlation_text');