# Customer Impact Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

Customer impact metrics and feature engineering tables that quantify how copper retirement affects individual customers.

## Tables (4)

| Table | Type | Description |
|-------|------|-------------|
| `copper_customers_impacted` | METRIC_VIEW | Customer impact metrics for the Lakelink Fiber copper retirement program |
| `feature_device_billing_dispute` | MANAGED | ML feature: billing dispute rate per physical device |
| `feature_device_complaint_rate` | MANAGED | ML feature: complaint rate per physical device |
| `feature_device_service_usage` | MANAGED | ML feature: service usage patterns per physical device |

## Key Relationships

* physical_device_id links feature tables -> bronze_copper_devices
* copper_customers_impacted is a METRIC VIEW over device-service-customer joins

## Table Details

### `copper_customers_impacted` (Metric View)

> Customer impact metrics for the Lakelink Fiber copper retirement program -- tracks how many customers are affected by copper retirement per state and service type.

This is a governed metric view that provides standardized customer impact KPIs. Note: metric views use display names, not snake_case.

Dimensions (9): State, Device Type, Risk Tier, Service Type, Customer Segment, Impact Category, Service Status, Wire Center, Criticality Level.

Measures (10): Customers Impacted, Services at Risk, Devices Impacting Customers, Total Allocations, Voice Services at Risk, Broadband Services at Risk, Fixed Line Services at Risk, Residential Customers, Enterprise Customers, Critical Impact Customers.

(19 cols total = 9 dims + 10 measures.)

### `feature_device_billing_dispute` (Managed)

> ML feature: billing dispute rate per physical device. Join: billing_dispute -> CFS -> physical_device.

Key columns: physical_device_id (FK to physical_device), dispute_count, dispute_count_weighted (1/CFS_per_customer weighting), dispute_amount_weighted, escalated_dispute_count, sla_breach_dispute_count, regulatory_dispute_count, earliest_dispute, latest_dispute, months_since_last_dispute. (10 cols.)

### `feature_device_complaint_rate` (Managed)

> ML feature: complaint rate per physical device. Join: customer_problem -> CFS -> physical_device.

Key columns: physical_device_id (FK to physical_device), complaint_count, complaint_rate_per_month, escalated_complaint_count, high_severity_count, sla_breach_count, first_contact_resolution_count, avg_resolution_hours, earliest_complaint, latest_complaint, months_since_last_complaint. (11 cols.)

### `feature_device_service_usage` (Managed)

> ML feature: service usage patterns per physical device. Direct join via physical_device_id.

Key columns: physical_device_id (FK to physical_device), active_months, avg_monthly_usage, avg_monthly_revenue, avg_monthly_volume_bytes, total_usage_records, first_usage_month, last_usage_month, months_since_last_usage, usage_trend_pct (month-over-month %). (10 cols.)
