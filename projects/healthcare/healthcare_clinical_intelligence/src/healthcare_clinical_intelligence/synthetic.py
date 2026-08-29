"""Deterministic, non-PHI FHIR fixtures for demos and pipeline-scale tests."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from typing import Any


def generate_fhir_bundle(patient_count: int = 25, seed: int = 42) -> dict[str, Any]:
    rng = random.Random(seed)
    resources: list[dict[str, Any]] = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    resources.extend([
        {
            "resourceType": "Organization", "id": "synthetic-org-001", "name": "Synthetic Community Hospital",
            "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov"}]}],
            "meta": {"lastUpdated": start.isoformat().replace("+00:00", "Z")},
        },
        {
            "resourceType": "Practitioner", "id": "synthetic-practitioner-001",
            "name": [{"given": ["Avery"], "family": "Morgan"}],
            "meta": {"lastUpdated": start.isoformat().replace("+00:00", "Z")},
        },
    ])
    for patient_number in range(1, patient_count + 1):
        patient_id = f"synthetic-p-{patient_number:05d}"
        birth_year = rng.randint(1940, 2010)
        resources.append({
            "resourceType": "Patient", "id": patient_id,
            "gender": rng.choice(["female", "male", "other"]),
            "birthDate": date(birth_year, rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
            "meta": {"lastUpdated": start.isoformat().replace("+00:00", "Z")},
        })
        resources.append({
            "resourceType": "Coverage", "id": f"synthetic-cov-{patient_number:05d}", "status": "active",
            "beneficiary": {"reference": f"Patient/{patient_id}"}, "payor": [{"reference": "Organization/synthetic-org-001"}],
            "meta": {"lastUpdated": start.isoformat().replace("+00:00", "Z")},
        })
        index_discharge: datetime | None = None
        for encounter_number in range(rng.randint(1, 4)):
            encounter_id = f"synthetic-e-{patient_number:05d}-{encounter_number:02d}"
            encounter_start = start + timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 23))
            encounter_end = encounter_start + timedelta(hours=rng.randint(1, 12))
            encounter_class = "IMP" if patient_number % 5 == 0 and encounter_number == 0 else rng.choices(["EMER", "AMB", "IMP"], weights=[25, 60, 15])[0]
            resources.append({
                "resourceType": "Encounter", "id": encounter_id, "status": "finished",
                "class": {"code": encounter_class}, "subject": {"reference": f"Patient/{patient_id}"},
                "period": {"start": encounter_start.isoformat().replace("+00:00", "Z"), "end": encounter_end.isoformat().replace("+00:00", "Z")},
                "meta": {"lastUpdated": encounter_end.isoformat().replace("+00:00", "Z")},
            })
            resources.extend([
                {
                    "resourceType": "Condition", "id": f"synthetic-c-{patient_number:05d}-{encounter_number:02d}",
                    "subject": {"reference": f"Patient/{patient_id}"}, "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": rng.choice(["I10", "E11.9", "J06.9"])}]},
                    "recordedDate": encounter_start.isoformat().replace("+00:00", "Z"),
                    "meta": {"lastUpdated": encounter_end.isoformat().replace("+00:00", "Z")},
                },
                {
                    "resourceType": "Procedure", "id": f"synthetic-pr-{patient_number:05d}-{encounter_number:02d}", "status": "completed",
                    "subject": {"reference": f"Patient/{patient_id}"}, "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "code": {"coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": "99213"}]},
                    "performedDateTime": encounter_start.isoformat().replace("+00:00", "Z"),
                    "meta": {"lastUpdated": encounter_end.isoformat().replace("+00:00", "Z")},
                },
                {
                    "resourceType": "MedicationRequest", "id": f"synthetic-m-{patient_number:05d}-{encounter_number:02d}", "status": "active",
                    "subject": {"reference": f"Patient/{patient_id}"}, "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "860975"}]},
                    "authoredOn": encounter_start.isoformat().replace("+00:00", "Z"),
                    "meta": {"lastUpdated": encounter_end.isoformat().replace("+00:00", "Z")},
                },
            ])
            if encounter_number == 0 and encounter_class == "IMP":
                index_discharge = encounter_end
        if index_discharge and patient_number % 5 == 0:
            readmit_id = f"synthetic-e-{patient_number:05d}-readmit"
            readmit_start = index_discharge + timedelta(days=7)
            readmit_end = readmit_start + timedelta(days=2)
            resources.append({
                "resourceType": "Encounter", "id": readmit_id, "status": "finished", "class": {"code": "IMP"},
                "subject": {"reference": f"Patient/{patient_id}"},
                "period": {"start": readmit_start.isoformat().replace("+00:00", "Z"), "end": readmit_end.isoformat().replace("+00:00", "Z")},
                "meta": {"lastUpdated": readmit_end.isoformat().replace("+00:00", "Z")},
            })
            resources.append({
                "resourceType": "Observation", "id": f"synthetic-o-{patient_number:05d}-{encounter_number:02d}",
                "status": "final", "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}]},
                "effectiveDateTime": encounter_start.isoformat().replace("+00:00", "Z"),
                "valueQuantity": {"value": round(rng.uniform(36.0, 39.5), 1), "unit": "Cel"},
                "meta": {"lastUpdated": encounter_end.isoformat().replace("+00:00", "Z")},
            })
    return {"resourceType": "Bundle", "type": "collection", "entry": [{"resource": resource} for resource in resources]}
