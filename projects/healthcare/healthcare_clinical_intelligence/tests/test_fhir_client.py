import pytest

from healthcare_clinical_intelligence.fhir_client import paginated_bundles, resource_url


def test_resource_url_encodes_incremental_parameters():
    url = resource_url("http://example.test/fhir/", "Patient", "2025-01-01T00:00:00Z", 50)
    assert url == "http://example.test/fhir/Patient?_count=50&_since=2025-01-01T00%3A00%3A00Z"


def test_pagination_follows_next_link():
    responses = {
        "first": {"resourceType": "Bundle", "link": [{"relation": "next", "url": "second"}]},
        "second": {"resourceType": "Bundle", "link": []},
    }
    assert list(paginated_bundles("first", responses.__getitem__)) == [responses["first"], responses["second"]]


def test_pagination_detects_loop():
    bundle = {"resourceType": "Bundle", "link": [{"relation": "next", "url": "first"}]}
    with pytest.raises(ValueError, match="loop"):
        list(paginated_bundles("first", lambda _: bundle))
