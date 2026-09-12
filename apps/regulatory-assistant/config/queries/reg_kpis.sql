-- reg_kpis.sql
-- Summary KPIs for the regulatory assistant top bar.
-- Sources: regulator (jurisdiction count), policy (pending filings),
--          document (document count)
--
-- NOTE: These are proxy KPIs from available tables. Real compliance
-- tracking requires P0-DATAGEN-REG + P3-GOLD regulatory_requirements_by_jurisdiction.

SELECT
  (SELECT COUNT(DISTINCT jurisdiction)
   FROM cdm_tmforum.tmf_enterprise.regulator
   WHERE status = 'active') AS jurisdictions_covered,

  (SELECT COUNT(*)
   FROM cdm_tmforum.tmf_marketsales.policy
   WHERE status IN ('pending', 'draft', 'under_review')
     AND (type LIKE '%regulatory%' OR enforcement_mode IS NOT NULL)) AS pending_filings,

  (SELECT COUNT(*)
   FROM cdm_tmforum.tmf_shared.document
   WHERE type IN ('policy', 'compliance_document', 'regulatory_filing', 'agreement', 'license')
     OR nature IN ('regulatory', 'administrative', 'legal')) AS documents_indexed,

  (SELECT COUNT(DISTINCT geographic_scope)
   FROM cdm_tmforum.tmf_marketsales.policy
   WHERE status = 'active'
     AND (type LIKE '%regulatory%' OR enforcement_mode IS NOT NULL)) AS active_policy_scopes
