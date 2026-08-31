import json
from pathlib import Path

from healthcare_clinical_intelligence.analytics import (
    clinical_activity_from_accepted,
    ed_utilization_from_accepted,
    eligible_ed_utilization_from_accepted,
)
from healthcare_clinical_intelligence.pipeline import run_fhir_file
from healthcare_clinical_intelligence.synthetic import generate_fhir_bundle


def test_generator_is_deterministic():
    bundle = generate_fhir_bundle(3, 7)
    assert bundle == generate_fhir_bundle(3, 7)
    assert len(bundle["entry"]) >= 9
    lab_observations = [
        entry["resource"] for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == "Observation"
    ]
    assert lab_observations
    assert all(observation["category"][0]["coding"][0]["code"] == "laboratory" for observation in lab_observations)
    coverages = [
        entry["resource"] for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == "Coverage"
    ]
    assert len(coverages) == 3
    assert all(coverage["period"]["start"] <= coverage["period"]["end"] for coverage in coverages)
    assert {coverage["payor"][0]["reference"] for coverage in coverages} == {
        "Organization/synthetic-payer-001"
    }


def test_ed_export_from_sample_bundle(tmp_path: Path):
    run_fhir_file(Path("data/samples/fhir_bundle.json"), tmp_path)
    rows = ed_utilization_from_accepted(tmp_path / "accepted.jsonl", tmp_path / "ed.csv")
    assert rows == [{"reporting_month": "2025-01", "ed_encounters": 1, "patients_with_ed_encounter": 1}]


def test_clinical_activity_export_from_generated_bundle(tmp_path: Path):
    source = tmp_path / "bundle.json"
    source.write_text(__import__("json").dumps(generate_fhir_bundle(3, 4)))
    run_fhir_file(source, tmp_path / "run")
    rows = clinical_activity_from_accepted(tmp_path / "run" / "accepted.jsonl", tmp_path / "clinical.csv")
    assert rows
    assert sum(row["conditions"] for row in rows) > 0


def test_eligibility_aware_ed_export_uses_member_month_denominator(tmp_path: Path):
    canonical_rows = [
        {
            "resource_type": "Coverage", "source_resource_id": "cov-1", "patient_id": "p1",
            "payer_id": "payer-a", "status": "active", "coverage_start": "2025-01-15", "coverage_end": "2025-02-10",
        },
        {
            "resource_type": "Coverage", "source_resource_id": "cov-2", "patient_id": "p2",
            "payer_id": "payer-a", "status": "active", "coverage_start": "2025-01-01", "coverage_end": "2025-01-31",
        },
        {
            "resource_type": "Encounter", "source_resource_id": "e-1", "patient_id": "p1",
            "encounter_class": "EMER", "status": "finished", "start_at": "2025-01-20T10:00:00Z",
        },
        {
            "resource_type": "Encounter", "source_resource_id": "e-2", "patient_id": "p2",
            "encounter_class": "EMER", "status": "completed", "start_at": "2025-01-21T10:00:00Z",
        },
        {
            "resource_type": "Encounter", "source_resource_id": "e-3", "patient_id": "p1",
            "encounter_class": "EMER", "status": "finished", "start_at": "2025-03-01T10:00:00Z",
        },
        {
            "resource_type": "Encounter", "source_resource_id": "e-4", "patient_id": "p1",
            "encounter_class": "EMER", "status": "in-progress", "start_at": "2025-02-01T10:00:00Z",
        },
    ]
    accepted_path = tmp_path / "accepted.jsonl"
    accepted_path.write_text("".join(json.dumps({"canonical": row}) + "\n" for row in canonical_rows))

    rows = eligible_ed_utilization_from_accepted(accepted_path, tmp_path / "eligible_ed.csv")

    assert rows == [
        {
            "reporting_month": "2025-01",
            "payer_organization_id": "payer-a",
            "member_months": 2,
            "ed_encounters": 2,
            "patients_with_ed_encounter": 2,
            "ed_encounters_per_1000_member_months": 1000.0,
        },
        {
            "reporting_month": "2025-02",
            "payer_organization_id": "payer-a",
            "member_months": 1,
            "ed_encounters": 0,
            "patients_with_ed_encounter": 0,
            "ed_encounters_per_1000_member_months": 0.0,
        },
    ]


def test_population_health_sql_contract_expands_coverage_months():
    sql = Path("sql/marts/035_population_health.sql").read_text()

    assert "generate_series" in sql
    assert "mart.member_eligibility_monthly" in sql
    assert "mart.ed_utilization_eligible_monthly" in sql
    assert "ed_encounters_per_1000_member_months" in sql
