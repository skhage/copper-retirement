-- wave_schedule.sql
-- Wire-center retirement wave schedule for the Gantt timeline.
-- TODO: Replace with copper_retirement.migration_tracking + P4-SEQ optimizer output
--       once those tables exist.
-- Currently: Uses tmf_enterprise.project with type='infrastructure_upgrade' as proxy.

SELECT
  p.project_id AS wire_center_id,
  p.name AS wire_center_name,
  p.status,
  p.priority,
  p.risk_level,
  p.planned_start_date,
  p.planned_end_date,
  p.actual_start_date,
  p.actual_end_date,
  p.approved_budget_amount AS migration_cost_usd,
  p.actual_cost_amount,
  p.completion_percentage,
  -- Milestone counts per project
  count(DISTINCT m.milestone_id) AS milestone_count,
  count(DISTINCT CASE WHEN m.status = 'achieved' THEN m.milestone_id END) AS milestones_achieved,
  count(DISTINCT CASE WHEN m.critical_path_flag = true THEN m.milestone_id END) AS critical_milestones,
  count(DISTINCT CASE WHEN m.regulatory_requirement_flag = true THEN m.milestone_id END) AS regulatory_milestones
FROM cdm_tmforum.tmf_enterprise.project p
LEFT JOIN cdm_tmforum.tmf_enterprise.milestone m ON m.project_id = p.project_id
WHERE p.type IN ('infrastructure_upgrade', 'network_rollout')
GROUP BY
  p.project_id, p.name, p.status, p.priority, p.risk_level,
  p.planned_start_date, p.planned_end_date,
  p.actual_start_date, p.actual_end_date,
  p.approved_budget_amount, p.actual_cost_amount, p.completion_percentage
ORDER BY p.planned_start_date
