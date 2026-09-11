-- recovery_summary.sql
-- Recovered copper summary by scrap grade and project.
-- Source: cdm_tmforum.copper_retirement.recovered_copper_tracking
--         (pending P0-DATAGEN-COMMODITY-EXECUTE, 5K rows)
--
-- NOTE: Table does not exist yet. Ready for when it lands.

-- SELECT
--   scrap_grade,
--   COUNT(*) AS record_count,
--   SUM(weight_lbs) AS total_weight_lbs,
--   SUM(gross_value_usd) AS total_gross_usd,
--   SUM(net_value_usd) AS total_net_usd,
--   AVG(recovery_efficiency_pct) AS avg_efficiency,
--   MIN(recovery_date) AS earliest_recovery,
--   MAX(recovery_date) AS latest_recovery
-- FROM cdm_tmforum.copper_retirement.recovered_copper_tracking
-- GROUP BY scrap_grade
-- ORDER BY total_net_usd DESC

-- Proxy: decommission work order summary (available NOW)
SELECT
  w.type,
  COUNT(*) AS work_orders,
  COUNT(DISTINCT w.party_id) AS distinct_contractors
FROM cdm_tmforum.tmf_enterprise.work w
WHERE w.type = 'decommission'
GROUP BY w.type
