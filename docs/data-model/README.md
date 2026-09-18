# Data model

The logical data model, split into six subject blocks. Entities that take part in
relationships across blocks appear on the neighbouring diagram in abbreviated
form, with a reference to the block where they are described in full.

Each entity lists its attributes, types and keys. Integrity constraints, indexes
and physical storage decisions belong to the implementation level and are not
part of the model — except where a note says otherwise.

| Block | Covers | |
|---|---|---|
| 1 | Measurement and accounting | [01-measurement-and-accounting.md](01-measurement-and-accounting.md) |
| 2 | Contracts and delivery points | [02-contracts-and-delivery-points.md](02-contracts-and-delivery-points.md) |
| 3 | Deviations and notifications | [03-deviations-and-notifications.md](03-deviations-and-notifications.md) |
| 4 | Documents | [04-documents.md](04-documents.md) |
| 5 | Access and audit | [05-access-and-audit.md](05-access-and-audit.md) |
| 6 | Infrastructure and integrations | [06-infrastructure-and-integrations.md](06-infrastructure-and-integrations.md) |

## Relationship to the implementation

Blocks 1 to 3 are implemented in this repository, in
[db/migrations](../../db/migrations). The physical schema follows the model, with
three deliberate differences, each carried as a comment on the column concerned:

- `measurement.quality` is an enum rather than the model's two booleans
  `is_valid` and `is_suspicious`. FR-08 describes a single state — a packet that
  fails validation is marked suspect — so two booleans allow a combination with
  no meaning.
- `contract_parameter` carries a second threshold,
  `accumulated_deviation_threshold`. The model has one, but the dispatcher alarm
  and the counterparty notification compare different quantities and cannot
  share it.
- A partial unique index enforces one contract parameter in force per delivery
  point. The model notes this kind of constraint as unenforceable in the schema;
  for a single open interval it is enforceable.

The physical schema also holds two tables absent from this model: `outbox` and
`processed_message`. They are implementation artefacts of the delivery
guarantees, not part of the domain, and the model is right to omit them. See
[ADR-007](../adr/0007-outbox-vs-cdc.md) and
[ADR-008](../adr/0008-delivery-guarantees.md).
