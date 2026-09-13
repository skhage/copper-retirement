-- reg_documents.sql
-- Fetch regulatory documents for the Document Browser.
-- Source: cdm_tmforum.tmf_shared.document (10K rows, ~1,679 legal/regulatory)
--
-- Filter for legal/regulatory documents. Schema is usable for layout;
-- text content fields are synthetic hashes pending real doc ingestion (P1-REG).

SELECT
  d.document_id,
  d.name                AS document_title,
  d.type                AS document_type,
  d.classification_level AS classification,
  d.status              AS document_status,
  d.file_type,
  d.file_size_bytes,
  d.language_code,
  d.version_number,
  d.author_name AS author,
  d.created_date,
  d.last_modified_date,
  d.effective_start_date,
  d.effective_end_date,
  d.description
FROM cdm_tmforum.tmf_shared.document d
WHERE (d.type IN ('policy', 'compliance_document', 'regulatory_filing', 'agreement', 'license')
       OR d.nature IN ('regulatory', 'administrative', 'legal'))
  AND (
    :document_type_filter = ''
    OR d.type = :document_type_filter
  )
  AND (
    :search_term = ''
    OR LOWER(d.name) LIKE CONCAT('%', LOWER(:search_term), '%')
    OR LOWER(d.description) LIKE CONCAT('%', LOWER(:search_term), '%')
  )
ORDER BY d.last_modified_date DESC
LIMIT 200
