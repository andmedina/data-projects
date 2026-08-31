# DE-007 Solution

The CSV validator now supports backward-compatible optional fields for payer, billing/rendering provider, ordered diagnoses, procedure coding, claim frequency/original claim, patient responsibility, and reason-coded adjustments. Row-level rules reject malformed entities and financials; file-level validation rejects claim lines that disagree on repeated header attributes.

Raw storage remains immutable and hash-idempotent. `staging.stg_claim_line` ranks raw records by source system and line identifier, exposing only the latest payload version to canonical transformations. The load creates or updates payer/provider dimensions, claim headers and lines, and repeating diagnosis/procedure/adjustment children.

Persistent controls fail closed for missing original claims, header/detail financial differences, line/adjustment differences, and inconsistent repeated header attributes. The claims-cost mart independently derives the current adjudication state: any claim referenced by a successor is superseded, terminal replacements remain included, and terminal voids contribute no cost.

The original seven-column fixture remains valid, so the expansion does not break the initial claims demonstration. Full X12 envelope parsing and trading-partner acknowledgement workflows remain a separate hardening phase.
