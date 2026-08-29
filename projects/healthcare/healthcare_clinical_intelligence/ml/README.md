# Readmission Cohort and Modeling

The implemented `readmission-cohort` command creates index inpatient encounters, predicts at discharge, and uses only earlier encounters for features. It exports labels for readmissions occurring in the following 30 days.

It is a synthetic-data cohort and feature engineering demonstration, not a clinically validated model. Train/evaluate models only after documenting leakage checks, patient-level temporal splits, class balance, calibration, and subgroup performance.
