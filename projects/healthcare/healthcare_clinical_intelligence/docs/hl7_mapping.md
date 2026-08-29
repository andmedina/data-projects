# HL7 v2 Mapping

HL7 v2 is a Phase 4 integration. Initial supported messages are ADT, ORU, and ORM.

| Segment | Canonical use |
| --- | --- |
| MSH | message control, type, source, event time |
| PID | source patient identifier and demographics |
| PV1 | encounter context |
| ORC/OBR | order context |
| OBX | clinical observation value, units, status |

Raw message text is retained exactly. The parser is intentionally limited to controlled synthetic messages; production variants require profile-specific validation and testing.
