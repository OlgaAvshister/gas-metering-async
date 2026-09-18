# Field mappings

How a value gets from a raw reading to a figure in an act. Each mapping states,
per target field, where it comes from and by what rule — which is what makes a
calculation checkable by someone who did not write it.

## Mapping 1 — Measurement to HourlyAggregate

| Target field | Source | Rule |
|---|---|---|
| `id` | System | Generated UUID |
| `node_id` | `Measurement.node_id` | Copied |
| `hour_start` | `Measurement.timestamp` | `date_trunc('hour', timestamp)` |
| `avg_volume` | `Measurement.volume` | `avg(volume)` where valid |
| `avg_pressure` | `Measurement.pressure` | `avg(pressure)` where valid |
| `avg_temperature` | `Measurement.temperature` | `avg(temperature)` where valid |
| `measurement_count` | `Measurement.id` | `count(id)` where valid |
| `is_complete` | `Measurement.timestamp` | `measurement_count >= 60` |

Suspect readings are excluded from every aggregate, which is what FR-08 means by
a packet that fails validation being kept out of accounting calculations.

*Implemented in `services/consumer/aggregator.py`.* The hour is recomputed from
the measurements rather than accumulated, so a late archive re-read corrects an
hour that was already published. During implementation this aggregate was first
computed as a sum divided by a fixed 60, which under-reports an hour with gaps;
the mapping says `avg`, and the code now follows it.

## Mapping 2 — HourlyAggregate, GasComposition and MethodVersion to AccountingValue

| Target field | Source | Rule |
|---|---|---|
| `id` | System | Generated UUID |
| `hourly_aggregate_id` | `HourlyAggregate.id` | Copied |
| `gas_composition_id` | `GasComposition.id` | Latest analysis at or before the hour — see mapping 3 |
| `method_version_id` | `MethodVersion.id` | Version in force at the hour — see mapping 4 |
| `standardized_volume` | `HourlyAggregate.avg_volume`, `avg_pressure`, `avg_temperature`; `GasComposition.composition_json`; `MethodVersion.coefficients_json` | Correction to standard conditions per the applicable standard, using the composition and the coefficients of the version applied |
| `is_calculated` | `HourlyAggregate.is_complete` | True when the hour was incomplete and calculated substitution was applied; false otherwise |
| `calculation_method` | Logic | The substitution method from [ADR-005](adr/0005-connection-loss.md) when `is_calculated` is true; null otherwise |
| `version_number` | System | 1 on first calculation, previous + 1 on a correction |
| `is_current` | System | True on the latest version, false on all earlier ones |
| `calculated_at` | System | `current_timestamp` |
| `created_by_user_id` | Context | `SYSTEM` for an automatic calculation; the user id for a manual recalculation |
| `correction_reason` | User input | Text on a correction; null on the first version |

The two reference lookups are what make FR-11 work: the result carries the
identifier of the method version used, so the same calculation can be repeated
years later and give the same answer.

## Mapping 3 — choosing the gas composition

| Criterion | Rule |
|---|---|
| Currency | `sampling_time <= hour_start` |
| Ordering | `order by sampling_time desc limit 1` |
| Binding | `node_id` = the node being calculated |
| Error handling | No chromatogram: the calculation does not run |

The composition applied is the latest one taken *before* the hour, never a later
one. A later analysis describes gas that had not yet flowed.

## Mapping 4 — choosing the method version

| Criterion | Rule |
|---|---|
| In force during the measurement period | `active_from <= hour_start and (active_to is null or active_to >= hour_start)` |
| Ordering | `order by version_number desc limit 1` |
| Error handling | No version: the calculation does not run |

Both mappings fail closed. Where an input is missing the calculation does not run
at all, rather than running with a substitute — which is the whole of
[ADR-003](adr/0003-method-versioning.md) in one rule.

## Mapping 5 — correcting an AccountingValue

A correction creates a new version. Nothing is overwritten (FR-12, NFR-11).

| Target field | Source | Rule |
|---|---|---|
| `id` | System | Generated UUID |
| `hourly_aggregate_id` | Previous version | Copied |
| `gas_composition_id` | Previous version | Copied, or the new one where the composition was refined |
| `method_version_id` | `MethodVersion.id` | Chosen by `hour_start`; unchanged by the recalculation |
| `standardized_volume` | Recalculation | Recomputed with the new inputs |
| `is_calculated` | Previous version | Copied |
| `calculation_method` | Previous version | Copied |
| `version_number` | Previous version | Previous + 1 |
| `is_current` | System | True |
| `calculated_at` | System | `current_timestamp` |
| `created_by_user_id` | Context | The user who initiated the correction |
| `correction_reason` | User input | The reason for the correction |

One line here carries the weight of an architectural decision:
`method_version_id` is chosen by `hour_start` and does not change on
recalculation. Recalculating an old period uses the method that was in force
then, not the one in force now. Without that rule the counterparty could not
verify its own archives, and it is the reason the reference data is versioned at
all.
