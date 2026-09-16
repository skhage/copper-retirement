# Circuits & Services

## Overview

The Circuits & Services domain maps Lakelink Fiber's service inventory to physical copper infrastructure — answering "which services run over copper, which customers are affected, and what revenue is at risk when a wire center retires." This is the bridge between Physical Plant (devices) and Customer Impact (accounts), enabling per-circuit revenue-at-risk calculations and migration sequencing.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.bronze_copper_services` | Bronze | One row per copper-candidate service | 17,655 | Copper-candidate customer-facing services filtered from TMF CFS (voice 7,140 + fixed_line 6,940 + broadband 3,575). |
| `copper_retirement.silver_device_service_impact` | Silver | One row per device-service pair | 440 | Enriched device-to-service mapping with SLA, churn risk, and revenue impact for copper devices. |
| `copper_retirement.gold_circuit_revenue_at_risk` | Gold | One row per circuit | 14,777 | Per-circuit revenue-at-risk with MRR, contract status, churn probability, and wire center context. |
| `copper_retirement.silver_contract_constraints` | Silver | One row per constrained contract | 249 | Contracts with copper-dependent terms that constrain migration timing. |
| `copper_retirement.silver_revenue_recognition_constraints` | Silver | One row per revenue constraint | 708 | Revenue recognition rules that affect copper retirement financial scheduling. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_service.customer_facing_service` | 100,000 | All customer-facing service instances — 17.7% are copper-candidate (voice, fixed_line, broadband). |
| `tmf_service.resource_facing_service` | 100,000 | Resource-facing service instances linking logical resources to customer services. |
| `tmf_service.service_order_item` | 100,000 | Service order line items — provisioning, migration, and disconnect events. |
| `tmf_resource.device_service_allocation` | 3,417 | Maps physical devices to service instances — critical for copper impact analysis. |
| `tmf_resource.logical_resource` | 100,000 | Logical network resources (circuits, VLANs, bearers) assigned to services. |

## Entity Relationships

```
bronze_copper_services
  └── service_id → tmf_service.customer_facing_service.customer_facing_service_id
  └── customer_id → tmf_customer.customer.customer_id

silver_device_service_impact
  └── physical_device_id → bronze_copper_devices.physical_device_id
  └── customer_facing_service_id → bronze_copper_services.service_id
  └── wire_center_id → wire_center_boundary.wire_center_id

gold_circuit_revenue_at_risk
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id
  └── customer_id → tmf_customer.customer.customer_id

device_service_allocation
  └── physical_device_id → tmf_enterprise.physical_device.physical_device_id
  └── service_id → tmf_service.customer_facing_service.customer_facing_service_id
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Circuits at Risk | Total copper-dependent circuits facing retirement | `gold_circuit_revenue_at_risk` COUNT |
| Monthly Revenue at Risk | Sum of MRR across all copper-dependent circuits | `gold_circuit_revenue_at_risk.mrr` SUM |
| Avg Churn Probability | Mean churn probability across copper circuits | `gold_circuit_revenue_at_risk.churn_probability` AVG |
| Services per Device | Average customer-facing services per copper device | `silver_device_service_impact` GROUP BY physical_device_id |
| Contract-Constrained Circuits | Circuits with active contracts blocking migration | `silver_contract_constraints` COUNT |

## Data Quality Notes

- **Service coverage:** 17,655 copper-candidate services out of 100K total CFS (17.7%). Covers voice, fixed_line, and broadband service types.
- **Device-service mapping:** 440 device-service pairs — sparse because only a subset of copper devices have explicit allocation records.
- **Revenue data:** 14,777 circuit revenue-at-risk rows with MRR values sourced from billing and contract systems.
- **Contract constraints:** 249 contracts with copper-dependent terms; 708 revenue recognition constraints.
- **Refresh:** Bronze/silver tables refreshed via DLP pipeline. Gold computed downstream.

## Related Domains

- **Physical Plant** — Copper device inventory feeds device-service allocation
- **Customer Impact** — Circuit-level churn and complaint data enriches revenue-at-risk
- **Financial Operations** — Revenue-at-risk aggregates drive EBITDA forecasting
- **Risk & ML** — Device risk scores inform circuit-level migration urgency
