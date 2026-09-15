# Circuits & Services Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

Customer-facing services, device-to-service impact mapping, resource capacity, contract/revenue constraints, and revenue at risk.

## Tables (6)

| Table | Type | Description |
|-------|------|-------------|
| `bronze_copper_services` | MATERIALIZED_VIEW | Bronze layer: copper-candidate customer-facing services |
| `silver_device_service_impact` | MATERIALIZED_VIEW | Silver layer: copper device to customer service impact mapping |
| `silver_resource_capacity` | MANAGED | Silver layer: network resource capacity at CO/exchange sites enriched with location |
| `silver_contract_constraints` | MANAGED | Silver layer: contract constraints on copper retirement |
| `silver_revenue_recognition_constraints` | MANAGED | Silver layer: ASC 606 revenue recognition constraints on copper retirement |
| `gold_circuit_revenue_at_risk` | MANAGED | Gold layer: per-circuit revenue at risk from copper retirement |

## Key Relationships

* service_id links bronze_copper_services -> silver_device_service_impact
* physical_device_id links silver_device_service_impact -> bronze_copper_devices
* service_id links gold_circuit_revenue_at_risk -> bronze_copper_services

## Table Details

### `bronze_copper_services` (Materialized View)

> Bronze layer: copper-candidate customer-facing services

Key columns: service_id, customer_id, service_type, service_status, circuit_id, bandwidth_mbps, monthly_recurring_revenue, service_start_date, geographic_address_id, state_code

### `silver_device_service_impact` (Materialized View)

> Silver layer: copper device to customer service impact mapping

Key columns: physical_device_id, service_id, customer_id, device_type, service_type, monthly_recurring_revenue, service_status, state_code, risk_tier

### `silver_resource_capacity` (Managed)

> Silver layer: network resource capacity at CO/exchange sites enriched with location data

Key columns: resource_id, site_name, site_type, capacity_total, capacity_used, utilization_pct, geographic_address_id, state_code, latitude, longitude

### `silver_contract_constraints` (Managed)

> Silver layer: contract constraints on copper retirement -- flags active contracts that may delay device decommissioning

Key columns: contract_id, customer_id, service_id, physical_device_id, contract_end_date, penalty_amount, constraint_type, state_code

### `silver_revenue_recognition_constraints` (Managed)

> Silver layer: ASC 606 revenue recognition constraints on copper retirement -- flags revenue recognition timing issues

Key columns: service_id, customer_id, revenue_recognition_end_date, deferred_revenue_amount, constraint_type, state_code

### `gold_circuit_revenue_at_risk` (Managed)

> Gold layer: per-circuit revenue at risk from copper retirement

Key columns: circuit_id, service_id, customer_id, monthly_recurring_revenue, annual_revenue, risk_tier, state_code, wire_center_clli
