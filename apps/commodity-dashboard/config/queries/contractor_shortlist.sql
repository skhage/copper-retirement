-- contractor_shortlist.sql
-- Contractor performance shortlist for assignment.
-- Sources: cdm_tmforum.copper_retirement.contractor_performance
--          (pending P0-DATAGEN-CONTRACTOR-EXECUTE, 10K rows)
--          tmf_businesspartner.bp_agreement (available NOW, 10K)
--
-- NOTE: contractor_performance does not exist yet.
-- Uses bp_agreement + work as available proxy.

-- Full version (uncomment after P0-DATAGEN-CONTRACTOR-EXECUTE):
-- SELECT
--   cp.contractor_performance_id,
--   bp.name AS contractor_name,
--   cp.contractor_type,
--   cp.safety_score,
--   cp.osha_recordable_rate,
--   cp.sla_met_pct,
--   cp.completion_rate_pct,
--   cp.incident_count,
--   cp.overall_rating,
--   cp.geographic_coverage_h3,
--   bp.status AS agreement_status,
--   bp.sla_tier
-- FROM cdm_tmforum.copper_retirement.contractor_performance cp
-- JOIN cdm_tmforum.tmf_businesspartner.bp_agreement bp
--   ON cp.bp_agreement_id = bp.bp_agreement_id
-- WHERE bp.status = 'active'
-- ORDER BY cp.overall_rating DESC
-- LIMIT 50

-- Proxy: active contractors with work order volume (available NOW)
SELECT
  bp.bp_agreement_id,
  bp.name AS contractor_name,
  bp.type AS agreement_type,
  bp.status,
  bp.sla_tier,
  COUNT(w.work_id) AS total_work_orders,
  SUM(CASE WHEN w.type = 'decommission' THEN 1 ELSE 0 END) AS decom_work_orders
FROM cdm_tmforum.tmf_businesspartner.bp_agreement bp
LEFT JOIN cdm_tmforum.tmf_enterprise.work w
  ON bp.party_id = w.party_id
WHERE bp.status = 'active'
GROUP BY bp.bp_agreement_id, bp.name, bp.type, bp.status, bp.sla_tier
ORDER BY total_work_orders DESC
LIMIT 50
