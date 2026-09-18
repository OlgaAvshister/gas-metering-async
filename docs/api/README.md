# API specification

[openapi.yaml](openapi.yaml) is the contract between the backend, the web
interface and the external systems: the SCADA gateway, the laboratory
information system and the counterparty's systems.

37 paths, 43 operations, 52 schemas, validated against OpenAPI 3.0.3.

## Reading it

Drop the file into [editor.swagger.io](https://editor.swagger.io) or run

```
npx @redocly/cli preview-docs docs/api/openapi.yaml
```

## How it was derived

Nothing here is decorative. Each part traces to something upstream:

- **Schemas** come from the [data model](../data-model/README.md). Entity
  attributes become properties; enums come from the values the model names.
- **Operations** come from the [use cases](../use-cases/README.md). Each one
  names the case it serves.
- **Error responses** come from the alternative scenarios in those cases. A
  second signature by the same party is a 409 because UC-25 says the system
  rejects it; a counterparty reaching outside its delivery point is a 403
  because NFR-12 says so.
- **Constraints** come from the non-functional requirements.

## Two conventions that run through it

**Every volume states its layer.** Responses carrying measured or calculated
volumes include a `layer` field, `operational` or `accounting`. FR-05 requires
the interface to mark which layer a figure belongs to; putting it in the contract
means a client cannot lose the distinction by accident.

**Nothing is overwritten.** Accounting values are versioned rather than updated,
so there is no `PUT /accounting-values/{id}`. Corrections go through
`POST /accounting-values/recalculate`, which creates a version and an adjustment
journal entry. Similarly there is no endpoint to edit a method version or a
contract parameter: both are closed and superseded, never amended (FR-12, FR-30,
ADR-003).

## What is implemented

Only `POST /measurements` exists in this repository, in `services/api`. The rest
of the specification describes the whole system; the services here implement its
asynchronous core. The intake endpoint is idempotent on the pair (node,
measurement time), which is what makes an archive re-read safe (FR-16, NFR-6).
