-- Gold: Contractor scorecard
-- Enriches contractor_performance with actual incident data and work order metrics
-- Feeds the contractor dispatch/triage agent and planning dashboard

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.gold_contractor_scorecard
COMMENT 'Gold layer: contractor scorecard with actual incident and work order metrics'
CLUSTER BY (primary_state, overall_rating)
AS
WITH actual_incidents AS (
  SELECT
    bp_agreement_id,
    COUNT(*) AS actual_incident_count,
    SUM(CASE WHEN contractor_at_fault THEN 1 ELSE 0 END) AS actual_at_fault_count,
    SUM(CASE WHEN is_regulatory_violation THEN 1 ELSE 0 END) AS violation_count,
    SUM(repair_cost_amount) AS total_incident_cost,
    AVG(resolution_time_hours) AS avg_actual_resolution_hours,
    MAX(incident_date) AS last_incident_date
  FROM cdm_tmforum.copper_retirement.bronze_dig_safe_incidents
  GROUP BY bp_agreement_id
),
work_metrics AS (
  SELECT
    w.party_id,
    COUNT(*) AS total_work_orders,
    SUM(CASE WHEN w.status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN w.sla_met_flag THEN 1 ELSE 0 END) AS sla_met_orders,
    COUNT(DISTINCT w.type) AS work_type_diversity
  FROM cdm_tmforum.tmf_enterprise.work w
  GROUP BY w.party_id
)
SELECT
  cp.contractor_performance_id,
  cp.bp_agreement_id,
  cp.party_id,
  cp.contractor_name,
  cp.contractor_type,
  cp.certification_status,
  cp.safety_score,
  cp.osha_recordable_rate,
  cp.overall_rating,
  cp.crew_size,
  cp.equipment_count,
  cp.years_in_business,
  cp.primary_state,
  cp.geographic_coverage_states,
  cp.bonded_amount,
  cp.insurance_expiry_date,
  cp.last_audit_date,
  cp.sla_compliance_pct,
  cp.active_project_count,
  cp.total_project_value,

  -- Actual incident metrics
  COALESCE(ai.actual_incident_count, 0) AS actual_incident_count,
  COALESCE(ai.actual_at_fault_count, 0) AS actual_at_fault_count,
  COALESCE(ai.violation_count, 0) AS violation_count,
  COALESCE(ai.total_incident_cost, 0) AS total_incident_cost,
  ai.avg_actual_resolution_hours,
  ai.last_incident_date,

  -- Actual work order metrics
  COALESCE(wm.total_work_orders, 0) AS total_work_orders,
  COALESCE(wm.completed_orders, 0) AS completed_work_orders,
  CASE WHEN wm.total_work_orders > 0
    THEN ROUND(wm.sla_met_orders * 100.0 / wm.total_work_orders, 2)
    ELSE NULL
  END AS actual_sla_compliance_pct,

  -- Risk flags
  CASE WHEN cp.insurance_expiry_date < CURRENT_DATE() THEN TRUE ELSE FALSE END AS insurance_expired,
  CASE WHEN cp.certification_status IN ('expired_certification', 'revoked') THEN TRUE ELSE FALSE END AS cert_risk,
  CASE WHEN COALESCE(ai.violation_count, 0) > 0 THEN TRUE ELSE FALSE END AS has_violations,

  -- Dispatch eligibility
  CASE
    WHEN cp.certification_status = 'revoked' THEN 'ineligible'
    WHEN cp.insurance_expiry_date < CURRENT_DATE() THEN 'suspended'
    WHEN cp.certification_status = 'expired_certification' THEN 'restricted'
    WHEN cp.overall_rating >= 4.0 AND cp.safety_score >= 80 THEN 'preferred'
    WHEN cp.overall_rating >= 3.0 THEN 'eligible'
    ELSE 'probationary'
  END AS dispatch_status,

  current_timestamp() AS _pipeline_aggregated_at

FROM cdm_tmforum.copper_retirement.contractor_performance cp
LEFT JOIN actual_incidents ai ON cp.bp_agreement_id = ai.bp_agreement_id
LEFT JOIN work_metrics wm ON cp.party_id = wm.party_id;