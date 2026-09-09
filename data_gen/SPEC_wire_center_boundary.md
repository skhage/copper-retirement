# Wire-Center Boundary Polygons — Synthetic Data Specification

**Task:** P0-DATAGEN-WIRECENTER  
**Author:** @data-engineer | **Date:** 2026-09-07  
**Status:** Schema spec complete. Ready for implementation.

---

## Purpose

Wire-center boundary polygons define the geographic serving area for each central office (CO) in the copper retirement analysis. They are needed to:
- Map copper plant records (`copper_loop_plant`) to geographic jurisdictions
- Assign regulator/PUC jurisdiction per CO area (P2-JOIN)
- Visualize retirement waves by wire-center on the P7-PLAN Gantt
- Scope FCC BDC broadband coverage overlays (P1-FCC)
- Drive per-wire-center capacity planning in `tmf_service.service_capacity`

---

## Source Table Profiling Summary

### `tmf_shared.geographic_site` (10K rows)
- **ID range:** 10001–20000 (LONG)
- **`state_province`:** Real US state names (50 states, uniformly distributed ~200 per state).
- **Sites in LEGACY_STATES** (CO, MN, WA, OR, ID, AZ): **1,157 sites** — these are the CO anchor candidates.
  - Colorado: 214, Washington: 213, Oregon: 202, Arizona: 180, Minnesota: 176, Idaho: 172
- **`site_type`, `site_name`, `site_code`:** All random hashes — unusable for CO/cabinet classification.
- **`latitude`, `longitude`:** Garbage range (0–99,982) — NOT valid geographic coordinates. Generator must assign real coordinates.
- **`backup_power_available`, `fiber_connectivity_available`, `carrier_neutral`:** BOOLEAN — usable attributes for CO characterization.
- **`power_capacity_kw`, `cooling_capacity_tons`:** DECIMAL — usable for CO capacity modeling.

### `tmf_shared.geographic_address` (10K rows)
- **ID range:** 10001–20000 (LONG)
- **`geographic_site_id` FK:** 100% coverage (10K/10K), 100% valid join to `geographic_site`. This is the **primary clustering mechanism**.
- **6,351 distinct sites** referenced. Distribution: mostly 1–2 addresses per site (median 1, max 7).
- **740 sites in LEGACY_STATES** have addresses linked (~1,148 addresses total).
- **`state_or_province`, `exchange_location_code`, `exchange_service_area_code`:** All random hashes — NOT usable for geographic clustering.
- **`latitude`, `longitude`:** Garbage range (34–99,992) — NOT valid coordinates.
- **`exchange_location_code`:** 10K distinct values — could serve as wire-center assignment key if overridden by generator with real CLLI codes.

### `tmf_shared.network_route` (1K rows)
- **`geographic_site_id` FK:** 938 distinct sites referenced.
- **`route_type`, `destination_location`, `waypoints`:** All random hashes.
- Not useful for wire-center boundary derivation in current form. Reference via `geographic_site_id` for post-generation join only.

### Existing Generator Pattern (`synthetic_assets.py`)
- **Bounding box:** Colorado Front Range — `LAT_RANGE = (39.4, 40.3)`, `LON_RANGE = (-105.4, -104.6)`
- **LEGACY_STATES:** `["CO", "MN", "WA", "OR", "ID", "AZ"]`
- **H3_RESOLUTION:** 9
- **Determinism:** `random.Random(seed)` — no wall-clock or network calls
- Wire-center generator should extend state coverage beyond Front Range to all 6 LEGACY_STATES.

---

## Blockers

1. **`geographic_site` lat/lon is garbage** — Generator must assign new realistic coordinates to each CO site from state bounding boxes. Do NOT read from the table.
2. **`geographic_site.site_type` is random** — Generator must classify sites as CO type using a simple rule: every `geographic_site` in LEGACY_STATES becomes a candidate CO. Use `fiber_connectivity_available` as a secondary signal (fiber-connected sites → hub/node type).
3. **`geographic_address` lat/lon is garbage** — Wire-center address assignment must use `geographic_site_id` FK grouping, NOT lat/lon proximity.
4. **H3 library required** — `h3` Python package must be available. Already used in `synthetic_assets.py` via `import h3`. Use `h3.latlng_to_cell()` and `h3.cell_to_boundary()` for polygon generation.
5. **GeoJSON polygon format** — Each boundary must serialize as a valid GeoJSON `Feature` string. Use `json.dumps()` with a `{"type": "Polygon", "coordinates": [[...]]}` structure.

---

## State Bounding Boxes for Coordinate Assignment

Use these bounds to generate realistic CO centroid coordinates within each LEGACY_STATE:

| State | Lat Min | Lat Max | Lon Min  | Lon Max  | Target Wire Centers |
|-------|---------|---------|----------|----------|---------------------|
| CO    | 36.99   | 41.00   | -109.06  | -102.04  | 50                  |
| MN    | 43.50   | 49.38   | -97.24   | -89.49   | 35                  |
| WA    | 45.54   | 49.00   | -124.79  | -116.47  | 35                  |
| OR    | 41.99   | 46.24   | -124.71  | -116.46  | 30                  |
| ID    | 41.99   | 49.00   | -117.24  | -111.04  | 25                  |
| AZ    | 31.33   | 37.00   | -114.82  | -109.04  | 25                  |
| **Total** | | | | | **200 wire centers** |

---

## Synthetic Table Schema: `wire_center_boundary`

**Target catalog/schema:** `cdm_tmforum.copper_retirement` (new schema — matches copper_loop_plant target)  
**Recommended row count:** 200 wire centers across 6 LEGACY_STATES  
**Output format:** Delta table (primary) + GeoJSON FeatureCollection file in `data_gen/output/wire_centers.geojson`  
**Determinism:** `random.Random(seed)` pattern from `synthetic_assets.py`

| Column | Type | Description | Value Range / FK |
|---|---|---|---|
| `wire_center_id` | STRING | PK — CLLI-style code | `"COXXX01"` pattern: 2-char state + 3-char city abbreviation + 2-digit index (e.g., `"CODENVER01"`, `"MNSPAUL02"`) |
| `geographic_site_id` | LONG | FK → `tmf_shared.geographic_site` | Sampled from LEGACY_STATE sites (IDs 10001–20000). 200 distinct values. |
| `wire_center_name` | STRING | Human-readable CO name | `"{City} CO {index}"` (e.g., `"Denver CO 01"`) |
| `state_code` | STRING | 2-char state abbreviation | `{"CO", "MN", "WA", "OR", "ID", "AZ"}` |
| `centroid_lat` | DECIMAL(9,6) | CO building latitude | Real coordinates within state bounding box. Round to 6 decimal places. |
| `centroid_lon` | DECIMAL(9,6) | CO building longitude | Real coordinates within state bounding box. Round to 6 decimal places. |
| `h3_cell_res7` | STRING | H3 cell at res 7 covering CO centroid | H3 res 7 — hex diameter ~5.1 km. Used as boundary basis. |
| `h3_cell_res9` | STRING | H3 cell at res 9 for fine join | Consistent with `synthetic_assets.py` `H3_RESOLUTION = 9`. |
| `boundary_geojson` | STRING | GeoJSON Polygon of serving area | H3 res 7 cell boundary via `h3.cell_to_boundary()`, serialized as `{"type":"Polygon","coordinates":[[...]]}` |
| `wire_center_type` | STRING | CO classification | `{"end_office", "tandem", "remote_terminal", "digital_loop_carrier"}` — weighted: end_office 60%, remote_terminal 25%, tandem 10%, digital_loop_carrier 5% |
| `address_count` | INT | Addresses in this wire center | Count of `geographic_address` records whose `geographic_site_id` maps to this wire center |
| `copper_device_count` | INT | Copper devices in serving area | Count from `tmf_enterprise.physical_device` WHERE device_type IN ('cpe','ont','patch_panel') via address FK |
| `estimated_copper_pairs` | INT | Estimated active copper pairs | `copper_device_count * 25` (consistent with copper_loop_plant target density) |
| `fiber_ready` | BOOLEAN | Fiber infrastructure available at CO | FROM `geographic_site.fiber_connectivity_available` via FK |
| `backup_power` | BOOLEAN | Generator/UPS at CO | FROM `geographic_site.backup_power_available` via FK |
| `area_sq_km` | DECIMAL(8,2) | Approximate serving area | Derived from H3 res 7 cell area (~16.2 km² baseline; scale by wire_center_type factor) |
| `annual_retire_priority` | INT | Retirement wave assignment | 1–5 (1=first wave, 5=last). Assign based on `copper_device_count DESC` so highest-density COs retire first. |
| `puc_filing_required` | BOOLEAN | State PUC notice required | TRUE for all — all LEGACY_STATES require notice (placeholder until REG spec complete) |
| `clli_code` | STRING | CLLI format code (8-char) | `wire_center_id` truncated/padded to 8 chars, uppercase. E.g., `"CODENVE1"` |
| `source` | STRING | Lineage marker | Constant: `"synthetic"` |
| `created_timestamp` | TIMESTAMP | Generator run time | `datetime.utcnow()` at generation time |

---

## GeoJSON Output: `wire_centers.geojson`

In addition to the Delta table, output a GeoJSON FeatureCollection file for direct GIS consumption:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Polygon", "coordinates": [[...]]},
      "properties": {
        "wire_center_id": "CODENVER01",
        "geographic_site_id": 14523,
        "state_code": "CO",
        "wire_center_type": "end_office",
        "copper_device_count": 142,
        "annual_retire_priority": 1
      }
    }
  ]
}
```

Polygons derived from `h3.cell_to_boundary(h3_cell_res7)` — H3 hex vertices in `[lon, lat]` order (GeoJSON convention). Close the ring by repeating the first vertex.

---

## FK Join Strategy

```
wire_center_boundary.geographic_site_id
  → tmf_shared.geographic_site.geographic_site_id
    → (state_province filters to LEGACY_STATES)

wire_center_boundary.wire_center_id
  → (assignment table: geographic_address.geographic_site_id → wire_center_id mapping)
    → copper_loop_plant.geographic_address_id
      → tmf_enterprise.physical_device.physical_device_id
```

**Address assignment rule:** Group `geographic_site_id` values from `geographic_address` into wire centers by spatial proximity of generated CO centroids. Each `geographic_site` record maps to exactly one wire center (nearest centroid by Euclidean distance within state).

**Cardinality:**
- 200 wire centers total
- ~740 LEGACY_STATE geographic_site records → ~3-4 sites per wire center (each site brings its 1-7 addresses)
- ~1,148 total addresses → ~5-6 addresses per wire center on average
- ~2,011 copper devices → ~10 devices per wire center on average
- Note: Low address-per-wire-center count is a synthetic data artifact. The addresses serve as FK targets for copper loop plant records, which is the primary use.

---

## Implementation Notes

1. **H3 library:** `import h3` — available in `synthetic_assets.py` environment. Use `h3.latlng_to_cell(lat, lon, 7)` for res-7 and `h3.cell_to_boundary(cell)` for polygon vertices (returns list of `(lat, lon)` tuples — flip to `[lon, lat]` for GeoJSON).
2. **Determinism seed:** Use `seed=42` (consistent with `synthetic_assets.py`). State-level seeds: CO→42, MN→43, WA→44, OR→45, ID→46, AZ→47.
3. **Geographic_site FK sampling:** Pull real IDs from catalog at generation time: `SELECT geographic_site_id FROM cdm_tmforum.tmf_shared.geographic_site WHERE state_province = '{state}' LIMIT {n}`.
4. **Device count computation:** At generation time, join `physical_device → geographic_address → geographic_site` to count copper devices per site, then sum per wire center.
5. **H3 collision handling:** If two COs in the same state land in the same H3 res-7 cell, shift the second CO by ±0.01° and recompute the cell.
6. **Output schema target:** `cdm_tmforum.copper_retirement.wire_center_boundary` — create schema if needed: `CREATE SCHEMA IF NOT EXISTS cdm_tmforum.copper_retirement`.
