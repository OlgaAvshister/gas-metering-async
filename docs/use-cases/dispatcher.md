# Use cases: Dispatcher

## UC-01. Monitoring nomination execution per line

**Goal.** Judge how the daily nomination is being met on each line and decide
whether the transport regime needs adjusting.

**Precondition.** The dispatcher is signed in and on the main monitoring screen.

**Main scenario**

1. The dispatcher selects a pipeline line from the list.
2. The system shows a chart for the current gas day with two series: the planned
   daily nomination, as a horizontal line at the approved volume, and the actual
   raw flow from the operational layer, updating every one to two minutes.
3. The system shows the figures: current flow, volume accumulated since the start
   of the day, and the deviation in absolute and relative terms.
4. The dispatcher judges whether actual flow sits inside the contractual corridor,
   which is drawn as a band of permitted values.
5. The dispatcher switches to another line if needed.
6. The dispatcher finishes monitoring and moves on to decisions.

**Result.** The dispatcher has a current picture of nomination execution across
all lines and can decide whether to adjust the regime.

**Extensions**

- **2a.** No data has arrived for the line:
  1. The system shows the last trustworthy value marked "no data since HH:MM,
     showing last measurement" (FR-14).
  2. The scenario continues at step 3.
- **2b.** The dispatcher picks another period, the previous day or a week:
  1. The system redraws the chart for that period.
  2. The scenario continues at step 3.
- **\*a.** At any step, actual flow leaves the contractual corridor:
  1. The system highlights that stretch of the chart in red and raises an alarm.
  2. The dispatcher moves to UC-02.

## UC-02. Receiving a deviation alarm

**Goal.** Learn in time that actual flow has left the contractual corridor, and
decide on an adjustment.

**Precondition.** The dispatcher is on the monitoring screen and the system is
receiving current telemetry.

**Main scenario**

1. The system records that actual raw flow has left the contractual corridor.
2. The system raises a visual alarm: the deviation stretch is highlighted in red
   and a pop-up or flashing indicator appears.
3. The system shows the deviation details: line, time recorded, size in absolute
   and relative terms, and how long the excess has lasted.
4. The system sends a notification to the counterparty automatically, in parallel
   with the dispatcher's alarm.
5. The dispatcher judges the severity and decides: open or close a valve, contact
   the counterparty, or do nothing.
6. The dispatcher acknowledges the alarm, which clears or moves to "handled".

**Result.** The dispatcher is informed, the counterparty is notified, and the
adjustment decision is made.

*Implemented: steps 1 and 4 — recording the deviation and dispatching the
notification. See [FR-07](../requirements/functional.md), FR-22.*

**Extensions**

- **4a.** The notification channel fails:
  1. The system records the non-delivery in the journal.
  2. The system retries through the fallback channel, SMS or e-mail (see UC-13).
  3. The scenario continues at step 5.
- **5a.** Flow returns inside the corridor before the dispatcher has decided:
  1. The system withdraws the alarm automatically and logs the event.
  2. The use case ends.
- **5b.** The dispatcher cannot make the adjustment because a valve has failed:
  1. The dispatcher records the incident with a comment.
  2. The system notifies IT operations.
  3. The scenario continues at step 6.

## UC-03. Acting during a loss of connection to a metering node

**Goal.** Keep steering the transport regime while no fresh data arrives from a
metering node.

**Precondition.** The dispatcher is on the monitoring screen and the system was
receiving data from the node until the connection dropped.

**Main scenario**

1. The system records the loss of connection: no new data within the configured
   interval.
2. The system moves the node's indicator to "connection lost".
3. The system keeps showing the last trustworthy measured value on the chart as a
   constant — a flat line — marked "no data since HH:MM, showing last
   measurement".
4. The system shows how long the connection has been down.
5. The dispatcher judges the situation: for a short outage, up to 15 minutes,
   keep watching; for a longer one, move to manual control with tightened
   supervision or contact the operator at the node.
6. When the connection returns, the system switches back to live data
   automatically and the marking disappears.

**Result.** The dispatcher keeps at least an approximate picture and can act on
incomplete information.

**Extensions**

- **2a.** Several nodes lose connection at once:
  1. The system shows the status and outage duration of each node separately.
  2. The dispatcher judges the scale of the problem.
  3. The scenario continues at step 5.
- **5a.** The connection has not returned for over two hours:
  1. The dispatcher starts the manual control procedure.
  2. The dispatcher records the incident.
  3. The scenario continues at step 6 when the connection returns.

## UC-04. Reviewing operational history for a shift

**Goal.** Analyse flow over the shift just ended, to judge the quality of control
or to prepare a report.

**Precondition.** The dispatcher is signed in.

**Main scenario**

1. The dispatcher opens the history view.
2. The dispatcher selects a line, a date and a time range — their own shift,
   00:00 to 12:00, for instance.
3. The system shows the flow chart from the operational layer for that period.
4. The system shows the aggregates: minimum, maximum and average flow, and total
   volume for the period.
5. The dispatcher can zoom into individual stretches of the chart.

**Result.** The dispatcher has the analysis for the shift just ended.

**Extensions**

- **2a.** The dispatcher wants to compare several lines:
  1. The dispatcher selects additional lines.
  2. The system overlays their charts.
  3. The scenario continues at step 4.
- **3a.** Data for part of the period is missing because of outages:
  1. The system marks those stretches "no data".
  2. The scenario continues at step 4.
