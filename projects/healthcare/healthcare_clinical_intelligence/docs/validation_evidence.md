# Local Integration Validation Evidence

The Docker-based Phase 1 workflow was executed locally against PostgreSQL and Airflow.

## PostgreSQL FHIR pipeline

The sample FHIR Bundle produced:

| Measure | Result |
| --- | ---: |
| Source resources | 4 |
| Raw resources loaded | 3 |
| Rejected/quarantined resources | 1 |
| Core patients | 1 |
| Core encounters | 1 |
| Core observations | 1 |
| Orphan observations | 0 |
| Invalid encounter periods | 0 |

The ED mart returned one January 2025 emergency encounter for one patient, with 1.00 encounters per patient.

## Idempotency and scale

Rerunning the same sample loaded zero new raw resources and identified three existing resource payloads as duplicates. A deterministic 100-patient synthetic Bundle contained 582 FHIR resources; all 582 loaded successfully. The resulting core model contained 101 patients, 242 encounters, and 242 observations, with zero orphan observations and zero invalid encounter periods. The ED mart contained 12 reporting months and 69 ED encounters.

## Airflow orchestration

The `clinical_fhir_pipeline` DAG was registered, unpaused, and triggered in the Docker Airflow standalone environment. The following tasks completed successfully:

1. `ingest_validate_and_quarantine_fhir`
2. `transform_and_load_core`
3. `publish_quality_report`

The manual DAG run completed with a `success` state. A scheduled run also completed successfully after the DAG was unpaused.

## HAPI FHIR REST integration

The local HAPI FHIR R4 server served its CapabilityStatement at `/fhir/metadata`. The project `fhir-publish` command upserted the four-resource sample Bundle through the REST API. The incremental client then retrieved and loaded one Patient, one Encounter, and two Observations; the malformed Observation was quarantined by the same validation rule used for file ingestion.

An incremental rerun used the saved Patient watermark, loaded zero new records, and identified the returned Patient as a duplicate. This validates source watermarking and idempotency against the live API.

## Multi-source resolution

The HAPI and Synthea copies of the same FHIR resource IDs initially exposed a staging upsert conflict. Staging now ranks resource versions by `last_updated_at`, ingestion timestamp, and raw identifier, retaining only the latest version per resource type and source resource ID. After applying that correction, the core load completed successfully with 101 patients, 242 encounters, 242 observations, zero orphan observations, and zero invalid encounter periods.

## Expanded clinical model

A 20-patient generated Bundle containing 317 resources was processed with zero rejections. The file-based clinical-activity export produced 12 monthly rows. The live database load populated 55 Conditions, 55 Procedures, 55 MedicationRequests, 20 Coverage records, one Organization, and one Practitioner; existing relationship and temporal quality checks remained clean.

## Claims header/detail model

The synthetic claims CSV loaded one valid service line to `raw.claim_line`, then built one canonical claim header and one canonical claim line. Its billed, allowed, and paid amounts were 200.00, 150.00, and 120.00 respectively. A rerun loaded zero new records and identified one duplicate. The new header-to-line reconciliation query returned no discrepancies.

## Expanded claims dimensions and adjudication lineage

On August 30, 2026, `claims_expanded.csv` loaded three valid line payloads covering an original two-line claim and its one-line replacement. The load populated one payer, two claims-origin providers, four ordered claim diagnoses, three line procedures, and three reason-coded line adjustments in the shared development database. Including the earlier base fixture, canonical totals were three claims and four claim lines. The expanded load rejected zero rows.

An identical rerun loaded zero raw rows and classified all three inputs as duplicates. Latest-version staging prevented retained history from multiplying canonical totals. The 13-control persistent gate passed all 12 non-warning controls, including original-claim integrity, header/line financial reconciliation, line/adjustment reconciliation, and cross-line header consistency. The only warning remained the two deliberate FHIR quarantine fixtures, so the gate completed `passed_with_warnings` with zero blocking results.

The replacement claim `c-101` resolved to original `c-100`. The adjudication-aware cost mart excluded the superseded original and reported February 2025 as one current claim/line with billed 180.00, allowed 140.00, paid 110.00, patient responsibility 30.00, and adjustment 40.00. This prevents original and replacement versions from being added together in dashboard totals.

## HL7 v2 result ingestion

The synthetic ORU^R01 fixture loaded one raw HL7 message and mapped its OBX result to `core.hl7_observation` for patient `p-001`. The mapped result retained the message control ID `MSG0002`, LOINC code `8310-5`, value `37.1`, unit `Cel`, and final status `F`. A rerun loaded zero new messages and zero new observations, confirming message-hash and OBX-key idempotency.

## HL7 ADT lifecycle and ORM orders

On August 31, 2026, the three-message ADT fixture loaded admit, transfer, and discharge events for synthetic encounter `hl7-visit-001` with zero rejects. The derived current state was `discharged` at `WARD^202^1`, with an admitted timestamp of February 1 at 10:00 UTC, discharge on February 2 at 10:00 UTC, and three retained lifecycle events. The original single A01 fixture also backfilled one admitted event for encounter `e-001` from retained/raw-compatible input.

The ORM^O01 fixture loaded one order event for `order-001`, patient `p-001`, encounter `e-001`, control `NW`, status `SC`, and CPT `71046` Chest radiograph at January 3 11:15 UTC. Identical ADT and ORM reruns loaded zero raw messages, identified three and one duplicates respectively, and inserted zero new canonical events.

The expanded quality gate evaluated 16 controls: 15 passed, the deliberate FHIR quarantine-volume control warned, and no result was blocking. ADT transition validity, ORM code completeness, and accepted-message-to-core reconciliation each observed zero violations. Both new current-state datasets exported successfully with the dashboard bundle.

## Readmission baseline and claims mart

A deterministic 250-patient synthetic FHIR Bundle produced 170 temporally valid index encounters, including 51 30-day readmission outcomes. A chronological logistic-regression baseline trained on pre-discharge encounter history, prior ED use, and age at prediction. Its holdout set contained 34 rows, with ROC-AUC 0.5889 and PR-AUC 0.3504. These metrics are synthetic-data engineering evidence only and are not clinically meaningful.

## Governed readmission baseline

On August 31, 2026, the governed workflow regenerated 3,932 accepted FHIR resources for 250 synthetic patients and produced 182 inpatient index rows with 55 outcomes. A strict patient-level temporal cutoff assigned 125 rows/77 patients to training and 23 rows/17 patients to holdout, with zero shared patients and no date overlap. Thirteen crossover patients (34 rows, 18.68% of the cohort) were explicitly excluded rather than leaked across the cutoff.

The holdout contained six outcomes. ROC-AUC was 0.7255, PR-AUC 0.5165, precision 0.6000, recall 0.5000, specificity 0.8824, Brier score 0.1943, and expected calibration error 0.1312. Five age/prior-ED subgroup rows were reviewed; the worst sufficiently sized subgroup Brier score was 0.3170. All nine technical checks passed, producing `approved_for_synthetic_demonstration` while retaining `clinical_use_approved: false`.

Rerunning the same cohort/configuration reproduced the experiment identifier and did not duplicate its registry entry. The dashboard bundle added one governance row, four populated calibration bins, five subgroup rows, nine approval checks, holdout predictions, the model card, and the experiment registry.

The `mart.claim_cost_monthly` view summarizes monthly claim, line, billed, allowed, paid, and unpaid amounts from the canonical claim-line model.

## Dashboard export and DA-001 reconciliation

After the dashboard data product was added, the full PostgreSQL migration and export were rerun on August 29, 2026. The bundle produced one executive snapshot, 12 ED-activity rows, 12 clinical-activity rows, one claims-cost row, three quality-control rows, and 14 pipeline-run rows. All quality controls passed.

The independent DA-001 validation recomputed the metric directly from `core.encounter`. It returned zero differences from `mart.ed_utilization_monthly`, found 68 qualifying completed emergency encounters across 12 months, and found zero qualifying encounters without a start timestamp. The count differs from the earlier 69-encounter scale test because later synthetic source versions were loaded into the shared development database; the latest-version staging rule intentionally determines the current canonical state.

## Eligibility-aware population health

On August 31, 2026, a deterministic 100-patient Coverage-enabled Bundle contained 1,553 FHIR resources, including a distinct synthetic payer Organization. The file path accepted all 1,553 with zero rejects. In the shared PostgreSQL environment, the final load added the new payer and 100 corrected Coverage payload versions, identified 1,452 unchanged payloads as duplicates, rejected none, and populated 100 active Coverage records whose periods expanded to 950 distinct member months across 12 payer-month rows. The equivalent file-only path emitted the same 12-month contract for the generated Bundle.

In the shared development database, 58 completed ED encounters occurred during an eligible month, covering 56 patient-months with ED use. Independent DA-002 SQL returned zero denominator discrepancies, zero numerator/patient discrepancies, zero rate-formula discrepancies, zero active Coverage records with missing periods, and zero overlapping active periods for the same patient/payer.

The expanded gate evaluated 18 controls: 17 passed, the historical deliberate FHIR-quarantine volume warned, and no result was blocking. The refreshed dashboard bundle contained 15 datasets when the governed model artifacts were included, adding 12 member-eligibility rows and 12 eligibility-aware ED rows; `data_quality.csv` contained all 18 latest control results.

## Persistent data-quality gate

DE-005 added eight database-configured checks with durable run and result history. Live normal-mode evaluation persisted eight results: seven passed and the FHIR quarantine-volume control warned because two deliberately malformed fixtures remain retained. All error-severity controls passed, so the overall state was `passed_with_warnings` with zero blocking results.

Strict mode evaluated the same database state with `--fail-on-warning`, persisted a failed gate run, and returned process exit code 1. A subsequent normal run restored the expected non-blocking development state. Independent SQL confirmed that every enabled definition had exactly one result in the latest run, no result had `fail` or `error` status, and no stale run remained `running`.

The finalized Airflow image was rebuilt with `enforce_quality_gate` and immutable policy snapshots. Manual run `de005_policy_snapshot_validation` completed successfully on August 29, 2026: ingestion, core transformation, and the quality gate each reached `success`. The scheduled run created when the DAG was unpaused also completed successfully. The final dashboard refresh read eight rows from the latest persisted quality run and 18 operational pipeline-run rows.

## Missing laboratory-result incident

DE-006 extended canonical FHIR Observations with category, typed values, UCUM unit identity, coded results, and documented absent reasons. The database migration initially exposed PostgreSQL's protection against inserting columns into the middle of an existing view. Preserving the original staging column order and appending the new fields made the migration backward-compatible without dropping the view or stored data.

The missing-result incident Bundle loaded one Patient, one Encounter, and one final laboratory Observation with no value or absent reason. The ten-control quality gate observed one missing lab result, persisted a critical failure, and returned exit code 1. The corrected Bundle retained a second raw Observation version, loaded that one changed payload, and identified the two unchanged resources as duplicates.

Latest-version staging selected the corrected payload and populated LOINC `718-7`, Quantity `13.4`, unit `g/dL`, and UCUM system/code in `core.observation`. The next quality run observed zero missing laboratory results: nine controls passed, one deliberate FHIR-quarantine warning remained, and no result was blocking. Independent SQL found two retained source versions, zero unexplained missing lab rows, and February 2025 mart completeness of 100.00% (one populated result out of one final laboratory Observation).

The final Airflow image was rebuilt from the exact reviewed revision with the typed Observation transformation, supported-value validation, and both new critical checks. Manual run `de006_release_validation` and the scheduled run created on unpause both completed successfully on August 30, 2026. The manual ingestion, core transformation, and `enforce_quality_gate` tasks each reached `success`. The final dashboard bundle contained one lab-completeness row, ten latest quality-result rows, and 27 pipeline-run rows.

## Environment note

The local machine already used `localhost:5432` for another PostgreSQL service. This project therefore uses host port `55432`; container-to-container services continue to use PostgreSQL port `5432`.
