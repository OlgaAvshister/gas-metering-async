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

**Extensions**

- **2a.** A delivery delay crosses the permitted threshold:
  1. The system shows a warning on the affected channel.
  2. The scenario continues at step 3.
- **2b.** A channel to a metering node is lost:
  1. The system highlights its status in red and raises an alert (UC-21).
  2. Recovery starts once the connection returns (UC-22).

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

**Extensions**

- **3a.** The alert is not acknowledged within the set time:
  1. The system escalates it to a senior specialist.
  2. The scenario continues at step 4.
- **4a.** The problem resolves itself, a fallback channel comes back for instance:
  1. The system withdraws the alert and records the recovery.
  2. The use case ends.

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

**Extensions**

- **2a.** The controller returns corrupted data:
  1. The system rejects it and notifies IT operations.
  2. The use case ends.
- **4a.** The archive is not deep enough to cover the whole outage:
  1. The system loads what is available and marks the remainder "unmeasured",
     without interpolation.
  2. The scenario continues at step 5.
