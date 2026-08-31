# HL7 v2 Mapping

The controlled Phase 4 integration supports `ADT^A01/A02/A03/A08`, `ORM^O01`, and `ORU^R01` synthetic messages.

| Segment | Canonical use |
| --- | --- |
| MSH | message control, type, source, event time |
| PID | source patient identifier and demographics |
| PV1 | encounter identifier, class, assigned/prior location |
| ORC/OBR | order identifier, control/status, service code, order time |
| OBX | clinical observation value, units, status |

Raw message text is retained exactly. The parser is intentionally limited to controlled synthetic messages; production variants require profile-specific validation and testing.

## Implemented controlled workflow

`hl7-postgres` validates message type, control ID, message timestamp, patient ID, and profile-specific fields before retaining the exact message text in `raw.hl7_message`. Syntactically valid messages whose PID does not resolve to `core.patient` are retained in raw storage and copied to quarantine with `UNRESOLVED_PATIENT_REFERENCE`.

Canonical mappings are:

- ADT events → `core.hl7_encounter_event`, with A01 admitted, A02 transferred, A03 discharged, and A08 updated;
- ORM orders → `core.hl7_order_event`, retaining order control/status and coded service context; and
- ORU results → `core.hl7_observation`, retaining OBX value, unit, and status.

`mart.hl7_encounter_current_state` derives the latest location plus admit/discharge timestamps from the immutable event timeline; A08 can refresh attributes without replacing the latest state-changing A01/A02/A03 state. `mart.hl7_order_current_state` selects the latest event for each order by message-event time. Raw payload hashes and profile-specific event keys make reruns idempotent; duplicate raw messages are still remapped so a schema migration can backfill new canonical entities from retained history.

Persistent controls fail on invalid ADT transitions, accepted messages without their expected canonical mapping, or mapped orders without service codes. Production requirements such as MLLP transport, ACK/NACK exchange, escape processing, repeating-field profiles, timezone variants, and interface-engine operations remain out of scope.
