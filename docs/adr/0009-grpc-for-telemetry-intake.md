# ADR-009: gRPC for telemetry intake, REST for everything else

## Status
Accepted

## Context
Telemetry reaches the system from the SCADA gateway, a machine partner rather than
a person. Today it arrives as JSON batches over `POST /measurements`.

For live traffic that is adequate. Fifty nodes at one measurement a minute
(NFR-9) is under one message a second, well within what a REST endpoint handles.

Two things strain it.

**The archive re-read.** After an outage the controller archive must be re-read
for up to 72 hours within 15 minutes (NFR-6). For a single node that is 4,320
readings; if every node lost its connection, 216,000. Sent as batches of a
thousand, that is over two hundred separate requests, each with its own headers
and JSON parsing, and the gateway has to split the archive and retry each piece
on its own.

**The contract.** In JSON the field name is the contract. When `flow_rate` was
renamed to `volume_raw` during implementation, any client still sending the old
name would have been rejected at runtime, with nothing to warn it beforehand.

## Options considered
1. **Keep REST batches.** No new technology. Leaves both problems in place.
2. **gRPC, client streaming.** The gateway opens one stream, sends every reading
   down it, and receives a single summary when it closes.
3. **gRPC, bidirectional streaming.** As option 2, but the server acknowledges
   each reading as it lands, so the gateway knows mid-stream exactly what is
   durable.
4. **The gateway publishes straight to Kafka.** No intake service at all.

## Decision
Option 2 for the SCADA gateway. REST stays for everything whose other side is a
person or a general-purpose client: the web interface, the laboratory
information system, the counterparty and the regulator.

Both intake paths write through the same code — measurement and outbox row in
one transaction — so nothing downstream of intake changes or knows which
protocol a reading arrived by.

## Rationale
Option 1 was rejected because the archive re-read is exactly the workload REST
batching handles worst, and it is also the workload with a hard deadline.

Option 3 was rejected as more than the problem needs. Per-reading
acknowledgement matters when a stream is so long that restarting it is
expensive. An archive re-read is bounded, and restarting it is safe: every
reading is idempotent on the pair (node, measurement time), so a stream broken
halfway is simply sent again and the duplicates are absorbed by the database
(FR-16). The idempotency already built makes the simpler option sufficient.

Option 4 was rejected because it hands an external partner the internals of the
system. The gateway would have to know topic names, the partitioning key and the
serialisation format, and it would bypass validation (FR-08), deduplication and
the outbox. The intake service is the boundary that keeps those decisions
internal.

REST is kept for people and general clients for reasons on the other side of the
same trade. gRPC does not run in a browser without a proxy, its binary payloads
cannot be read or sent by hand, and a partner has to generate code from our
contract before it can call us at all. For a machine partner that is acceptable,
because it gets a compiled contract in return. For a person, or for a system we
integrate with on its own terms, it is not.

Throughput is not the argument. At this volume REST would carry live traffic
without trouble; the decision rests on the archive re-read and on the contract.

## Consequences
- The contract lives in `proto/telemetry.proto` and is versioned with the code.
  Fields are identified by number on the wire, so a field may be renamed freely
  but a number is never reused or repurposed.
- Two intake paths must not drift apart, so the write path is shared code rather
  than two implementations.
- Debugging needs a gRPC-aware tool such as `grpcurl`; `curl` and a browser no
  longer reach this endpoint.
- The gateway has to generate a client from the `.proto` file, which is a
  dependency on us it does not have today.
