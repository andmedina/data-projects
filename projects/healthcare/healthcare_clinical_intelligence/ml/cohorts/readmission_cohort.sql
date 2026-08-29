-- Contract only: implement once inpatient encounter mappings and core facts are complete.
-- Prediction time is index discharge; no future rows may contribute to features.
select
    encounter_id as index_encounter_id,
    patient_id,
    end_at as prediction_at,
    end_at + interval '30 days' as outcome_window_end
from core.encounter
where encounter_class = 'IMP'
  and end_at is not null;
