# ADR-001: Separate operational and accounting data layers

## Status
Accepted

## Context
The dispatcher needs flow and composition data within one to two minutes in
order to react to a deviation from the daily nomination. Raw readings are
acceptable — experience filters the noise — but a number must be on screen now.

The accounting engineer needs volumes corrected to standard conditions
(temperature, pressure, gas composition) before they enter the accounting
records. Correction depends on a laboratory chromatography result, which
arrives with a physical delay and is not produced hourly. The publication
deadline for accounting data is defined in NFR-2.

Correcting to standard conditions is not noise filtering that could be
optimised away. It is a physical delay imposed by laboratory analysis.

## Options considered
1. **Single data layer.** All measurements are stored once. Records are updated
   as corrections arrive. Dispatcher and engineer read the same rows.
2. **Two parallel layers.** An operational layer (raw telemetry, under two
   minutes) and an accounting layer (corrected to standard conditions, delayed
   by composition availability). The layers are independent and data does not
   migrate between them.
3. **Single layer with on-demand recalculation.** Only raw telemetry is stored.
   The volume is recalculated on each engineer request from the raw reading and
   the latest available composition.

## Decision
Option 2. The system maintains two parallel layers. Both derive from the same
primary source — measurements taken at the metering node — but run through two
independent processing pipelines with different publication contracts. The
operational layer serves monitoring only; the accounting layer serves transfer
acts only. Data never moves from one layer to the other.

## Rationale
The delay is physical and cannot be removed, so the only way to keep both speed
and accuracy is to separate the flows. The dispatcher will never get a corrected
figure to steer by, and the engineer will never get a fast one to sign off on.
Each role gets what it needs, when it can exist.

Option 1 was rejected because updating records when composition arrives rewrites
history, which violates the immutability of accounting data (NFR-11). It also
means the dispatcher watches numbers that may later change, which undermines
trust in the monitoring screen.

Option 3 was rejected because recalculating on every request adds load, offers
no fixed reference point, and destroys reproducibility — the same query at two
different times can return two different results.

## Consequences
- Stored volume roughly doubles.
- The interface becomes harder to design: every figure must visibly declare
  which layer it came from.
- Mitigated by explicit colour coding on screen and by strict access rules —
  the dispatcher cannot steer on accounting data, the engineer cannot cite
  operational data in an act.