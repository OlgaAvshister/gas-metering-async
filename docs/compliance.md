# Compliance: legal and contractual constraints

What the system is obliged to observe, and how it observes it. Three areas
matter: access control between the parties of the joint venture, the
cross-border data regime, and auditability of every accounting operation.

## 1. Access control between the parties

The operator and the counterparty are separate legal entities with opposing
commercial interests in the same delivery. The system must guarantee that the
counterparty can reach only the data of its own delivery point, and can neither
view, change nor delete the operator's primary records for other deliveries.
Every action a counterparty takes — signing in, viewing, querying, exporting —
is logged with the time and the user.

This does not follow from convenience. It protects the operator's commercial
confidentiality, since data about other counterparties and volumes is not
disclosable, and at the same time it gives the counterparty transparency: seeing
only its own data removes any suspicion of manipulation. The role model and the
isolation of access therefore satisfy the confidentiality terms of the contract
and the basic principles of fair competition at once. For the counterparty it is
also the guarantee that the operator cannot write someone else's volumes onto its
metering point.

Realised by NFR-12, FR-28 and FR-29, and by `NodeAccessRight` in the
[data model](data-model/05-access-and-audit.md).

## 2. Cross-border storage and transfer

The system serves a joint venture between two countries and processes personal
data of its users — names and contact details for notifications. That data falls
under the personal data legislation of both the Russian Federation and the
Republic of Kazakhstan, and both jurisdictions impose localisation requirements:
databases holding personal data of their citizens must be stored on their
territory.

Where the servers physically sit is a deployment question — cloud provider, data
centre region, replication settings — and not a functional requirement. At the
analysis and MVP stage the system is designed so that the data *can* be split
logically, personal data first, by which party of the joint venture it belongs
to.

Accounting data — hourly volumes, gas quality figures — is not personal data and
does not fall under localisation, so there is no need to mark jurisdiction at
record level for it; organisational separation through the role model is
sufficient. This keeps the storage policies applicable to exactly the data the
law names, once an infrastructure model is chosen, without loading the accounting
path with constraints it does not need.

## 3. Auditability and retention

The system must keep an immutable chronological journal of every change to
accounting data — delivery figures, acts, corrections — recording who acted, when,
and on what grounds, whether a document number or a comment. This journal is the
instrument for settling disputes between the parties and the basis for external
audit by the regulators of either country.

All primary accounting documents, change journals and calculation records are
retained for **5 years**. That period is the stricter of the accounting and tax
retention requirements of the two jurisdictions, so applying it to everything
satisfies both at once.

The system must be able to reproduce any calculation of accounting volume and gas
quality, for any date within the retention period, from the stored accounting
layer inputs — the corrected values, the gas composition — and the method version
applied. This is driven by the possibility of inspection by either side's
regulator: an auditor must be able to recompute the totals from the source data
rather than take the final figures in an act on trust. The mechanism is the
retention of every version and the binding of accounting records to immutable
primary data.

Pricing and final financial amounts stay outside the MVP and are computed in the
adjacent finance systems.

Realised by NFR-4, NFR-11, FR-12, FR-13, FR-26 and FR-27, and by
[ADR-003](adr/0003-method-versioning.md).
