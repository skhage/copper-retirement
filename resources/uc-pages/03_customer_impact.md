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

This is a governed metric view that provides standardized customer impact KPIs. Key dimensions: state_code, service_type. Key measures: customers_impacted, services_at_risk, total_mrr_at_risk.

### `feature_device_billing_dispute` (Managed)

> ML feature: billing dispute rate per physical device. Join: billing_dispute -> CFS -> physical_device.

Key columns: physical_device_id, dispute_count_90d, dispute_rate, avg_dispute_amount, last_dispute_date

### `feature_device_complaint_rate` (Managed)

> ML feature: complaint rate per physical device. Join: customer_problem -> CFS -> physical_device.

Key columns: physical_device_id, complaint_count_90d, complaint_rate, complaint_severity_avg, last_complaint_date

### `feature_device_service_usage` (Managed)

> ML feature: service usage patterns per physical device. Direct join via physical_device_id.

Key columns: physical_device_id, avg_daily_usage_mb, peak_usage_mb, usage_trend_30d, active_services_count
