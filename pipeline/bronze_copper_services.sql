-- Bronze: Copper-candidate customer-facing services
-- Filters to voice, fixed_line, broadband service types (copper-carried)
-- Source: cdm_tmforum.tmf_service.customer_facing_service (100K → ~17,655 copper)

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.bronze_copper_services
COMMENT 'Bronze layer: copper-candidate customer-facing services'
CLUSTER BY (service_type, service_status)
AS
SELECT
  cfs.customer_facing_service_id,
  cfs.service_type,
  cfs.status AS service_status,
  cfs.customer_id,
  cfs.geographic_address_id,
  cfs.start_date,
  cfs.end_date,
  cfs.h3_res8,
  c.name AS customer_name,
  c.segment_classification AS customer_segment,
  c.type AS customer_type,
  current_timestamp() AS _pipeline_ingested_at
FROM cdm_tmforum.tmf_service.customer_facing_service cfs
LEFT JOIN cdm_tmforum.tmf_customer.customer c
  ON cfs.customer_id = c.customer_id
WHERE cfs.service_type IN ('voice', 'fixed_line', 'broadband');