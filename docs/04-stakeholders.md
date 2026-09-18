# Roles and their conflicts

Four roles work with the same figures and want incompatible things from them.
Setting out what each one fears, rather than what each one asks for, is what made
the conflicts visible — and every architectural decision in
[docs/adr](adr/README.md) resolves one of them.

## Dispatcher

**Problems**

- Flow and composition data arrive 15 to 30 minutes late, while the decision to
  open or close a valve has to be made now.
- The system shows raw, unverified figures that jump around with sensor noise, so
  a real deviation is hard to tell from measurement error.
- Nothing marks which kind of figure is on screen: raw telemetry, or something
  already corrected and filtered. That breeds distrust of every reading — even a
  correct one costs time to double-check.
- There is no single screen where the planned nomination and the actual
  parameters meet per line, so the picture is held in the head or in a hand-kept
  spreadsheet.

**Fear.** If the system does not make clear which figure is trustworthy, I will
either miss a real deviation by taking it for noise, or react to a false spike.
Either way: a wrong adjustment, a failed delivery, penalties.

**Success.** A deviation of actual transport from the daily nomination is noticed
and dealt with — an adjustment command issued — within the operational shift.

## Accounting engineer

**Problems**

- The operational data the dispatcher works from keeps changing after the fact,
  as laboratory results and refined compositions arrive, so the final act drifts
  until the last hour before reporting is due.
- Discrepancies against the counterparty's metering nodes on the other side of
  the pipe reach several percent, and the balance has to be recalculated by hand
  to find the unaccounted gas.
- Primary data — pressure, temperature, composition — arrives from different
  sources (operator, laboratory, counterparty) at different times in different
  formats, and is hard to bring into one protocol.

**Fear.** If the system does not make the calculations transparent and trace every
change — who corrected a figure, when, and why — I will sign an act containing an
error. That means direct financial loss for our side, or months of litigation
with the partner.

**Success.** The gas transfer act is signed by both parties without a protocol of
disagreement.

## Counterparty representative

**Problems**

- Corrections are opaque: the operator changes figures in closed periods, and the
  counterparty cannot see the history or judge whether the changes were
  justified.
- Methods differ: the operator calculates to one standard with one set of
  coefficients, the counterparty to another, and the system offers no common
  recalculation for reconciliation.
- There is no automatic notification of a recorded deviation at the moment it
  happens, so the counterparty learns of everything from the monthly act, with no
  chance to influence the situation.

**Fear.** If the system is built purely for the operator's convenience — no audit
trail, no access to primary data for the partner — the counterparty signs acts
blind. An external audit then uncovers volume losses and shows our share of the
gas was systematically understated, which means the joint venture breaks up and
the claims are large.

**Success.** Volumes and gas quality calculated by the operator's system match
the counterparty's own calculations within the contractual tolerance, and the act
is signed remotely with no further enquiries.

## System administrator and IT operations

**Problems**

- Communication channels between the head station and the partner's remote office
  fail: data tears, packets are lost, recovery is manual.
- Access control exists on trust alone — the dispatcher can change operational
  parameters and the engineer can edit calculation reference data — which risks
  accidental or deliberate corruption of accounting data.

**Fear.** If the accounting database fails during month-end close, we will not
recover the information before the deadline. Reporting to the regulator and to
the partner fails, and recovery takes weeks.

**Success.** All data flows from metering nodes and user workstations are
delivered to storage, intact and queryable, no later than five minutes after each
hour closes, with no packet loss.

## Where each conflict is resolved

| Conflict | Between | Resolved by |
|---|---|---|
| Speed against accuracy | Dispatcher and accounting engineer | [ADR-001](adr/0001-two-data-layers.md) |
| Finality against correctness | Counterparty and accounting engineer | [ADR-002](adr/0002-period-closing.md) |
| One current method against historical reproducibility | Accounting engineer and counterparty | [ADR-003](adr/0003-method-versioning.md) |
| Acting in time against notifying first | Dispatcher and counterparty | [ADR-004](adr/0004-counterparty-notification.md) |
| Showing something against showing only what was measured | Dispatcher and metrology | [ADR-005](adr/0005-connection-loss.md) |
