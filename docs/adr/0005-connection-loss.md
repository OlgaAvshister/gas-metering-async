# ADR-005: Behaviour on loss of connection to a metering node

## Status
Accepted

## Context
When the connection to a remote metering node drops — for an hour or two, say —
the dispatcher needs to keep seeing some figure for flow on screen. Steering the
regime blind is not an option, and even a rough extrapolation from the last
measured value beats an empty chart.

The accounting engineer, as metrologist, requires that nothing unmeasured is
presented as fact. Extrapolation or interpolation across a gap is a fabricated
number. If the dispatcher takes it for reality and acts on it — leaving the
supply open in the belief that flow is steady — the accounting record is
distorted. Showing nothing at all is not safe either: the dispatcher will act
blind regardless.

Marking an extrapolation "unreliable" does not settle it. Under pressure a
dispatcher may still rely on the figure, because a curve reads as information in
a way that blank space does not. Showing nothing removes the instrument they need
while the outage lasts.

## Options considered
1. **Extrapolation.** The system keeps showing movement by extending the trend
   from the last measurements.
2. **Blank screen.** During an outage the dispatcher sees no data for that node.
3. **Last value as a constant.** The dispatcher's screen shows the last
   trustworthy measurement with the outage marked explicitly.
4. **Interpolation in the accounting layer.** The gap is filled with a calculated
   value carrying no special marking.

## Decision
Options 3 and 4 combined, with amendments.

On the dispatcher's screen, in the operational layer: the last trustworthy
measured value is shown as a constant — a flat line — marked explicitly with "no
data since HH:MM, showing last measurement". No interpolation or extrapolation is
applied.

In the accounting layer: the gap is not left empty. The volume is completed by
calculated substitution under the regulated procedure, either from the average
over a comparable period or from the fallback method. The period is marked
"unmeasured" and the substituting value carries a "calculated" flag naming the
substitution method.

## Rationale
Option 1 was rejected: the risk that the dispatcher takes a generated curve for
reality is too high, for the reason given above — a curve reads as information.

Option 2 was rejected: it leaves the dispatcher without an instrument for the
duration of the outage, which is unsafe.

The risk of mistaking a flat line for reality is lower, because a flat line is
easier to recognise as an artefact.

The accounting layer needs to be complete for the balance to work, but marking
the uncertainty explicitly is honest and transparent to both parties.

## Consequences
- The dispatcher sees a frozen value rather than movement, which degrades control
  quality while the outage lasts.
- The accounting record gains calculated stretches, which then need agreeing with
  the counterparty.
- Offset by redundant communication channels and a manual control mode with
  tightened supervision.
- The "calculated" flag gives the counterparty an explicit signal to challenge,
  which is more honest than hidden interpolation.
- These stretches are the first thing the counterparty challenges, and they are
  what corrective acts are usually about (see [ADR-002](0002-period-closing.md)).
