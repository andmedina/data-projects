# ML Methodology

## Candidate use case

Predict 30-day readmission following an eligible inpatient discharge using only information available at prediction time.

## Cohort contract

- **Index event:** eligible inpatient discharge.
- **Observation window:** prior 365 days, ending at the index discharge.
- **Prediction time:** index discharge.
- **Outcome window:** 1–30 days after the index discharge.
- **Outcome:** qualifying inpatient readmission within that window.

Splits are patient-level and strictly time-aware. The 80% row timestamp defines a candidate cutoff; patients entirely before the cutoff form training, patients entirely after it form holdout, and patients crossing it are excluded and reported. Features must not include events, status updates, labs, diagnoses, or encounter fields recorded after prediction time.

## Evaluation

Report prevalence, ROC-AUC, PR-AUC, recall, precision, specificity, confusion matrix, Brier score, expected calibration error, fixed-width calibration bins, and subgroup performance. Current subgroup review covers age band and prior ED-use history because those are the documented cohort fields; it must not imply evaluation of unmodeled protected characteristics. Confidence intervals remain a future extension.

## Required artifacts before modeling

`ml/cohorts/` cohort SQL, feature lineage, a data dictionary, leakage checks, a reproducible training configuration, holdout predictions, evaluation report, experiment registry, approval result, and model card.

## Implemented cohort export

`hci readmission-cohort <accepted.jsonl>` implements the prediction-time contract for synthetic FHIR output. `hci train-readmission-baseline <cohort.csv>` trains and evaluates the reproducible engineering baseline and writes all governance artifacts.

## Approval boundary

The default policy requires at least 20 holdout rows, zero patient/date overlap, no more than 25% crossover-row exclusion, ROC-AUC of at least 0.50, Brier score no greater than 0.30, expected calibration error no greater than 0.25, at least two reviewed subgroups with five or more rows, and Brier score no greater than 0.35 for those reviewed subgroups. `--fail-on-governance` returns a nonzero process status when any check fails.

These thresholds detect pipeline or model regressions in the fixed synthetic demonstration. They are not clinical acceptance thresholds. Even a passing report has `clinical_use_approved: false`; clinical validation, external data, governance bodies, prospective monitoring, and accountable human approval are absent.
