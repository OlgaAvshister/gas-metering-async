# Use cases: Counterparty representative

## UC-11. Reviewing accounting data for one's own delivery point

**Goal.** Check the operator's calculations of gas volume and quality at the
delivery point, and be satisfied they are correct.

**Precondition.** The counterparty representative is signed in.

**Main scenario**

1. The counterparty opens the accounting data screen.
2. The system shows the delivery points assigned to this counterparty by contract
   (per NFR-12).
3. The counterparty selects a point and a period.
4. The system shows, from the accounting layer: the total gas volume at standard
   conditions; the gas composition; the method versions applied; the date of
   calculation; and the "calculated" flag on any substituted periods.
5. The counterparty can open the calculation detail, following the link to the
   source data.
6. The counterparty can open the act that was produced (UC-08).

**Result.** The counterparty has everything needed to check the calculations.

**Alternatives**

- The counterparty asks for a period that is not fully calculated: the system
  shows what is available and marks the rest "calculation not complete".
- The counterparty exports the data: the system produces a file in the agreed
  format, Excel or CSV.

## UC-12. Uploading one's own calculations for reconciliation

**Goal.** Compare the counterparty's own calculations against the operator's, to
find discrepancies before the act is signed.

**Precondition.** The counterparty representative is signed in.

**Main scenario**

1. The counterparty opens the reconciliation section.
2. The counterparty selects a delivery point and a period.
3. The counterparty uploads a file with their own calculations, in Excel or CSV,
   or the system fetches it through the API where that integration exists.
4. The counterparty presses "run comparison".
5. The system compares the operator's accounting-layer figures against the
   uploaded ones, for volume and quality.
6. The system displays the discrepancies: those beyond the contractual tolerance
   are highlighted, with the percentage difference and any known causes.
7. The counterparty analyses them and, if needed, raises a query with the
   operator or flags discrepancies for discussion.
8. The counterparty can produce a discrepancy report.

**Result.** The counterparty can see whether their calculations agree with the
operator's, and can decide whether to sign the act or ask for a correction.

**Alternatives**

- Nothing falls outside the tolerance: the system shows "no discrepancies found".
- The uploaded file is in the wrong format: the system rejects it and states
  which formats are accepted.

## UC-13. Receiving a deviation notification

**Goal.** Learn promptly of a material deviation of actual transport from the
nomination, in order to adjust the intake schedule.

**Precondition.** The counterparty is registered in the system with notification
channels recorded — SMS, e-mail.

**Main scenario**

1. The system records a deviation of actual flow from the nomination beyond the
   contractual threshold (within UC-02).
2. The system composes the notification, carrying: the date and time of the
   event; the line or delivery point; the size of the deviation in absolute and
   relative terms; the intended action, where known; and a link to the detail
   screen in the system.
3. The system sends the notification through the recorded channels — SMS, e-mail,
   API — within three minutes of the deviation being recorded.
4. The counterparty receives it and can sign in to see the detail (UC-11).

**Result.** The counterparty is informed promptly and can adjust their plans.

*Implemented: composing and dispatching the notification with the delivery
guarantees around it. Sending itself is simulated — no real gateway. See
[NFR-5](../requirements/non-functional.md), NFR-13.*

**Alternatives**

- One channel is unavailable, an SMS fails to send: the system sends through the
  fallback channel.
- The deviation clears before the notification goes out: the system sends a
  notification of "deviation recorded and cleared".

## UC-14. Reviewing the correction history

**Goal.** Check what changes were made to the accounting data for the
counterparty's delivery point, and be satisfied they were justified.

**Precondition.** The counterparty representative is signed in.

**Main scenario**

1. The counterparty opens the correction journal.
2. The system offers filters covering only the data they are entitled to see —
   their own delivery point.
3. The counterparty sets the filters: period, type of change, user.
4. The system shows the entries with the date and time of the change, the type of
   action (calculation, correction, calculated substitution), the grounds as a
   comment, and the previous and new values.
5. The counterparty reviews the history and opens the detail of any change.

**Result.** The counterparty has transparent information about every change and
can verify the calculations.

**Alternatives**

- Nothing matches the filters: the system shows "no records found".
- The counterparty exports the journal: the system produces a file.
