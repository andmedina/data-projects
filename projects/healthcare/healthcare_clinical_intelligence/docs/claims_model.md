# Claims Model

The controlled claims integration uses a line-grain CSV contract while preserving separate canonical grains:

| Entity | Grain | Purpose |
| --- | --- | --- |
| `core.claim` | one submitted or adjusted claim header | member, payer, billing provider, frequency/original-claim lineage, and financial totals |
| `core.claim_line` | one service line | service date, rendering provider, and financial detail |
| `core.claim_diagnosis` | one ordered diagnosis per claim | diagnosis coding and sequence |
| `core.claim_line_procedure` | one procedure code per line | billed-service coding |
| `core.claim_line_adjustment` | one reason-coded adjustment per line | adjustment group, reason, and amount |
| `core.provider` | one provider identity | shared FHIR/claims provider identity plus optional NPI |
| `core.payer` | one payer identity | payer name and originating source |

## Controlled CSV contract

The original seven fields remain supported: `claim_id`, `claim_line_id`, `patient_id`, `service_date`, `billed_amount`, `allowed_amount`, and `paid_amount`. Expanded records can add:

- payer, billing-provider, and rendering-provider identity;
- ordered `SYSTEM:CODE` diagnoses separated with `|`;
- a procedure code system and code;
- patient-responsibility amount;
- adjustment group, reason, and amount; and
- claim frequency `1` (original), `7` (replacement), or `8` (void), with an original claim reference for replacement/void records.

Validation rejects incomplete entity/code pairs, malformed ten-digit NPIs, duplicate or malformed diagnosis tokens, negative/non-finite amounts, invalid financial hierarchies, incomplete adjustments, and invalid replacement/void lineage. Valid lines are written unchanged to `raw.claim_line`; rejected lines retain the payload and reason codes in `quarantine.claim_line`.

The staging view selects the latest raw payload for each source-system/line identifier. This preserves every received version in raw storage without allowing historical versions to multiply canonical financial totals. Canonical loads rebuild repeating diagnosis, procedure, and adjustment children for the affected claims and remain idempotent.

## Financial and reconciliation rules

- `paid_amount <= allowed_amount <= billed_amount`;
- `paid_amount + patient_responsibility_amount <= allowed_amount`;
- adjustment amounts are nonnegative, no greater than billed amount, and require both group and reason codes;
- claim header financials equal the sum of their service lines;
- claim-line adjustment summaries equal normalized adjustment details;
- every replacement/void claim resolves to a retained original claim; and
- member, payer, billing provider, frequency, original claim, and diagnosis list agree across lines belonging to one claim.

## Run it

The expanded synthetic fixture demonstrates dimensions, ordered diagnoses, procedures, adjustments, and replacement lineage:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli claims-pipeline data/samples/claims_expanded.csv --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

X12 837/835 envelope parsing, trading-partner acknowledgements, and production code-set licensing remain out of scope. This is an X12-like normalized demonstration, not a certified EDI implementation.
