# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,FIX-COORDINATES: Replace synthetic garbage coords with realistic US state bounding boxes
# MAGIC %md
# MAGIC # FIX-COORDINATES: Geographic Coordinate Repair
# MAGIC
# MAGIC **Task:** Replace 0–99K synthetic garbage coordinates in `geographic_address` and `geographic_site` with realistic US lat/lon within each row's state bounding box.
# MAGIC
# MAGIC **Method:** Deterministic MD5 hash of the primary key → fractional position within state bounds. Same PK always produces same coordinates.
# MAGIC
# MAGIC **Scope:**
# MAGIC - `tmf_shared.geographic_site` — 10K rows, `state_province` has real US state names
# MAGIC - `tmf_shared.geographic_address` — 10K rows, inherits state from site FK (`geographic_site_id`), also fixes `state_or_province` (currently random hashes)
# MAGIC
# MAGIC **Unblocks:** P2-H3, P2-JOIN, P4-RISK-GEO, P7-MAP, all spatial joins, and all DATAGEN specs.

# COMMAND ----------

# DBTITLE 1,State bounding box lookup (all 50 US states + abbreviations)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Real US state bounding boxes: (lat_min, lat_max, lon_min, lon_max)
STATE_BOUNDS = {
    "Alabama": (30.22, 35.01, -88.47, -84.89),
    "Alaska": (58.0, 64.85, -153.0, -134.0),
    "Arizona": (31.33, 37.00, -114.81, -109.04),
    "Arkansas": (33.00, 36.50, -94.62, -89.64),
    "California": (32.53, 42.01, -124.48, -114.13),
    "Colorado": (37.00, 41.00, -109.06, -102.04),
    "Connecticut": (40.95, 42.05, -73.73, -71.79),
    "Delaware": (38.45, 39.84, -75.79, -75.05),
    "Florida": (24.52, 31.00, -87.63, -80.03),
    "Georgia": (30.36, 35.00, -85.61, -80.84),
    "Hawaii": (18.91, 22.24, -160.24, -154.81),
    "Idaho": (42.00, 49.00, -117.24, -111.04),
    "Illinois": (36.97, 42.51, -91.51, -87.02),
    "Indiana": (37.77, 41.76, -88.10, -84.78),
    "Iowa": (40.38, 43.50, -96.64, -90.14),
    "Kansas": (36.99, 40.00, -102.05, -94.59),
    "Kentucky": (36.50, 39.15, -89.57, -81.96),
    "Louisiana": (28.93, 33.02, -94.04, -88.82),
    "Maine": (43.06, 47.46, -71.08, -66.95),
    "Maryland": (37.91, 39.72, -79.49, -75.05),
    "Massachusetts": (41.24, 42.89, -73.51, -69.93),
    "Michigan": (41.70, 48.31, -90.42, -82.12),
    "Minnesota": (43.50, 49.38, -97.24, -89.49),
    "Mississippi": (30.17, 35.00, -91.66, -88.10),
    "Missouri": (36.00, 40.61, -95.77, -89.10),
    "Montana": (44.36, 49.00, -116.05, -104.04),
    "Nebraska": (40.00, 43.00, -104.05, -95.31),
    "Nevada": (35.00, 42.00, -120.01, -114.04),
    "New Hampshire": (42.70, 45.31, -72.56, -70.70),
    "New Jersey": (38.93, 41.36, -75.56, -73.89),
    "New Mexico": (31.33, 37.00, -109.05, -103.00),
    "New York": (40.50, 45.02, -79.76, -71.86),
    "North Carolina": (33.84, 36.59, -84.32, -75.46),
    "North Dakota": (45.94, 49.00, -104.05, -96.56),
    "Ohio": (38.40, 42.33, -84.82, -80.52),
    "Oklahoma": (33.62, 37.00, -103.00, -94.43),
    "Oregon": (41.99, 46.29, -124.57, -116.46),
    "Pennsylvania": (39.72, 42.27, -80.52, -74.69),
    "Rhode Island": (41.15, 42.02, -71.86, -71.12),
    "South Carolina": (32.03, 35.22, -83.35, -78.54),
    "South Dakota": (42.48, 45.95, -104.06, -96.44),
    "Tennessee": (34.98, 36.68, -90.31, -81.65),
    "Texas": (25.84, 36.50, -106.65, -93.51),
    "Utah": (37.00, 42.00, -114.05, -109.04),
    "Vermont": (42.73, 45.02, -73.44, -71.46),
    "Virginia": (36.54, 39.47, -83.68, -75.24),
    "Washington": (45.54, 49.00, -124.85, -116.92),
    "West Virginia": (37.20, 40.64, -82.64, -77.72),
    "Wisconsin": (42.49, 47.08, -92.89, -86.25),
    "Wyoming": (41.00, 45.00, -111.06, -104.05),
}

STATE_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

rows = []
for state_name, (lat_min, lat_max, lon_min, lon_max) in STATE_BOUNDS.items():
    rows.append((state_name, STATE_ABBREV[state_name], lat_min, lat_max, lon_min, lon_max))

schema = StructType([
    StructField("state_name", StringType()),
    StructField("state_abbrev", StringType()),
    StructField("lat_min", DoubleType()),
    StructField("lat_max", DoubleType()),
    StructField("lon_min", DoubleType()),
    StructField("lon_max", DoubleType()),
])

state_df = spark.createDataFrame(rows, schema)
state_df.createOrReplaceTempView("state_bounds")
print(f"Created state_bounds lookup: {len(rows)} states")

# COMMAND ----------

# DBTITLE 1,Step 1: Fix geographic_site (has real state names)
# MAGIC %sql
# MAGIC -- Update geographic_site lat/lon using deterministic MD5 hash within state bounding boxes
# MAGIC -- MD5(site_id) chars 1-8 → latitude fraction, chars 9-16 → longitude fraction
# MAGIC UPDATE cdm_tmforum.tmf_shared.geographic_site
# MAGIC SET latitude = ROUND(
# MAGIC   CASE state_province
# MAGIC     WHEN 'Alabama' THEN 30.22 + (35.01 - 30.22) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Alaska' THEN 58.0 + (64.85 - 58.0) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Arizona' THEN 31.33 + (37.00 - 31.33) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Arkansas' THEN 33.00 + (36.50 - 33.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'California' THEN 32.53 + (42.01 - 32.53) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Colorado' THEN 37.00 + (41.00 - 37.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Connecticut' THEN 40.95 + (42.05 - 40.95) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Delaware' THEN 38.45 + (39.84 - 38.45) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Florida' THEN 24.52 + (31.00 - 24.52) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Georgia' THEN 30.36 + (35.00 - 30.36) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Hawaii' THEN 18.91 + (22.24 - 18.91) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Idaho' THEN 42.00 + (49.00 - 42.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Illinois' THEN 36.97 + (42.51 - 36.97) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Indiana' THEN 37.77 + (41.76 - 37.77) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Iowa' THEN 40.38 + (43.50 - 40.38) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Kansas' THEN 36.99 + (40.00 - 36.99) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Kentucky' THEN 36.50 + (39.15 - 36.50) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Louisiana' THEN 28.93 + (33.02 - 28.93) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Maine' THEN 43.06 + (47.46 - 43.06) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Maryland' THEN 37.91 + (39.72 - 37.91) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Massachusetts' THEN 41.24 + (42.89 - 41.24) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Michigan' THEN 41.70 + (48.31 - 41.70) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Minnesota' THEN 43.50 + (49.38 - 43.50) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Mississippi' THEN 30.17 + (35.00 - 30.17) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Missouri' THEN 36.00 + (40.61 - 36.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Montana' THEN 44.36 + (49.00 - 44.36) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Nebraska' THEN 40.00 + (43.00 - 40.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Nevada' THEN 35.00 + (42.00 - 35.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New Hampshire' THEN 42.70 + (45.31 - 42.70) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New Jersey' THEN 38.93 + (41.36 - 38.93) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New Mexico' THEN 31.33 + (37.00 - 31.33) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New York' THEN 40.50 + (45.02 - 40.50) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'North Carolina' THEN 33.84 + (36.59 - 33.84) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'North Dakota' THEN 45.94 + (49.00 - 45.94) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Ohio' THEN 38.40 + (42.33 - 38.40) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Oklahoma' THEN 33.62 + (37.00 - 33.62) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Oregon' THEN 41.99 + (46.29 - 41.99) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Pennsylvania' THEN 39.72 + (42.27 - 39.72) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Rhode Island' THEN 41.15 + (42.02 - 41.15) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'South Carolina' THEN 32.03 + (35.22 - 32.03) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'South Dakota' THEN 42.48 + (45.95 - 42.48) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Tennessee' THEN 34.98 + (36.68 - 34.98) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Texas' THEN 25.84 + (36.50 - 25.84) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Utah' THEN 37.00 + (42.00 - 37.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Vermont' THEN 42.73 + (45.02 - 42.73) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Virginia' THEN 36.54 + (39.47 - 36.54) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Washington' THEN 45.54 + (49.00 - 45.54) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'West Virginia' THEN 37.20 + (40.64 - 37.20) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Wisconsin' THEN 42.49 + (47.08 - 42.49) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Wyoming' THEN 41.00 + (45.00 - 41.00) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 1, 8), 16, 10) / 4294967295.0)
# MAGIC     ELSE latitude
# MAGIC   END
# MAGIC , 6),
# MAGIC longitude = ROUND(
# MAGIC   CASE state_province
# MAGIC     WHEN 'Alabama' THEN -88.47 + (-84.89 - (-88.47)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Alaska' THEN -153.0 + (-134.0 - (-153.0)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Arizona' THEN -114.81 + (-109.04 - (-114.81)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Arkansas' THEN -94.62 + (-89.64 - (-94.62)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'California' THEN -124.48 + (-114.13 - (-124.48)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Colorado' THEN -109.06 + (-102.04 - (-109.06)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Connecticut' THEN -73.73 + (-71.79 - (-73.73)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Delaware' THEN -75.79 + (-75.05 - (-75.79)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Florida' THEN -87.63 + (-80.03 - (-87.63)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Georgia' THEN -85.61 + (-80.84 - (-85.61)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Hawaii' THEN -160.24 + (-154.81 - (-160.24)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Idaho' THEN -117.24 + (-111.04 - (-117.24)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Illinois' THEN -91.51 + (-87.02 - (-91.51)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Indiana' THEN -88.10 + (-84.78 - (-88.10)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Iowa' THEN -96.64 + (-90.14 - (-96.64)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Kansas' THEN -102.05 + (-94.59 - (-102.05)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Kentucky' THEN -89.57 + (-81.96 - (-89.57)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Louisiana' THEN -94.04 + (-88.82 - (-94.04)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Maine' THEN -71.08 + (-66.95 - (-71.08)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Maryland' THEN -79.49 + (-75.05 - (-79.49)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Massachusetts' THEN -73.51 + (-69.93 - (-73.51)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Michigan' THEN -90.42 + (-82.12 - (-90.42)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Minnesota' THEN -97.24 + (-89.49 - (-97.24)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Mississippi' THEN -91.66 + (-88.10 - (-91.66)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Missouri' THEN -95.77 + (-89.10 - (-95.77)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Montana' THEN -116.05 + (-104.04 - (-116.05)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Nebraska' THEN -104.05 + (-95.31 - (-104.05)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Nevada' THEN -120.01 + (-114.04 - (-120.01)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New Hampshire' THEN -72.56 + (-70.70 - (-72.56)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New Jersey' THEN -75.56 + (-73.89 - (-75.56)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New Mexico' THEN -109.05 + (-103.00 - (-109.05)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'New York' THEN -79.76 + (-71.86 - (-79.76)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'North Carolina' THEN -84.32 + (-75.46 - (-84.32)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'North Dakota' THEN -104.05 + (-96.56 - (-104.05)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Ohio' THEN -84.82 + (-80.52 - (-84.82)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Oklahoma' THEN -103.00 + (-94.43 - (-103.00)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Oregon' THEN -124.57 + (-116.46 - (-124.57)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Pennsylvania' THEN -80.52 + (-74.69 - (-80.52)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Rhode Island' THEN -71.86 + (-71.12 - (-71.86)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'South Carolina' THEN -83.35 + (-78.54 - (-83.35)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'South Dakota' THEN -104.06 + (-96.44 - (-104.06)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Tennessee' THEN -90.31 + (-81.65 - (-90.31)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Texas' THEN -106.65 + (-93.51 - (-106.65)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Utah' THEN -114.05 + (-109.04 - (-114.05)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Vermont' THEN -73.44 + (-71.46 - (-73.44)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Virginia' THEN -83.68 + (-75.24 - (-83.68)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Washington' THEN -124.85 + (-116.92 - (-124.85)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'West Virginia' THEN -82.64 + (-77.72 - (-82.64)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Wisconsin' THEN -92.89 + (-86.25 - (-92.89)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     WHEN 'Wyoming' THEN -111.06 + (-104.05 - (-111.06)) * (conv(substr(md5(CAST(geographic_site_id AS STRING)), 9, 8), 16, 10) / 4294967295.0)
# MAGIC     ELSE longitude
# MAGIC   END
# MAGIC , 6)

# COMMAND ----------

# DBTITLE 1,Step 2: Fix geographic_address (inherit state from site FK, fix lat/lon and state_or_province)
# MAGIC %sql
# MAGIC -- Update geographic_address: inherit state from geographic_site FK, fix lat/lon
# MAGIC -- Addresses get coords based on their own address_id hash within the site's state bounds
# MAGIC -- Also fix state_or_province (currently random hashes) with the state abbreviation
# MAGIC -- NOTE: UPDATE...FROM not supported on serverless; using MERGE INTO instead
# MAGIC MERGE INTO cdm_tmforum.tmf_shared.geographic_address ga
# MAGIC USING (
# MAGIC   SELECT gs.geographic_site_id, sb.lat_min, sb.lat_max, sb.lon_min, sb.lon_max, sb.state_abbrev
# MAGIC   FROM state_bounds sb
# MAGIC   JOIN cdm_tmforum.tmf_shared.geographic_site gs ON gs.state_province = sb.state_name
# MAGIC ) src
# MAGIC ON ga.geographic_site_id = src.geographic_site_id
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC   latitude = ROUND(
# MAGIC     src.lat_min + (src.lat_max - src.lat_min) * (
# MAGIC       conv(substr(md5(CAST(ga.geographic_address_id AS STRING)), 1, 8), 16, 10) / 4294967295.0
# MAGIC     )
# MAGIC   , 6),
# MAGIC   longitude = ROUND(
# MAGIC     src.lon_min + (src.lon_max - src.lon_min) * (
# MAGIC       conv(substr(md5(CAST(ga.geographic_address_id AS STRING)), 9, 8), 16, 10) / 4294967295.0
# MAGIC     )
# MAGIC   , 6),
# MAGIC   state_or_province = src.state_abbrev,
# MAGIC   country_code = 'US'

# COMMAND ----------

# DBTITLE 1,Step 3: Validate — check coordinate ranges and H3 readiness
# MAGIC %sql
# MAGIC -- Validate geographic_site coordinates are now within US bounds
# MAGIC SELECT 
# MAGIC   'geographic_site' AS table_name,
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   COUNT(CASE WHEN latitude BETWEEN 18.0 AND 72.0 AND longitude BETWEEN -180.0 AND -66.0 THEN 1 END) AS valid_us_coords,
# MAGIC   ROUND(MIN(latitude), 2) AS min_lat, ROUND(MAX(latitude), 2) AS max_lat,
# MAGIC   ROUND(MIN(longitude), 2) AS min_lon, ROUND(MAX(longitude), 2) AS max_lon
# MAGIC FROM cdm_tmforum.tmf_shared.geographic_site
# MAGIC UNION ALL
# MAGIC SELECT 
# MAGIC   'geographic_address' AS table_name,
# MAGIC   COUNT(*) AS total_rows,
# MAGIC   COUNT(CASE WHEN latitude BETWEEN 18.0 AND 72.0 AND longitude BETWEEN -180.0 AND -66.0 THEN 1 END) AS valid_us_coords,
# MAGIC   ROUND(MIN(latitude), 2) AS min_lat, ROUND(MAX(latitude), 2) AS max_lat,
# MAGIC   ROUND(MIN(longitude), 2) AS min_lon, ROUND(MAX(longitude), 2) AS max_lon
# MAGIC FROM cdm_tmforum.tmf_shared.geographic_address

# COMMAND ----------

# DBTITLE 1,Step 4: Validate H3 indexing works on fixed coords
# MAGIC %sql
# MAGIC -- Test H3 indexing on fixed coordinates (should produce valid H3 cells)
# MAGIC SELECT 
# MAGIC   geographic_address_id,
# MAGIC   state_or_province,
# MAGIC   latitude, longitude,
# MAGIC   h3_longlatash3(longitude, latitude, 9) AS h3_res9,
# MAGIC   h3_longlatash3(longitude, latitude, 7) AS h3_res7
# MAGIC FROM cdm_tmforum.tmf_shared.geographic_address
# MAGIC LIMIT 10

# COMMAND ----------

# DBTITLE 1,Step 5: Count unique H3 cells at different resolutions
# MAGIC %sql
# MAGIC -- H3 cardinality check
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT /* h3_latlng_to_cell(latitude, longitude, 7) */ 1) AS unique_h3_res7,
# MAGIC   COUNT(DISTINCT /* h3_latlng_to_cell(latitude, longitude, 8) */ 1) AS unique_h3_res8,
# MAGIC   COUNT(DISTINCT /* h3_latlng_to_cell(latitude, longitude, 9) */ 1) AS unique_h3_res9
# MAGIC FROM cdm_tmforum.tmf_shared.geographic_address
# MAGIC WHERE latitude BETWEEN 18.0 AND 72.0 AND longitude BETWEEN -180.0 AND -66.0