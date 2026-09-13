-- Silver: Device-to-service impact mapping
-- Links copper devices to customer services via device_service_allocation
-- Critical for retirement impact analysis: which customers lose service when a device retires

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.silver_device_service_impact (
  CONSTRAINT valid_device EXPECT (physical_device_id IS NOT NULL),
  CONSTRAINT valid_service EXPECT (customer_facing_service_id IS NOT NULL)
)
COMMENT 'Silver layer: copper device to customer service impact mapping'
CLUSTER BY (state_code, device_type)
AS
SELECT
  -- Device context
  scpe.physical_device_id,
  scpe.device_type,
  scpe.device_status,
  scpe.state_code,
  scpe.wire_center_id,
  scpe.wire_center_name,
  scpe.computed_risk_tier,
  scpe.addr_h3_res8,

  -- Allocation details
  dsa.device_service_allocation_id,
  dsa.allocation_status,
  dsa.criticality_level,
  dsa.service_role,

  -- Service details
  bcs.customer_facing_service_id,
  bcs.service_type,
  bcs.service_status,
  bcs.customer_id,
  bcs.customer_name,
  bcs.customer_segment,

  -- Impact metrics
  CASE
    WHEN bcs.service_type = 'voice' THEN 'voice_disruption'
    WHEN bcs.service_type = 'broadband' THEN 'data_disruption'
    WHEN bcs.service_type = 'fixed_line' THEN 'line_disruption'
    ELSE 'unknown_impact'
  END AS impact_category,

  current_timestamp() AS _pipeline_processed_at

FROM cdm_tmforum.copper_retirement.silver_copper_plant_enriched scpe
INNER JOIN cdm_tmforum.tmf_resource.device_service_allocation dsa
  ON scpe.physical_device_id = dsa.physical_device_id
INNER JOIN cdm_tmforum.copper_retirement.bronze_copper_services bcs
  ON dsa.service_id = bcs.customer_facing_service_id;