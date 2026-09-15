# Physical Plant Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

Physical copper infrastructure -- devices, cable pairs, wire center boundaries, and enriched plant views with alarm/performance data.

## Tables (6)

| Table | Type | Description |
|-------|------|-------------|
| `bronze_copper_devices` | MATERIALIZED_VIEW | Bronze layer: copper-relevant physical devices filtered from TMF physical_device |
| `copper_loop_plant` | MANAGED | Physical copper cable pair inventory -- gauge, length, splice points, test results |
| `copper_plant_wire_center_jurisdiction` | MANAGED | Denormalized copper plant view joining cable pairs, physical devices, wire centers |
| `wire_center_boundary` | MANAGED | Wire center geographic boundaries with GeoJSON polygons, copper plant statistics |
| `silver_copper_plant_enriched` | MATERIALIZED_VIEW | Silver layer: copper devices enriched with alarm, performance, and risk features |
| `retirement_milestones` | MANAGED | Copper retirement project milestones per wire center |

## Key Relationships

* physical_device_id links copper_loop_plant -> bronze_copper_devices
* wire_center_clli links wire_center_boundary -> copper_plant_wire_center_jurisdiction
* physical_device_id links silver_copper_plant_enriched -> bronze_copper_devices

## Table Details

(See full column details in the generated content at copper-retirement/resources/uc-pages/)
