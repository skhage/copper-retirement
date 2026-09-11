-- policy_rules.sql
-- Fetch regulatory policies and their rules for the compliance checklist
-- and jurisdiction table. Source: cdm_tmforum.tmf_marketsales.policy (10K)
-- + policy_rule (100K). Per @pm REVIEW-UNDERUTILIZED: these 110K rows of
-- executable regulatory rules are the biggest untapped opportunity.
--
-- NOTE: Pending @data-analyst PROFILE-POLICY-RULES results to determine
-- whether rule content is meaningful or all synthetic hashes.

SELECT
  p.policy_id,
  p.name                AS policy_name,
  p.type                AS policy_type,
  p.status              AS policy_status,
  p.geographic_scope,
  p.enforcement_mode,
  p.effective_start_date,
  p.effective_end_date,
  pr.policy_rule_id,
  pr.rule_name,
  pr.rule_category,
  pr.rule_type,
  pr.rule_status,
  pr.severity_level,
  pr.threshold_value,
  pr.enforcement_action
FROM cdm_tmforum.tmf_marketsales.policy p
JOIN cdm_tmforum.tmf_marketsales.policy_rule pr
  ON p.policy_id = pr.policy_id
WHERE (
    p.type LIKE '%regulatory%'
    OR p.type LIKE '%compliance%'
    OR p.enforcement_mode IS NOT NULL
  )
  AND (
    :jurisdiction_filter = ''
    OR p.geographic_scope = :jurisdiction_filter
  )
ORDER BY p.effective_start_date DESC
LIMIT 1000
