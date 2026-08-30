-- Two raw source versions must be retained for the incident Observation.
select source_system, source_resource_id, count(*) as retained_versions,
       min(last_updated_at) as first_source_version,
       max(last_updated_at) as latest_source_version
from raw.fhir_resource
where resource_type = 'Observation'
  and source_system = 'lab_incident'
  and source_resource_id = 'lab-incident-o-001'
group by source_system, source_resource_id;

-- The canonical row must reflect the corrected latest version and typed UCUM unit.
select observation_id, observation_status, category_code, coding_system, code,
       value_type, value_numeric, unit, unit_system, unit_code,
       data_absent_reason_code
from core.observation
where observation_id = 'lab-incident-o-001';

-- Must return zero rows after correction.
select observation_id
from core.observation
where category_code = 'laboratory'
  and observation_status in ('final', 'amended', 'corrected')
  and data_absent_reason_code is null
  and case value_type
      when 'Quantity' then value_numeric is null
      when 'Integer' then value_numeric is null
      when 'String' then nullif(btrim(value_text), '') is null
      when 'Boolean' then value_boolean is null
      when 'CodeableConcept' then value_code is null and nullif(btrim(value_code_display), '') is null
      else true
  end;

-- The corrected incident month must reconcile to complete.
select reporting_month, final_laboratory_observations, observations_with_result,
       observations_with_absent_reason, observations_missing_result,
       result_completeness_percent
from mart.lab_result_completeness_monthly
where reporting_month = date '2025-02-01';

-- Demonstrates that the same control blocked before remediation and passed after it.
select q.triggered_by, q.status as gate_status, r.observed_value,
       r.failure_threshold, r.status as check_status
from operational.quality_run q
join operational.quality_result r using (quality_run_id)
where q.triggered_by in ('de006_missing_result', 'de006_corrected_result')
  and r.check_name = 'final_laboratory_observations_missing_result'
order by q.started_at;
