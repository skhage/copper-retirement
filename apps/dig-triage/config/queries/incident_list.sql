-- incident_list.sql
-- Dig-safe incident list for the triage console
-- Requires: P0-DATAGEN-DIGSAFE-EXECUTE (dig_safe_incident table)
--
-- Parameters:
--   :severity_filter  - 'critical'|'major'|'minor'|'informational' or '' for all
--   :state_filter     - state abbreviation or '' for all
--   :status_filter    - 'open'|'in_progress'|'resolved' or '' for all

SELECT
  dsi.incident_id,
  dsi.incident_date,
  dsi.incident_timestamp,
  dsi.severity,
  dsi.cable_type,
  dsi.cable_damage_type,
  dsi.root_cause,
  dsi.state,
  CAST(dsi.latitude AS DOUBLE)          AS latitude,
  CAST(dsi.longitude AS DOUBLE)         AS longitude,
  dsi.resolution_time_hours,
  dsi.reroute_required,
  dsi.service_interruption,
  dsi.affected_pair_count,
  CAST(dsi.repair_cost_amount AS DOUBLE) AS repair_cost,
  dsi.contractor_at_fault,
  dsi.one_call_ticket_submitted,
  w.type                                AS work_type,
  w.status                              AS work_status,
  w.category                            AS work_category,
  bpa.type                              AS contractor_type,
  bpa.status                            AS contractor_status
FROM cdm_tmforum.tmf_resource.dig_safe_incident dsi
LEFT JOIN cdm_tmforum.tmf_enterprise.work w
  ON w.work_id = dsi.work_id
LEFT JOIN cdm_tmforum.tmf_businesspartner.bp_agreement bpa
  ON bpa.bp_agreement_id = dsi.bp_agreement_id
WHERE (:severity_filter = '' OR dsi.severity = :severity_filter)
  AND (:state_filter = '' OR dsi.state = :state_filter)
ORDER BY dsi.incident_timestamp DESC
LIMIT 200
