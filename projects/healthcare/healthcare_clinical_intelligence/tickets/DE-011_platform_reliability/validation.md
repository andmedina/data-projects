# DE-011 Validation

Validated locally on 2026-09-02 against PostgreSQL 16 in Docker using a uniquely named temporary database.

| Check | Result |
| --- | ---: |
| Python tests | 64 passed |
| Ruff lint | passed |
| Ruff formatting | passed |
| mypy source/scripts | passed |
| Coverage | 60.47% (60% floor) |
| First migration | applied |
| Identical second migration | already current |
| FHIR source resources | 621 |
| Claims source lines | 3 |
| HL7 source messages | 5 |
| Persistent quality checks | 29 |
| Blocking quality failures | 0 |
| Expected warnings | 2 |
| Dashboard datasets | 18 |
| Dashboard contract | valid |
| Query benchmarks | 5 passed |
| Stale runs after completion | 0 |
| Missing completion timestamps | 0 |
| Count mismatches | 0 |

The two expected warnings are the deliberate malformed FHIR quarantine fixture and the governed OMOP vocabulary backlog. The runner then repeated FHIR, claims, and all three HL7 fixture paths; each reported zero newly loaded raw records. The temporary database was removed by the runner's exact-name cleanup path.

The retained local development database was also migrated and refreshed. It reported 27 passes, two expected warnings, no failures, zero current operational-health defects, all 12 expected indexes, five passing query benchmarks, and a valid 18-dataset governed-model dashboard bundle.
