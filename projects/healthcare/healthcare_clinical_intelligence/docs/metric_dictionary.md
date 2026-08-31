# Metric Dictionary

## Emergency department encounter intensity

**Status:** implemented and independently reconciled for synthetic Phase 1 data.

**Business question:** How much completed ED activity occurs monthly, and how concentrated is repeat use among observed ED patients?

**Numerator:** encounters whose normalized class is `EMER`, whose status is `finished` or `completed`, and whose start timestamp falls within the reporting month.

**Denominator:** distinct patients with at least one qualifying ED encounter in the reporting month.

**Grain:** reporting month.

**Validation:** `tickets/DA-001_ed_utilization/validation.sql` independently reconciles encounter and distinct-patient counts and checks for missing reporting timestamps.

**Limitation:** This denominator measures observed ED users, not eligible member months, so the ratio must not be labeled a population utilization rate. Facility and demographic segments are deferred until their mappings are present and validated.

## Eligibility-aware emergency department utilization

**Status:** implemented and independently reconciled for the controlled synthetic Coverage profile.

**Business question:** How many completed ED encounters occur per 1,000 covered member months for each payer?

**Numerator:** encounters whose normalized class is `EMER`, whose status is `finished` or `completed`, whose start timestamp falls in the reporting month, and whose patient has active Coverage for that payer during the same month.

**Denominator:** distinct patient/payer/month combinations expanded from inclusive active Coverage periods.

**Calculation:** `1,000 × eligible ED encounters ÷ member months`, rounded to two decimal places.

**Grain:** reporting month and payer organization.

**Validation:** `tickets/DA-002_eligibility_aware_ed_utilization/validation.sql` independently rebuilds the denominator and numerator and verifies the published rate.

**Limitations:** Any calendar-month overlap counts as one full member month; partial months are not prorated. When a patient has simultaneous Coverage from multiple payers, the encounter is attributed to each payer because the controlled Encounter profile does not identify the responsible Coverage. The result is synthetic and is not a certified HEDIS measure.

## Claim paid amount

**Status:** implemented for the controlled synthetic claims source.

**Definition:** sum of service-line `paid_amount` within the claim service month for the current adjudication state. A claim referenced by a replacement or void is excluded; the terminal replacement is included and a terminal void contributes no cost. Claim header totals must reconcile to service-line totals.

**Grain:** reporting month.

**Limitation:** This is synthetic financial activity, not adjudicated production claims or a measure of total cost of care. The controlled model does not implement every X12 reversal, coordination-of-benefits, or remittance scenario.

## Clinical activity volume

**Status:** implemented for synthetic FHIR Conditions, Procedures, and MedicationRequests.

**Definition:** count of canonical clinical activity records by their recorded, performed, or authored month.

**Grain:** reporting month.

**Limitation:** Counts describe source-system activity and are not clinical quality, outcome, or prevalence measures.

## Laboratory result completeness

**Status:** implemented, incident-tested, and independently reconciled for synthetic FHIR data.

**Denominator:** final, amended, or corrected Observations categorized as `laboratory` with an effective timestamp in the reporting month.

**Complete numerator:** denominator records with a usable typed `value[x]` or documented FHIR `dataAbsentReason`.

**Unexplained missing result:** denominator record with neither a usable typed value nor documented absent reason.

**Calculation:** 100 × complete numerator ÷ denominator, at reporting-month grain.

**Validation:** `tickets/DE-006_missing_laboratory_results/validation.sql` reconciles raw versions, the typed canonical value, unexplained nulls, the monthly mart, and pre/post-remediation gate results.

**Limitation:** This measures transport/model completeness, not clinical plausibility, reference-range interpretation, result timeliness, or fitness for patient care.
