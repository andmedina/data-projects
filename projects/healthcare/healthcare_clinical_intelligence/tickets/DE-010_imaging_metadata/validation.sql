-- DE-010 validation. Exception queries must return zero rows.

select count(*) as studies,
       count(distinct patient_id) as patients,
       sum(number_of_series) as declared_series,
       sum(number_of_instances) as declared_instances
from core.imaging_study;

select modality_code,
       count(*) as series,
       sum(number_of_instances) as instances
from core.imaging_series
group by modality_code
order by modality_code;

select study.imaging_study_id
from core.imaging_study study
left join core.patient patient on patient.patient_id = study.patient_id
left join core.encounter encounter on encounter.encounter_id = study.encounter_id
where patient.patient_id is null
   or (study.encounter_id is not null and encounter.encounter_id is null);

select study.imaging_study_id
from core.imaging_study study
left join core.imaging_series series on series.imaging_study_id = study.imaging_study_id
group by study.imaging_study_id, study.number_of_series, study.number_of_instances
having study.number_of_series <> count(series.series_uid)
    or study.number_of_instances <> coalesce(sum(series.number_of_instances), 0);

select imaging_study_id, series_uid
from core.imaging_series
where nullif(btrim(modality_code), '') is null;

select study_uid, count(*)
from core.imaging_study
where study_uid is not null
group by study_uid
having count(*) > 1
union all
select series_uid, count(*)
from core.imaging_series
group by series_uid
having count(*) > 1;
