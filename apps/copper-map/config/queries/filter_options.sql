-- filter_options.sql
-- Distinct values for filter panel dropdowns
-- Returns one row per unique combination of filter dimension

SELECT
  'state' AS filter_type,
  ga.state_or_province AS filter_value,
  COUNT(DISTINCT pd.physical_device_id) AS device_count
FROM cdm_tmforum.tmf_enterprise.physical_device pd
INNER JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON ga.geographic_address_id = pd.geographic_address_id
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  AND ga.state_or_province IS NOT NULL
GROUP BY ga.state_or_province

UNION ALL

SELECT
  'device_type' AS filter_type,
  pd.device_type AS filter_value,
  COUNT(DISTINCT pd.physical_device_id) AS device_count
FROM cdm_tmforum.tmf_enterprise.physical_device pd
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
GROUP BY pd.device_type

UNION ALL

SELECT
  'risk_tier' AS filter_type,
  tier.name AS filter_value,
  0 AS device_count  -- TODO: Real counts when P4-RISK lands
FROM (SELECT 'critical' AS name UNION ALL SELECT 'high' UNION ALL SELECT 'medium' UNION ALL SELECT 'low') tier

ORDER BY filter_type, device_count DESC
