# Circuits & Services

## Overview

The Circuits & Services domain maps Lakelink Fiber's copper-carried customer services to the physical devices that deliver them, and quantifies the revenue at risk when those circuits are retired. This domain bridges the Physical Plant (what's deployed) with Customer Impact (who's affected) through device-service allocation, and feeds the financial models with per-circuit revenue exposure.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.bronze_copper_services` | Bronze | One row per copper-candidate CFS | 17,655 | Copper-candidate customer-facing services (voice 7,140 + fixed_line 6,940 + broadband 3,575) filtered from 100K CFS records. |
| `copper_retirement.silver_device_service_impact` | Silver | One row per device-service pair | 440 | Copper device to customer service impact mapping — shows which services are disrupted when a device is retired. DLP materialized view. |
| `copper_retirement.gold_circuit_revenue_at_risk` | Gold | One row per circuit | 14,777 | Per-circuit revenue at risk from copper retirement — 47 columns including monthly unit price, estimated annual revenue, ERP billed amounts, contract details. Richest gold table in the schema. |
| `copper_retirement.feature_device_service_usage` | Feature | One row per physical device | 6,351 | ML feature: service usage patterns per device — active months, avg monthly revenue, avg monthly volume, usage trend. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_service.customer_facing_service` | 100,000 | All CFS records — 17.7% are copper-candidate (voice + fixed_line + broadband). |
| `tmf_service.resource_facing_service` | 100,000 | Network-layer RFS records provisioned on physical/logical resources. |
| `tmf_resource.device_service_allocation` | 3,417 | Allocation relationship between physical devices and service instances. Critical join table for impact analysis. |

### External Sources

| Table | Rows | Description |
|---|---|---|
| `salesforce_source.contract_line_item` | N/A | Circuit-level MRR with `UnitPrice`. Feeds per-circuit revenue-at-risk calculation. |
| `oracle_erp_source.ra_billed_circuit_rates` | 56,000 | Billed circuit rates with circuit-level detail — source of truth for actual billed amounts. |

## Entity Relationships

```
bronze_copper_services
  └── customer_facing_service_id → tmf_service.customer_facing_service.customer_facing_service_id
  └── customer_id → tmf_customer.customer.customer_id
  └── geographic_address_id → tmf_shared.geographic_address.geographic_address_id
  └── h3_res8 (spatial join) → bronze_copper_devices.h3_res8

silver_device_service_impact (DLP materialized view)
  └── physical_device_id → silver_copper_plant_enriched.physical_device_id
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id
  └── Aggregates: affected_service_count, affected_customer_count per device

gold_circuit_revenue_at_risk
  └── circuit_id → tmf_resource.logical_resource.logical_resource_id
  └── source_line_item_id → salesforce_source.contract_line_item.Id
  └── source_contract_id → salesforce_source.contract.Id
  └── physical_device_id → bronze_copper_devices.physical_device_id

feature_device_service_usage
  └── physical_device_id → bronze_copper_devices.physical_device_id
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Revenue at Risk | Estimated annual revenue lost per circuit when copper is retired (USD) | `gold_circuit_revenue_at_risk.estimated_annual_revenue` |
| Monthly Unit Price | Actual ERP-billed monthly unit price per circuit | `gold_circuit_revenue_at_risk.monthly_unit_price` |
| Affected Services per Device | Count of customer-facing services disrupted by retiring a device | `silver_device_service_impact.affected_service_count` |
| Affected Customers per Device | Count of distinct customers impacted by a device retirement | `silver_device_service_impact.affected_customer_count` |
| Voice Services at Risk | Count of voice services requiring E911 compliance before retirement | `gold_wire_center_scorecard.voice_services` |
| Avg Monthly Revenue per Device | Average monthly revenue from services on a copper device | `feature_device_service_usage.avg_monthly_revenue` |

## Data Quality Notes

- **Circuit revenue data:** `gold_circuit_revenue_at_risk` is the richest gold table (47 columns, 14,777 rows). Revenue figures are sourced from Oracle ERP billed rates and Salesforce contract line items.
- **Device-service mapping:** Only 440 device-service impact records (from 2,672 copper devices) — not every device has an allocated service. Gaps are expected for backbone/infrastructure devices without direct customer allocation.
- **Service types:** Bronze services split: voice (7,140), fixed_line (6,940), broadband (3,575). Voice services have E911 regulatory implications for retirement sequencing.
- **Feature coverage:** `feature_device_service_usage` covers 6,351 devices (broader than copper-only) for ML feature completeness.
- **Refresh:** `bronze_copper_services` and `silver_device_service_impact` are DLP materialized views, refreshed on schedule.

## Related Domains

- **Physical Plant** — Device inventory and wire center boundaries that anchor the service impact analysis
- **Customers** — Customer records linked via `customer_id` on copper services
- **Risk & ML** — `feature_device_service_usage` feeds the V5 risk model as service-usage features
- **Financial** — Circuit revenue at risk rolls up into EBITDA forecast models
