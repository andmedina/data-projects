# Readmission Cohort and Modeling

The implemented `readmission-cohort` command creates index inpatient encounters, predicts at discharge, and uses only earlier encounters for features. It exports labels for readmissions occurring in the following 30 days.

It is a synthetic-data cohort and feature engineering demonstration, not a clinically validated model. Train/evaluate models only after documenting leakage checks, patient-level temporal splits, class balance, calibration, and subgroup performance.

Use the generated FHIR workflow before exporting the cohort:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli generate-synthetic --patients 250 --output data/synthetic/fhir_bundle.json
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/synthetic/fhir_bundle.json --output output/generated
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli readmission-cohort output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli train-readmission-baseline output/readmission_cohort.csv
```

The baseline uses chronological train/test partitions, prior encounter history, prior ED use, and age at prediction. It reports ROC-AUC and PR-AUC only when both partitions contain both outcome classes.
