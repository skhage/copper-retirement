-- cost_benefit.sql
-- Per-wire-center cost/benefit analysis.
-- Sources: tmf_enterprise.project (budget), tmf_enterprise.budget (detail),
--          tmf_enterprise.work (decommission labor costs).
-- TODO: Add gold_circuit_revenue_at_risk from P3-DLP-REVENUE for revenue-at-risk MRR.
-- TODO: Add recovered_copper_tracking from P0-DATAGEN-COMMODITY-EXECUTE for scrap recovery.

SELECT
  p.project_id AS wire_center_id,
  p.name AS wire_center_name,
  p.approved_budget_amount AS budget_allocated,
  p.actual_cost_amount AS cost_spent,
  p.approved_budget_amount - p.actual_cost_amount AS budget_remaining,
  p.forecast_cost_amount AS forecast_total_cost,
  p.cost_variance_amount,
  p.expected_roi_percentage,
  -- Budget line items
  count(DISTINCT b.budget_id) AS budget_line_count,
  sum(b.allocated_amount) AS total_budget_lines,
  -- Decommission work orders for this project
  (
    SELECT count(*)
    FROM cdm_tmforum.tmf_enterprise.work w
    WHERE w.type = 'decommission'
      AND w.party_id = p.party_id
  ) AS decommission_work_count
FROM cdm_tmforum.tmf_enterprise.project p
LEFT JOIN cdm_tmforum.tmf_enterprise.budget b ON b.project_id = p.project_id
WHERE p.project_id = :wire_center_id
GROUP BY
  p.project_id, p.name, p.approved_budget_amount, p.actual_cost_amount,
  p.forecast_cost_amount, p.cost_variance_amount, p.expected_roi_percentage, p.party_id
