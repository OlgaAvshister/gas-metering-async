# User stories
The use cases describe how a role works with the system step by step. The stories below
cut the same ground into deliverable pieces for a backlog: each one names who needs it,
what they need and why, and carries acceptance criteria a tester can check without asking
the analyst. Every story traces back to its use case and requirements.

Two formats are used for acceptance criteria, on purpose:
- **Given / When / Then** where behaviour depends on a sequence of events (alarms,
  notifications, re-reads).
- **Rule checklist** where the story is about content or constraints that hold regardless
  of order (what a document contains, who may see what).

Every story includes at least one negative or failure criterion, because that is where
the use cases' extensions live.

## Prioritization
MoSCoW against the MVP goal stated in [02-scope.md](02-scope.md): the operator and the
counterparty must agree on delivered volumes before the act is signed, and the operator
must react to deviations within the contractual time.
- **Must**: without it the act cannot be produced lawfully, or a contractual obligation
  (notification time, access separation) is broken.
- **Should**: removes manual work and disputes, but the process can run without it
  for the first release.
- **Could**: convenience for a single role, no contractual consequence.

| Story | Title | Priority | Use case | Requirements |
|---|---|---|---|---|
| US-01 | Deviation alarm for the dispatcher | Must | UC-02 | FR-07 |
| US-02 | Deviation notification to the counterparty | Must | UC-13 | FR-22, NFR-5 |
| US-03 | Archive re-read without loss or duplicates | Must | UC-22 | FR-16, NFR-6 |
| US-04 | Last trustworthy value during connection loss | Must | UC-03 | FR-14 |
| US-05 | Counterparty sees only their own delivery points | Must | UC-11 | FR-20, NFR-12 |
| US-06 | Automatic correction to standard conditions | Must | UC-06 | FR-10, FR-11 |
| US-07 | Recalculation creates a new version | Must | UC-06 (manual) | FR-12, FR-13, FR-17 |
| US-08 | Transfer act as PDF | Must | UC-08 | FR-19 |
| US-09 | Corrective act for a closed period | Should | UC-09 | FR-18 |
| US-10 | Counterparty uploads own calculations | Should | UC-12 | FR-21 |
| US-11 | Data arrival status before calculation | Should | UC-05 | FR-09 |
| US-12 | Shift history for the dispatcher | Could | UC-04 | FR-06 |

US-09 is Should although corrective acts are a legal mechanism: in the first month after
launch no period has closed yet, so the need arises only after T + 10 working days.

## US-01. Deviation alarm for the dispatcher
**As a** dispatcher, **I want** to be alerted as soon as actual flow on a line leaves the
contractual corridor, **so that** I can adjust the transport regime before the volume
deviation grows.
Priority: Must · Traces to: UC-02, FR-07
**Acceptance criteria**
1. **Given** a line with an active contract parameter and a materiality threshold,
   **when** a telemetry value arrives that takes actual flow outside the threshold,
   **then** a deviation is recorded within 1 minute of the telemetry being received.
2. **Given** a recorded deviation, **when** the dispatcher views the monitoring screen,
   **then** the stretch is highlighted and the alarm shows the line, time recorded,
   deviation in absolute and relative terms, and how long it has lasted.
3. **Given** an open deviation, **when** further out-of-threshold values arrive,
   **then** no new deviation is opened; the existing one is extended.
4. **Given** an open deviation, **when** flow returns inside the corridor,
   **then** the alarm is withdrawn automatically and the event stays in the journal.
5. **Given** a line with no active contract parameter for the current time,
   **when** telemetry arrives, **then** no deviation is recorded and the line is shown as
   "no nomination", rather than measured against a zero plan.
**Open question:** FR-07 uses one threshold for both the dispatcher alarm and the
counterparty notification. The alarm needs an instantaneous threshold, the notification
an accumulated one. To be agreed with the dispatcher and the commercial side.

## US-02. Deviation notification to the counterparty
**As a** counterparty representative, **I want** to be notified of a material deviation
from the nomination, **so that** I can adjust my intake schedule in time.
Priority: Must · Traces to: UC-13, FR-22, NFR-5
**Acceptance criteria**
1. **Given** a counterparty with at least one notification channel recorded,
   **when** a deviation is recorded on their delivery point, **then** the notification
   is sent within 3 minutes of recording.
2. The notification contains: date and time of the event, line or delivery point,
   deviation in absolute and relative terms, and a link to the detail screen.
3. **Given** an open deviation that keeps growing, **when** new telemetry arrives,
   **then** no further notification is sent; one notification per open deviation.
4. **Given** the primary channel fails, **when** sending is attempted, **then** the system
   retries with a delay and, after the retry budget is spent, sends via the fallback
   channel and records the failure in the journal.
5. **Given** the notification worker crashes after sending but before confirming,
   **when** the message is redelivered, **then** the counterparty does not receive a
   second notification for the same deviation.
6. **Given** a counterparty with no channel recorded, **when** a deviation is recorded,
   **then** the system records "not deliverable: no channel" and raises an alert to
   IT operations.
**Open question:** criterion 5 holds only up to the moment of sending. If the worker dies
between the gateway accepting the message and the system recording it, a duplicate is
still possible. Closing that gap needs an idempotency key supported by the gateway.

## US-03. Archive re-read without loss or duplicates
**As an** IT operations specialist, **I want** the system to recover data from a metering
node's archive after an outage, **so that** accounting volumes are calculated on complete
data without manual repair.
Priority: Must · Traces to: UC-22, FR-16, NFR-6
**Acceptance criteria**
1. **Given** a node that was offline for up to 72 hours, **when** the connection is
   restored, **then** the archive for the outage period is re-read and loaded within
   15 minutes.
2. **Given** measurements that are already stored, **when** the archive returns the same
   node and timestamp, **then** no second record is created.
3. **Given** an hourly aggregate already published for an hour inside the outage,
   **when** the missing measurements for that hour are loaded, **then** the aggregate is
   recomputed from all measurements of the hour, not incremented.
4. **Given** accounting volumes already calculated for the affected period,
   **when** the re-read completes, **then** the period is marked "needs recalculation".
5. **Given** the archive does not cover the whole outage, **when** the re-read completes,
   **then** the uncovered interval is marked "unmeasured" and is not filled by
   interpolation.
**Open question:** FR-16 is silent on value conflicts, when the archive returns a
different value for a timestamp already stored. Currently the first value wins.
Needs a rule from the accounting engineer: keep the first, take the archive, or flag
for review.

## US-04. Last trustworthy value during connection loss
**As a** dispatcher, **I want** to see the last trustworthy measurement and how long data
has been missing, **so that** I can keep steering the regime on incomplete information
without mistaking stale data for live data.
Priority: Must · Traces to: UC-03, FR-14
**Acceptance criteria**
1. **Given** no new telemetry from a node within the configured interval,
   **when** the interval expires, **then** the node's status changes to "connection lost".
2. While the connection is lost, the chart shows the last trustworthy value as a flat
   line marked "no data since HH:MM, showing last measurement", together with the outage
   duration.
3. The operational layer never contains interpolated or extrapolated values.
4. **Given** the connection returns, **when** fresh telemetry arrives, **then** live data
   is shown again and the marking disappears without the dispatcher refreshing the page.
5. **Given** several nodes lose connection at once, **when** the dispatcher opens the
   overview, **then** each node's status and outage duration is shown separately.

## US-05. Counterparty sees only their own delivery points
**As a** counterparty representative, **I want** to review the accounting data for my
delivery point, **so that** I can check the operator's calculations before signing the
act.
Priority: Must · Traces to: UC-11, FR-20, NFR-12
**Acceptance criteria (rules)**
- The list of delivery points contains only those assigned to the counterparty by contract.
- For a selected point and period the screen shows: volume at standard conditions, gas
  composition, method versions applied, date of calculation, and a "calculated" flag on
  substituted periods.
- A request for a node or delivery point outside the counterparty's contract returns
  "access denied" (HTTP 403), both in the interface and through the API, and does not
  reveal whether that node exists.
- A period that is not fully calculated is shown with the missing part marked
  "calculation not complete".
- Every view and export by the counterparty is written to the audit journal.

## US-06. Automatic correction to standard conditions
**As an** accounting engineer, **I want** volumes corrected to standard conditions as soon
as all inputs are present, **so that** I do not have to start calculations by hand.
Priority: Must · Traces to: UC-06, FR-10, FR-11
**Acceptance criteria**
1. **Given** validated telemetry, a gas composition and an assigned method version for a
   node and period, **when** the last of these arrives, **then** the correction starts
   automatically and the hourly volume is published within NFR-2 limits.
2. The stored result references the method version applied and the input records used.
3. **Given** the method version changes after the calculation, **when** the result is
   viewed, **then** it still shows the version that was active at calculation time.
4. **Given** telemetry marked suspect by validation, **when** other inputs arrive,
   **then** the calculation does not start and the period shows "manual check required".
5. **Given** no gas composition within the regulated deadline, **when** the deadline
   passes, **then** the period shows "awaiting laboratory".

## US-07. Recalculation creates a new version
**As an** accounting engineer, **I want** each recalculation to keep the previous value,
**so that** every change to accounting data can be explained during an audit.
Priority: Must · Traces to: UC-06 (manual), FR-12, FR-13, FR-17
**Acceptance criteria**
1. **Given** an open period, **when** the engineer starts a recalculation with a reason,
   **then** a new version of the value is created and the previous version stays
   available.
2. The correction journal records: date and time, user, type of action, reason,
   previous value, new value, link to the version.
3. **Given** a recalculation request without a reason, **when** it is submitted,
   **then** it is rejected with "reason required".
4. **Given** a closed period (after T + 10 working days), **when** the engineer tries to
   recalculate, **then** the action is refused and a corrective act is offered instead.

## US-08. Transfer act as PDF
**As an** accounting engineer, **I want** to produce the monthly transfer act as a PDF,
**so that** both parties have a legally significant document to sign.
Priority: Must · Traces to: UC-08, FR-19
**Acceptance criteria (rules)**
- The act contains: total volume at standard conditions, weighted average quality
  figures, method versions applied, and the list of periods filled by calculated
  substitution.
- The act is stored with a unique number and production date and can be downloaded
  again later with identical content.
- If the period is not fully calculated, the engineer is warned and can either wait or
  produce the act with calculated stretches flagged; the act cannot be produced silently.
- For a period whose act is already signed, producing a new act is refused and a
  corrective act is offered.

## US-09. Corrective act for a closed period
**As an** accounting engineer, **I want** to record refined data for a closed period in a
separate corrective act, **so that** the signed original stays intact.
Priority: Should · Traces to: UC-09, FR-18
**Acceptance criteria**
1. **Given** a closed period and a stated reason, **when** the engineer produces a
   corrective act, **then** a new document is created linked to the original by number
   and date, and the original is not modified.
2. The corrective act lists each corrected figure with its value before and after, and
   the corrected totals.
3. **Given** the discrepancy is within the contractual threshold, **then** the act is
   marked "simplified procedure"; **given** it exceeds the threshold, **then** it is marked
   "requires agreement of the parties".
4. **Given** an open period, **when** the engineer tries to produce a corrective act,
   **then** the action is refused, since an ordinary recalculation is still possible.

## US-10. Counterparty uploads own calculations
**As a** counterparty representative, **I want** to upload my own calculations and compare
them with the operator's, **so that** discrepancies are found before the act is signed,
not after.
Priority: Should · Traces to: UC-12, FR-21
**Acceptance criteria**
1. **Given** a valid Excel or CSV file for my delivery point and period, **when** I run
   the comparison, **then** volume and quality figures are compared per measure and
   discrepancies beyond the contractual tolerance are highlighted with the percentage
   difference.
2. **Given** no figures exceed the tolerance, **then** the result reads "no discrepancies
   found".
3. **Given** a file in another format or with missing columns, **when** I upload it,
   **then** it is rejected with the list of accepted formats and the missing columns
   named.
4. **Given** a file containing a delivery point outside my contract, **when** I upload it,
   **then** those rows are rejected and not compared.
5. I can download a discrepancy report for the comparison.

## US-11. Data arrival status before calculation
**As an** accounting engineer, **I want** to see which inputs for a node and period have
arrived, **so that** I know what is holding up the calculation and whom to chase.
Priority: Should · Traces to: UC-05, FR-09
**Acceptance criteria (rules)**
- For a node and period the screen shows the status of each input: telemetry (received,
  awaited, partly lost), gas composition (received, awaited), method version (assigned,
  not assigned).
- When all inputs are present, the status reads "ready to calculate" with the expected
  calculation time.
- When the gas composition is past the regulated deadline, a warning is shown.
- When part of the telemetry is irrecoverably lost, the period is marked "manual entry
  required".

## US-12. Shift history for the dispatcher
**As a** dispatcher, **I want** to review flow on a line for my shift, **so that** I can
assess the quality of control and prepare the shift report.
Priority: Could · Traces to: UC-04, FR-06
**Acceptance criteria**
1. **Given** a line, date and time range, **when** the dispatcher opens the history,
   **then** the flow chart and the minimum, maximum and average flow and total volume for
   the range are shown.
2. **Given** missing data inside the range, **then** those stretches are marked "no data"
   and excluded from the aggregates, and the aggregates say so.
3. The dispatcher can overlay several lines on one chart.
