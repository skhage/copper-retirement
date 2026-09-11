-- jurisdiction_regulators.sql
-- Fetch regulators by jurisdiction for the Jurisdiction Map and StateRegCard.
-- Source: cdm_tmforum.tmf_enterprise.regulator (1K rows, 133 active)
--
-- Caveat: text fields (name, contact_info, etc) are synthetic hashes.
-- Schema structure is usable for layout; display values need mock overlay.

SELECT
  r.regulator_id,
  r.name                AS regulator_name,
  r.jurisdiction,
  r.authority_level,     -- federal, state_puc, municipal
  r.status,              -- active, inactive, merged, etc.
  r.regulatory_domain,
  r.contact_name,
  r.contact_email,
  r.website_url,
  r.effective_start_date,
  r.effective_end_date
FROM cdm_tmforum.tmf_enterprise.regulator r
WHERE r.status = 'active'
  AND (
    :jurisdiction_filter = ''
    OR r.jurisdiction = :jurisdiction_filter
  )
ORDER BY r.authority_level, r.jurisdiction
