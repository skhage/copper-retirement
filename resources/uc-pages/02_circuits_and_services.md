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

* customer_facing_service_id links bronze_copper_services -> silver_device_service_impact
* physical_device_id links silver_device_service_impact -> bronze_copper_devices
* circuit_id links gold_circuit_revenue_at_risk -> logical resources (tmf_resource.logical_resource)

## Table Details

### `bronze_copper_services` (Materialized View) — 12 columns, 17,655 rows

> Bronze layer: copper-candidate customer-facing services

Key columns: customer_facing_service_id, customer_id, service_type, service_status, geographic_address_id, start_date, end_date, h3_res8, customer_name, customer_segment, customer_type

### `silver_device_service_impact` (Materialized View) — 20 columns, 440 rows

> Silver layer: copper device to customer service impact mapping

Key columns: physical_device_id, device_type, device_status, state_code, wire_center_id, computed_risk_tier, customer_facing_service_id, service_type, customer_id, impact_category

### `silver_resource_capacity` (Managed) — 44 columns, 19,717 rows

> Silver layer: network resource capacity at CO/exchange sites enriched with location data

Key columns: resource_capacity_id, physical_resource_id, infrastructure_layer, technology_domain, total_capacity, used_capacity, utilization_pct, geographic_site_id, state_or_province, h3_res8, capacity_health, migration_readiness

### `silver_contract_constraints` (Managed) — 23 columns, 249 rows

> Silver layer: contract constraints on copper retirement — flags active contracts that may delay device decommissioning

Key columns: contract_number, customer_id, customer_facing_service_id, physical_device_id, contract_status, effective_date, expiration_date, days_until_expiry, constraint_status, eligible_for_retirement, earliest_retirement_date

### `silver_revenue_recognition_constraints` (Managed) — 27 columns, 708 rows

> Silver layer: ASC 606 revenue recognition constraints on copper retirement — flags revenue recognition timing issues

Key columns: customer_facing_service_id, customer_id, total_deferred_amount, total_recognized_amount, recognition_pct_complete, days_until_fully_recognized, constraint_severity, revrec_eligible_for_retirement, earliest_safe_retirement_date

### `gold_circuit_revenue_at_risk` (Managed) — 47 columns, 14,777 rows

> Gold layer: per-circuit revenue at risk from copper retirement

Key columns: circuit_id, monthly_unit_price, estimated_annual_revenue, physical_device_id, device_type, state_code, computed_risk_tier, clli_code, fiber_ready, revenue_tier, action_priority, ml_risk_tier, ml_composite_risk_score
