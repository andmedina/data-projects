# DA-002 Solution

FHIR Coverage validation now requires a status and an ordered inclusive period. Raw JSON remains unchanged, while staging appends the period boundaries and core stores typed dates with a database constraint. The deterministic generator assigns each synthetic patient one active Coverage period linked to a distinct synthetic payer Organization.

The population-health mart expands active Coverage periods to calendar months and deduplicates the patient/payer/month grain before aggregation. The ED numerator joins qualified encounters to those distinct eligible months, so encounters outside a patient's Coverage period are excluded. Rates are payer-specific because Encounter does not carry an authoritative Coverage identifier; a patient with simultaneous active Coverage from multiple payers is attributed to each payer and must be interpreted accordingly.

Two persistent critical controls prevent active Coverage with incomplete dates and overlapping active periods for the same patient/payer. The denominator expansion itself remains distinct as a defensive measure. The older `mart.ed_utilization_monthly` view remains an observed-user intensity metric, avoiding a breaking semantic change for existing consumers.
