---
id: flutter-ddd-domain-modeling
name: flutter-ddd-domain-modeling
version: 1.0.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: Models complex Flutter feature domains with opt-in Domain-Driven Design while preserving Clean Architecture.
tags: [flutter, mobile, ddd, domain-modeling, aggregates, value-objects]
---

# Flutter DDD Domain Modeling

## When To Apply

Apply this skill only when `/new-feature` persists
`domain_modeling.mode: ddd` in the approved Mobile Spec Packet. It supplements
`flutter-clean-architecture` and `flutter-freezed-domain-modeling`; it never
replaces them.

`domain_modeling.mode: standard` is the default. A standard feature keeps the
existing Clean Architecture flow and must not be blocked because DDD inputs or
artifacts are absent.

Use DDD when the feature has business invariants, meaningful state transitions,
multiple objects that must remain consistent, or an offline policy that needs a
local business model. Do not use it merely because the API has multiple DTOs or
the UI has several screens.

## Instruction

### 1. Resolve The Modeling Mode Before Code

The developer may set `domain_modeling: ddd` explicitly. When it is omitted,
persist `domain_modeling.mode: standard`.

If the inputs suggest DDD but do not select it, present the evidence and ask
the developer to choose `standard` or `ddd`; never silently upgrade the
feature. Examples of evidence are a non-trivial lifecycle, rules spanning
several local objects, or offline mutations that require reconciliation.

For `ddd`, do not generate code until the initial review approves a
`domain_modeling` section containing:

- `bounded_context`: the feature boundary and responsibility;
- `ubiquitous_language`: business terms and their definitions;
- `aggregates`: roots, internal entities and references to other aggregates by
  identifier only;
- `invariants`: rules that each aggregate root enforces;
- `server_authority`: rules validated locally for UX versus rules the backend
  authoritatively confirms;
- `offline_policy`: optional local mutation, synchronization and conflict
  behavior.

If business rules, domain boundaries, or server authority are missing, stop
with `blocked_input`. An API schema alone is not sufficient evidence for a DDD
model.

### 2. Model The Mobile Domain

Keep the domain pure Dart: no Flutter, JSON, HTTP, database, BLoC, or generated
API classes. Use the existing Freezed skill for entities and value objects.

- An aggregate root is the only public mutation boundary for its aggregate.
- A value object is immutable, validates itself on construction and compares by
  value. Examples: `Money`, `Quantity`, `OrderId`.
- Internal entities belong to their aggregate root. Reference another aggregate
  through its identifier, never through a mutable object graph.
- Put domain behavior and invariant checks on the aggregate root or a pure
  domain service. Do not hide them in a BLoC, mapper, repository implementation
  or widget.
- Repository interfaces remain domain ports and operate on domain types. DTOs
  remain in Data and UI models remain in Presentation.

### 3. Respect Mobile Authority Boundaries

The mobile client is not the authority for cross-user consistency, authorization,
pricing, stock, payment approval, or other server-owned decisions. It may
validate locally for immediate feedback, but it must send a command to the
backend and reconcile with the authoritative response.

Distinguish these events:

| Event kind | Example | Owner |
|---|---|---|
| UI intention | `ConfirmPressed` | BLoC / Presentation |
| Local domain fact | `OrderConfirmationRequested` | Domain aggregate |
| Integration message | `POST /orders/{id}/confirm` response or push update | Data / backend contract |

Do not expose local domain events as trusted backend events. Map commands and
responses in the repository or data source boundary.

### 4. Handle Offline Deliberately

When `offline_policy` permits a local mutation, document whether it is
optimistic, provisional, or read-only. Persist only the required domain state,
record synchronization failures, and reconcile using the backend response.
Conflicts that require a server decision must surface as a domain failure or a
review state; never silently overwrite the authoritative result.

### 5. Test The Model

For every declared invariant, add a pure-Dart unit test proving both the valid
and rejected paths. Also test state transitions, value-object validation and
the mapping boundary for every backend-authoritative response that can revise
local state. Widget and integration tests remain required by `/new-feature`;
they do not substitute these domain tests.

## Example

```yaml
domain_modeling:
  mode: ddd
  bounded_context: checkout
  ubiquitous_language:
    order: Draft purchase selected by a shopper.
    order_line: A product and its requested quantity within an order.
  aggregates:
    - root: Order
      entities: [OrderLine]
      references_by_id: [CustomerId]
  invariants:
    - An order can be submitted only when it has at least one line.
    - A submitted order cannot change its lines.
  server_authority:
    local: [quantity_is_positive, order_has_lines]
    backend: [inventory_reservation, final_price, payment_approval]
  offline_policy:
    mutations: provisional
    reconciliation: Refresh the order from the backend after submission.
```

## Restrictions

- Never require this skill for `domain_modeling.mode: standard`.
- Never infer business invariants, bounded contexts, or server authority from a
  DTO shape alone.
- Never make every entity an aggregate root.
- Never duplicate backend authorization or integrity decisions in the client.
- Never let Domain import Data, Presentation, Flutter, serialization, or
  transport concerns.
