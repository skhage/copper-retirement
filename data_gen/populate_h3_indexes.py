# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,P2-H3: Coordinate repair + H3 index population
# MAGIC %md
# MAGIC # Spatial data prep: coordinate repair + H3 index population
# MAGIC
# MAGIC > **SYNTHETIC DATA** — coordinates in the TMF SID demo dataset are synthetic; Part A places them deterministically inside real US state bounding boxes.
# MAGIC
# MAGIC **Parameters:** `catalog` (default `cdm_tmforum`, bundle var `catalog_name`), `repair_coordinates` (default `false`). All SQL runs against `USE CATALOG <catalog>` — no hardcoded catalog names (ACC-DE-PARAMETERIZE).
# MAGIC
# MAGIC **Part A (optional, `repair_coordinates=true`)** — merged from the retired `data_gen/fix_coordinates` (ACC-NB-DEMO-CONSOLIDATE): replaces out-of-range lat/lon in `tmf_shared.geographic_site` / `geographic_address` using an MD5 hash of the primary key -> fractional position inside the row's state bounding box (same PK always gives the same coordinates) and sets `geographic_address.state_or_province` to the state abbreviation. Run once on a fresh workspace **before** Part B.
# MAGIC
# MAGIC **Part B** — populates h3_res8/h3_res9.
# MAGIC
# MAGIC ## Part B: Populate H3 Index Columns
# MAGIC
# MAGIC **Task:** Populate h3_res8 and h3_res9 columns on 3 tables using `h3_longlatash3(longitude, latitude, resolution)`.
# MAGIC
# MAGIC **Prerequisites (completed by @data-engineer 2026-09-12):**
# MAGIC - `ALTER TABLE ADD COLUMNS` executed on all 3 tables (columns exist, all NULL)
# MAGIC - H3 function validated: 100% conversion rate on 10K addresses
# MAGIC - FK chains validated: physical_device → geographic_address (100%), CFS → geographic_address (100%)
# MAGIC
# MAGIC **Run All cells below to populate.**

# COMMAND ----------

# DBTITLE 1,Parameters: catalog and coordinate repair flag
dbutils.widgets.text("catalog", "cdm_tmforum")
dbutils.widgets.dropdown("repair_coordinates", "false", ["false", "true"])
CATALOG = dbutils.widgets.get("catalog")
REPAIR_COORDINATES = dbutils.widgets.get("repair_coordinates") == "true"

# All later %sql cells resolve 2-part names (tmf_shared.*, tmf_enterprise.*, tmf_service.*) against this catalog
spark.sql(f"USE CATALOG IDENTIFIER('{CATALOG}')")
print(f"Catalog: {spark.catalog.currentCatalog()} | repair_coordinates={REPAIR_COORDINATES}")

# COMMAND ----------

# DBTITLE 1,Part A: Coordinate repair (optional)
# MAGIC %md
# MAGIC ## Part A: Coordinate repair (optional — `repair_coordinates=true`)
# MAGIC Rewrites shared TMF MDM coordinates, so it is off by default. Only rows whose lat/lon fall **outside** their state bounding box are touched, so later refinements are preserved (verified 2026-10-24: all 1,548 sites in the 8 checked states are already in-box, so a re-run here is a no-op). Deterministic: MD5(PK) chars 1–8 -> latitude fraction, chars 9–16 -> longitude fraction inside the state bounding box.

# COMMAND ----------

# DBTITLE 1,Part A1: State bounding box lookup
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# US state bounding boxes: (abbrev, lat_min, lat_max, lon_min, lon_max)
STATE_BOUNDS = {
    "Alabama": ("AL", 30.22, 35.01, -88.47, -84.89), "Alaska": ("AK", 58.0, 64.85, -153.0, -134.0),
    "Arizona": ("AZ", 31.33, 37.00, -114.81, -109.04), "Arkansas": ("AR", 33.00, 36.50, -94.62, -89.64),
    "California": ("CA", 32.53, 42.01, -124.48, -114.13), "Colorado": ("CO", 37.00, 41.00, -109.06, -102.04),
    "Connecticut": ("CT", 40.95, 42.05, -73.73, -71.79), "Delaware": ("DE", 38.45, 39.84, -75.79, -75.05),
    "Florida": ("FL", 24.52, 31.00, -87.63, -80.03), "Georgia": ("GA", 30.36, 35.00, -85.61, -80.84),
    "Hawaii": ("HI", 18.91, 22.24, -160.24, -154.81), "Idaho": ("ID", 42.00, 49.00, -117.24, -111.04),
    "Illinois": ("IL", 36.97, 42.51, -91.51, -87.02), "Indiana": ("IN", 37.77, 41.76, -88.10, -84.78),
    "Iowa": ("IA", 40.38, 43.50, -96.64, -90.14), "Kansas": ("KS", 36.99, 40.00, -102.05, -94.59),
    "Kentucky": ("KY", 36.50, 39.15, -89.57, -81.96), "Louisiana": ("LA", 28.93, 33.02, -94.04, -88.82),
    "Maine": ("ME", 43.06, 47.46, -71.08, -66.95), "Maryland": ("MD", 37.91, 39.72, -79.49, -75.05),
    "Massachusetts": ("MA", 41.24, 42.89, -73.51, -69.93), "Michigan": ("MI", 41.70, 48.31, -90.42, -82.12),
    "Minnesota": ("MN", 43.50, 49.38, -97.24, -89.49), "Mississippi": ("MS", 30.17, 35.00, -91.66, -88.10),
    "Missouri": ("MO", 36.00, 40.61, -95.77, -89.10), "Montana": ("MT", 44.36, 49.00, -116.05, -104.04),
    "Nebraska": ("NE", 40.00, 43.00, -104.05, -95.31), "Nevada": ("NV", 35.00, 42.00, -120.01, -114.04),
    "New Hampshire": ("NH", 42.70, 45.31, -72.56, -70.70), "New Jersey": ("NJ", 38.93, 41.36, -75.56, -73.89),
    "New Mexico": ("NM", 31.33, 37.00, -109.05, -103.00), "New York": ("NY", 40.50, 45.02, -79.76, -71.86),
    "North Carolina": ("NC", 33.84, 36.59, -84.32, -75.46), "North Dakota": ("ND", 45.94, 49.00, -104.05, -96.56),
    "Ohio": ("OH", 38.40, 42.33, -84.82, -80.52), "Oklahoma": ("OK", 33.62, 37.00, -103.00, -94.43),
    "Oregon": ("OR", 41.99, 46.29, -124.57, -116.46), "Pennsylvania": ("PA", 39.72, 42.27, -80.52, -74.69),
    "Rhode Island": ("RI", 41.15, 42.02, -71.86, -71.12), "South Carolina": ("SC", 32.03, 35.22, -83.35, -78.54),
    "South Dakota": ("SD", 42.48, 45.95, -104.06, -96.44), "Tennessee": ("TN", 34.98, 36.68, -90.31, -81.65),
    "Texas": ("TX", 25.84, 36.50, -106.65, -93.51), "Utah": ("UT", 37.00, 42.00, -114.05, -109.04),
    "Vermont": ("VT", 42.73, 45.02, -73.44, -71.46), "Virginia": ("VA", 36.54, 39.47, -83.68, -75.24),
    "Washington": ("WA", 45.54, 49.00, -124.85, -116.92), "West Virginia": ("WV", 37.20, 40.64, -82.64, -77.72),
    "Wisconsin": ("WI", 42.49, 47.08, -92.89, -86.25), "Wyoming": ("WY", 41.00, 45.00, -111.06, -104.05),
}
schema = StructType([StructField(n, t) for n, t in [
    ("state_name", StringType()), ("state_abbrev", StringType()), ("lat_min", DoubleType()),
    ("lat_max", DoubleType()), ("lon_min", DoubleType()), ("lon_max", DoubleType())]])
spark.createDataFrame([(k, *v) for k, v in STATE_BOUNDS.items()], schema).createOrReplaceTempView("state_bounds")
print(f"state_bounds lookup: {len(STATE_BOUNDS)} states")

# COMMAND ----------

# DBTITLE 1,Part A2: Repair geographic_site and geographic_address coordinates
HASH_FRAC = "conv(substr(md5(CAST({pk} AS STRING)), {start}, 8), 16, 10) / 4294967295.0"

if not REPAIR_COORDINATES:
    print("Skipping coordinate repair (repair_coordinates=false)")
else:
    # A2a: geographic_site has real state names in state_province
    spark.sql(f"""
        MERGE INTO tmf_shared.geographic_site gs
        USING state_bounds sb ON gs.state_province = sb.state_name
        -- Only repair rows OUTSIDE their state box: preserves later coordinate refinements (idempotent)
        WHEN MATCHED AND NOT (COALESCE(gs.latitude BETWEEN sb.lat_min AND sb.lat_max, FALSE)
                              AND COALESCE(gs.longitude BETWEEN sb.lon_min AND sb.lon_max, FALSE)) THEN UPDATE SET
          latitude  = ROUND(sb.lat_min + (sb.lat_max - sb.lat_min) * {HASH_FRAC.format(pk='gs.geographic_site_id', start=1)}, 6),
          longitude = ROUND(sb.lon_min + (sb.lon_max - sb.lon_min) * {HASH_FRAC.format(pk='gs.geographic_site_id', start=9)}, 6)
    """)
    # A2b: geographic_address inherits state from its site FK; also fixes state_or_province
    spark.sql(f"""
        MERGE INTO tmf_shared.geographic_address ga
        USING (
          SELECT gs.geographic_site_id, sb.lat_min, sb.lat_max, sb.lon_min, sb.lon_max, sb.state_abbrev
          FROM state_bounds sb JOIN tmf_shared.geographic_site gs ON gs.state_province = sb.state_name
        ) src
        ON ga.geographic_site_id = src.geographic_site_id
        WHEN MATCHED AND NOT (COALESCE(ga.latitude BETWEEN src.lat_min AND src.lat_max, FALSE)
                              AND COALESCE(ga.longitude BETWEEN src.lon_min AND src.lon_max, FALSE)) THEN UPDATE SET
          latitude  = ROUND(src.lat_min + (src.lat_max - src.lat_min) * {HASH_FRAC.format(pk='ga.geographic_address_id', start=1)}, 6),
          longitude = ROUND(src.lon_min + (src.lon_max - src.lon_min) * {HASH_FRAC.format(pk='ga.geographic_address_id', start=9)}, 6),
          state_or_province = src.state_abbrev,
          country_code = 'US'
    """)

# Validate: coordinates within US bounds (runs either way)
display(spark.sql("""
    SELECT t AS table_name, COUNT(*) AS total_rows,
           COUNT_IF(latitude BETWEEN 18.0 AND 72.0 AND longitude BETWEEN -180.0 AND -66.0) AS valid_us_coords,
           ROUND(MIN(latitude), 2) AS min_lat, ROUND(MAX(latitude), 2) AS max_lat,
           ROUND(MIN(longitude), 2) AS min_lon, ROUND(MAX(longitude), 2) AS max_lon
    FROM (SELECT 'geographic_site' AS t, latitude, longitude FROM tmf_shared.geographic_site
          UNION ALL SELECT 'geographic_address', latitude, longitude FROM tmf_shared.geographic_address)
    GROUP BY t
"""))

# COMMAND ----------

# DBTITLE 1,Cell 1: Populate geographic_address H3 columns
# MAGIC %sql
# MAGIC -- Step 1: Populate h3_res8 and h3_res9 on geographic_address (10K rows)
# MAGIC -- h3_longlatash3 takes (longitude, latitude, resolution) — note lon FIRST
# MAGIC MERGE INTO tmf_shared.geographic_address AS target
# MAGIC USING (
# MAGIC   SELECT 
# MAGIC     geographic_address_id,
# MAGIC     h3_longlatash3(longitude, latitude, 8) AS h3_res8_new,
# MAGIC     h3_longlatash3(longitude, latitude, 9) AS h3_res9_new
# MAGIC   FROM tmf_shared.geographic_address
# MAGIC   WHERE latitude IS NOT NULL AND longitude IS NOT NULL
# MAGIC ) AS source
# MAGIC ON target.geographic_address_id = source.geographic_address_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.h3_res8 = source.h3_res8_new,
# MAGIC   target.h3_res9 = source.h3_res9_new

# COMMAND ----------

# DBTITLE 1,Cell 2: Populate physical_device H3 via geographic_address FK join
# MAGIC %sql
# MAGIC -- Step 2: Populate h3_res8 and h3_res9 on physical_device via geographic_address_id FK
# MAGIC -- 10K devices, 2,672 copper (cpe/ont/olt/patch_panel), 100% FK match
# MAGIC MERGE INTO tmf_enterprise.physical_device AS target
# MAGIC USING (
# MAGIC   SELECT 
# MAGIC     pd.physical_device_id,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 8) AS h3_res8_new,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 9) AS h3_res9_new
# MAGIC   FROM tmf_enterprise.physical_device pd
# MAGIC   JOIN tmf_shared.geographic_address ga 
# MAGIC     ON pd.geographic_address_id = ga.geographic_address_id
# MAGIC   WHERE ga.latitude IS NOT NULL AND ga.longitude IS NOT NULL
# MAGIC ) AS source
# MAGIC ON target.physical_device_id = source.physical_device_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.h3_res8 = source.h3_res8_new,
# MAGIC   target.h3_res9 = source.h3_res9_new

# COMMAND ----------

# DBTITLE 1,Cell 3: Populate CFS H3 via geographic_address FK join
# MAGIC %sql
# MAGIC -- Step 3: Populate h3_res8 and h3_res9 on customer_facing_service via geographic_address_id FK
# MAGIC -- 100K CFS rows, 17,655 copper (voice/fixed_line/broadband), 100% FK match
# MAGIC MERGE INTO tmf_service.customer_facing_service AS target
# MAGIC USING (
# MAGIC   SELECT 
# MAGIC     cfs.customer_facing_service_id,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 8) AS h3_res8_new,
# MAGIC     h3_longlatash3(ga.longitude, ga.latitude, 9) AS h3_res9_new
# MAGIC   FROM tmf_service.customer_facing_service cfs
# MAGIC   JOIN tmf_shared.geographic_address ga 
# MAGIC     ON cfs.geographic_address_id = ga.geographic_address_id
# MAGIC   WHERE ga.latitude IS NOT NULL AND ga.longitude IS NOT NULL
# MAGIC ) AS source
# MAGIC ON target.customer_facing_service_id = source.customer_facing_service_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   target.h3_res8 = source.h3_res8_new,
# MAGIC   target.h3_res9 = source.h3_res9_new

# COMMAND ----------

# DBTITLE 1,Cell 4: Validate H3 population
# MAGIC %sql
# MAGIC -- Step 4: Validate H3 population across all 3 tables
# MAGIC SELECT 'geographic_address' AS table_name, COUNT(*) AS total, COUNT(h3_res8) AS h3_res8_pop, COUNT(h3_res9) AS h3_res9_pop, COUNT(DISTINCT h3_res8) AS distinct_res8, COUNT(DISTINCT h3_res9) AS distinct_res9
# MAGIC FROM tmf_shared.geographic_address
# MAGIC UNION ALL
# MAGIC SELECT 'physical_device', COUNT(*), COUNT(h3_res8), COUNT(h3_res9), COUNT(DISTINCT h3_res8), COUNT(DISTINCT h3_res9)
# MAGIC FROM tmf_enterprise.physical_device
# MAGIC UNION ALL
# MAGIC SELECT 'customer_facing_service', COUNT(*), COUNT(h3_res8), COUNT(h3_res9), COUNT(DISTINCT h3_res8), COUNT(DISTINCT h3_res9)
# MAGIC FROM tmf_service.customer_facing_service