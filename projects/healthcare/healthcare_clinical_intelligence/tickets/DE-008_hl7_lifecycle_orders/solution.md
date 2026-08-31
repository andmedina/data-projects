# DE-008 Solution

The dependency-free parser now validates common envelope fields and profile-specific content before producing normalized encounter, order, or observation events. ADT trigger codes map to explicit lifecycle states, PV1 retains visit/class/location context, and ORM ORC/OBR fields retain order control/status and coded service context.

Valid source text remains immutable in `raw.hl7_message`. Canonical event tables use message/profile keys for idempotency. On a duplicate raw hash, the loader retrieves the retained raw identifier and still attempts canonical inserts; this supports safe backfills after adding a new mapping without duplicating source history.

Current-state views rank immutable events rather than overwriting history. A08 updates can refresh the latest attributes without replacing the most recent A01/A02/A03 lifecycle state, and order state is ranked by message-event time rather than the original requested time. Persistent controls independently detect illegal encounter transitions, missing order codes, and accepted messages with no expected canonical event. Unresolved PID identifiers are retained in raw, copied to quarantine, and reflected as a partial pipeline outcome.
