-- incident_detail.sql
-- Detailed incident view with all joins for the detail panel
-- Requires: P0-DATAGEN-DIGSAFE-EXECUTE
--
-- Parameters:
--   :incident_id  - specific incident ID

SELECT
  dsi.incident_id,
  dsi.incident_date,
  dsi.incident_timestamp,
  dsi.severity,
  dsi.cable_type,
  dsi.cable_damage_type,
  dsi.root_cause,
  dsi.state,
  CAST(dsi.latitude AS DOUBLE)            AS latitude,
  CAST(dsi.longitude AS DOUBLE)           AS longitude,
  dsi.resolution_time_hours,
  dsi.reroute_required,
  dsi.service_interruption,
  dsi.affected_pair_count,
  CAST(dsi.repair_cost_amount AS DOUBLE)  AS repair_cost,
  dsi.contractor_at_fault,
  dsi.one_call_ticket_submitted,
  CAST(dsi.depth_of_cover_inches AS DOUBLE) AS depth_of_cover_inches,
  -- Work order detail
  w.work_id,
  w.type                                  AS work_type,
  w.status                                AS work_status,
  w.priority                              AS work_priority,
  -- Contractor detail
  bpa.bp_agreement_id,
  bpa.type                                AS contractor_type,
  bpa.sla_tier,
  bpa.governing_law_jurisdiction,
  -- Address detail
  ga.street_name,
  ga.city,
  ga.state_or_province,
  ga.postcode,
  -- Network route (if affected)
  nr.network_route_id
FROM cdm_tmforum.tmf_resource.dig_safe_incident dsi
LEFT JOIN cdm_tmforum.tmf_enterprise.work w
  ON w.work_id = dsi.work_id
LEFT JOIN cdm_tmforum.tmf_businesspartner.bp_agreement bpa
  ON bpa.bp_agreement_id = dsi.bp_agreement_id
LEFT JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON ga.geographic_address_id = dsi.geographic_address_id
LEFT JOIN cdm_tmforum.tmf_shared.network_route nr
  ON nr.network_route_id = dsi.network_route_id
WHERE dsi.incident_id = :incident_id
