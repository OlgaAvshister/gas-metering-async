# ADR-002: Period closing and the corrective act

## Status
Accepted

## Context
The counterparty requires that once a transfer act is signed, the period is
closed for good. The figures do not change under any circumstances. That gives
them predictability and a clean legal position.

The accounting engineer requires the ability to reopen a closed period when a
refined gas composition arrives after signing — from an independent laboratory,
say — or when a systematic error is found in the primary data. Otherwise the act
carries figures known to be wrong.

A hard cut-off date loses some of those refinements and makes acts less accurate.
Allowing reopening means the act is never final, and the counterparty loses any
confidence that a signed figure will still stand a month later.

## Options considered
1. **Unlimited reopening.** A period can be corrected at any time as new data
   arrives.
2. **Hard close with no changes.** Once the act is signed the period is closed
   permanently.
3. **Close plus a corrective act.** A hard cut-off at T + 10 working days. After
   it the original act cannot be changed, and every later refinement is issued as
   a separate corrective act.

## Decision
Option 3. The cut-off is T + 10 working days after the reporting period ends.
After that date the period is closed and the original act does not change. Every
refinement arriving later is issued as a separate corrective act: a new document
linked to the original, which does not modify it.

## Rationale
Legal certainty outweighs the last fractions of a percent of accuracy, because
the cost of a dispute over revising a signed act is higher than the cost of the
error.

Option 1 was rejected: unlimited reopening destroys the counterparty's trust, as
a signed act stops being final.

Option 2 was rejected: it makes it impossible to correct objective errors, such
as a refined gas composition that arrives late.

A corrective act allows material errors to be fixed without blurring the boundary
of the closed period.

## Consequences
- Refinements arriving after T + 10 days never enter the original act; they live
  separately.
- Offset by the corrective act mechanism, which is signed through a simplified
  procedure when the discrepancy exceeds the contractual threshold.
- Moving the resolution into organisational process is acceptable, but it needs
  an explicit procedure and an SLA for agreement — otherwise a corrective act
  hangs indefinitely.
