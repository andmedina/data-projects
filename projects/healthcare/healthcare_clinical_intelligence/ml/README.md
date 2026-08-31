# Readmission Cohort and Model Governance

The `readmission-cohort` command creates index inpatient encounters, predicts at discharge, and uses only earlier encounters for features. It exports labels for inpatient readmissions occurring in the following 30 days.

The governed baseline applies a strict temporal cutoff and assigns whole patients to one partition. Patients with index events on both sides of the cutoff are excluded and quantified so neither patient leakage nor date overlap is hidden.

Use the generated FHIR workflow before exporting the cohort:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli generate-synthetic --patients 250 --output data/synthetic/fhir_bundle.json
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/synthetic/fhir_bundle.json --output output/generated
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli readmission-cohort output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli train-readmission-baseline output/readmission_cohort.csv --fail-on-governance
```

The baseline writes:

- a JSON report with configuration, environment, split evidence, discrimination, threshold metrics, calibration, subgroup review, and approval checks;
- holdout predictions for independent review;
- a model card that prohibits clinical use;
- an idempotent JSONL experiment registry keyed by cohort, configuration, implementation, runtime, and approval policy; and
- dashboard-ready governance, calibration, subgroup, and approval datasets when the report is supplied to `dashboard-export`.

The technical gate checks holdout size, zero patient/date overlap, crossover exclusions, ROC-AUC, Brier score, expected calibration error, and sufficiently sized subgroup Brier scores. Passing means only `approved_for_synthetic_demonstration`; `clinical_use_approved` is always false. Thresholds are engineering controls for this fixture, not evidence of clinical utility or fairness.
