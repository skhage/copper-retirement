# Physical Plant

## Overview

The Physical Plant domain tracks Lakelink Fiber's copper network infrastructure — every device, cable pair, wire center boundary, and fiber-readiness indicator involved in the copper-to-fiber migration. This is the foundational domain for the copper retirement program: it answers "where is copper deployed, what condition is it in, and which wire centers are ready to retire."

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.bronze_copper_devices` | Bronze | One row per copper device | 2,672 | Copper-relevant physical devices filtered from TMF physical_device (CPE 688, ONT 663, OLT 661, patch_panel 660). |
| `copper_retirement.copper_loop_plant` | Reference | One row per copper pair | 50,000 | Physical copper cable pair inventory — gauge, length, splice points, test results, moisture status. |
| `copper_retirement.copper_plant_wire_center_jurisdiction` | Reference | One row per copper pair | 6,328 | Denormalized view joining cable pairs, devices, wire center boundaries, and state PUC jurisdiction requirements. |
| `copper_retirement.silver_copper_plant_enriched` | Silver | One row per copper device | 2,672 | Copper devices enriched with alarm rates, performance metrics, and risk features from TMF source tables. |
| `copper_retirement.silver_resource_capacity` | Silver | One row per resource capacity record | 19,717 | Network resource capacity at CO/exchange sites — fiber infrastructure readiness and migration capacity. |
| `copper_retirement.gold_wire_center_scorecard` | Gold | One row per wire_center_id | 103 | Per-wire-center retirement readiness scorecard: composite 0–100 score, risk severity, alarm rates, fiber readiness, regulatory requirements. |
| `copper_retirement.wire_center_boundary` | Reference | One row per wire center | 1,802 | Wire center geographic boundaries with GeoJSON polygons, copper plant statistics, fiber readiness indicators. 103 CLLI-aligned rows for LEGACY states + 1,699 legacy sequential rows. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_enterprise.physical_device` | 10,000 | Complete standalone network devices — 26.7% are copper-relevant (2,672 devices). |
| `tmf_resource.equipment` | 10,000 | Discrete equipment units installed within physical devices — line cards, network modules. |
| `tmf_resource.connection_point` | 10,000 | Logical/physical connection endpoints on resources — ports, interfaces, connectors. |
| `tmf_resource.resource_specification` | 10,000 | Master catalog of resource type definitions — specs for copper and fiber equipment. |

## Entity Relationships

```
bronze_copper_devices
  └── physical_device_id → silver_copper_plant_enriched.physical_device_id
        └── physical_device_id + h3_res8 → gold_wire_center_scorecard (aggregated by wire_center_id)

copper_loop_plant
  └── physical_device_id → bronze_copper_devices.physical_device_id
  └── geographic_address_id → tmf_shared.geographic_address.geographic_address_id

copper_plant_wire_center_jurisdiction
  └── physical_device_id → bronze_copper_devices.physical_device_id
  └── wire_center_id → wire_center_boundary.wire_center_id
  └── state_code → state_puc_jurisdiction_requirements.jurisdiction_state_code

wire_center_boundary
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id
  └── geographic_site_id → tmf_shared.geographic_site.geographic_site_id

silver_resource_capacity
  └── geographic_site_id → tmf_shared.geographic_site.geographic_site_id
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Total Copper Devices | Count of copper-relevant physical devices (CPE + ONT + OLT + patch_panel) | `copper_retirement_project_status` metric view |
| Retirement Readiness Score | Composite 0–100 score per wire center: fiber_ready (30pts) + risk_severity (20pts) + alarm_rate (20pts) + priority (30pts) | `gold_wire_center_scorecard.retirement_readiness_score` |
| Fiber Ready Pct | Percentage of devices in fiber-ready wire centers | `copper_retirement_project_status.Fiber Ready Pct` |
| Critical Risk Devices | Count of devices classified as critical risk tier per wire center | `gold_wire_center_scorecard.critical_risk_devices` |
| Avg Alarm Count | Mean alarm count across copper devices at a wire center — higher = more urgent | `gold_wire_center_scorecard.avg_alarm_count` |
| Copper Device Count | Total copper devices per wire center | `gold_wire_center_scorecard.copper_device_count` |

## Data Quality Notes

- **H3 coverage:** 100% of devices have H3 hex indexes populated (res8 and res9). 1,699 distinct H3 cells across 2,672 devices.
- **Geographic coverage:** Devices span all 50 US states (sourced from `tmf_enterprise.physical_device` without state filtering). 100% valid US coordinates. Wire center assignments and scorecards are scoped to 6 LEGACY_STATES (CO, MN, WA, OR, ID, AZ) only.
- **Synthetic data:** `copper_loop_plant` (50K rows) is synthetic, generated with MDM-compliant FK values.
- **Wire centers:** 103 wire centers (6 LEGACY states) with scorecards. Boundary table contains 103 CLLI-aligned rows plus 1,699 legacy sequential rows. Scorecard, jurisdiction, and boundary all join on CLLI-style `wire_center_id`.
- **Refresh:** Bronze/silver/gold tables are refreshed via DLP pipeline (8 materialized views).

## Related Domains

- **Circuits & Services** — Device-to-service impact analysis via `silver_device_service_impact`
- **Risk & ML** — Device risk predictions feed into wire center scorecard aggregation
- **Regulatory** — Wire center PUC jurisdiction requirements determine filing deadlines
- **Financial** — Wire center retirement priority drives EBITDA forecast scheduling
