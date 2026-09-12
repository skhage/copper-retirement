-- device_detail.sql
-- Per-device detail for a selected H3 hex cell or state filter
-- This query works NOW with empty h3_cell param; h3_cell filtering requires P2-H3
--
-- Parameters:
--   :h3_cell      - H3 cell index or '' for all
--   :state_filter  - state abbreviation or '' for all
--   :device_type   - 'cpe'|'ont'|'olt'|'patch_panel' or '' for all

SELECT
  pd.physical_device_id                             AS device_id,
  pd.device_type,
  pd.serial_number,
  pd.status                                         AS device_status,
  pd.installation_date,
  CAST(ga.latitude AS DOUBLE)                       AS latitude,
  CAST(ga.longitude AS DOUBLE)                      AS longitude,
  ga.state_or_province                              AS state,
  ga.locality                         AS city,
  -- Alarm counts per device
  COUNT(DISTINCT a.alarm_id)                        AS alarm_count,
  SUM(CASE WHEN a.perceived_severity = 'critical' THEN 1 ELSE 0 END) AS critical_alarms,
  SUM(CASE WHEN a.perceived_severity = 'major' THEN 1 ELSE 0 END)    AS major_alarms,
  -- TODO: Add risk_score from gold table when P4-RISK lands
  -- rs.risk_score,
  50.0                                              AS risk_score
FROM cdm_tmforum.tmf_enterprise.physical_device pd
INNER JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON ga.geographic_address_id = pd.geographic_address_id
LEFT JOIN cdm_tmforum.tmf_resource.alarm a
  ON a.physical_resource_id = pd.physical_device_id
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  AND (:h3_cell = '' OR ga.h3_res9 = CAST(:h3_cell AS BIGINT))
  AND (:state_filter = '' OR ga.state_or_province = :state_filter)
  AND (:device_type = '' OR pd.device_type = :device_type)
GROUP BY
  pd.physical_device_id, pd.device_type, pd.serial_number,
  pd.status, pd.installation_date,
  ga.latitude, ga.longitude, ga.state_or_province, ga.locality
ORDER BY critical_alarms DESC, alarm_count DESC
LIMIT 100
