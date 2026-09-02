create or replace view mart.imaging_activity_monthly as
select date_trunc('month', study.started_at)::date as reporting_month,
       count(distinct study.imaging_study_id) as imaging_studies,
       count(distinct study.patient_id) as patients_with_imaging,
       count(series.series_uid) as imaging_series,
       coalesce(sum(series.number_of_instances), 0) as imaging_instances,
       count(distinct series.modality_code) as distinct_modalities
from core.imaging_study study
left join core.imaging_series series on series.imaging_study_id = study.imaging_study_id
group by date_trunc('month', study.started_at)::date;
