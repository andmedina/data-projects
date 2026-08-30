create or replace view mart.lab_result_completeness_monthly as
with classified as (
    select date_trunc('month', effective_at)::date as reporting_month,
           data_absent_reason_code is not null as has_documented_absent_reason,
           case value_type
               when 'Quantity' then value_numeric is not null
               when 'Integer' then value_numeric is not null
               when 'String' then nullif(btrim(value_text), '') is not null
               when 'Boolean' then value_boolean is not null
               when 'CodeableConcept' then value_code is not null or nullif(btrim(value_code_display), '') is not null
               else false
           end as has_result_value
    from core.observation
    where category_code = 'laboratory'
      and observation_status in ('final', 'amended', 'corrected')
      and effective_at is not null
)
select reporting_month,
       count(*) as final_laboratory_observations,
       count(*) filter (where has_result_value) as observations_with_result,
       count(*) filter (where not has_result_value and has_documented_absent_reason) as observations_with_absent_reason,
       count(*) filter (where not has_result_value and not has_documented_absent_reason) as observations_missing_result,
       round(
           100.0 * count(*) filter (where has_result_value or has_documented_absent_reason) / nullif(count(*), 0),
           2
       ) as result_completeness_percent
from classified
group by reporting_month;
