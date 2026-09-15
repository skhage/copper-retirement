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
* clli_code links wire_center_boundary -> copper_plant_wire_center_jurisdiction
* physical_device_id links silver_copper_plant_enriched -> bronze_copper_devices

## Table Details

### `bronze_copper_devices` (Materialized View) — 16 columns, 2,672 rows

> Bronze layer: copper-relevant physical devices filtered from TMF physical_device

Key columns: physical_device_id, device_type, device_status, serial_number, firmware_version, installation_date, geographic_address_id, h3_res8, state_code, city, addr_latitude, addr_longitude

### `copper_loop_plant` (Managed) — 22 columns, 50,000 rows

> Physical copper cable pair inventory — gauge, length, splice points, test results

Key columns: copper_pair_id, cable_segment_id, physical_device_id, geographic_address_id, cable_gauge_awg, segment_length_ft, loop_length_ft, splice_point_count, cable_type, cable_vintage_year, pair_status, last_test_date, test_result_db_loss, moisture_detected

### `copper_plant_wire_center_jurisdiction` (Managed) — 51 columns, 6,328 rows

> Denormalized copper plant view joining cable pairs, physical devices, wire centers, and regulatory jurisdictions

Key columns: copper_pair_id, physical_device_id, geographic_address_id, state_code, wire_center_id, clli_code, wire_center_type, fiber_ready, puc_filing_required, distance_to_wire_center_km, cable_gauge_awg, pair_status, puc_name, governor_notice_days, section_214_required

### `wire_center_boundary` (Managed) — 21 columns, 1,699 rows

> Wire center geographic boundaries with GeoJSON polygons and copper plant statistics

Key columns: wire_center_id, wire_center_name, state_code, centroid_lat, centroid_lon, boundary_geojson, wire_center_type, copper_device_count, estimated_copper_pairs, fiber_ready, area_sq_km, annual_retire_priority, clli_code

### `silver_copper_plant_enriched` (Materialized View) — 37 columns, 2,672 rows

> Silver layer: copper devices enriched with alarm, performance, and risk features

Key columns: physical_device_id, device_type, device_status, state_code, alarm_count, critical_alarm_rate, sla_breach_rate, test_fail_rate, problem_count, wire_center_id, clli_code, fiber_ready, computed_risk_tier, puc_name, section_214_required

### `retirement_milestones` (Managed) — 14 columns, 927 rows

> Copper retirement project milestones per wire center

Key columns: milestone_id, wire_center_id, name, type, status, priority, planned_date, actual_date, forecast_date, completion_percentage, critical_path_flag, risk_level
