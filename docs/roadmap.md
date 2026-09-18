# Product roadmap

What is in the MVP, what comes after, and — the part worth reading — why each
deferred item is deferred. A roadmap that only lists features hides the reasoning
that put them in that order.

## MVP, the current scope

- Intake and validation of data from metering instruments, across two
  independent layers, operational and accounting.
- Operational monitoring with configurable notifications on deviation from the
  contractual nomination.
- Calculation of accounting volumes and quality figures against versioned
  reference data — physical constants, coefficients, correction methods.
- Producing gas transfer acts and signing them by both parties.
- Reconciliation against the counterparty's figures, with discrepancies shown.
- Role-based access control between operator and counterparty, with every action
  logged.
- An immutable audit journal of every change to accounting data.

## Release v2

**Predictive analytics** — forecasting deviations and the expected nomination
corridor for daily planning. Not in the MVP because it needs several months of
actual delivery history before a model means anything. At launch there is not
enough data, the forecasts would be unreliable, and an unreliable forecast is
worse than none: it invites people to act on it.

**Full versioning of the calculation algorithms** — bitemporal storage not only
of reference values but of the calculation logic itself, the set of figures and
the order of operations. Deferred because methods are stable at this stage and
change once or twice a year. Building that complexity early would slow
development with no immediate return; once there is a track record of changes it
becomes critical for reproducing historical calculations. See
[ADR-003](adr/0003-method-versioning.md), where this was the rejected third
option.

**Anomaly detection as a sign of leaks** — automatic detection of abnormal
consumption patterns. Needs algorithms trained on a representative sample of
normal and abnormal operation, which does not exist at launch. It also needs
additional sensors, which widens the hardware side of the project beyond the
functional MVP.

**Escalation to the dispatcher on an unacknowledged signal** — alerting
operational staff when the counterparty has not acknowledged within the agreed
time. This mirrors the counterparty's backup channel, but its value only appears
once there are statistics on failures and the primary channel's reliability is
established. In the MVP the manual workaround is enough.

## Release v3

**Billing integration** — passing accounting data to the finance systems for
pricing and invoicing. Needs exchange formats agreed at contract level, which is
outside the technical team's control and depends on adjacent systems being ready.
Held as a separate stage precisely because it is organisationally, not
technically, gated.

**Mobile workplaces** for dispatchers and field staff — readings and
notifications on mobile devices. Widens the security requirements (device
control, channel protection) and needs a mobile interface designed in its own
right. Not critical to the basic accounting cycle, so it follows once the desktop
version is stable.

## What the implementation in this repository adds

The asynchronous core built here is not a roadmap item — it is the delivery
mechanism underneath the MVP scope. But building it surfaced two things that
belong on this roadmap and were not on it:

**Idempotency keys on the notification gateway.** The notification worker can
still send twice if it fails between sending and recording. Closing that needs
the receiving gateway to honour an idempotency key, which is a change to an
external contract and therefore a roadmap item rather than a fix. See
[ADR-008](adr/0008-delivery-guarantees.md).

**Observability of the delivery chain.** Correlation ids flow end to end, but
there is nowhere to collect them. Structured logs shipped to a log store, with
consumer lag and outbox age on a dashboard, is what turns NFR-7 and NFR-13 from
requirements into something anyone can actually watch.
