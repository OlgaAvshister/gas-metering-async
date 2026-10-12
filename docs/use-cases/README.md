# Use cases

Sequences of interaction between users and the system, grouped by role, covering
every role defined in FR-28. Each case carries a main success scenario and
extensions: errors, external system failures, and situations where an action is
forbidden by the state of the object.

Extensions follow Cockburn's notation. Each one is tied to the step where the
scenario branches off and says where it goes next:

- **3a** is the first extension at step 3, **3b** the second;
- **\*a** can happen at any step;
- **3a, 5a** applies at either step;
- each extension ends with "continues at step N", "returns to step N" or "the use
  case ends".

Most cases are at user-goal level: one person, one sitting, one result. Closing a
reporting month is a summary-level goal that spans UC-08, UC-10, UC-25 and, when
needed, UC-09.

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
