-- The outbox now carries commands for RabbitMQ alongside events for Kafka.
-- The pattern is not Kafka-specific: it atomically ties a database change to a
-- message sent anywhere.

ALTER TABLE outbox
    ADD COLUMN destination text NOT NULL DEFAULT 'kafka',
    ADD COLUMN routing_key text;

ALTER TABLE outbox
    ADD CONSTRAINT outbox_destination_check
    CHECK (destination IN ('kafka', 'rabbitmq'));

COMMENT ON COLUMN outbox.destination IS
    'Which broker the relay delivers this row to.';

COMMENT ON COLUMN outbox.routing_key IS
    'RabbitMQ routing key. Unlike partition_key it selects a queue rather than '
    'a partition, so the two are kept separate.';

INSERT INTO schema_migrations (version) VALUES ('0004_outbox_destination');