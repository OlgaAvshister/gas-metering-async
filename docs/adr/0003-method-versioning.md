# ADR-003: Versioning the method reference data

## Status
Accepted

## Context
The accounting engineer requires one current version of the calculation method to
be in force — density coefficients, calorific values, standard conditions per the
applicable standard. That keeps maintenance and reporting simple and avoids
confusion between several parallel reference sets.

The counterparty requires that if one method was in force when an act was signed,
every future recalculation of that act uses exactly that version, even after the
method has officially changed — for instance when the regulator issues a new
edition of the standard. Without that the counterparty cannot verify its own
archives.

Holding several method versions at once, each tied to the periods it applies to,
means a more complex architecture, more computing resources and strict versioning
discipline. That is expensive and not straightforward. Without it, the engineer
recalculates an old act under the new method, gets different figures, and the
counterparty raises a claim.

## Options considered
1. **A single current method.** Only the current version is stored and every
   calculation uses it.
2. **Versioned reference data.** Each calculation records the identifier of the
   reference version it used. Recalculating a historical period uses the version
   that was active at the time of the calculation.
3. **Full bitemporal storage.** Not only the reference data but the calculation
   algorithms themselves are versioned, so any historical calculation is
   reproducible with every rule that applied at the time.

## Decision
Option 2. The MVP holds a versioned method reference set with full chronological
binding. Each calculation records the identifier of the method version it used.
Versioning of the calculation algorithms themselves is deferred to v2; in the
first version the algorithms are fixed, and recalculating a historical period
uses the reference version that was active at the time.

## Rationale
The counterparty requires reproducibility — it is a condition of the joint
venture. Without it the partner will not sign acts and will not accept the
system.

Option 1 was rejected: it does not make historical calculations reproducible.

Option 3 was rejected: full bitemporal storage including algorithms is
disproportionate complexity for an MVP. Versioning the reference data solves most
of the problem and leaves room to grow.

## Consequences
- Two to three weeks added to core development.
- Every calculation operation is permanently more complex: each read has to state
  the reference version explicitly.
- Versioning of calculation algorithms (v2) remains a separate project.
