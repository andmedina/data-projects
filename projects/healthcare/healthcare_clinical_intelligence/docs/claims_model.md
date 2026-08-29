# Claims Model

Claims are a Phase 3 extension. The target grain is deliberately split:

- `fact_claim`: one submitted/adjudicated claim header
- `fact_claim_line`: one billed service line belonging to a claim

Every line retains patient/member, payer, provider, service date, diagnosis/procedure coding, billed amount, allowed amount, paid amount, and patient responsibility. Financial validations enforce `paid <= allowed <= billed` unless a documented adjustment rule applies.

X12 837/835 parsing is deferred until CSV/FHIR claim normalization and reconciliation are complete.

## Implemented controlled CSV workflow

The platform validates synthetic claim-line CSV records, writes valid lines to `raw.claim_line`, quarantines invalid rows with reason codes, and builds `core.claim` and `core.claim_line`. Claim headers reconcile to the sum of their service lines, and reruns are idempotent through source-line IDs and payload hashes.

Run it with:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli claims-pipeline data/samples/claims.csv --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```
