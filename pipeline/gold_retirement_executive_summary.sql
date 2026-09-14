-- Gold: Copper retirement executive summary
-- Top-level KPIs for executive dashboard and reporting
-- One row per state with aggregated retirement program metrics

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.gold_retirement_executive_summary
COMMENT 'Gold layer: per-state executive summary of copper retirement program'
CLUSTER BY (state_code)
AS
WITH device_summary AS (
  -- Use ML model predictions for risk tiers (4-tier: low/medium/high/critical)
  -- silver_copper_plant_enriched.computed_risk_tier only has binary rates → 2 tiers
  SELECT
    scp.state_code,
    COUNT(*) AS total_copper_devices,
    SUM(CASE WHEN scp.device_status = 'active' THEN 1 ELSE 0 END) AS active_devices,
    SUM(CASE WHEN grp.risk_tier_predicted = 'critical' THEN 1 ELSE 0 END) AS critical_risk_count,
    SUM(CASE WHEN grp.risk_tier_predicted = 'high' THEN 1 ELSE 0 END) AS high_risk_count,
    COUNT(DISTINCT scp.wire_center_id) AS wire_center_count,
    SUM(CASE WHEN scp.fiber_ready THEN 1 ELSE 0 END) AS fiber_ready_devices
  FROM cdm_tmforum.copper_retirement.silver_copper_plant_enriched scp
  LEFT JOIN cdm_tmforum.copper_retirement.gold_device_risk_predictions grp
    ON scp.physical_device_id = grp.physical_device_id
  GROUP BY scp.state_code
),
service_summary AS (
  SELECT
    state_code,
    COUNT(DISTINCT customer_facing_service_id) AS total_affected_services,
    COUNT(DISTINCT customer_id) AS total_affected_customers,
    COUNT(DISTINCT CASE WHEN service_type = 'voice' THEN customer_facing_service_id END) AS voice_count,
    COUNT(DISTINCT CASE WHEN service_type = 'broadband' THEN customer_facing_service_id END) AS broadband_count
  FROM cdm_tmforum.copper_retirement.silver_device_service_impact
  GROUP BY state_code
),
incident_summary AS (
  SELECT
    state,
    COUNT(*) AS total_incidents,
    SUM(CASE WHEN is_regulatory_violation THEN 1 ELSE 0 END) AS total_violations,
    SUM(repair_cost_amount) AS total_repair_cost,
    AVG(resolution_time_hours) AS avg_resolution_hours
  FROM cdm_tmforum.copper_retirement.bronze_dig_safe_incidents
  GROUP BY state
),
contractor_summary AS (
  SELECT
    primary_state,
    COUNT(*) AS available_contractors,
    AVG(overall_rating) AS avg_contractor_rating,
    SUM(crew_size) AS total_crew_capacity,
    SUM(CASE WHEN dispatch_status = 'preferred' THEN 1 ELSE 0 END) AS preferred_contractors,
    SUM(CASE WHEN dispatch_status = 'ineligible' THEN 1 ELSE 0 END) AS ineligible_contractors
  FROM cdm_tmforum.copper_retirement.gold_contractor_scorecard
  GROUP BY primary_state
)
SELECT
  ds.state_code,
  ds.total_copper_devices,
  ds.active_devices,
  ds.critical_risk_count,
  ds.high_risk_count,
  ds.wire_center_count,
  ds.fiber_ready_devices,
  ROUND(ds.fiber_ready_devices * 100.0 / NULLIF(ds.total_copper_devices, 0), 1) AS fiber_ready_pct,

  COALESCE(ss.total_affected_services, 0) AS total_affected_services,
  COALESCE(ss.total_affected_customers, 0) AS total_affected_customers,
  COALESCE(ss.voice_count, 0) AS voice_services_at_risk,
  COALESCE(ss.broadband_count, 0) AS broadband_services_at_risk,

  COALESCE(ins.total_incidents, 0) AS total_dig_incidents,
  COALESCE(ins.total_violations, 0) AS regulatory_violations,
  COALESCE(ins.total_repair_cost, 0) AS total_repair_cost,
  ins.avg_resolution_hours,

  COALESCE(cs.available_contractors, 0) AS available_contractors,
  cs.avg_contractor_rating,
  COALESCE(cs.total_crew_capacity, 0) AS total_crew_capacity,
  COALESCE(cs.preferred_contractors, 0) AS preferred_contractors,

  -- Program health indicator (considers critical + high risk devices)
  CASE
    WHEN (ds.critical_risk_count + ds.high_risk_count) > ds.total_copper_devices * 0.5 THEN 'red'
    WHEN (ds.critical_risk_count + ds.high_risk_count) > ds.total_copper_devices * 0.3 THEN 'amber'
    ELSE 'green'
  END AS program_health_status,

  current_timestamp() AS _pipeline_aggregated_at

FROM device_summary ds
LEFT JOIN service_summary ss ON ds.state_code = ss.state_code
LEFT JOIN incident_summary ins ON ds.state_code = ins.state
LEFT JOIN contractor_summary cs ON ds.state_code = cs.primary_state;