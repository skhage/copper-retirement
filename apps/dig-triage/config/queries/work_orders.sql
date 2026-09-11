-- work_orders.sql
-- Repair/emergency work orders linked to triage incidents
-- Available NOW (22K rows, no dependency on dig_safe_incident)
--
-- Parameters:
--   :work_status_filter  - 'dispatched'|'in_progress'|'completed' or '' for all
--   :work_type_filter    - 'repair'|'emergency' or '' for all

SELECT
  w.work_id,
  w.type                        AS work_type,
  w.status                      AS work_status,
  w.category                    AS work_category,
  w.priority,
  w.scheduled_start_date,
  w.scheduled_end_date,
  w.actual_start_date,
  w.actual_end_date,
  w.party_id                    AS contractor_party_id,
  bpa.type                      AS contractor_type,
  bpa.status                    AS contractor_status,
  bpa.sla_tier
FROM cdm_tmforum.tmf_enterprise.work w
LEFT JOIN cdm_tmforum.tmf_businesspartner.bp_agreement bpa
  ON bpa.party_id = w.party_id
  AND bpa.status = 'active'
WHERE w.type IN ('repair', 'emergency')
  AND (:work_status_filter = '' OR w.status = :work_status_filter)
  AND (:work_type_filter = '' OR w.type = :work_type_filter)
ORDER BY w.scheduled_start_date DESC
LIMIT 100
