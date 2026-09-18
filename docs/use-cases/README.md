# Use cases

Sequences of interaction between users and the system, grouped by role, covering
every role defined in FR-28. Each case carries a main scenario and alternative
branches, including errors, external system failures, and situations where an
action is forbidden by the state of the object.

The section exists to check the requirements for completeness with business
representatives, and as the basis for interface design and test cases.

| Role | Cases | |
|---|---|---|
| Dispatcher | UC-01 – UC-04 | [dispatcher.md](dispatcher.md) |
| Accounting engineer | UC-05 – UC-10 | [accounting-engineer.md](accounting-engineer.md) |
| Counterparty representative | UC-11 – UC-14 | [counterparty.md](counterparty.md) |
| Administrator | UC-16 – UC-19 | [administration.md](administration.md) |
| IT operations | UC-20 – UC-22 | [operations.md](operations.md) |
| Financial controller, laboratory, regulator, signing | UC-15, UC-23 – UC-25 | [other-roles.md](other-roles.md) |

Three cases are covered by the implementation in this repository, and say so
where they are described: UC-02 (recording a deviation and dispatching the
notification), UC-13 (delivering the notification) and UC-22 (archive re-read
without duplication).
