# Traceability matrix

Every business goal down to the artefacts that deliver it and the figure it is
measured by. The last column says where the implementation in this repository
covers it — blank means specified but not built, which is the case for most of
the system.

The matrix is what makes the specification checkable: a goal with no artefacts is
a goal nobody is delivering, and an artefact under no goal is work nobody asked
for.

## Goal 1 — cut detection of a discrepancy from a month to a shift

| Requirement or conflict | Artefacts | How it is measured | Implemented |
|---|---|---|---|
| Conflict 1, speed against accuracy: the dispatcher needs operational data, the engineer needs accurate accounting data | [ADR-001](adr/0001-two-data-layers.md), FR-02 – FR-05 | Operational layer available within 2 min (NFR-1) | Operational layer: `services/api`, `services/consumer/aggregator.py` |
| Conflict 4, notifying the counterparty about material deviations | [ADR-004](adr/0004-counterparty-notification.md), FR-07, FR-22 | Notification delivered within 3 min of the deviation being recorded (NFR-5) | `services/consumer/deviation_detector.py`, `services/worker/notifier.py` |
| The dispatcher must see plan against fact on one time axis | FR-06, UC-01, UC-02, `GET /delivery-points/{id}/nomination-status` | Deviation computed and displayed in real time | |
| A deviation must be recorded automatically when the threshold is crossed | FR-07, NFR-1, NFR-13 | Under 1 min from telemetry received to deviation recorded (FR-07) | `services/consumer/deviation_detector.py` |
| The operational layer must not interpolate across an outage | FR-14, UC-03, `GET /nodes/{id}/status` | Last trustworthy value shown, marked with the time data stopped | |

## Goal 2 — legally sound accounting, reconcilable and reproducible

| Requirement or conflict | Artefacts | How it is measured | Implemented |
|---|---|---|---|
| Conflict 2, when a period closes: laboratory against engineer against counterparty | [ADR-002](adr/0002-period-closing.md), NFR-2, NFR-3, FR-17 | Period closes at T + 10 working days (NFR-3); accounting volumes published within 30 min of the composition arriving (NFR-2) | |
| The accounting layer holds volumes corrected to standard conditions | FR-04, FR-09, FR-10, UC-06, UC-23, mapping 2 | Correction runs once telemetry and composition are both present (FR-10) | |
| Calculations reproducible for audit and for the counterparty | [ADR-003](adr/0003-method-versioning.md), NFR-4, FR-11, FR-27 | Method versions retained 5 years and calculations reproducible (NFR-4) | |
| Accounting data append-only, corrections versioned | NFR-11, FR-12, FR-13, mapping 5 | A correction creates a version; the original stays readable. The journal holds time, user, grounds, old and new value | |
| The counterparty can reach primary data to verify | NFR-12, FR-20, FR-21, UC-10, UC-11, UC-12 | The counterparty sees primary data, calculations and the correction journal for its own points (NFR-12) | |
| Reconciliation: automatic comparison of calculations | FR-21, UC-10, UC-12, `POST /reconciliations` | Counterparty data loaded and discrepancies displayed (FR-21) | |
| Regulator export with reproducibility | NFR-4, FR-26, FR-27, UC-24, `POST /audit-exports` | An auditor can repeat a calculation and get an identical result (FR-27) | |

## Goal 3 — automate producing acts and closing periods

| Requirement or conflict | Artefacts | How it is measured | Implemented |
|---|---|---|---|
| The engineer produces an act for a period without recalculating by hand | FR-19, UC-08, `POST /reporting-periods/{id}/acts` | Hourly volumes within 4 h of the hour ending (NFR-2); the monthly act within 5 min of the request (NFR-10) | |
| The act is a PDF carrying everything required | FR-19, FR-24, `TransferAct.pdf_link` | The generated PDF is available for download | |
| Both parties sign, with access control | NFR-12, FR-32, UC-25, `POST /acts/{actId}/signatures` | A signature is accepted only with the right (NFR-12). Conflicts: 403 no right, 409 already signed or period closed | |
| A corrective act for changes after the period closed | FR-18, UC-09, `POST /acts/{actId}/corrective-acts` | The corrective act is a separate document linked to the original, which it does not modify (FR-18) | |
| The period closes to changes after 10 working days | NFR-3, FR-17 | After T + 10 the original act cannot be changed (FR-17) | |
| Financial summary of signed acts | FR-23, UC-15, `GET /financial-summaries` | The summary carries totals per line and aggregated quality figures (FR-23) | |

## Goal 4 — data integrity and recovery after an outage

| Requirement or conflict | Artefacts | How it is measured | Implemented |
|---|---|---|---|
| Conflict 3, re-reading the archive: controller memory is limited and the engineer's deadlines are fixed | [ADR-005](adr/0005-connection-loss.md), NFR-6, FR-15, FR-16 | An archive re-read covering up to 72 h completes within 15 min (NFR-6) | Duplicate control: `services/api`, unique constraint on (node, measured_at) |
| On an outage, calculated substitution in the accounting layer | NFR-6, FR-15, mapping 2 (`is_calculated`, `calculation_method`) | The substituted period carries the "calculated" flag naming the method (FR-15) | |
| After recovery, re-read the local archive without loss or duplication | NFR-6, FR-16 | Duplicates and overlapping periods controlled (FR-16) | `services/api`, covered by `tests/test_intake.py` |
| On an outage the dispatcher sees the last trustworthy value as a constant | FR-14, UC-03, `GET /nodes/{id}/status` | Last trustworthy value shown, marked with the time data stopped (FR-14) | |
| Incoming data validated for integrity and physical plausibility | FR-08, `POST /measurements` | Packets failing validation are marked suspect and sent for manual review (FR-08) | `services/api` (the suspect flag; validation rules not implemented) |
| Channel monitoring for IT operations | UC-20, UC-21, `GET /communication-channels`, `GET /alerts` | The dashboard shows channel status, delays and lost packets; alerts on excess delay (FR-31) | |
| Raw measurements reach central storage before the hour closes | NFR-7, FR-07 | Within 5 min of the hour closing (NFR-7) | Outbox lag is the metric: `created_at` to `published_at` |
| Metering node maintenance events recorded | FR-25 | Each event tied to a node, with timestamp and user | |

## Cross-cutting requirements

Not tied to a single goal, but load-bearing.

| Area | Requirement | Artefacts | How it is measured | Implemented |
|---|---|---|---|---|
| Availability | The system is available to everyone during critical periods | NFR-8 | At least 99.9% a month, about 43 minutes. No planned work from the 25th to the 5th | |
| Capacity | Retention for both layers | NFR-9 | Raw layer 1 year, accounting layer 3 years, at least 50 nodes at one measurement a minute | |
| Security and audit | Access control, every action logged | NFR-12, FR-01, FR-28, FR-29, UC-18, `GET /audit-log` | Everything is logged. The counterparty sees only its own nodes (NFR-12). The administrator manages users and roles (FR-28) | |
| Asynchronous operations | Regulator export, large volumes | UC-24, `POST /audit-exports` | Asynchronous pattern: POST returns 202, GET returns status and download link | |
| End-to-end notification latency | From measurement to the counterparty being told | NFR-13, FR-07, FR-22, NFR-1, NFR-5 | Under 6 min: telemetry ≤ 2, recording ≤ 1, notification ≤ 3 | Traced end to end by correlation id |

## Consistency check

| Check | Result |
|---|---|
| Any goal with nothing delivering it? | No. Each of the four goals has between four and six artefacts. |
| Any orphan requirements, tied to no goal? | No. Every NFR and every key FR appears, with the cross-cutting ones listed separately. |
| A measure for every goal? | Yes. Each goal rests on measurable NFRs — latencies, deadlines, availability. |
| Every conflict traceable? | Yes. Four conflicts, each tied to an ADR and to a goal. |

## What the implementation column shows

Six rows out of thirty-one are covered by code. They are not a random sixth: they
are the rows where the measure is a latency or a guarantee about delivery, which
is exactly what the asynchronous core exists to provide. The rows left blank are
interfaces, documents and physical calculation — specified, and deliberately not
built here.

Two rows gained something the specification did not ask for. Duplicate control on
intake is enforced by a unique constraint rather than by application logic, so
FR-16 cannot be violated by a code path that forgets to check. And NFR-7 acquired
a concrete metric it did not have: the age of the oldest unpublished outbox row,
which is the delivery lag stated as a number rather than as an intention. See
[ADR-007](adr/0007-outbox-vs-cdc.md) and [ADR-008](adr/0008-delivery-guarantees.md).
