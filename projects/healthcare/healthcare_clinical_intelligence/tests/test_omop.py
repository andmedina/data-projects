from pathlib import Path


def test_omop_subset_defines_source_preserving_v54_domains() -> None:
    sql = Path("sql/omop/050_omop_subset.sql").read_text()

    for view_name in (
        "person",
        "observation_period",
        "visit_occurrence",
        "condition_occurrence",
        "procedure_occurrence",
        "measurement",
        "drug_exposure",
        "payer_plan_period",
    ):
        assert f"create or replace view omop.{view_name}" in sql
    assert "source_to_standard_concept_status" in sql
    assert "clinical_event_span" in sql
    assert "active_coverage" in sql
    assert "when 'IMP' then 9201" in sql
    assert "when 'AMB' then 9202" in sql
    assert "when 'EMER' then 9203" in sql


def test_omop_identifier_refresh_is_idempotent_and_ordered() -> None:
    sql = Path("sql/omop/051_refresh_omop_ids.sql").read_text()

    assert "on conflict (entity_type, source_id) do nothing" in sql
    assert "order by entity_type, source_id" in sql
    assert "omop.observation_period_source" in sql
    assert "category_code = 'laboratory'" in sql


def test_omop_migration_creates_views_before_refreshing_identifiers() -> None:
    init_sql = Path("sql/000_init.sql").read_text()

    assert init_sql.index("omop/050_omop_subset.sql") < init_sql.index("omop/051_refresh_omop_ids.sql")


def test_omop_documentation_does_not_claim_conformance() -> None:
    documentation = Path("docs/omop_mapping.md").read_text().lower()

    assert "not an omop-conformant cdm instance" in documentation
    assert "concept id `0`" in documentation
