-- Silver: Revenue recognition constraints on copper retirement
-- Links Oracle ERP revenue recognition schedule (ASC 606) to copper services/devices
-- Flags circuits with DEFERRED revenue that impose timing constraints on copper retirement
-- Retiring a circuit mid-recognition-period creates ASC 606 accounting complications
-- Sources: oracle_erp_source.revenue_recognition_schedule (120K) → ra_customer_trx_all (10K)
--          → tmf_customer.bill → customer → customer_facing_service → device_service_allocation → physical_device

CREATE OR REFRESH MATERIALIZED VIEW cdm_tmforum.copper_retirement.silver_revenue_recognition_constraints (
  CONSTRAINT valid_transaction EXPECT (customer_trx_id IS NOT NULL),
  CONSTRAINT valid_customer EXPECT (customer_id IS NOT NULL),
  CONSTRAINT positive_deferred EXPECT (total_deferred_amount >= 0)
)
COMMENT 'Silver layer: ASC 606 revenue recognition constraints on copper retirement — flags circuits with deferred revenue that block safe decommissioning'
CLUSTER BY (customer_id)
AS
WITH recognized_totals AS (
  -- Pre-aggregate recognized amounts per transaction (avoids correlated subquery)
  SELECT CUSTOMER_TRX_ID, SUM(RECOGNIZED_AMOUNT) AS total_recognized_amount
  FROM cdm_tmforum.oracle_erp_source.revenue_recognition_schedule
  WHERE STATUS = 'RECOGNIZED'
  GROUP BY CUSTOMER_TRX_ID
),
deferred_summary AS (
  -- Aggregate deferred revenue recognition by transaction
  SELECT
    rrs.CUSTOMER_TRX_ID,
    COUNT(*) AS deferred_period_count,
    SUM(rrs.RECOGNIZED_AMOUNT) AS total_deferred_amount,
    MIN(rrs.RECOGNITION_DATE) AS first_deferred_date,
    MAX(rrs.RECOGNITION_DATE) AS last_deferred_date,
    COALESCE(rt.total_recognized_amount, 0) AS total_recognized_amount
  FROM cdm_tmforum.oracle_erp_source.revenue_recognition_schedule rrs
  LEFT JOIN recognized_totals rt ON rrs.CUSTOMER_TRX_ID = rt.CUSTOMER_TRX_ID
  WHERE rrs.STATUS = 'DEFERRED'
  GROUP BY rrs.CUSTOMER_TRX_ID, rt.total_recognized_amount
),
transaction_customer AS (
  -- Resolve transaction → customer via bill
  SELECT
    trx.CUSTOMER_TRX_ID,
    trx.TRX_NUMBER,
    trx.TRX_DATE,
    trx.INVOICE_AMOUNT,
    trx.INVOICE_CURRENCY_CODE,
    trx.TMF_BILL_ID,
    b.customer_id,
    b.billing_account_id
  FROM cdm_tmforum.oracle_erp_source.ra_customer_trx_all trx
  INNER JOIN cdm_tmforum.tmf_customer.bill b
    ON trx.TMF_BILL_ID = b.bill_id
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
    pd.status AS device_status,
    pd.installation_date
  FROM cdm_tmforum.tmf_resource.device_service_allocation dsa
  INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
    ON dsa.physical_device_id = pd.physical_device_id
  WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
)
SELECT
  -- Transaction identifiers
  ds.CUSTOMER_TRX_ID AS customer_trx_id,
  tc.TRX_NUMBER AS transaction_number,
  tc.TRX_DATE AS transaction_date,
  tc.INVOICE_AMOUNT AS invoice_amount,
  tc.INVOICE_CURRENCY_CODE AS currency_code,
  tc.TMF_BILL_ID AS bill_id,

  -- Customer
  tc.customer_id,
  tc.billing_account_id,

  -- Copper service (may be NULL if customer has no copper service)
  cs.customer_facing_service_id,
  cs.service_type,
  cs.service_status,
  cs.geographic_address_id,
  cs.h3_res8 AS service_h3_res8,

  -- Copper device (may be NULL if service has no allocated device)
  cd.physical_device_id,
  cd.device_type,
  cd.device_status,

  -- Revenue recognition schedule
  ds.deferred_period_count,
  ds.total_deferred_amount,
  ds.total_recognized_amount,
  ds.first_deferred_date,
  ds.last_deferred_date,

  -- Completion metrics
  ROUND(
    ds.total_recognized_amount / NULLIF(ds.total_recognized_amount + ds.total_deferred_amount, 0) * 100, 1
  ) AS recognition_pct_complete,
  DATEDIFF(ds.last_deferred_date, CURRENT_DATE()) AS days_until_fully_recognized,

  -- Constraint classification
  CASE
    WHEN ds.last_deferred_date > CURRENT_DATE() AND ds.total_deferred_amount >= 50000
      THEN 'hard_block'
    WHEN ds.last_deferred_date > CURRENT_DATE() AND ds.total_deferred_amount >= 10000
      THEN 'significant_constraint'
    WHEN ds.last_deferred_date > CURRENT_DATE()
      THEN 'minor_constraint'
    ELSE 'no_constraint'
  END AS constraint_severity,

  -- Retirement eligibility from rev rec perspective
  CASE
    WHEN ds.last_deferred_date > CURRENT_DATE() THEN FALSE
    ELSE TRUE
  END AS revrec_eligible_for_retirement,

  -- Earliest safe retirement date (after last deferred period + 30 day buffer)
  CASE
    WHEN ds.last_deferred_date > CURRENT_DATE()
    THEN DATE_ADD(ds.last_deferred_date, 30)
    ELSE CURRENT_DATE()
  END AS earliest_safe_retirement_date,

  current_timestamp() AS _pipeline_processed_at

FROM deferred_summary ds
INNER JOIN transaction_customer tc
  ON ds.CUSTOMER_TRX_ID = tc.CUSTOMER_TRX_ID
LEFT JOIN copper_services cs
  ON tc.customer_id = cs.customer_id
LEFT JOIN copper_devices cd
  ON cs.customer_facing_service_id = cd.customer_facing_service_id;