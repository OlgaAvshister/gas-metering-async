# ER model: contracts and delivery points

The contract reference data. Nominations and deviation thresholds live here, in
`ContractParameter`, which is what FR-07 means by "the threshold value held in
the contract reference data".

```mermaid
erDiagram
    Contract ||--o{ DeliveryPoint : "covers"
    DeliveryPoint ||--o{ ContractParameter : "parameterised by"
    DeliveryPoint ||--o{ NodeDeliveryLink : "linked through"
    MeteringNode ||--o{ NodeDeliveryLink : "linked through"

    Contract {
        uuid id PK
        varchar counterparty_name
        varchar contract_number
        date start_date
        date end_date
    }

    DeliveryPoint {
        uuid id PK
        uuid contract_id FK
        varchar name
        varchar code
    }

    MeteringNode {
        uuid id PK
        varchar name
        varchar code
        text description
    }

    NodeDeliveryLink {
        uuid id PK
        uuid node_id FK
        uuid delivery_point_id FK
    }

    ContractParameter {
        uuid id PK
        uuid delivery_point_id FK
        timestamp valid_from
        timestamp valid_to
        decimal daily_nomination
        decimal deviation_threshold
    }
```

## Notes

`NodeDeliveryLink` resolves a many-to-many relationship: one metering node can
serve several delivery points and one delivery point can be fed by several nodes.
This is why `Deviation` holds both `node_id` and `delivery_point_id` explicitly
rather than deriving one from the other.

`ContractParameter` is valid over an interval (`valid_from`, `valid_to`) rather
than being tied to a single gas day. A change of nomination closes the current
row and opens a new one, so the parameter in force at any past moment stays
recoverable — the same approach as `MethodVersion`.

Per the MVP assumptions, these rows are loaded as reference data and are not
editable through the interface (FR-30).
