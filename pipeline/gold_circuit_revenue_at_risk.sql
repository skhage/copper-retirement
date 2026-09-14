-- Gold: Circuit-level revenue at risk from copper retirement
-- Joins ERP billed circuit rates to copper devices via logical_resource
-- Sources: oracle_erp_source.ra_billed_circuit_rates (56K) → tmf_resource.logical_resource → physical_device (copper)
-- Enriched with geographic, risk tier, wire center, and regulatory context

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.gold_circuit_revenue_at_risk (
  CONSTRAINT valid_circuit EXPECT (circuit_id IS NOT NULL),
  CONSTRAINT valid_device EXPECT (physical_device_id IS NOT NULL),
  CONSTRAINT positive_revenue EXPECT (monthly_unit_price >= 0)
)
COMMENT 'Gold layer: per-circuit revenue at risk from copper retirement — joins ERP billing to copper plant'
CLUSTER BY (device_type)
AS
SELECT
  -- Circuit identifiers
  r.SERVICE_CIRCUIT_ID AS circuit_id,
  r.SOURCE_LINE_ITEM_ID AS source_line_item_id,
  r.SOURCE_CONTRACT_ID AS source_contract_id,

  -- Billing
  r.BILLED_UNIT_PRICE AS monthly_unit_price,
  r.BILLED_TOTAL_AMOUNT AS total_billed_amount,
  r.BILLED_UNIT_PRICE * 12 AS estimated_annual_revenue,

  -- Circuit attributes from logical_resource
  lr.logical_resource_id,
  lr.resource_type AS circuit_resource_type,
  lr.technology_domain,
  lr.bandwidth_mbps,
  lr.operational_state AS circuit_operational_state,
  lr.lifecycle_status AS circuit_lifecycle_status,

  -- Physical device
  pd.physical_device_id,
  pd.device_type,
  pd.status AS device_status,
  pd.serial_number,
  pd.firmware_version,
  pd.installation_date,

  -- Geographic
  ga.state_or_province AS state_code,
  ga.locality AS city,
  ga.latitude,
  ga.longitude,
  ga.h3_res8,
  ga.h3_res9,

  -- Risk context from silver enriched layer
  scp.computed_risk_tier,
  scp.alarm_count,
  scp.critical_alarm_rate,
  scp.sla_breach_rate,
  scp.problem_count,

  -- Wire center context
  scp.wire_center_id,
  scp.wire_center_name,
  scp.clli_code,
  scp.fiber_ready,
  scp.annual_retire_priority,

  -- Regulatory context
  scp.puc_filing_required,
  scp.puc_name,
  scp.governor_notice_days,
  scp.puc_notice_days,
  scp.residential_direct_notice_days,
  scp.section_214_required,

  -- Revenue risk classification
  CASE
    WHEN r.BILLED_UNIT_PRICE >= 10000 THEN 'high_value'
    WHEN r.BILLED_UNIT_PRICE >= 1000 THEN 'medium_value'
    WHEN r.BILLED_UNIT_PRICE >= 100 THEN 'standard'
    ELSE 'low_value'
  END AS revenue_tier,

  -- Combined risk-revenue priority
  CASE
    WHEN scp.computed_risk_tier = 'critical' AND r.BILLED_UNIT_PRICE >= 1000 THEN 'immediate_action'
    WHEN scp.computed_risk_tier = 'critical' OR r.BILLED_UNIT_PRICE >= 10000 THEN 'high_priority'
    WHEN scp.computed_risk_tier = 'high' AND r.BILLED_UNIT_PRICE >= 100 THEN 'elevated'
    ELSE 'monitor'
  END AS action_priority,

  current_timestamp() AS _pipeline_aggregated_at

FROM cdm_tmforum.oracle_erp_source.ra_billed_circuit_rates r
INNER JOIN cdm_tmforum.tmf_resource.logical_resource lr
  ON r.SERVICE_CIRCUIT_ID = lr.logical_resource_id
INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
  ON lr.physical_device_id = pd.physical_device_id
LEFT JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON pd.geographic_address_id = ga.geographic_address_id
LEFT JOIN cdm_tmforum.copper_retirement.silver_copper_plant_enriched scp
  ON pd.physical_device_id = scp.physical_device_id
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel');