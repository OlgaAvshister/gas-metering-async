# ADR-008: At-least-once delivery with idempotent consumers

## Status
Accepted

## Context
The specification requires that a controller archive re-read produces neither
loss nor duplication (NFR-6, FR-16), but it never states what delivery guarantee
holds between the services themselves. That guarantee is not a detail: it decides
whether every consumer in the system has to be idempotent.

At three points a message can be delivered once, twice or not at all, and each
presents the same choice.

The relay publishes a row and then marks it published. Mark first and a crash
between the two steps loses the message; mark second and it is republished.

A Kafka consumer processes a message and then commits its offset. Commit first
and a crash loses the message; commit second and it is redelivered.

A RabbitMQ worker sends a notification and then acknowledges the message.
Acknowledge first and a crash loses it; acknowledge second and it is redelivered.

## Decision
At-least-once everywhere. In each case the durable work happens first and the
bookkeeping second: mark published after publishing, commit the offset after
processing, acknowledge after sending. `enable.auto.commit` is off in every
consumer, because the library would otherwise move the offset on a timer,
independently of whether the work succeeded.

Every consumer is therefore required to tolerate a repeated message.

## Rationale
Exactly-once across two independent systems is not achievable; what is achievable
is at-least-once delivery combined with idempotent processing, which is
indistinguishable in its result.

The choice between losing and duplicating is settled by what can be detected and
repaired afterwards. A duplicate is visible and can be filtered. A lost
measurement leaves no trace anywhere: nothing in the logs, nothing in the
database, and no way to know it existed. For a system whose purpose is to settle
disputes over volumes, a silent loss is the worse failure by a wide margin.

## Consequences
Idempotency is achieved in two different ways, chosen per consumer.

**By construction, where the operation allows it.** The hourly aggregate is
recomputed from scratch from the measurements of that hour rather than
incremented, so processing the same measurement twice changes nothing. This has a
second benefit that decided the design: late archive data arriving under FR-16
corrects an hour that was already published, which an incremental total could not
do.

**By deduplication, where it does not.** Sending a notification cannot be made
idempotent — two emails are two emails, and no recomputation collapses them — so
the worker records what it has already sent and checks before sending. The same
approach, in the `processed_message` table, covers consumers whose work is not
naturally repeatable.

Deduplication keys are taken from the domain — `measurement_id`, `deviation_id` —
never from the transport. A Kafka offset differs between two copies of the same
event, so it cannot identify a duplicate; a domain identifier is generated once
and travels with both copies.

A residual gap remains in the notification worker, between sending the message
and recording that it was sent. It cannot be closed from this side: doing so
requires an idempotency key honoured by the receiving gateway, which is how
payment APIs solve the same problem.
