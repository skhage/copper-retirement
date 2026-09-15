# Customer Impact

## Overview

The Customer Impact domain quantifies how Lakelink Fiber's copper retirement affects subscribers — how many customers are impacted, by what service types, in which segments, and at what urgency level. It is the thinnest domain within the `copper_retirement` schema (one metric view backed by `silver_device_service_impact`), but draws on the richest source ecosystem: TMF customer master, billing, complaints, churn, contracts, and Salesforce CRM.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.copper_customers_impacted` | Metric View | One row per device-service allocation | 440 | Governed metric view: customer impact KPIs for copper retirement. 9 dimensions (state, device type, risk tier, service type, customer segment, impact category, service status, wire center, criticality level) and 10 measures. Source: `silver_device_service_impact`. |
| `copper_retirement.silver_device_service_impact` | Silver | One row per device-service allocation | 440 | DLP materialized view mapping copper devices to customer services. 22 columns including customer_id, customer_segment, service_type, impact_category, criticality_level. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_customer.customer` | 10,000 | Core master entity — SSOT for customer identity, segmentation, and lifecycle. |
| `tmf_customer.bill` | 10,000 | Customer invoices with billing period, total amount, and tax. |
| `tmf_customer.churn_retention_statistic` | 10,000 | Churn/retention metrics per customer — voluntary, involuntary, retention success. |
| `tmf_customer.customer_problem` | 100,000 | Customer complaints in Trouble-to-Resolve (T2R) process — correlates with copper plant condition. |
| `tmf_customer.commitment` | 10,000 | Contractual commitments — migration timing constraints (can't migrate mid-contract). |

### CRM & MDM Sources

| Table | Rows | Description |
|---|---|---|
| `salesforce_source.account` | 10,000 | CRM account records for migration campaign targeting. |
| `salesforce_source.contract` | 14,022 | Active contracts with circuit-level MRR for revenue impact. |
| `salesforce_source.contact` | 30,000 | CRM contacts per account — migration notification targeting for FCC 90-day direct notice (FCC 26-19). |
| `mdm_source.customer_crosswalk` | 20,000 | Cross-system identity resolution (Salesforce ↔ Oracle ERP ↔ TMF golden customer_id). |

## Entity Relationships

```
copper_customers_impacted (METRIC VIEW)
  └── source: silver_device_service_impact
        └── customer_id → tmf_customer.customer.customer_id
        └── physical_device_id → silver_copper_plant_enriched.physical_device_id
        └── customer_facing_service_id → bronze_copper_services.customer_facing_service_id

tmf_customer.customer
  └── customer_id → mdm_source.customer_crosswalk.tmf_customer_id
  └── customer_id → tmf_customer.bill.customer_id
  └── customer_id → tmf_customer.churn_retention_statistic.customer_id
  └── customer_id → tmf_customer.customer_problem.customer_id
  └── customer_id → tmf_customer.commitment.customer_id

mdm_source.customer_crosswalk
  └── salesforce_account_id → salesforce_source.account.Id
  └── oracle_erp_customer_number → oracle_erp_source (various)
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Customers Impacted | COUNT(DISTINCT customer_id) — unique customers affected by copper retirement | `copper_customers_impacted` |
| Services at Risk | COUNT(DISTINCT customer_facing_service_id) — unique services depending on copper | `copper_customers_impacted` |
| Voice Services at Risk | Voice (POTS/VoIP) services at risk — subject to regulatory notice requirements | `copper_customers_impacted` |
| Residential Customers | Residential customers impacted — subject to FCC 90-day direct notice (FCC 26-19) | `copper_customers_impacted` |
| Enterprise Customers | Enterprise customers impacted — typically higher revenue per customer | `copper_customers_impacted` |
| Critical Impact Customers | Customers on critical-risk devices requiring immediate migration | `copper_customers_impacted` |
| Broadband Services at Risk | Broadband (DSL/internet) services facing disruption | `copper_customers_impacted` |
| Fixed Line Services at Risk | Dedicated circuit services at risk of disruption | `copper_customers_impacted` |

## Data Quality Notes

- **Thinnest domain:** Only 440 rows in the core table (`silver_device_service_impact`). This represents device-service allocations, not total customers — one device can serve multiple services, and one customer can have multiple services.
- **Customer master coverage:** TMF `customer` has 10K records; MDM crosswalk maps 20K cross-system identities across Salesforce/Oracle/TMF.
- **Metric view:** `copper_customers_impacted` is a governed YAML metric view (not materialized) — queries evaluate on-demand against `silver_device_service_impact`.
- **Contact coverage:** 30K contacts in Salesforce for 10K accounts — adequate for migration notification planning.
- **Phase 2 opportunity:** @data-planner notes this domain is thin in `copper_retirement` schema. A dedicated `silver_copper_customers` table aggregating TMF customer, billing, complaints, and contract data per copper-impacted customer would strengthen the domain.
- **Refresh:** `silver_device_service_impact` is a DLP materialized view, refreshed on pipeline schedule.

## Related Domains

- **Circuits & Services** — Service allocation data that feeds the customer impact mapping
- **Physical Plant** — Device risk tiers that determine customer migration urgency
- **Regulatory** — FCC 90-day notice requirements for residential customers (FCC 26-19)
- **Financial** — Per-customer revenue at risk via circuit revenue data
