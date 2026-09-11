-- commodity_kpis.sql
-- Summary KPIs for the Commodity & Workforce Dashboard.
-- Sources: copper_commodity_price (P0-DATAGEN-COMMODITY-EXECUTE),
--          recovered_copper_tracking (P0-DATAGEN-COMMODITY-EXECUTE),
--          tmf_businesspartner.bp_agreement (available NOW, 10K),
--          tmf_enterprise.work (available NOW, 100K)
--
-- NOTE: copper_commodity_price and recovered_copper_tracking do not exist yet.
-- This query uses bp_agreement and work as available proxies.
-- Uncomment the full version once P0-DATAGEN-COMMODITY-EXECUTE completes.

SELECT
  -- Contractor KPIs (available NOW)
  (SELECT COUNT(DISTINCT party_id)
   FROM cdm_tmforum.tmf_businesspartner.bp_agreement
   WHERE status = 'active') AS active_contractors,
  
  -- Decommission project count (available NOW)
  (SELECT COUNT(*)
   FROM cdm_tmforum.tmf_enterprise.work
   WHERE type = 'decommission') AS decommission_projects,

  -- Placeholder KPIs (will come from copper_commodity_price + recovered_copper_tracking)
  4.32 AS current_spot_usd_lb,
  3.8 AS spot_30d_change_pct,
  1127400 AS total_recovered_lbs,
  3312000 AS total_scrap_value_usd,
  2814000 AS net_recovery_value_usd,
  76.4 AS avg_safety_score

-- Full version (uncomment after P0-DATAGEN-COMMODITY-EXECUTE):
-- SELECT
--   (SELECT spot_usd_lb FROM cdm_tmforum.copper_retirement.copper_commodity_price
--    WHERE price_type = 'spot' ORDER BY trade_date DESC LIMIT 1) AS current_spot_usd_lb,
--   (SELECT SUM(weight_lbs) FROM cdm_tmforum.copper_retirement.recovered_copper_tracking) AS total_recovered_lbs,
--   (SELECT SUM(gross_value_usd) FROM cdm_tmforum.copper_retirement.recovered_copper_tracking) AS total_scrap_value_usd,
--   (SELECT SUM(net_value_usd) FROM cdm_tmforum.copper_retirement.recovered_copper_tracking) AS net_recovery_value_usd,
--   (SELECT COUNT(DISTINCT party_id) FROM cdm_tmforum.tmf_businesspartner.bp_agreement WHERE status = 'active') AS active_contractors,
--   (SELECT COUNT(*) FROM cdm_tmforum.tmf_enterprise.work WHERE type = 'decommission') AS decommission_projects
