# ADR-007: Transactional outbox rather than change data capture

## Status
Accepted

## Context
A service that accepts a measurement has to do two things: store it in PostgreSQL
and publish an event about it. These are two separate systems with no shared
transaction, which leaves a hole whichever order they run in.

Write to the database first and the process can die before publishing: the
measurement exists and no consumer ever learns of it. Publish first and the
transaction can roll back: consumers process a measurement that is not in the
database. This is the dual-write problem, and reordering does not remove it.

Two-phase commit does not apply. Kafka is not an XA resource — it has no
interface for "prepare but do not commit" held open under an external
coordinator, and its own transactions cover only writes within Kafka itself.
Beyond that, 2PC is blocking: a coordinator failure between phases leaves
participants holding locks with no way to resolve, and in PostgreSQL a forgotten
prepared transaction blocks vacuum and grows the database until it fails.

## Options considered
1. **Publish directly after committing.** Simple, and loses events on a crash
   between the two steps.
2. **Transactional outbox.** The business row and its event are written to the
   same database in one transaction. A separate relay reads unpublished rows and
   delivers them to the broker.
3. **Change data capture.** A tool such as Debezium reads the PostgreSQL
   write-ahead log and turns row changes into messages. The application does
   nothing and knows nothing about it.

## Decision
Option 2. The API and the consumers write their events and commands to an
`outbox` table inside the same transaction as the business row. A relay process
publishes them afterwards and marks the row published. A `destination` column
selects the broker, so the same table and the same relay serve both Kafka and
RabbitMQ.

## Rationale
Option 1 was rejected because a lost event is undetectable and unrecoverable.

Option 3 was rejected primarily because CDC publishes table rows, not domain
events. The shape of a table is an internal matter for the service that owns it —
columns get renamed, tables get split, technical fields appear. Under CDC every
such change breaks every consumer, because they are reading the physical schema.
The outbox gives a contract instead: the payload is what the service chose to
publish, and the table underneath can be restructured freely.

Two further reasons: an event does not always correspond to one row — some are
assembled from several tables, and some, such as "period closed", correspond to
no row at all — and CDC is a separate piece of infrastructure to run, with
replication slots that grow the write-ahead log when neglected.

CDC remains the better answer where the source application cannot be modified, or
where the volume makes an extra write per event expensive.

## Consequences
- One extra write per event, and a relay process to run and monitor.
- Delivery is at-least-once rather than exactly-once: a crash between publishing
  and marking the row republishes it. See [ADR-008](0008-delivery-guarantees.md).
- The `outbox` and `processed_message` tables exist in the physical schema but
  not in the domain model. They are implementation artefacts, and the ER model is
  correct to omit them.
- The unpublished row count and the age of the oldest unpublished row become the
  primary health metric of the delivery chain, and the natural place to alert on
  NFR-7.
