# DS-002 Solution

The training workflow now chooses a temporal cutoff, assigns patients wholly before or after it, and excludes any patient with index events on both sides. The report records the cutoff, partition dates, patient counts, overlap checks, and crossover exclusion rate.

A deterministic experiment ID covers the cohort bytes, feature/target contract, implementation/configuration, approval policy, Python version, and scikit-learn version. Each experiment writes the evaluation report, holdout predictions, model card, and one idempotent JSONL registry row.

Evaluation includes discrimination, threshold behavior, fixed-width calibration bins, Brier score, expected calibration error, and age/prior-ED subgroup results with row counts. The approval policy is executable and exposed in the report. Passing authorizes only the synthetic portfolio demonstration; clinical approval remains hard-coded false.

The dashboard exporter turns the governed report into four refreshable CSV datasets and copies the predictions, model card, and registry beside the report.
