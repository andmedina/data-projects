-- DE-008 independent validation. Exception queries must return zero rows.

-- Controlled lifecycle state and event count.
select encounter_id,
       patient_id,
       current_state,
       current_location,
       admitted_at,
       discharged_at,
       lifecycle_events
from mart.hl7_encounter_current_state
where encounter_id = 'hl7-visit-001';

-- Controlled ORM order mapping.
select order_id,
       patient_id,
       encounter_id,
       order_control,
       order_status,
       code_system,
       code,
       code_display,
       ordered_at,
       latest_event_at,
       message_control_id
from mart.hl7_order_current_state
where order_id = 'order-001';

-- Lifecycle transitions must follow the controlled state machine.
with timeline as (
    select encounter_id,
           message_control_id,
           event_code,
           lag(event_code) over (
               partition by encounter_id
               order by event_at, hl7_encounter_event_id
           ) as previous_event_code
    from core.hl7_encounter_event
)
select encounter_id, message_control_id, event_code, previous_event_code
from timeline
where (event_code = 'A01' and previous_event_code is not null)
   or (event_code in ('A02', 'A03', 'A08')
       and coalesce(previous_event_code, '') not in ('A01', 'A02', 'A08'))
   or previous_event_code = 'A03';

-- Accepted controlled messages must map to the expected canonical event type.
select message.raw_hl7_message_id,
       message.message_control_id,
       message.message_type
from raw.hl7_message message
where (message.message_type like 'ADT^%'
       and not exists (
           select 1 from core.hl7_encounter_event event
           where event.message_control_id = message.message_control_id
       ))
   or (message.message_type = 'ORM^O01'
       and not exists (
           select 1 from core.hl7_order_event order_event
           where order_event.message_control_id = message.message_control_id
       ))
   or (message.message_type = 'ORU^R01'
       and not exists (
           select 1 from core.hl7_observation observation
           where observation.message_control_id = message.message_control_id
       ));

-- Core rows must retain a raw source message and known patient.
select event.message_control_id
from core.hl7_encounter_event event
left join raw.hl7_message raw_message
  on raw_message.raw_hl7_message_id = event.source_raw_hl7_message_id
left join core.patient patient on patient.patient_id = event.patient_id
where raw_message.raw_hl7_message_id is null or patient.patient_id is null
union all
select order_event.message_control_id
from core.hl7_order_event order_event
left join raw.hl7_message raw_message
  on raw_message.raw_hl7_message_id = order_event.source_raw_hl7_message_id
left join core.patient patient on patient.patient_id = order_event.patient_id
where raw_message.raw_hl7_message_id is null or patient.patient_id is null;
