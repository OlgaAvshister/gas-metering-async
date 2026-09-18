# Functional requirements

The functions the system performs within the MVP scope. Requirements are grouped
by processing flow: intake, storage and calculation, operational monitoring,
abnormal situations, documents, interaction with the second party of the joint
venture, and the supporting roles. Each requirement is written as a checkable
statement and traces back to a source — an architectural decision, a role's
need, or a business goal.

Requirements marked **implemented** are covered by the services in this
repository; the rest belong to parts of the system outside its scope.

## Intake and storage

**FR-01.** The system shall authenticate users by login and password.

**FR-02.** The system shall maintain two parallel data layers for every
measurement: an operational layer and an accounting layer. Both draw on a single
primary source — measurements taken at the metering node — but run through
independent processing pipelines. See [ADR-001](../adr/0001-two-data-layers.md).
*Implemented: the operational layer.*

**FR-03.** The operational layer shall hold raw telemetry at operating
conditions (volume, pressure, temperature) with minimal delay, and shall be used
solely for operational monitoring by the dispatcher. *Implemented.*

**FR-04.** The accounting layer shall hold gas volumes corrected to standard
conditions using the gas composition and versioned method reference data. The
accounting layer is the source for transfer acts and for reconciliation with the
counterparty.

**FR-05.** The system shall mark every displayed figure in the interface with the
layer it belongs to. The dispatcher shall not be able to steer transport on
accounting data, and the accounting engineer shall not cite operational data in
an act.

**FR-08.** The system shall accept, validate and store telemetry from metering
nodes automatically, including volumetric flow, pressure and temperature. On
receiving a packet the system shall check its integrity (no loss, correct
checksums) and the physical plausibility of its values (ranges, absence of
outliers). Packets that fail validation shall be marked suspect and routed to a
manual review queue. Working that queue is outside the MVP: flagged packets are
excluded from accounting calculations and made available to IT operations for
export. *Implemented: intake, storage and the suspect flag.*

**FR-09.** The system shall accept and store laboratory gas composition results
automatically. Where automatic intake is not possible, the system shall provide
manual upload with the sampling date and time, the metering node and the
laboratory analysis identifier.

## Calculation and versioning

**FR-10.** The system shall initiate correction of gas volume from operating to
standard conditions automatically once both validated telemetry and a gas
composition exist for the period concerned. The result is placed in the
accounting layer.

**FR-11.** Every accounting calculation shall apply the version of the method
reference data that was active at the time of calculation, and shall store the
identifier of the applied version alongside the result. See
[ADR-003](../adr/0003-method-versioning.md).

**FR-12.** The system shall version accounting values. A correction shall not
overwrite an existing record but create a new version of the value. All versions
remain available for review and audit.

**FR-13.** The system shall keep a complete history of every change to accounting
data in an immutable journal. Each entry shall carry the time of the change, the
user identifier, the reason for the change, the previous value, the new value and
a reference to the version created.

## Operational monitoring

**FR-06.** The system shall give the dispatcher a view, per pipeline line, of the
planned daily nomination and the actual raw gas flow from the operational layer
on a single time axis.

**FR-07.** The system shall detect automatically when the actual raw flow moves
outside the contractual materiality threshold, using the threshold value held in
the contract reference data, and shall raise a visual alarm on the dispatcher's
screen. No more than one minute shall pass between receiving the telemetry and
recording the deviation. *Implemented.*

**FR-22.** The system shall notify the counterparty's representative
automatically of a recorded material deviation of actual transport from the
nomination. See [ADR-004](../adr/0004-counterparty-notification.md).
*Implemented.*

## Abnormal situations

**FR-14.** On loss of connection to a metering node the system shall display the
last trustworthy measured value on the dispatcher's screen as a constant, with
the period of missing data marked explicitly. Interpolation and extrapolation in
the operational layer are not permitted. See
[ADR-005](../adr/0005-connection-loss.md).

**FR-15.** On loss of connection to a metering node the system shall substitute a
calculated volume in the accounting layer for the period without measurements,
following the regulated method. The substituted period and value shall carry a
"calculated" flag naming the substitution method applied.

**FR-16.** Once the connection to a metering node is restored, the system shall
initiate a re-read of the controller's local archive for the period of the
outage. The system shall control duplicates and overlapping periods so that no
data is lost or recorded twice. *Implemented.*

## Documents

**FR-17.** The system shall set a closing date of T + 10 working days from the end
of each reporting period. After that date the original transfer act may not be
changed. See [ADR-002](../adr/0002-period-closing.md).

**FR-18.** The system shall support a corrective act for clarifications received
after the reporting period has closed. A corrective act is a separate document
linked to the original act and does not modify it.

**FR-19.** The system shall let the accounting engineer produce the gas transfer
act for a reporting period as a PDF.

**FR-32.** The system shall support signing of a transfer act by both parties of
the joint venture. The operator may sign only acts covering its own delivery
points, and the counterparty only those it has access to. Each signature is
recorded with the party, the user and the time.

## Interaction with the counterparty

**FR-20.** The system shall give the counterparty's representative read access to
primary data, calculations and the correction journal for the metering nodes of
the delivery point defined by contract.

**FR-21.** The system shall let the counterparty's representative upload their own
calculated data and compare it automatically against the operator's calculations,
showing the discrepancies found.

## Supporting roles

**FR-23.** The system shall let the financial controller export a financial
summary of signed gas transfer acts for an arbitrary period, in a format suitable
for the finance systems. The summary shall carry the total accounting volumes per
pipeline line and aggregated gas quality figures.

**FR-24.** The system shall give the financial controller read access to signed
transfer acts and corrective acts as PDF.

**FR-25.** The system shall record events relating to metering node maintenance,
including instrument replacement, calibration and manual entry of readings during
incidents. Each event shall be tied to a specific metering node and carry a
timestamp and the identifier of the user who recorded it (dispatcher or IT
operations).

**FR-26.** The system shall let the regulator (external auditor) export the full
data set for an arbitrary period on request, including raw measurements from the
operational layer, corrected volumes from the accounting layer, the method
versions applied, the complete correction journal and every act produced.

**FR-27.** The regulator export shall make every calculation reproducible: using
the exported input data and the stated method versions, any auditor shall be able
to repeat an accounting calculation and obtain an identical result.

**FR-28.** The system shall let the administrator create users, assign roles, and
block and unblock accounts. Supported roles: Dispatcher, Accounting engineer,
Counterparty representative, Financial controller, Administrator, IT operations,
Laboratory technician, Regulator.

**FR-29.** The system shall give the administrator access to the audit journal of
all user actions, filterable by user, time and action type.

**FR-30.** The system shall let the administrator view method reference data and
add new versions; editing a version already created is forbidden, so that
calculations stay reproducible. Changing contract parameters (nominations,
deviation thresholds) through the interface is not part of the MVP.

**FR-31.** The system shall give IT operations a dashboard for the state of the
communication channels to the metering nodes and of the integration gateways. The
dashboard shall show the status of each channel, data delivery delays, lost
packets and the overall integrity of the data stores. The system shall raise
alerts to IT operations automatically on packet loss, on delivery delay beyond
the permitted figure, and on a storage integrity failure.
