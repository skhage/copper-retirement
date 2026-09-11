-- wire_center_boundaries.sql
-- GeoJSON polygon boundaries for wire-center overlay on the map
-- BLOCKED: Requires P0-DATAGEN-WIRECENTER-EXECUTE to create the table
--
-- Parameters:
--   :state_filter - state abbreviation or '' for all

-- TODO: Replace with actual table when P0-DATAGEN-WIRECENTER-EXECUTE lands
-- Expected schema from SPEC_wire_center_boundary.md:
--   wire_center_id, wire_center_name, geographic_site_id, state,
--   boundary_geojson (GeoJSON polygon string), center_lat, center_lon,
--   address_count, h3_cells (array of H3 indexes)

-- Placeholder: return empty result set with expected schema
SELECT
  CAST(NULL AS LONG) AS wire_center_id,
  CAST(NULL AS STRING) AS wire_center_name,
  CAST(NULL AS LONG) AS geographic_site_id,
  CAST(NULL AS STRING) AS state,
  CAST(NULL AS STRING) AS boundary_geojson,
  CAST(NULL AS DOUBLE) AS center_lat,
  CAST(NULL AS DOUBLE) AS center_lon,
  CAST(NULL AS INT) AS address_count
WHERE 1 = 0
