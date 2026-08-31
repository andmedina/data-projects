# DS-002 — Govern the Readmission Baseline

## Business context

The first synthetic readmission baseline produced discrimination metrics but did not satisfy its own documented governance contract. Row-level chronological splitting could place one patient in both partitions, and the workflow had no calibration evidence, subgroup review, experiment registry, model card, or enforceable approval decision.

## Requirements

- Split whole patients across a strict temporal cutoff and quantify excluded crossover patients.
- Hash cohort/configuration/implementation/runtime into a reproducible experiment ID.
- Retain holdout predictions, calibration bins, subgroup evidence, and threshold metrics.
- Write an idempotent experiment registry and synthetic-only model card.
- Evaluate explicit technical approval checks and optionally fail the CLI process.
- Prohibit clinical approval regardless of technical result.
- Export governance datasets and artifacts with the dashboard bundle.

## Acceptance criteria

1. Train and holdout have zero patient overlap and zero date overlap.
2. Crossover exclusions are reported and remain within the documented policy threshold.
3. The report contains ROC-AUC, PR-AUC, threshold metrics, Brier score, expected calibration error, calibration bins, and subgroup rows.
4. Identical reruns reproduce the experiment ID and do not duplicate the registry entry.
5. The model card and every report state that clinical use is prohibited.
6. `--fail-on-governance` returns success only when every synthetic-demo check passes.
7. The dashboard bundle includes governance, calibration, subgroup, approval, prediction, registry, and model-card artifacts.

Status: complete for the synthetic engineering baseline.
