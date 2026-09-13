-- reg_documents.sql
-- Fetch regulatory documents from the live FCC regulatory corpus.
-- Source: cdm_tmforum.copper_retirement.fcc_regulatory_document (305 docs)
-- Includes FCC orders, state PUC dockets, guidance, retirement notices, and Section 214 filings.

SELECT
  d.document_id,
  d.title                    AS document_title,
  d.document_type,
  d.issuing_body,
  d.jurisdiction_state_code  AS jurisdiction,
  d.effective_date,
  d.document_status,
  d.regulatory_topic,
  d.summary_text             AS description,
  d.citation_reference,
  d.docket_number,
  d.notice_period_days,
  d.word_count,
  d.page_count
FROM cdm_tmforum.copper_retirement.fcc_regulatory_document d
WHERE (
    :document_type_filter = ''
    OR d.document_type = :document_type_filter
  )
  AND (
    :search_term = ''
    OR LOWER(COALESCE(d.title, '')) LIKE CONCAT('%', LOWER(:search_term), '%')
    OR LOWER(COALESCE(d.summary_text, '')) LIKE CONCAT('%', LOWER(:search_term), '%')
    OR LOWER(COALESCE(d.regulatory_topic, '')) LIKE CONCAT('%', LOWER(:search_term), '%')
  )
ORDER BY d.effective_date DESC
LIMIT 200
