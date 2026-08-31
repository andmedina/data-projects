# Dashboard Data Product

Power BI is the planned dashboard client. The database-backed export command creates one refreshable bundle containing executive, utilization, clinical-activity, claims-cost, laboratory-completeness, HL7 current-state, quality, and pipeline-operability datasets:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli dashboard-export \
  --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence" \
  --output output/dashboard \
  --model-report output/readmission_baseline_report.json
```

The optional model report is validated as JSON and copied into the bundle. `manifest.json` records every dataset, filename, row count, generation timestamp, and optional model artifact.

| Dataset | Intended page | Grain |
| --- | --- | --- |
| `executive_overview.csv` | Executive summary | one refresh snapshot |
| `ed_utilization_monthly.csv` | ED activity | reporting month |
| `clinical_activity_monthly.csv` | Clinical activity | reporting month |
| `claim_cost_monthly.csv` | Claims cost | reporting month |
| `lab_result_completeness_monthly.csv` | Laboratory completeness | reporting month |
| `hl7_encounter_current_state.csv` | HL7 operations | encounter |
| `hl7_order_current_state.csv` | HL7 operations | order |
| `data_quality.csv` | Data trust | latest persisted quality-run control |
| `pipeline_runs.csv` | Pipeline operations | pipeline run |

Run `quality-gate` before the export so the data-trust page receives the latest persisted results. Use the metric definitions in `docs/metric_dictionary.md`. Display the data refresh timestamp and validation status on every published page. Do not label ED encounter intensity as a population utilization rate.

The laboratory page should display final-result volume, populated values, documented absent reasons, unexplained missing results, and completeness percentage together. It must state that completeness is a data-pipeline measure rather than clinical interpretation.

The claims-cost page uses only the current adjudication state: superseded originals and terminal void claims are excluded. Display paid, patient-responsibility, and reason-coded adjustment amounts separately; do not add original and replacement versions together.

## File-only prototype

For a file-based prototype, export dashboard-ready data without a database:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli ed-utilization output/fhir/accepted.jsonl --output output/ed_utilization_monthly.csv
```

Before publishing any visual, validate totals with an independent SQL query and save the validation evidence in the associated DA ticket. Dashboard files and exports containing anything beyond approved synthetic data must not be committed.

The first page should use `reporting_month`, `ed_encounters`, and `patients_with_ed_encounter` from the export. It should display the metric definition, refresh/source timestamp, and validation status alongside the visual.

For a clinical-activity page, generate the companion export:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli clinical-activity output/fhir/accepted.jsonl --output output/clinical_activity_monthly.csv
```

This page can show monthly condition, procedure, and medication-request volumes. The fields are technical activity measures, not clinical quality measures.
