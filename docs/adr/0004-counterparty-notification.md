# ADR-004: Immediate adjustment with parallel notification

## Status
Accepted

## Context
When offtake runs above or below the daily nomination, the dispatcher needs to
change the flow regime immediately — closing or opening a valve — to keep the
breach small and avoid penalties. The action has to happen within two to five
minutes.

The counterparty requires notification of any material deviation before the
dispatcher makes the adjustment, or at the same time, so that they can adjust
their own intake schedule and not fail their end consumers.

A round of agreement with the counterparty — a phone call, correspondence,
confirmation — takes at least 15 to 30 minutes. If the dispatcher waits for
confirmation, the moment passes and the nomination is breached materially. If the
dispatcher acts with no notification at all, the counterparty sees a sudden jump
in flow on their side and breaches their own limits.

## Options considered
1. **Agreement before adjustment.** The dispatcher notifies the counterparty and
   waits for confirmation before changing the regime.
2. **Adjustment without notification.** The dispatcher acts immediately and the
   counterparty finds out afterwards.
3. **Act and notify in parallel.** The system sends the notification
   automatically at the moment the deviation is recorded, at the same time as it
   raises the dispatcher's alarm. The dispatcher does not wait for confirmation.

## Decision
Option 3. The system sends the notification to the counterparty automatically at
the moment the deviation is recorded, together with raising the dispatcher's
alarm. The notification carries the cause, the size of the deviation and the
intended action. The dispatcher does not wait for confirmation; the adjustment is
made immediately through the existing control systems.

## Rationale
The time to reach agreement is three to five times the permitted reaction window.
Waiting guarantees a breach of the nomination. Acting without notification leaves
the counterparty in the dark, which is worse for the relationship than informing
them alongside the action.

Option 1 was rejected: it makes the adjustment impossible in the time available.

Option 2 was rejected: the counterparty gets a sudden jump in flow with no chance
to prepare.

Automatic notification lets the counterparty prepare, even when they can no
longer influence the event itself.

## Consequences
- The counterparty is informed after the fact, with a delay of one to two
  minutes, rather than in advance.
- This does not solve the problem of influencing the event, but it solves the
  problem of surprise.
- Predictive modelling — daily planning of expected deviation corridors — is out
  of MVP scope and moves to the v2 roadmap, where it would let the counterparty
  see expected ranges ahead of time.
