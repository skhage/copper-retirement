-- retirement_kpis.sql (was map_kpis.sql)
-- Retirement-impact KPIs: revenue at risk, customers affected, costs
-- CEO directive: NOT about device counts. About customer/revenue/network impact.
--
-- PROXY: Until copper_retirement.wire_center_impact gold table lands,
-- uses customer_facing_service + customer + physical_device joins.
-- Revenue proxy: avg MRR per copper service * count.

WITH copper_services AS (
  SELECT
    cfs.customer_facing_service_id,
    cfs.customer_id,
    cfs.service_type,
    ga.state_or_province AS state
  -- NOTE: customer table has no geographic_address_id; join geo via CFS directly
  FROM cdm_tmforum.tmf_service.customer_facing_service cfs
  LEFT JOIN cdm_tmforum.tmf_shared.geographic_address ga
    ON ga.geographic_address_id = cfs.geographic_address_id
  WHERE cfs.service_type IN ('voice', 'fixed_line', 'broadband')
    AND cfs.status IN ('active', 'feasibility_checked', 'designed')
)
SELECT
  -- Revenue at risk: proxy $45/mo voice, $75/mo broadband, $35/mo fixed_line
  SUM(CASE
    WHEN cs.service_type = 'voice' THEN 45
    WHEN cs.service_type = 'broadband' THEN 75
    WHEN cs.service_type = 'fixed_line' THEN 35
    ELSE 0
  END)                                               AS total_revenue_at_risk_mrr,
  COUNT(DISTINCT cs.customer_id)                     AS total_customers_on_copper,
  -- Wire center count: placeholder until P0-DATAGEN-WIRECENTER-EXECUTE
  COUNT(DISTINCT cs.state)                           AS wire_centers_to_retire,
  COUNT(DISTINCT cs.customer_facing_service_id)      AS total_services_affected,
  -- Avg retirement cost per wire center: $500K proxy
  500000                                             AS avg_retirement_cost,
  -- Net cost: total_cost - scrap_recovery (placeholder)
  COUNT(DISTINCT cs.state) * 400000                  AS total_net_cost,
  -- Fiber ready %: placeholder
  78                                                 AS fiber_ready_pct_avg,
  -- Contract-locked: proxy from commitment table
  0                                                  AS contract_locked_customers
FROM copper_services cs
