-- Gold: Wire center retirement scorecard
-- Aggregates copper plant metrics per wire center for retirement planning
-- Primary dashboard data source for the copper retirement planning app

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.gold_wire_center_scorecard
COMMENT 'Gold layer: per-wire-center retirement readiness scorecard'
CLUSTER BY (state_code)
AS
WITH device_metrics AS (
  SELECT
    wire_center_id,
    wire_center_name,
    clli_code,
    state_code,
    fiber_ready,
    puc_filing_required,
    annual_retire_priority,
    puc_name,
    section_214_required,
    governor_notice_days,
    puc_notice_days,
    residential_direct_notice_days,
    COUNT(*) AS copper_device_count,
    COUNT(DISTINCT device_type) AS device_type_count,
    SUM(CASE WHEN device_status = 'active' THEN 1 ELSE 0 END) AS active_device_count,
    AVG(alarm_count) AS avg_alarm_count,
    AVG(critical_alarm_rate) AS avg_critical_alarm_rate,
    AVG(sla_breach_rate) AS avg_sla_breach_rate,
    SUM(CASE WHEN computed_risk_tier = 'critical' THEN 1 ELSE 0 END) AS critical_risk_devices,
    SUM(CASE WHEN computed_risk_tier = 'high' THEN 1 ELSE 0 END) AS high_risk_devices,
    AVG(distance_to_wire_center_km) AS avg_distance_km,
    MIN(addr_latitude) AS bbox_min_lat,
    MAX(addr_latitude) AS bbox_max_lat,
    MIN(addr_longitude) AS bbox_min_lon,
    MAX(addr_longitude) AS bbox_max_lon
  FROM cdm_tmforum.copper_retirement.silver_copper_plant_enriched
  WHERE wire_center_id IS NOT NULL
  GROUP BY
    wire_center_id, wire_center_name, clli_code, state_code,
    fiber_ready, puc_filing_required, annual_retire_priority,
    puc_name, section_214_required, governor_notice_days,
    puc_notice_days, residential_direct_notice_days
),
service_impact AS (
  SELECT
    wire_center_id,
    COUNT(DISTINCT customer_facing_service_id) AS affected_service_count,
    COUNT(DISTINCT customer_id) AS affected_customer_count,
    COUNT(DISTINCT CASE WHEN service_type = 'voice' THEN customer_facing_service_id END) AS voice_services,
    COUNT(DISTINCT CASE WHEN service_type = 'broadband' THEN customer_facing_service_id END) AS broadband_services,
    COUNT(DISTINCT CASE WHEN service_type = 'fixed_line' THEN customer_facing_service_id END) AS fixed_line_services
  FROM cdm_tmforum.copper_retirement.silver_device_service_impact
  GROUP BY wire_center_id
),
incident_metrics AS (
  SELECT
    ga.h3_res8,
    COUNT(*) AS incident_count,
    SUM(CASE WHEN dsi.is_regulatory_violation THEN 1 ELSE 0 END) AS violation_count,
    SUM(dsi.repair_cost_amount) AS total_repair_cost,
    AVG(dsi.resolution_time_hours) AS avg_resolution_hours
  FROM cdm_tmforum.copper_retirement.bronze_dig_safe_incidents dsi
  LEFT JOIN cdm_tmforum.tmf_shared.geographic_address ga
    ON dsi.geographic_address_id = ga.geographic_address_id
  GROUP BY ga.h3_res8
)
SELECT
  dm.*,
  COALESCE(si.affected_service_count, 0) AS affected_service_count,
  COALESCE(si.affected_customer_count, 0) AS affected_customer_count,
  COALESCE(si.voice_services, 0) AS voice_services,
  COALESCE(si.broadband_services, 0) AS broadband_services,
  COALESCE(si.fixed_line_services, 0) AS fixed_line_services,

  -- Retirement readiness score (0-100)
  ROUND(
    (CASE WHEN dm.fiber_ready THEN 30 ELSE 0 END) +
    (CASE WHEN dm.critical_risk_devices > 3 THEN 20 ELSE dm.critical_risk_devices * 5 END) +
    (CASE WHEN dm.avg_critical_alarm_rate > 0.2 THEN 20 ELSE dm.avg_critical_alarm_rate * 100 END) +
    (CASE WHEN dm.annual_retire_priority <= 3 THEN 15 ELSE 5 END) +
    (CASE WHEN COALESCE(si.affected_customer_count, 0) < 50 THEN 15 ELSE 5 END)
  , 1) AS retirement_readiness_score,

  RANK() OVER (
    ORDER BY dm.annual_retire_priority ASC,
    dm.critical_risk_devices DESC,
    dm.avg_critical_alarm_rate DESC
  ) AS retirement_priority_rank,

  current_timestamp() AS _pipeline_aggregated_at

FROM device_metrics dm
LEFT JOIN service_impact si ON dm.wire_center_id = si.wire_center_id;