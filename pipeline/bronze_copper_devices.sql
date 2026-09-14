-- Bronze: Copper devices from physical_device
-- Filters to copper-relevant device types (CPE, ONT, OLT, patch_panel)
-- Source: cdm_tmforum.tmf_enterprise.physical_device (10K rows → ~2,672 copper)

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.bronze_copper_devices
COMMENT 'Bronze layer: copper-relevant physical devices filtered from TMF physical_device'
CLUSTER BY (device_type)
AS
SELECT
  pd.physical_device_id,
  pd.device_type,
  pd.status AS device_status,
  pd.serial_number,
  pd.firmware_version,
  pd.commissioned_date AS manufacture_date,
  pd.installation_date,
  pd.geographic_address_id,
  pd.h3_res8,
  ga.state_or_province AS state_code,
  ga.locality AS city,
  ga.latitude AS addr_latitude,
  ga.longitude AS addr_longitude,
  ga.h3_res8 AS addr_h3_res8,
  ga.h3_res9 AS addr_h3_res9,
  current_timestamp() AS _pipeline_ingested_at
FROM cdm_tmforum.tmf_enterprise.physical_device pd
LEFT JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON pd.geographic_address_id = ga.geographic_address_id
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel');