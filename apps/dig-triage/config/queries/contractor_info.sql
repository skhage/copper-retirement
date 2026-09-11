-- contractor_info.sql
-- Contractor lookup for the triage console
-- Available NOW (10K agreements, 1,254 active)
--
-- Parameters:
--   :bp_agreement_id  - specific contractor agreement ID, or 0 for all active

SELECT
  bpa.bp_agreement_id,
  bpa.party_id,
  bpa.type                      AS agreement_type,
  bpa.status                    AS agreement_status,
  bpa.sla_tier,
  bpa.governing_law_jurisdiction,
  -- Count of repair/emergency work orders per contractor
  COALESCE(wk.work_order_count, 0) AS work_order_count,
  COALESCE(wk.active_work_orders, 0) AS active_work_orders
FROM cdm_tmforum.tmf_businesspartner.bp_agreement bpa
LEFT JOIN (
  SELECT
    party_id,
    COUNT(*) AS work_order_count,
    SUM(CASE WHEN status IN ('dispatched', 'in_progress') THEN 1 ELSE 0 END) AS active_work_orders
  FROM cdm_tmforum.tmf_enterprise.work
  WHERE type IN ('repair', 'emergency')
  GROUP BY party_id
) wk ON wk.party_id = bpa.party_id
WHERE bpa.status = 'active'
  AND (:bp_agreement_id = 0 OR bpa.bp_agreement_id = :bp_agreement_id)
ORDER BY wk.work_order_count DESC NULLS LAST
LIMIT 50
