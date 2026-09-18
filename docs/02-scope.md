# MVP scope

## In scope

- Intake of telemetry from metering nodes and of gas composition from the
  laboratory information system, including re-reading controller archives once a
  connection is restored.
- Two data layers: operational (raw measurements, for monitoring) and accounting
  (corrected to standard conditions, for calculation).
- Operational monitoring of nomination execution per pipeline line, with an alarm
  on deviation.
- Automatic notification of the second party of the joint venture about recorded
  deviations.
- Calculation of accounting volumes against versioned method reference data, with
  the version recorded in every calculation.
- An immutable correction journal: who, when, on what grounds.
- Production of the transfer act for a reporting period, and of a corrective act
  after the period has closed.
- Reconciliation against the counterparty's metering data, with discrepancies
  displayed.
- Access control between roles and between the two parties.

## Out of scope

**Control of process equipment.** The system issues no commands to valves and is
not part of the process control loop. It records a deviation and signals the
dispatcher; the decision and the action stay with people and with the existing
control systems.

**Replacing SCADA.** SCADA remains the source of telemetry; this system is a
consumer of it.

**Billing and settlement.** The system produces the act as an accounting
document; invoicing and payment happen in the finance systems.

**Predictive analytics.** Forecasting deviations, expected nomination corridors,
and anomaly detection as a sign of leaks — deferred to v2.

**Metrological support for instruments.** Calibration scheduling and certificate
records stay in the existing systems and are integrated as reference data.

**Mobile workplaces.** Web interface only.

**Working through a protocol of disagreement.** The system records that a party
refused to sign and moves the act to "disagreement" status; the protocol itself
is drawn up and worked through by the parties outside the system.

## Assumptions

- Metering nodes are fitted with controllers holding a local archive, deep enough
  to recover data after a typical outage.
- Contract parameters — nominations, permitted tolerances, the materiality
  threshold for deviations, act signing deadlines — enter the system as reference
  data and are not editable through the interface in the MVP.
- Both parties use one instance of the system. The counterparty's own accounting
  system is integrated for reconciliation but not replaced.

## Scope of the implementation in this repository

The services here cover the asynchronous core: intake and validation of
telemetry (FR-08), archive re-read without loss or duplication (FR-16), hourly
aggregation in the operational layer, deviation detection against the nomination
(FR-07) and notification of the counterparty (FR-22, NFR-5, NFR-13).

The accounting layer, the documents, the interfaces and the supporting roles are
specified but not implemented. They are marked as such in the requirements.
