-- plan_kpis.sql
-- Summary KPIs for the Retirement Plan Tracker.
-- Sources: tmf_enterprise.project (10K), tmf_enterprise.milestone (10K),
--          tmf_enterprise.budget (100K), tmf_enterprise.work (100K, decommission type).
-- TODO: Replace with copper_retirement.migration_tracking once P0-DATAGEN-MIGRATION-EXECUTE runs.

SELECT
  -- Project counts by status (proxy for wire-center plan status)
  count(DISTINCT p.project_id) AS total_projects,
  count(DISTINCT CASE WHEN p.status = 'active' THEN p.project_id END) AS active_projects,
  count(DISTINCT CASE WHEN p.status = 'completed' THEN p.project_id END) AS completed_projects,
  count(DISTINCT CASE WHEN p.status IN ('approved', 'draft') THEN p.project_id END) AS planned_projects,
  count(DISTINCT CASE WHEN p.status IN ('on_hold', 'suspended') THEN p.project_id END) AS blocked_projects,

  -- Budget totals
  sum(p.approved_budget_amount) AS total_budget_approved,
  sum(p.actual_cost_amount) AS total_cost_spent,
  sum(p.approved_budget_amount) - sum(p.actual_cost_amount) AS budget_remaining,

  -- Milestone progress
  count(DISTINCT m.milestone_id) AS total_milestones,
  count(DISTINCT CASE WHEN m.status = 'achieved' THEN m.milestone_id END) AS milestones_achieved,
  count(DISTINCT CASE WHEN m.critical_path_flag = true AND m.status IN ('at_risk', 'missed')
    THEN m.milestone_id END) AS critical_milestones_at_risk,

  -- Decommission work orders
  (
    SELECT count(*)
    FROM cdm_tmforum.tmf_enterprise.work w
    WHERE w.type = 'decommission'
  ) AS decommission_work_orders

FROM cdm_tmforum.tmf_enterprise.project p
LEFT JOIN cdm_tmforum.tmf_enterprise.milestone m ON m.project_id = p.project_id
WHERE p.type IN ('infrastructure_upgrade', 'network_rollout')
