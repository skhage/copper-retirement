-- milestone_timeline.sql
-- Milestones for wire-center detail panel with regulatory/critical path flags.
-- Parameterized by project_id (wire_center_id).

SELECT
  m.milestone_id,
  m.project_id AS wire_center_id,
  m.name,
  m.type,
  m.status,
  m.priority,
  m.planned_date,
  m.actual_date,
  m.forecast_date,
  m.completion_percentage,
  m.critical_path_flag,
  m.regulatory_requirement_flag,
  m.contractual_obligation_flag,
  m.payment_trigger_flag,
  m.risk_level,
  m.risk_description,
  m.variance_days,
  m.project_phase
FROM cdm_tmforum.tmf_enterprise.milestone m
WHERE m.project_id = :wire_center_id
ORDER BY m.planned_date
