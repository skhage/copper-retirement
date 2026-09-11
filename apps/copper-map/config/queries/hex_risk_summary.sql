-- wire_center_impact.sql (was hex_risk_summary.sql)
-- Wire center retirement impact summary for the map.
-- CEO directive: show customer, revenue, and network impact per area.
--
-- BLOCKED: Requires copper_retirement.wire_center_impact gold table
-- (depends on P0-DATAGEN-WIRECENTER-EXECUTE + P2-H3 + P4-RISK).
--
-- PROXY: Uses geographic_address H3 + physical_device + customer_facing_service
-- to compute per-H3-cell retirement impact.
--
-- Parameters:
--   :state_filter    - state abbreviation or '' for all
--   :priority_tier   - 'retire-now'|'plan-next'|'evaluate'|'defer' or '' for all

WITH device_locations AS (
  SELECT
    ga.h3_index                                      AS h3_cell,
    AVG(CAST(ga.latitude AS DOUBLE))                 AS center_lat,
    AVG(CAST(ga.longitude AS DOUBLE))                AS center_lon,
    ga.state_or_province                             AS state,
    COUNT(DISTINCT pd.physical_device_id)            AS copper_devices,
    COUNT(DISTINCT a.alarm_id)                       AS active_alarms
  FROM cdm_tmforum.tmf_shared.geographic_address ga
  INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
    ON pd.geographic_address_id = ga.geographic_address_id
    AND pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  LEFT JOIN cdm_tmforum.tmf_resource.alarm a
    ON a.physical_resource_id = pd.physical_device_id
  WHERE ga.h3_index IS NOT NULL
    AND (:state_filter = '' OR ga.state_or_province = :state_filter)
  GROUP BY ga.h3_index, ga.state_or_province
),
service_impact AS (
  -- Count customers and services per state (proxy for wire center)
  SELECT
    c.geographic_address_id,
    COUNT(DISTINCT c.customer_id) AS customers_affected,
    COUNT(DISTINCT cfs.customer_facing_service_id) AS services_affected,
    SUM(CASE
      WHEN cfs.service_type = 'voice' THEN 45
      WHEN cfs.service_type = 'broadband' THEN 75
      WHEN cfs.service_type = 'fixed_line' THEN 35
      ELSE 0
    END) AS revenue_at_risk_mrr
  FROM cdm_tmforum.tmf_customer.customer c
  INNER JOIN cdm_tmforum.tmf_service.customer_facing_service cfs
    ON cfs.customer_id = c.customer_id
    AND cfs.service_type IN ('voice', 'fixed_line', 'broadband')
    AND cfs.status = 'active'
  GROUP BY c.geographic_address_id
)
SELECT
  dl.h3_cell,
  dl.center_lat,
  dl.center_lon,
  dl.state,
  dl.copper_devices,
  dl.active_alarms,
  COALESCE(SUM(si.customers_affected), 0) AS customers_affected,
  COALESCE(SUM(si.services_affected), 0) AS services_affected,
  COALESCE(SUM(si.revenue_at_risk_mrr), 0) AS revenue_at_risk_mrr,
  -- Network disruption proxy: alarm density normalized
  LEAST(100, ROUND(dl.active_alarms * 100.0 / NULLIF(dl.copper_devices, 0) / 3.0)) AS network_disruption_score,
  -- Retirement priority: composite of fiber readiness, low disruption, high value
  -- TODO: Replace with P4-RISK model output
  50 AS retirement_priority,
  'evaluate' AS priority_tier
FROM device_locations dl
LEFT JOIN cdm_tmforum.tmf_shared.geographic_address ga2
  ON ga2.h3_index = dl.h3_cell
LEFT JOIN service_impact si
  ON si.geographic_address_id = ga2.geographic_address_id
GROUP BY dl.h3_cell, dl.center_lat, dl.center_lon, dl.state, dl.copper_devices, dl.active_alarms
ORDER BY revenue_at_risk_mrr DESC
LIMIT 500
