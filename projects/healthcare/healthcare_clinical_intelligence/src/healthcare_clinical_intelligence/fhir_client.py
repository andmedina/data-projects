"""FHIR REST client with explicit pagination and incremental-query support."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def resource_url(base_url: str, resource_type: str, since: str | None = None, count: int = 100) -> str:
    query: dict[str, str | int] = {"_count": count}
    if since:
        query["_since"] = since
    return f"{base_url.rstrip('/')}/{resource_type}?{urlencode(query)}"


def fetch_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=30) as response:  # noqa: S310 - caller controls trusted FHIR endpoint
        return json.loads(response.read())


def put_resource(base_url: str, resource: dict[str, Any]) -> None:
    """Create or replace a resource by stable FHIR type and id."""
    resource_type, resource_id = resource["resourceType"], resource["id"]
    request = Request(
        f"{base_url.rstrip('/')}/{resource_type}/{resource_id}",
        data=json.dumps(resource).encode(),
        method="PUT",
        headers={"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"},
    )
    with urlopen(request, timeout=30):  # noqa: S310 - caller controls trusted FHIR endpoint
        pass


def publish_bundle(base_url: str, payload: dict[str, Any]) -> int:
    """Upsert all resources from a controlled synthetic Bundle."""
    resources = list(iter_resources_from_payload(payload))
    for resource in resources:
        put_resource(base_url, resource)
    return len(resources)


def iter_resources_from_payload(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    if payload.get("resourceType") == "Bundle":
        for entry in payload.get("entry", []):
            resource = entry.get("resource")
            if isinstance(resource, dict):
                yield resource
    else:
        yield payload


def paginated_bundles(
    initial_url: str, fetcher: Callable[[str], dict[str, Any]] = fetch_json
) -> Iterator[dict[str, Any]]:
    """Yield every Bundle, following only FHIR ``next`` links."""
    next_url: str | None = initial_url
    visited: set[str] = set()
    while next_url:
        if next_url in visited:
            raise ValueError("FHIR pagination loop detected")
        visited.add(next_url)
        bundle = fetcher(next_url)
        yield bundle
        next_url = next((link.get("url") for link in bundle.get("link", []) if link.get("relation") == "next"), None)


def latest_last_updated(bundle: dict[str, Any]) -> str | None:
    timestamps = [
        (entry.get("resource", {}).get("meta", {}) or {}).get("lastUpdated") for entry in bundle.get("entry", [])
    ]
    return max((timestamp for timestamp in timestamps if timestamp), default=None)


def utc_now() -> str:
    return datetime.now().astimezone().isoformat()
