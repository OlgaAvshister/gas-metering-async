# Non-functional requirements

Requirements on how well the system works: latency, availability, storage
capacity, integrity and access control. Each carries a figure and a two-sided
justification — why it cannot be stricter (a technical or economic limit) and why
it cannot be looser (a business consequence). Written this way, a requirement can
be checked at acceptance and defended when the project budget is revisited.

Requirements marked **implemented** are covered by the services in this
repository; the rest belong to parts of the system outside its scope.

## Latency

**NFR-1.** The operational data layer (raw telemetry) shall be available to the
dispatcher no more than 2 minutes after the measurement.

- *No stricter:* communication channels on remote sections cannot guarantee
  delivery within 30 seconds.
- *No looser:* beyond 2 minutes the dispatcher has less than a minute to decide
  inside the 3–5 minute reaction window.

**NFR-2.** Hourly accounting volumes shall be published no later than 30 minutes
after the gas composition is received, and no later than 4 hours after the end of
the hour.

- *No stricter:* 30 minutes is the minimum time to deliver and validate a
  chromatogram; demanding 15 would leave the laboratory no margin to re-check.
- *No looser:* 4 hours is the latest the engineer can still close the daily
  balance before the reporting handover at 08:00 or 20:00.

**NFR-5.** A notification of a material deviation shall reach the counterparty no
later than 3 minutes after the system records the deviation. *Implemented.*

- *No stricter (< 1 minute):* external channels (API, SMS, e-mail) cannot
  guarantee delivery within a minute; promising it would create false
  expectations and false alarms about failures.
- *No looser (> 3 minutes):* the counterparty needs 5–10 minutes to react by
  redistributing gas between consumers. 3 minutes is achievable and leaves them
  2–7 minutes to act.

**NFR-7.** Raw measurements from metering nodes shall reach central storage no
later than 5 minutes after the close of the hour. *Implemented.*

- *No stricter (< 3 minutes):* hourly batch processing cannot start before the
  hour ends; under 3 minutes is technically difficult and leaves no margin for
  channel delays.
- *No looser (> 10 minutes):* the engineer starts building balances as soon as
  the hour closes; more than 5 minutes per hour accumulates and pushes the daily
  balance back by 2–3 hours.

**NFR-10.** The final act for a reporting month shall be produced within 5
minutes of the request.

- *No stricter (< 2 minutes):* a monthly act aggregates roughly 4,320 records per
  node, includes recalculations and PDF generation; 2 minutes is too tight for
  that volume without cutting corners.
- *No looser (> 10 minutes):* the engineer produces the act several times a
  month; waiting longer than 5 minutes breaks up the work, he switches to other
  tasks and loses context, and the total time grows several-fold.

**NFR-13.** End-to-end latency from the moment of measurement to delivery of the
deviation notification to the counterparty shall not exceed 6 minutes.
*Implemented.*

- *No stricter (< 4 minutes):* physically impossible to guarantee over unstable
  channels and external delivery providers (SMS, e-mail), once the time to record
  the deviation is included.
- *No looser (> 6 minutes):* the counterparty's operational window tops out at
  5–10 minutes. Beyond 6 minutes they are left under 4 minutes to react, which
  substantially devalues the notification. The requirement is end-to-end:
  NFR-1 (≤ 2 min to deliver telemetry) + recording the deviation (≤ 1 min) +
  NFR-5 (≤ 3 min to deliver the notification) = 6 minutes.

## Recovery and integrity

**NFR-6.** On restoration of a connection the system shall re-read the
controller's local archive for an outage of up to 72 hours without loss or
duplication, and shall complete the re-read within 15 minutes. *Implemented:
the no-loss, no-duplication guarantee.*

- *No stricter (> 72 hours, or < 10 minutes to re-read):* controller memory is
  limited and does not hold more than 72 hours (an assumption about the
  environment). Re-reading 4,320 records from 50 nodes in under 10 minutes is an
  excessive demand on computing capacity.
- *No looser (< 48 hours, or > 30 minutes to re-read):* the regulated time to
  restore a connection is 24–48 hours, so 72 hours gives margin. Waiting more
  than 30 minutes shifts the engineer's balance work and risks missing daily
  deadlines.

**NFR-3.** A reporting period shall close to changes 10 working days after it
ends.

- *No stricter (5 days):* refined laboratory analyses and data from the
  counterparty physically cannot arrive within 5 days, particularly when the
  period ends before public holidays.
- *No looser (15–20 days):* the counterparty needs legal certainty to plan its
  obligations; stretching beyond 15 days undermines trust in the accounting
  system.

**NFR-4.** The system shall retain versions of the method reference data and
guarantee that a calculation can be reproduced with the version active at the
time, for 5 years. Reproducibility means repeating the calculation from stored
accounting-layer inputs (corrected values, gas composition, the method version
applied), not from raw telemetry. Calculation inputs are stored together with the
result.

- *No stricter (> 5 years):* retention periods for accounting and tax records do
  not exceed 5 years in most jurisdictions; holding data longer raises storage
  cost without legal necessity.
- *No looser (< 5 years):* 5 years is the usual retention period for tax
  inspection and audit in both jurisdictions of the joint venture.

**NFR-11.** Accounting data shall be immutable once recorded (append-only). A
correction creates a new version of the value and the original record remains
available. The correction journal holds the time, the user, the reason, and the
previous and new values. The journal is retained for 5 years.

- *No stricter (no corrections at all after recording):* makes it impossible to
  fix objective errors, such as a refined gas composition, without reopening the
  period — which contradicts conflict 2.
- *No looser (a journal without the previous value or without the reason):*
  without "before and after" there is no audit; without a reason a correction
  looks arbitrary. The 5 years match the retention of method versions (NFR-4).

**NFR-14.** Recovery point objective (RPO) shall be no more than 15 minutes and
recovery time objective (RTO) no more than 4 hours.

- *No stricter:* an RPO under 5 minutes requires synchronous replication to a
  standby data centre, which raises infrastructure cost and duplicates NFR-8.
- *No looser:* losing more than 15 minutes of telemetry means the period must be
  substituted by calculation and becomes a matter of dispute with the
  counterparty; an RTO beyond 4 hours during period close misses the deadline for
  producing the act.

## Availability and capacity

**NFR-8.** System availability shall be at least 99.9% per month (about 43
minutes of downtime). Planned maintenance is forbidden from the 25th to the 5th.

- *No stricter (99.99%):* requires a fault-tolerant cluster with hot standby,
  raising infrastructure cost two- to threefold; excessive for an accounting
  system.
- *No looser (< 99.0%):* more than 7 hours of downtime a month during period
  close misses deadlines and incurs penalties. 99.9% leaves about 43 minutes —
  enough for one maintenance window outside peak plus margin for failures.

**NFR-9.** Storage capacity: at least 50 metering nodes, one measurement per
minute, retention of 1 year for the raw layer and 3 years for the accounting
layer. One year of raw data is sufficient: reproducibility across the full
retention period rests on the stored accounting-layer inputs (see NFR-4), not on
re-reading raw telemetry.

- *No stricter (> 100 nodes, or 5 years for both layers):* the first phase covers
  only the trunk lines (50 nodes), and a multiple of that is not justified for an
  MVP. Three years of raw data is excessive: once corrected into the accounting
  layer, raw data is needed only to reproduce primary measurements for the last
  year.
- *No looser (< 30 nodes, or < 1 year of accounting layer):* 30 nodes would not
  cover even the main lines of the first phase. Less than 3 years of accounting
  data makes it impossible to analyse trends or settle disputes over earlier
  periods.

## Access control

**NFR-12.** Access control: the operator has full read and write access to all
data. The counterparty has read access to primary data, calculations and the
correction journal for the metering nodes of the delivery point defined by
contract. Data on other nodes, not relating to deliveries to that counterparty,
is not available. All actions are logged.

- *No stricter (the counterparty sees every node):* breaches the operator's
  commercial confidentiality over other deliveries.
- *No looser (the counterparty sees only the final act, without primary data):*
  without primary data and history the counterparty cannot verify the operator's
  calculations, which destroys trust and brings manual reconciliation back.
