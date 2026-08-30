# DE-006 Solution — Missing Laboratory Results

## Root cause

The incident fixture represents an upstream final laboratory Observation that omitted both `value[x]` and `dataAbsentReason`. A separate platform defect amplified the risk: raw JSON retained Observation values, but the original canonical model stored only status, code, relationships, and effective time. That model could not prove whether a result was absent at the source or lost during transformation.

## Correction

The staging and core layers now preserve:

- Observation category and LOINC identity;
- typed Quantity, String, Boolean, Integer, and CodeableConcept values;
- human-readable unit plus UCUM system/code; and
- FHIR data-absent-reason code.

The generated synthetic source now produces one categorized glucose laboratory Observation per normal encounter. `mart.lab_result_completeness_monthly` separates populated results, documented absent reasons, and unexplained missing results.

Two error-severity DE-005 controls fail closed when final laboratory Observations lack a usable result/absent reason or a reporting timestamp. This prevents an incomplete lab dataset from reaching a normal Airflow success state.

## Remediation and recovery

`fhir_lab_incident_missing.json` loaded three valid resources, including one final lab with no result. The quality gate evaluated ten controls, observed one unexplained missing lab result, and returned exit code 1.

`fhir_lab_incident_corrected.json` supplied a later version of the same Observation with corrected status and hemoglobin `13.4 g/dL`. The second load inserted one new raw Observation version and recognized the unchanged Patient and Encounter as duplicates. Latest-version staging updated the existing core row without duplicating it. The next gate observed zero missing results and returned a non-blocking `passed_with_warnings` state; the remaining warning is the repository's deliberate invalid FHIR fixture history.

The exact commit-candidate Airflow image then completed manual run `de006_release_validation` and its scheduled run successfully. All three manual tasks—including the ten-control quality gate—reached `success`, proving the corrected result remains healthy under orchestration rather than only through direct CLI execution.

## Prevention

- Preserve raw payload versions and source timestamps for replay and diagnosis.
- Keep result types separate instead of coercing every value to text.
- Require either a usable result or explicit absent reason for final lab Observations.
- Gate missing effective timestamps because undated results cannot enter monthly reporting.
- Reconcile the dashboard mart independently to canonical records.
- Treat thresholds and any accepted absent-reason codes as data-owner policy.
