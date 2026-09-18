# ADR-006: Kafka for events, RabbitMQ for commands

## Status
Accepted

## Context
The system handles two different kinds of asynchronous traffic.

Meter readings arrive continuously. Order matters per metering node, several
independent consumers need the same data — validation, deviation detection, and
analytics later — and a new consumer must be able to replay history. This follows
directly from [ADR-001](0001-two-data-layers.md): a single primary source feeding
two independent processing pipelines.

When a deviation crosses the contractual threshold, a unit of work is created:
notify the counterparty, and later generate a settlement act. Each task has
exactly one executor and a lifecycle — succeeded, retried, or failed and left for
manual review. [ADR-004](0004-counterparty-notification.md) makes this
time-critical: the notification goes out at the moment the deviation is recorded,
within the three minutes NFR-5 allows.

Using one broker for both would force a compromise. A log-based broker has no
per-message acknowledgement, no delayed retry and no dead-lettering. A queue
broker cannot replay a stream or serve several independent consumer groups
cheaply.

## Decision
- Kafka carries domain events. The topic `measurements.recorded` is partitioned
  by `node_id`, which guarantees ordering per metering node while allowing nodes
  to be processed in parallel. Each pipeline reads it as its own consumer group.
- RabbitMQ carries commands through a topic exchange, with manual
  acknowledgement, delayed retry built on TTL plus a dead-letter exchange, and a
  dead letter queue for manual handling.
- Publishing to either broker from a service that also writes to the database
  goes through the transactional outbox (see [ADR-007](0007-outbox-vs-cdc.md)).

## Rationale
Each transport is used for what it is designed for, and the failure modes become
explicit and measurable: consumer lag for Kafka, queue depth and dead letter
queue size for RabbitMQ.

The difference matters most when a message cannot be processed at all. In
RabbitMQ a poison message is dead-lettered and the queue carries on. In Kafka a
partition is read strictly in order, so a permanently failing message stalls
every message behind it until the consumer parks it explicitly in a dead letter
topic. FR-08 already requires that a packet failing validation is flagged and
routed to a manual review queue rather than blocking intake; with one broker that
requirement would have to be met twice over, in two incompatible ways.

## Consequences
- Two brokers to operate and to reason about, which is the cost accepted here.
- Kafka has no message lifecycle, so retry counting and dead-lettering are
  assembled by hand in the consumer, and the retry counter does not survive a
  consumer restart. RabbitMQ keeps the equivalent counter itself in the `x-death`
  header.
- Two transports mean two sets of operational knowledge for whoever runs the
  system.
