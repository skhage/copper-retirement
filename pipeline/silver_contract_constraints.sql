-- Silver: Contract constraints on copper retirement
-- Links Ironclad CLM contracts to copper services/devices via MDM crosswalk
-- Flags services and devices that cannot be retired due to active MSA constraints
-- Sources: ironclad_clm_source.contract_record (25) → salesforce_source.account → mdm_source.customer_crosswalk
--          → tmf_service.customer_facing_service → tmf_resource.device_service_allocation → physical_device

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.silver_contract_constraints (
  CONSTRAINT valid_contract EXPECT (contract_number IS NOT NULL),
  CONSTRAINT valid_customer EXPECT (customer_id IS NOT NULL)
)
COMMENT 'Silver layer: contract constraints on copper retirement — maps active MSAs to copper services and devices'
CLUSTER BY (constraint_status, customer_id)
AS
WITH contract_customer AS (
  -- Resolve contract → customer via MDM crosswalk
  SELECT
    cr.contract_number,
    cr.record_type,
    cr.status AS contract_status,
    TO_DATE(cr.effective_date, 'yyyy-MM-dd') AS effective_date,
    TO_DATE(cr.expiration_date, 'yyyy-MM-dd') AS expiration_date,
    cr.attachment_path,
    a.Id AS salesforce_account_id,
    a.Name AS account_name,
    cw.MASTER_CUSTOMER_ID AS customer_id
  FROM cdm_tmforum.ironclad_clm_source.contract_record cr
  INNER JOIN cdm_tmforum.salesforce_source.account a
    ON cr.account_id = a.Id
  INNER JOIN cdm_tmforum.mdm_source.customer_crosswalk cw
    ON cr.account_id = cw.SOURCE_PARTY_ID
    AND cw.SOURCE_SYSTEM = 'SALESFORCE'
),
copper_services AS (
  -- Copper-candidate services per customer
  SELECT
    cfs.customer_id,
    cfs.customer_facing_service_id,
    cfs.service_type,
    cfs.status AS service_status,
    cfs.geographic_address_id,
    cfs.h3_res8
  FROM cdm_tmforum.tmf_service.customer_facing_service cfs
  WHERE cfs.service_type IN ('voice', 'fixed_line', 'broadband')
),
copper_devices AS (
  -- Map services to copper devices via allocation
  SELECT
    dsa.service_id AS customer_facing_service_id,
    pd.physical_device_id,
    pd.device_type,
    pd.status AS device_status
  FROM cdm_tmforum.tmf_resource.device_service_allocation dsa
  INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
    ON dsa.physical_device_id = pd.physical_device_id
  WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
)
SELECT
  cc.contract_number,
  cc.record_type,
  cc.contract_status,
  cc.effective_date,
  cc.expiration_date,
  cc.attachment_path,
  cc.salesforce_account_id,
  cc.account_name,
  cc.customer_id,

  cs.customer_facing_service_id,
  cs.service_type,
  cs.service_status,
  cs.geographic_address_id,
  cs.h3_res8 AS service_h3_res8,

  cd.physical_device_id,
  cd.device_type,
  cd.device_status,

  -- Contract timing
  DATEDIFF(cc.expiration_date, CURRENT_DATE()) AS days_until_expiry,
  DATEDIFF(CURRENT_DATE(), cc.effective_date) AS days_since_effective,

  -- Constraint classification
  CASE
    WHEN cc.contract_status = 'Activated' AND cc.expiration_date > CURRENT_DATE() THEN 'active_constraint'
    WHEN cc.contract_status = 'Activated' AND cc.expiration_date <= CURRENT_DATE() THEN 'expired_pending_renewal'
    WHEN cc.contract_status = 'Expired' AND cc.expiration_date > CURRENT_DATE() THEN 'recently_expired'
    ELSE 'no_constraint'
  END AS constraint_status,

  -- Retirement eligibility
  CASE
    WHEN cc.contract_status = 'Activated' AND cc.expiration_date > CURRENT_DATE() THEN FALSE
    ELSE TRUE
  END AS eligible_for_retirement,

  -- Earliest possible retirement date (contract expiry + 90 day notice period per FCC 26-19)
  CASE
    WHEN cc.contract_status = 'Activated' AND cc.expiration_date > CURRENT_DATE()
    THEN DATE_ADD(cc.expiration_date, 90)
    ELSE CURRENT_DATE()
  END AS earliest_retirement_date,

  current_timestamp() AS _pipeline_processed_at

FROM contract_customer cc
LEFT JOIN copper_services cs
  ON cc.customer_id = cs.customer_id
LEFT JOIN copper_devices cd
  ON cs.customer_facing_service_id = cd.customer_facing_service_id;