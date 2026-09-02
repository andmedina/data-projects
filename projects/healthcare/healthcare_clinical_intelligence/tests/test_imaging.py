from pathlib import Path


def test_imaging_sql_preserves_header_series_grain_and_no_pixels() -> None:
    staging = Path("sql/staging/010_staging_views.sql").read_text()
    core = Path("sql/core/020_core_schema.sql").read_text()
    mart = Path("sql/marts/036_imaging_activity.sql").read_text()

    assert "staging.stg_imaging_study" in staging
    assert "staging.stg_imaging_series" in staging
    assert "core.imaging_study" in core
    assert "core.imaging_series" in core
    assert "pixel" not in (staging + core).lower()
    assert "imaging_instances" in mart
