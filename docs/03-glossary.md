# Glossary

## Parties and organisations

| Term | Definition |
|---|---|
| Joint venture | KazRosGas, an enterprise with parties from Kazakhstan and Russia, buying, selling and transporting gas. Both parties hold an equal interest in the accuracy of the metering. |
| Transport operator | The party operating the metering nodes and keeping the primary record. In this document, the owner of the system. |
| Counterparty | The second party of the joint venture, which accepts or disputes the calculated volumes and signs the act. |

## Measurement and accounting

| Term | Definition |
|---|---|
| Metering node | A site with a flow meter, pressure and temperature sensors, a controller and a local archive. |
| Operating conditions | The actual temperature and pressure of the gas at the point of measurement. A volume at operating conditions is not directly comparable between nodes. |
| Standard conditions | The normalised temperature and pressure — 20 °C and 101.325 kPa — that a measured volume is corrected to for comparability and calculation. |
| Correction to standard conditions | Recalculating a measured volume for pressure, temperature and the compressibility factor, which depends on the gas composition. |
| Gas composition | The percentage of each component in the gas, determined by chromatography. Arrives with a delay relative to the moment of measurement. |
| Operational accounting | The practice of using telemetry at operating conditions to steer the transport regime. These figures carry no legal weight. |
| Commercial (accounting) record | Verified volumes corrected to standard conditions. The basis for the transfer act and for settlement. |
| Gas day | The reporting period for gas accounting, which does not coincide with the calendar day: as a rule it runs 10:00 to 10:00. |

## Planning and execution

| Term | Definition |
|---|---|
| Nomination | The planned transport volume for a gas day, agreed between the parties. The baseline for tracking execution. |
| Deviation | The difference between actual transport and the nomination. A deviation is material when it exceeds the contractual threshold. |
| Pipeline line | An individual line within a transport corridor. Metering and monitoring are kept per line. |

## Documents and procedures

| Term | Definition |
|---|---|
| Gas transfer act | The document recording the volume and quality of gas transferred over a reporting period. Signed by both parties of the joint venture. |
| Protocol of disagreement | The document drawn up when a party disputes the calculated volumes; it records the subject of the dispute and each party's position. |
| Period closing | The moment after which the original act may no longer be changed: T + 10 working days from the end of the reporting period. |
| Corrective act | A separate document covering refinements that arrived after the period closed. Linked to the original act, but does not modify it. |
| Calculated substitution | Reconstructing the volume for a period without measurements, following the regulated method. Flagged as calculated, naming the method applied. |

## The system

| Term | Definition |
|---|---|
| Operational layer | The storage and publication path for raw measurements with minimal delay. The data source for monitoring. Not to be confused with operational accounting as a practice. |
| Accounting layer | The storage path for corrected volumes with full traceability. The data source for acts and reconciliation. |
| Method version | A fixed set of coefficients and calculation rules that was in force over a given period. Every calculation stores the identifier of the version applied. |
| Correction journal | The immutable record of every change to accounting data: author, time, grounds, previous and new value. |
| Archive re-read | Loading data from a node controller's local archive once a connection is restored, with control over duplicates and overlapping periods. |
| SCADA | The external system collecting telemetry from industrial equipment. The source of operational data; outside the MVP boundary. |

## Terms introduced by the implementation

These do not belong to the business domain. They are named here because the
services and the architectural decisions use them.

| Term | Definition |
|---|---|
| Transactional outbox | A table in which a service writes an outgoing message inside the same transaction as the business row, so that the two cannot diverge. A relay publishes the rows afterwards. See [ADR-007](adr/0007-outbox-vs-cdc.md). |
| At-least-once | A delivery guarantee under which a message arrives at least once and may arrive more than once. See [ADR-008](adr/0008-delivery-guarantees.md). |
| Idempotent processing | Processing where handling the same message twice leaves the same result as handling it once. |
| Dead letter queue / topic | Where a message goes once it has failed every retry, to be dealt with by a person rather than automatically. |
