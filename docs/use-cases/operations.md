# Use cases: IT operations

## UC-20. Monitoring the state of the communication channels

**Goal.** Keep watch over the channels to the metering nodes and over the
integration gateways, to catch problems in time.

**Precondition.** The IT operations specialist is signed in.

**Main scenario**

1. The specialist opens the monitoring dashboard.
2. The system shows: the channels to the metering nodes (N nodes in total, K
   connected, M lost); the integration gateways (SCADA, laboratory, the
   counterparty's API); data delivery delays, current, average and maximum;
   whether packets have been lost; and the state of the data stores, free space
   and integrity.
3. The specialist watches the dashboard and drills into a specific channel when
   needed.

**Result.** The specialist has a current picture of the infrastructure.

**Alternatives**

- A channel is lost: the system highlights the status in red and the specialist
  moves to recovery (UC-22).
- A delay crosses the permitted threshold: the system shows a warning.

## UC-21. Receiving an alert about data loss

**Goal.** Learn promptly of data loss or a storage integrity failure, and start
putting it right.

**Precondition.** Monitoring is active.

**Main scenario**

1. The system records an event: packet loss, delay beyond the permitted figure,
   or a storage integrity failure.
2. The system raises an alert for IT operations carrying the type of event, the
   time, the node or channel affected, and the probable cause.
3. The specialist receives it by e-mail, SMS or on the dashboard.
4. The specialist goes into the system to analyse and resolve the problem.

**Result.** IT operations is informed in time and can begin recovery.

**Alternatives**

- The problem resolves itself, a fallback channel comes back for instance: the
  system withdraws the alert and records the recovery.
- The alert is not acknowledged within the set time: the system escalates it to a
  senior specialist.

## UC-22. Recovering data after a connection outage

**Role.** IT operations; the system runs this automatically.

**Goal.** Recover data from a metering node once the connection returns, with
neither loss nor duplication.

**Precondition.** The connection to the metering node was lost and has since been
restored.

**Main scenario**

1. The system records that the connection to the node has returned.
2. The system starts re-reading the controller's local archive for the period of
   the outage automatically.
3. The system checks the data received against what is already stored, excluding
   duplicates and overlaps.
4. The system loads the missing data into the operational layer.
5. The system updates the node's status on the monitoring dashboard (UC-20).
6. If calculations had already been applied to that period, the system marks them
   as needing recalculation.
7. The specialist can see the status of the operation and when it finished.

**Result.** The data is recovered with neither loss nor duplication, and the
system is ready to recalculate the accounting volumes.

*Implemented: steps 3 and 4 — duplicate control on intake, enforced by a unique
constraint on node and measurement time rather than by application logic. See
[FR-16](../requirements/functional.md), NFR-6.*

**Alternatives**

- The archive is not deep enough to cover the whole outage: the system loads what
  is available and marks the remainder "unmeasured".
- The controller returns corrupted data: the system rejects it and notifies IT
  operations.
