# DS-002 Validation Evidence

Executed August 31, 2026 with 250 deterministic synthetic patients and seed 42.

| Measure | Result |
| --- | ---: |
| FHIR resources accepted/rejected | 3,932 / 0 |
| Cohort rows/outcomes | 182 / 55 |
| Train rows/patients | 125 / 77 |
| Holdout rows/patients | 23 / 17 |
| Patient overlap / temporal overlap | 0 / false |
| Excluded crossover rows/patients | 34 / 13 |
| ROC-AUC / PR-AUC | 0.7255 / 0.5165 |
| Brier score / expected calibration error | 0.1943 / 0.1312 |
| Approval checks passed | 9 of 9 |
| Technical status | approved for synthetic demonstration |
| Clinical use approved | false |

An immediate rerun returned success with `--fail-on-governance`, reproduced the experiment ID, and left one registry entry for that experiment. The dashboard export produced four calibration rows, five subgroup rows, nine approval rows, and copied all governed artifacts.
