# ML Methodology

## Candidate use case

Predict 30-day readmission following an eligible inpatient discharge using only information available at prediction time.

## Cohort contract

- **Index event:** eligible inpatient discharge.
- **Observation window:** prior 365 days, ending at the index discharge.
- **Prediction time:** index discharge.
- **Outcome window:** 1–30 days after the index discharge.
- **Outcome:** qualifying inpatient readmission within that window.

Splits must be patient-level and time-aware. Features must not include events, status updates, labs, diagnoses, or encounter fields recorded after prediction time.

## Evaluation

Report prevalence, ROC-AUC, PR-AUC, recall, precision, calibration, confidence intervals where feasible, and subgroup performance. A synthetic-data model is strictly an engineering demonstration and never clinically validated or deployable.

## Required artifacts before modeling

`ml/cohorts/` cohort SQL, feature lineage, a data dictionary, leakage checks, a reproducible training configuration, evaluation report, and model card.

## Implemented cohort export

`hci readmission-cohort <accepted.jsonl>` implements the prediction-time contract for synthetic FHIR output. It uses prior encounter history only; its outcome is a later inpatient encounter within 30 days. It deliberately stops before model training because synthetic outcomes do not establish clinical utility.
