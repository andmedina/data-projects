# DA-001 Solution — Emergency Department Utilization

## Implementation

`mart.ed_utilization_monthly` aggregates the canonical encounter table at calendar-month grain. It counts only completed emergency encounters and reports both distinct ED patients and encounters per patient with ED activity.

The transformation is intentionally narrow. It does not infer eligibility from the presence of any clinical record, and it does not assign a facility when an encounter has no modeled service-provider/location relationship. Those shortcuts would produce attractive but misleading rates and segments.

## Validation approach

`validation.sql` independently recomputes monthly counts from `core.encounter` and compares them with the mart using a full outer join. A passing reconciliation returns zero discrepancy rows. Separate queries profile all class/status combinations and count qualifying emergency encounters without a start timestamp.

The dashboard bundle exposes the result as `ed_utilization_monthly.csv`; its manifest records the row count generated during each refresh. This makes the dashboard input reproducible from the database rather than dependent on a manually maintained spreadsheet.

## Local validation result

On August 29, 2026, the checks ran against the local synthetic PostgreSQL environment after applying `sql/000_init.sql`:

- the full-outer-join reconciliation returned zero discrepancy rows;
- 68 `EMER` / `finished` encounters qualified across 12 reporting months;
- zero qualifying emergency encounters were missing `start_at`; and
- the dashboard bundle contained 12 ED rows and all three cross-domain quality controls passed.

These values describe the current repeatable local data state. They are test evidence, not healthcare performance benchmarks.

## Interpretation constraints

- Synthetic data supports engineering validation, not clinical or operational conclusions.
- `patients_with_ed_encounter` is a user count, not an eligible-population denominator.
- The intensity ratio can reveal repeat use within the observed ED cohort but cannot be compared as a population rate across health plans.
- Facility, geography, race/ethnicity, and coverage segments should be added only after their source mappings and completeness controls are implemented.
