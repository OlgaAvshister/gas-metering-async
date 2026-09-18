# Documentation

The full analysis package for the gas metering and reconciliation system, and the
record of what implementing part of it revealed.

Read in this order the first time:

| | |
|---|---|
| [01-context.md](01-context.md) | What the business is, how the work is done today, and the one fact about the domain that shapes everything else |
| [02-scope.md](02-scope.md) | MVP boundaries, assumptions, and what this repository actually implements |
| [03-glossary.md](03-glossary.md) | Terms, including the ones the implementation introduced |
| [04-stakeholders.md](04-stakeholders.md) | Four roles, their fears, and the five conflicts between them |
| [adr](adr/README.md) | Eight architectural decisions, five from the analysis and three from the implementation |

Then the specification proper:

| | |
|---|---|
| [requirements/functional.md](requirements/functional.md) | 32 functional requirements |
| [requirements/non-functional.md](requirements/non-functional.md) | 14 non-functional requirements, each with a two-sided justification |
| [use-cases](use-cases/README.md) | 25 use cases by role |
| [data-model](data-model/README.md) | Six subject blocks of the ER model |
| [api](api/README.md) | OpenAPI 3.0 specification, 39 paths |
| [diagrams](diagrams/README.md) | BPMN processes, sequence and use case diagrams |
| [mappings.md](mappings.md) | Field-level transformation rules |

And the material that ties it together:

| | |
|---|---|
| [traceability.md](traceability.md) | Every business goal down to its artefacts, its measure, and where the code covers it |
| [compliance.md](compliance.md) | Access control between the parties, cross-border data, retention |
| [roadmap.md](roadmap.md) | What was deferred, and why |

## How this package came about

The specification was written first and in full, as an exercise in taking a
domain from context to contract without a team and without a customer to ask.

The asynchronous core was then implemented against it — not to finish the system,
but to find out what the specification got wrong. Prose survives review; code does
not. Four defects surfaced that had passed a read-through, three architectural
decisions turned out to be missing, and several requirements gained a measure
they had not had.

The findings are recorded where they belong rather than in a list of their own:
in the ADRs that resolve them, in the notes on the data model, and in the
implementation column of the traceability matrix. The project README summarises
the four that matter most.
