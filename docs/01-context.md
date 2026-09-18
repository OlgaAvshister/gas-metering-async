# Context and purpose

> This is a study project. The domain is modelled on a real joint venture, but
> the requirements, decisions and data here were written from public knowledge of
> how gas metering works; no proprietary material was used.

## The business

KazRosGas is a joint venture that buys, sells and transports gas between
Kazakhstan and Russia. Both parties hold an equal economic interest in the volume
and quality of the gas transferred, yet primary metering is carried out at
metering nodes operated by one of them — the transport operator.

That asymmetry is the root of everything else in this specification. One party
produces the figures; both parties are paid according to them.

## How the work is done today

Operational data from the metering nodes reaches the dispatch service through
SCADA, but is not matched automatically against the daily nominations; execution
is tracked by hand.

Accounting volumes are calculated by the accounting engineer in separate
spreadsheets, from telemetry, laboratory composition results and coefficient
reference tables. The inputs arrive from different sources, at different times,
in different formats.

Reconciliation against the counterparty's own metering data happens once the
reporting period has ended, so discrepancies surface after the fact — when it is
too late to act on what caused them.

The gas transfer act is assembled manually, and the history of corrections is not
recorded in machine-readable form, which makes disagreements between the parties
hard to work through.

## The central fact about this domain

Operational and accounting data are fundamentally different quantities.

A flow meter reading taken at operating conditions becomes an accounting volume
only after correction to standard conditions, and that correction needs the gas
composition, which a laboratory determines with a delay.

Current practice does not separate these two streams explicitly, and the result
is that nobody involved fully trusts the figures. Every architectural decision in
this specification follows from this one constraint: the fast number and the
accurate number cannot be the same number.

## Purpose of the system

The system provides a single loop for collecting, processing and agreeing data
about gas deliveries:

- operational monitoring of nomination execution, for the dispatch service
- calculation of accounting volumes with full traceability of sources and
  corrections, for the accounting engineer
- symmetrical access to primary data and change history, for the second party of
  the joint venture

The aim is to cut the time it takes to detect a discrepancy from a reporting
period down to an operational shift, and to make the procedure for producing a
transfer act legally defensible.

## Business goals

1. Cut detection of a discrepancy between actual transport and the nomination
   from a reporting period (a month) to an operational shift.
2. Produce the gas transfer act with full traceability of data sources and
   corrections, without manual assembly in spreadsheets.
3. Reduce the share of acts signed with a protocol of disagreement, by giving
   both parties symmetrical access to primary data and change history.
4. Eliminate irrecoverable data loss when connections to remote metering nodes
   drop.
