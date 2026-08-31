# DA-002 — Eligibility-Aware ED Utilization

## Business context

The existing ED metric measures encounter intensity among patients who used the ED. It cannot answer a population-health question because it has no eligibility denominator. A payer or population-health analyst needs completed ED encounters normalized by the number of covered members exposed during each reporting month.

## Requirements

- Require and retain FHIR Coverage start/end dates for the controlled synthetic profile.
- Expand active Coverage periods into distinct patient/payer member months.
- Count only finished or completed emergency encounters occurring during an eligible month.
- Report payer-specific ED encounters per 1,000 member months.
- Prevent overlapping Coverage rows from duplicating denominator months.
- Preserve the existing observed-user intensity metric under its current name.
- Provide equivalent PostgreSQL and file-only calculation paths.
- Export the denominator and rate through the dashboard contract.
- Add blocking controls for missing or overlapping active Coverage periods.

## Acceptance criteria

1. A deterministic 100-patient load produces Coverage periods with zero rejected resources.
2. Active Coverage expands to distinct patient/payer/month rows without duplicate member months.
3. The mart denominator and eligible ED numerator independently reconcile to core data.
4. Ineligible and unfinished ED encounters do not enter the numerator.
5. The published rate equals `1,000 × eligible ED encounters ÷ member months` at payer/month grain.
6. Missing-period and overlapping-period controls both observe zero violations.
7. Automated tests, dashboard export, and `validation.sql` pass.

Status: complete for the controlled synthetic FHIR Coverage profile.
