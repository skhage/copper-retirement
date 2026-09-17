-- Silver: Copper plant enriched with risk signals
-- Joins copper devices with alarms, service problems, and risk scores
-- Source: bronze_copper_devices + alarms + resource_performance + risk_target

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.silver_copper_plant_enriched (
  CONSTRAINT valid_device_id EXPECT (physical_device_id IS NOT NULL),
  CONSTRAINT valid_state EXPECT (state_code IS NOT NULL)
)
COMMENT 'Silver layer: copper devices enriched with alarm, performance, and risk features'
AS
SELECT
  bcd.physical_device_id,
  bcd.device_type,
  bcd.device_status,
  bcd.serial_number,
  bcd.firmware_version,
  bcd.manufacture_date,
  bcd.installation_date,
  bcd.geographic_address_id,
  bcd.state_code,
  bcd.city,
  bcd.addr_latitude,
  bcd.addr_longitude,
  bcd.addr_h3_res8,
  bcd.addr_h3_res9,

  -- Risk scores from copper_risk_target
  crt.alarm_count,
  crt.critical_alarm_rate,
  crt.service_affecting_rate,
  crt.sla_breach_count,
  crt.sla_breach_rate,
  crt.test_fail_rate,
  crt.problem_count,
  crt.recurring_problem_rate,

  -- Wire center context from spatial join
  cwj.wire_center_id,
  cwj.wire_center_name,
  cwj.clli_code,
  cwj.fiber_ready,
  cwj.annual_retire_priority,
  cwj.puc_filing_required,
  cwj.distance_to_wire_center_km,

  -- Jurisdiction
  cwj.puc_name,
  cwj.puc_short_name,
  cwj.governor_notice_days,
  cwj.puc_notice_days,
  cwj.residential_direct_notice_days,
  cwj.section_214_required,

  -- Computed risk tier
  CASE
    WHEN crt.critical_alarm_rate > 0.3 OR crt.sla_breach_rate > 0.2 THEN 'critical'
    WHEN crt.critical_alarm_rate > 0.15 OR crt.sla_breach_rate > 0.1 THEN 'high'
    WHEN crt.critical_alarm_rate > 0.05 OR crt.sla_breach_rate > 0.05 THEN 'medium'
    ELSE 'low'
  END AS computed_risk_tier,

  current_timestamp() AS _pipeline_processed_at

FROM cdm_tmforum.copper_retirement.bronze_copper_devices bcd
LEFT JOIN cdm_tmforum.copper_retirement.copper_risk_target crt
  ON bcd.physical_device_id = crt.physical_device_id
LEFT JOIN (
  SELECT DISTINCT
    physical_device_id,
    wire_center_id,
    wire_center_name,
    clli_code,
    fiber_ready,
    annual_retire_priority,
    puc_filing_required,
    distance_to_wire_center_km,
    puc_name,
    puc_short_name,
    governor_notice_days,
    puc_notice_days,
    residential_direct_notice_days,
    section_214_required
  FROM cdm_tmforum.copper_retirement.copper_plant_wire_center_jurisdiction
) cwj ON bcd.physical_device_id = cwj.physical_device_id;