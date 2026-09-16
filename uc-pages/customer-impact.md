# Customer Impact

## Overview

The Customer Impact domain tracks how copper retirement affects Lakelink Fiber's customer base — answering "how many customers are impacted, what is their churn risk, and what contractual obligations constrain migration timing." This domain connects physical plant retirement decisions to customer experience, billing, and retention outcomes.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.copper_customers_impacted` | Metric View | Aggregated metric | — | Metric view: count of customers impacted by copper retirement, segmented by wire center and risk tier. |
| `copper_retirement.silver_device_service_impact` | Silver | One row per device-service-customer tuple | 440 | Device-to-service-to-customer mapping with churn risk, SLA tier, and revenue impact. |
| `copper_retirement.silver_contract_constraints` | Silver | One row per constrained contract | 249 | Active contracts with copper-dependent terms that block or delay migration. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_customer.customer` | 10,000 | Master customer records — golden customer_id, segment, status, geographic location. |
| `tmf_customer.customer_product_order_item` | 1,000 | Product order line items per customer — tracks what customers have ordered. |
| `tmf_customer.churn_retention_statistic` | 10,000 | Historical churn and retention metrics per customer — churn probability, tenure, win-back status. |
| `tmf_customer.bill` | 10,000 | Customer billing records — invoice amounts, payment status, billing cycle. |
| `tmf_customer.customer_problem` | 100,000 | Customer complaints and trouble tickets — correlates with copper plant condition. |
| `tmf_customer.commitment` | 10,000 | Contractual commitments — term length, early termination penalties, migration eligibility dates. |
| `tmf_customer.billing_dispute` | 100,000 | Billing disputes — correlates with copper quality degradation and service interruptions. |

### CRM Source Tables

| Table | Rows | Description |
|---|---|---|
| `salesforce_source.contract` | 14,022 | Salesforce contracts with term dates and renewal status. |
| `salesforce_source.contract_line_item` | 56,088 | Circuit-level MRR with UnitPrice — per-circuit revenue for copper retirement financial modeling. |
| `mdm_source.customer_crosswalk` | 20,000 | Cross-system customer identity resolution (Salesforce ↔ Oracle ERP ↔ TMF golden customer_id). |

## Entity Relationships

```
tmf_customer.customer
  └── customer_id → bronze_copper_services.customer_id
  └── customer_id → gold_circuit_revenue_at_risk.customer_id
  └── customer_id → tmf_customer.bill.customer_id
  └── customer_id → tmf_customer.customer_problem.customer_id
  └── customer_id → tmf_customer.commitment.customer_id

mdm_source.customer_crosswalk
  └── tmf_customer_id → tmf_customer.customer.customer_id
  └── salesforce_account_id → salesforce_source.account.account_id
  └── oracle_customer_id → oracle_erp_source tables

tmf_customer.churn_retention_statistic
  └── customer_id → tmf_customer.customer.customer_id

tmf_customer.billing_dispute
  └── customer_id → tmf_customer.customer.customer_id
  └── bill_id → tmf_customer.bill.bill_id
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Customers Impacted | Distinct customers with at least one copper-dependent service | `copper_customers_impacted` metric view |
| Avg Churn Risk | Mean churn probability across copper-impacted customers | `tmf_customer.churn_retention_statistic` filtered to copper customers |
| Contract-Blocked Customers | Customers with active commitments preventing immediate migration | `tmf_customer.commitment` WHERE end_date > CURRENT_DATE |
| Complaint Rate | Customer problems per copper-impacted customer per month | `tmf_customer.customer_problem` GROUP BY customer_id, month |
| Billing Dispute Rate | Disputes per copper customer — indicator of copper quality degradation | `tmf_customer.billing_dispute` GROUP BY customer_id |
| Revenue per Customer | Average MRR per copper-impacted customer | `gold_circuit_revenue_at_risk` SUM(mrr) / COUNT(DISTINCT customer_id) |

## Data Quality Notes

- **Customer master:** 10,000 customers in TMF, cross-referenced via 20K crosswalk records to Salesforce and Oracle ERP.
- **Complaints volume:** 100K customer_problem records + 100K billing_dispute records provide rich signal for copper quality correlation.
- **Contract data:** 10K commitments track migration eligibility windows. 249 contracts have explicit copper-dependent constraints.
- **Churn statistics:** 10K records with historical churn/retention metrics. Used as features in the risk model.
- **Coverage:** Not all 10K customers have copper services — copper-impacted subset determined via device-service-customer joins.

## Related Domains

- **Circuits & Services** — Device-service mapping determines which customers are copper-impacted
- **Financial Operations** — Customer-level MRR feeds EBITDA impact calculations
- **Risk & ML** — Churn statistics and complaint rates are features in the device risk model
- **Regulatory** — Customer notification requirements depend on state PUC rules
