# Claims Model

Claims are a Phase 3 extension. The target grain is deliberately split:

- `fact_claim`: one submitted/adjudicated claim header
- `fact_claim_line`: one billed service line belonging to a claim

Every line retains patient/member, payer, provider, service date, diagnosis/procedure coding, billed amount, allowed amount, paid amount, and patient responsibility. Financial validations enforce `paid <= allowed <= billed` unless a documented adjustment rule applies.

X12 837/835 parsing is deferred until CSV/FHIR claim normalization and reconciliation are complete.
