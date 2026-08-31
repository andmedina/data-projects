# DE-008 — Persist HL7 Lifecycle and Order Events

## Business context

The initial HL7 path retained valid message text and mapped ORU observations, but ADT and ORM messages stopped at validation. Operations users could not reconstruct encounter movement, inspect current encounter state, or relate orders to a patient and visit.

## Requirements

- Validate controlled ADT A01/A02/A03/A08, ORM O01, and ORU R01 profiles.
- Preserve exact raw message text and deterministic message identifiers.
- Normalize ADT encounter events and ORM order events for known core patients.
- Derive current encounter and order state without deleting event history.
- Backfill canonical mappings when a retained raw duplicate is reprocessed.
- Quarantine unresolved patient references and reject incomplete profile fields.
- Fail the persistent gate on invalid lifecycle transitions or unmapped accepted messages.
- Prove idempotency and independent SQL reconciliation using synthetic fixtures.

## Acceptance criteria

1. The lifecycle fixture loads three events in admit → transfer → discharge order.
2. Current state for `hl7-visit-001` is discharged at `WARD^202^1`.
3. The ORM fixture loads one coded order for `order-001` and encounter `e-001`.
4. All controlled raw ADT, ORM, and ORU messages resolve to their expected core entity.
5. Lifecycle transition, order-code, and mapping-reconciliation controls observe zero violations.
6. Identical reruns add zero raw or canonical events.
7. Automated tests, dashboard export, and `validation.sql` pass.

Status: complete for the controlled synthetic HL7 profiles.
