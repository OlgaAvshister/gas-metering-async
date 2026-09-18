# ER model: measurement and accounting

The two data layers of [ADR-001](../adr/0001-two-data-layers.md). `Measurement`
and `HourlyAggregate` form the operational layer; `AccountingValue` is the
accounting layer, and it exists only once a `GasComposition` and a
`MethodVersion` are available to correct the volume with.

```mermaid
erDiagram
    MeteringNode ||--o{ Measurement : "produces"
    HourlyAggregate ||--o{ Measurement : "aggregated per hour"
    HourlyAggregate ||--o{ AccountingValue : "calculation versions"
    GasComposition ||--o{ AccountingValue : "corrected with"
    MethodVersion ||--o{ AccountingValue : "calculated under"

    Measurement {
        uuid id PK
        uuid node_id FK
        timestamp timestamp
        decimal volume_raw
        decimal pressure
        decimal temperature
        boolean is_valid
        boolean is_suspicious
        timestamp received_at
        uuid packet_id
    }

    HourlyAggregate {
        uuid id PK
        uuid node_id FK
        timestamp hour_start
        decimal avg_volume
        decimal avg_pressure
        decimal avg_temperature
        int measurement_count
        boolean is_complete
    }

    GasComposition {
        uuid id PK
        uuid node_id FK
        timestamp sampling_time
        timestamp received_at
        varchar lab_identifier
        jsonb composition_json
        boolean is_active
    }

    MethodVersion {
        uuid id PK
        varchar method_name
        varchar version_number
        timestamp active_from
        timestamp active_to
        jsonb coefficients_json
    }

    AccountingValue {
        uuid id PK
        uuid hourly_aggregate_id FK
        uuid gas_composition_id FK
        uuid method_version_id FK
        uuid created_by_user_id FK
        decimal standardized_volume
        boolean is_calculated
        varchar calculation_method
        int version_number
        boolean is_current
        timestamp calculated_at
        text correction_reason
    }
```

## Notes

`MethodVersion.active_to` is NULL on the version currently in force. Validity
periods do not overlap: exactly one version of the reference data is active at
any moment. The constraint is enforced in the implementation and is not
expressible in the schema.

`GasComposition.is_active` means the chromatogram is fit to be used in
calculations. When a refined analysis arrives for the same sampling period, the
previous record is set to `is_active = false` but stays in the database. This is
not the same as the versioning on `AccountingValue`: there it is the result of a
calculation that is versioned, here it is the fitness of the laboratory inputs.

`AccountingValue` carries both `version_number` and `is_current`, which is how
FR-12 is met: a correction adds a version rather than overwriting one.
