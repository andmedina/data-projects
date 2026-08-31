# DE-007 — Expand Claims Adjudication Dimensions

## Business context

The initial controlled claims path retained header/detail financials but could not explain payer, provider, diagnosis, procedure, or adjustment context. It also treated original and replacement claims as independent cost activity, which could overstate dashboard totals.

## Requirements

- Preserve every accepted source-line payload and select only its latest version for canonical loading.
- Normalize payer and provider dimensions, ordered diagnoses, line procedures, and reason-coded adjustments.
- Retain original/replacement/void lineage using controlled claim-frequency codes.
- Reconcile claim headers to lines and line adjustment summaries to adjustment details.
- Exclude superseded originals and terminal voids from current-state cost reporting.
- Quarantine invalid expanded records with deterministic reason codes.
- Demonstrate rerun idempotency and independent database validation using synthetic data only.

## Acceptance criteria

1. `claims_expanded.csv` passes file validation and loads three records with zero rejects.
2. The canonical model contains the expected payer, two claims providers, ordered diagnosis rows, procedure rows, and adjustment rows.
3. Replacement claim `c-101` resolves to original claim `c-100`.
4. Header/line, line/adjustment, original-claim, and repeated-header controls all observe zero violations.
5. February 2025 current-state cost includes the replacement and excludes its superseded original.
6. An identical rerun loads zero new records and reports three duplicates.
7. Automated tests and `validation.sql` pass.

Status: complete for the controlled synthetic claims contract.
