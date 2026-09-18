# Use cases: Accounting engineer

## UC-05. Checking that the inputs for a calculation have arrived

**Goal.** Establish whether all the data needed to calculate the accounting
volume for a node is available, and what is holding things up.

**Precondition.** The engineer is signed in.

**Main scenario**

1. The engineer opens the data arrival screen.
2. The engineer selects a metering node or line, and a period.
3. The system shows the status of each input for that period: telemetry (volume,
   pressure, temperature) as received, awaited or partly lost; gas composition
   (the chromatogram) as received or awaited from the laboratory; and the method
   version as assigned or not assigned.
4. If everything has arrived, the system shows "ready to calculate" and when the
   recalculation is expected to run.
5. If something is missing, the system shows exactly what, and when it is
   expected, from the laboratory's schedule.

**Result.** The engineer knows what stage the data preparation has reached.

**Alternatives**

- The gas composition is later than the regulated deadline: the system shows a
  warning and the engineer contacts the laboratory.
- Part of the telemetry is irrecoverably lost: the system marks the period
  "manual entry required" and the engineer enters readings from fallback sources.

## UC-06. Running the correction to standard conditions

**Role.** Accounting engineer; normally the system runs this by itself.

**Goal.** Obtain the gas volume corrected to standard conditions, for use in acts
and reconciliation.

**Precondition.** For the chosen node and period, all inputs are present:
validated telemetry, gas composition, and an assigned method version.

**Main scenario, automatic**

1. The system records that all inputs for a node and period are present.
2. The system starts the correction automatically.
3. The system applies the method reference version active at the time of
   calculation.
4. The system converts the volume from operating to standard conditions, applying
   pressure, temperature and the compressibility factor derived from the gas
   composition.
5. The system stores the result in the accounting layer together with the
   identifier of the method version applied and references to the source data —
   the calculation inputs.
6. The system moves the period's status to "calculated".
7. The engineer is notified that the calculation has finished (optional).

**Result.** The accounting layer holds new data, ready for use in acts.

**Main scenario, manual recalculation**

1. The engineer opens the calculation management screen.
2. The engineer selects a node and period and states the reason for
   recalculating.
3. The system checks whether the period is closed; if it is, recalculation is
   forbidden and only a corrective act is available.
4. The system recalculates under the same rules (FR-10).
5. The system stores a new version of the accounting value (FR-12) and an entry
   in the correction journal (FR-13).

**Result.** Accounting data is updated and the change is recorded in the journal.

**Alternatives**

- The gas composition has not arrived within the deadline (NFR-2): the system
  shows "awaiting laboratory" and the engineer raises a manual request.
- Telemetry failed validation, with outliers or anomalies: the system marks the
  data suspect and does not start the calculation; the engineer checks it by
  hand.

## UC-07. Reviewing the correction journal

**Goal.** Check the history of changes to accounting data for a period or node,
and understand why they were made.

**Precondition.** The engineer is signed in.

**Main scenario**

1. The engineer opens the correction journal.
2. The engineer sets filters: metering node or line, period, type of change,
   user.
3. The system shows the entries with the date and time of the change, the user
   identifier, the type of action (calculation, manual correction, calculated
   substitution), the grounds — a user comment or a reference to the regulation —
   the previous value, the new value, and a link to the data version.
4. The engineer reviews the entries and opens the detail of any change.

**Result.** The engineer has the full history of changes, for audit or analysis.

**Alternatives**

- Nothing matches the filters: the system shows "no records found".
- The engineer exports the journal: the system produces a file in the agreed
  format.

## UC-08. Producing the transfer act

**Goal.** Produce the legally significant document covering volume and quality of
gas transferred over a reporting period.

**Precondition.** The reporting period has ended and the accounting data has been
calculated and stored.

**Main scenario**

1. The engineer opens the transfer acts section.
2. The engineer selects the reporting period, a month.
3. The engineer presses "produce act".
4. The system gathers the data from the accounting layer for that period: total
   volume at standard conditions; weighted average quality figures — calorific
   value, density and so on — derived from the gas composition; references to the
   method versions applied; and the list of periods filled by calculated
   substitution, if any.
5. The system generates a PDF from the agreed template.
6. The system stores the act in the document store with a unique number and the
   date it was produced.
7. The system displays the PDF for review and download.

**Result.** The engineer has a transfer act ready for the parties to sign.

**Alternatives**

- The period is not fully calculated, with gaps or a pending gas composition: the
  system warns the engineer and offers either to wait or to produce the act with
  the calculated stretches flagged.
- The period is already closed and its act signed: producing a new act is
  forbidden and only a corrective act is available.

## UC-09. Producing a corrective act

**Goal.** Record refinements to a closed period without changing the original
act.

**Precondition.** The reporting period is closed — T + 10 working days have
passed — but refined data has arrived or an error has been found.

**Main scenario**

1. The engineer opens the corrective acts section.
2. The engineer selects the original act that needs correcting.
3. The engineer states the reason: a refined composition arrived, an error was
   found, data came from the counterparty, and so on.
4. The engineer starts a recalculation with the new inputs — UC-06, manual, with
   the check that the period is closed.
5. The system records a new version of the values (FR-12) and an entry in the
   correction journal (FR-13).
6. The engineer presses "produce corrective act".
7. The system generates a PDF holding: a reference to the original act, by number
   and date; the reason for the correction; the list of corrected figures showing
   the value before and after; and the corrected totals.
8. The system stores the corrective act as a separate document linked to the
   original.

**Result.** The engineer has recorded a legally sound refinement without breaking
the integrity of the closed period.

**Alternatives**

- The discrepancy is within the contractual threshold: the corrective act follows
  the simplified procedure, without separate agreement.
- The discrepancy exceeds the threshold: the system marks the act as requiring
  agreement between the parties.

## UC-10. Reconciling against the counterparty's data

**Goal.** Compare the operator's calculations with the counterparty's data and
find discrepancies before the act is signed.

**Precondition.** The engineer is signed in and the period has been calculated.

**Main scenario**

1. The engineer opens the reconciliation section.
2. The engineer selects a period and a line.
3. The engineer uploads a file with the counterparty's data, or the system
   fetches it through the API where that integration exists.
4. The system compares the operator's and the counterparty's figures for each
   measure: volume and quality.
5. The system displays the discrepancies: those beyond the contractual tolerance
   are highlighted, with the percentage difference and any known causes.
6. The engineer analyses them and, if needed, starts a recalculation (UC-06) or
   contacts the counterparty.

**Result.** The engineer has found and analysed the discrepancies and is ready for
the act to be signed.

**Alternatives**

- Nothing falls outside the tolerance: the system shows "no discrepancies found,
  act ready for signing".
- The counterparty's data has not been loaded: the engineer is told to upload it
  or to wait for the API response.
