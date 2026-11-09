-- Silver: Copper plant enriched with risk signals
-- Joins copper devices with alarms, service problems, and risk scores
-- Source: bronze_copper_devices + alarms + resource_performance + risk_target

CREATE OR REFRESH MATERIALIZED VIEW silver_copper_plant_enriched (
  CONSTRAINT valid_device_id EXPECT (physical_device_id IS NOT NULL),
  CONSTRAINT valid_state EXPECT (state_code IS NOT NULL)
)
COMMENT 'DERIVED FROM SYNTHETIC DATA — Silver layer: copper devices enriched with alarm, performance, and risk features'
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
  -- Notice periods are REAL cited values from jurisdiction_requirements_cited (ACC-DE-DEF-SYNTH-NOTICE-LINEAGE, 2026-11-04).
  -- The old synthetic values from copper_plant_wire_center_jurisdiction are no longer used. NULL = UNKNOWN (never inferred).
  CAST(NULL AS BIGINT) AS governor_notice_days,           -- no cited governor-notice requirement exists: UNKNOWN
  jrs.notice_days AS puc_notice_days,                     -- state_discontinuance_notice (state PUC rule/statute)
  jrs.citation_url AS puc_notice_citation_url,
  jru.notice_days AS residential_direct_notice_days,      -- US copper_retirement_notice (47 CFR Part 51 Subpart D)
  jru.citation_url AS residential_notice_citation_url,
  cwj.section_214_required,

  -- Computed risk tier
  CASE
    WHEN crt.critical_alarm_rate > 0.3 OR crt.sla_breach_rate > 0.2 THEN 'critical'
    WHEN crt.critical_alarm_rate > 0.15 OR crt.sla_breach_rate > 0.1 THEN 'high'
    WHEN crt.critical_alarm_rate > 0.05 OR crt.sla_breach_rate > 0.05 THEN 'medium'
    ELSE 'low'
  END AS computed_risk_tier,

  current_timestamp() AS _pipeline_processed_at

FROM bronze_copper_devices bcd
LEFT JOIN copper_risk_target crt
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
    section_214_required
  FROM copper_plant_wire_center_jurisdiction
) cwj ON bcd.physical_device_id = cwj.physical_device_id
-- Cited state notice period: one verified row per state, else NULL (conflicting or missing rows = UNKNOWN, no fan-out)
-- MN (ACC-DE-MN-PUC-NOTICE-SEMANTIC-1106): the 60 days in Minn. Stat. 237.181 subd. 3(3) is advance written notice of the
-- PUC public meeting, NOT a filing lead time before discontinuance, so puc_notice_days is NULL (UNKNOWN) for MN.
-- The citation URL is still carried so users can read the statute (https://www.revisor.mn.gov/statutes/cite/237.181).
LEFT JOIN (
  SELECT jurisdiction_code,
         CAST(min(CASE WHEN requirement_key = 'MN|state_discontinuance_notice|MN-PUC-237.181' THEN NULL
                       ELSE value_numeric END) AS BIGINT) AS notice_days,
         min(citation_url) AS citation_url
  FROM jurisdiction_requirements_cited
  WHERE requirement_type = 'state_discontinuance_notice'
    AND verification_status <> 'UNVERIFIED'
  GROUP BY jurisdiction_code
  HAVING count(*) = 1
) jrs ON jrs.jurisdiction_code = bcd.state_code
-- Cited federal copper retirement notice (applies in all states)
LEFT JOIN (
  SELECT CAST(min(value_numeric) AS BIGINT) AS notice_days,
         min(citation_url) AS citation_url
  FROM jurisdiction_requirements_cited
  WHERE jurisdiction_code = 'US'
    AND requirement_type = 'copper_retirement_notice'
    AND verification_status <> 'UNVERIFIED'
  HAVING count(*) = 1
) jru ON TRUE;