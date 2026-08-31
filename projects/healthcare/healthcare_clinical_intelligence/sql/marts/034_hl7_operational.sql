create or replace view mart.hl7_encounter_current_state as
with ranked_event as (
    select event.*,
           row_number() over (
               partition by encounter_id
               order by event_at desc, hl7_encounter_event_id desc
           ) as recency_rank
    from core.hl7_encounter_event event
), ranked_state_event as (
    select event.*,
           row_number() over (
               partition by encounter_id
               order by event_at desc, hl7_encounter_event_id desc
           ) as state_recency_rank
    from core.hl7_encounter_event event
    where event_code <> 'A08'
), encounter_summary as (
    select encounter_id,
           min(event_at) filter (where event_code = 'A01') as admitted_at,
           max(event_at) filter (where event_code = 'A03') as discharged_at,
           count(*) as lifecycle_events
    from core.hl7_encounter_event
    group by encounter_id
)
select latest.encounter_id,
       latest.patient_id,
       latest_state.event_state as current_state,
       latest.patient_class,
       latest.assigned_location as current_location,
       latest.event_at as latest_event_at,
       summary.admitted_at,
       summary.discharged_at,
       summary.lifecycle_events
from ranked_event latest
join encounter_summary summary using (encounter_id)
join ranked_state_event latest_state
  on latest_state.encounter_id = latest.encounter_id
 and latest_state.state_recency_rank = 1
where latest.recency_rank = 1;

create or replace view mart.hl7_order_current_state as
with ranked_order as (
    select order_event.*,
           row_number() over (
               partition by order_id
               order by event_at desc, hl7_order_event_id desc
           ) as recency_rank
    from core.hl7_order_event order_event
)
select order_id,
       patient_id,
       encounter_id,
       order_control,
       order_status,
       code_system,
       code,
       code_display,
       ordered_at,
       message_control_id,
       event_at as latest_event_at
from ranked_order
where recency_rank = 1;
