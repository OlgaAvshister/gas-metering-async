# Architectural decision records

Each record states the conflict of requirements it arose from, the alternatives
considered, and the price of the option chosen. Together they answer why the
system is built the way it is.

Decisions are fixed as of the MVP. A decision is changed by writing a new record
that supersedes the old one; existing records are not edited.

| # | Decision | Arising from |
|---|---|---|
| [001](0001-two-data-layers.md) | Separate operational and accounting data layers | Dispatcher needs speed, accounting engineer needs accuracy, and the delay is physical |
| [002](0002-period-closing.md) | Period closing and the corrective act | Counterparty needs finality, accounting engineer needs to fix late errors |
| [003](0003-method-versioning.md) | Versioning the method reference data | Engineer wants one current method, counterparty needs historical reproducibility |
| [004](0004-counterparty-notification.md) | Immediate adjustment with parallel notification | Reaction window is 3–5 minutes, agreement takes 15–30 |
| [005](0005-connection-loss.md) | Behaviour on loss of connection to a metering node | Dispatcher needs a figure on screen, metrology forbids inventing one |
| [006](0006-kafka-and-rabbitmq.md) | Kafka for events, RabbitMQ for commands | Event streams and commands need different guarantees |
| [007](0007-outbox-vs-cdc.md) | Transactional outbox rather than change data capture | A database write and a broker publish cannot share a transaction |
| [008](0008-delivery-guarantees.md) | At-least-once delivery with idempotent consumers | Losing a message is undetectable; duplicating one is not |

Records 001 to 005 come from the original systems analysis. Records 006 to 008
were written during implementation, which is where the questions they answer
first became unavoidable.
