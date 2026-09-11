-- migration_status.sql
-- Migration status breakdown for KPIs and summary charts.
-- Sources: tmf_enterprise.work (decommission orders), tmf_enterprise.workforce_employee_pool (crew capacity).
-- TODO: Replace with copper_retirement.migration_tracking once P0-DATAGEN-MIGRATION-EXECUTE runs.

SELECT
  -- Decommission work order status
  w.status AS migration_status,
  count(*) AS order_count,
  -- Crew capacity summary
  (
    SELECT count(DISTINCT pool_id)
    FROM cdm_tmforum.tmf_enterprise.workforce_employee_pool
    WHERE status = 'active'
  ) AS active_crew_pools,
  (
    SELECT count(DISTINCT employee_id)
    FROM cdm_tmforum.tmf_enterprise.workforce_employee_assignment
    WHERE status = 'active'
  ) AS active_crew_members
FROM cdm_tmforum.tmf_enterprise.work w
WHERE w.type = 'decommission'
GROUP BY w.status
ORDER BY order_count DESC
