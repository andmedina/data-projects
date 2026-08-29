# DE-002 — Incremental FHIR Loading

Implement watermarks based on FHIR `meta.lastUpdated`, stable source IDs, payload hashes, and an idempotent upsert strategy. The FHIR REST client and checkpoint schema are now present. Remaining acceptance evidence: integration-test a HAPI FHIR server, persist checkpoints after a successful paginated load, and demonstrate late-arriving updates with lineage preserved.
