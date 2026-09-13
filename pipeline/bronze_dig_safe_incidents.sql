-- Bronze: Dig-safe incidents
-- Source: cdm_tmforum.copper_retirement.dig_safe_incident (5K rows)

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.bronze_dig_safe_incidents
COMMENT 'Bronze layer: dig-safe incident registry with contractor enrichment'
CLUSTER BY (state, severity)
AS
SELECT
  dsi.incident_id,
  dsi.work_id,
  dsi.bp_agreement_id,
  dsi.geographic_address_id,
  dsi.network_route_id,
  dsi.state,
  dsi.latitude,
  dsi.longitude,
  dsi.incident_date,
  dsi.incident_timestamp,
  dsi.severity,
  dsi.cable_type,
  dsi.cable_damage_type,
  dsi.root_cause,
  dsi.contractor_at_fault,
  dsi.one_call_ticket_submitted,
  dsi.resolution_time_hours,
  dsi.reroute_required,
  dsi.service_interruption,
  dsi.affected_pair_count,
  dsi.repair_cost_amount,
  dsi.depth_of_cover_inches,
  cp.contractor_name,
  cp.contractor_type,
  cp.safety_score AS contractor_safety_score,
  cp.overall_rating AS contractor_overall_rating,
  CASE
    WHEN dsi.contractor_at_fault AND NOT dsi.one_call_ticket_submitted THEN TRUE
    ELSE FALSE
  END AS is_regulatory_violation,
  current_timestamp() AS _pipeline_ingested_at
FROM cdm_tmforum.copper_retirement.dig_safe_incident dsi
LEFT JOIN cdm_tmforum.copper_retirement.contractor_performance cp
  ON dsi.bp_agreement_id = cp.bp_agreement_id;