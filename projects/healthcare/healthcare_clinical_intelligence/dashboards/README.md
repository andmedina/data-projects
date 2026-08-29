# Dashboards

Power BI is the planned dashboard client. Begin with the `mart.ed_utilization_monthly` view and metric definitions in `docs/metric_dictionary.md`.

For a file-based prototype, export dashboard-ready data without a database:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli ed-utilization output/fhir/accepted.jsonl --output output/ed_utilization_monthly.csv
```

Before publishing any visual, validate totals with an independent SQL query and save the validation evidence in the associated DA ticket. Dashboard files and exports containing anything beyond approved synthetic data must not be committed.

The first page should use `reporting_month`, `ed_encounters`, and `patients_with_ed_encounter` from the export. It should display the metric definition, refresh/source timestamp, and validation status alongside the visual.
