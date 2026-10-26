"""Provision the UC objects the unified accelerator app reads (Dig Triage, Plan, Map, Commodity tabs).

ACC-QA-DEF-FRESH-PROVISION (Dig Triage objects) + ACC-DE-FRESH-APP-GOLD (Plan/Map/Commodity objects).

Runs as task 3 of seed_synthetic_sources_job, AFTER refresh_pipeline, because it reads pipeline outputs:
  inputs : <schema>.dig_safe_incident, <schema>.copper_plant_wire_center_jurisdiction   (seeded, task 1)
           <schema>.bronze_copper_devices, <schema>.silver_device_service_impact         (pipeline, task 2)
  outputs: <schema>.silver_dig_incident_enriched (table, SYNTHETIC)
           <schema>.incident_lookup(p_incident_id), <schema>.proximity_search(p_latitude, p_longitude, p_radius_km),
           <schema>.reroute_suggest(p_incident_id)                                       (SQL table functions)

The 811 table <catalog>.provable_resilience_intelligence.stg_811_dig_ticket is created by task 1 (seed);
it is not touched here.

Plan/Map/Commodity objects (ACC-DE-FRESH-APP-GOLD). Their original producers were interactive notebooks that
no longer exist, so they ship as lossless snapshots in --snapshot-dir (<name>.ddl.sql with {fq} placeholder +
<name>.jsonl, see manifest.json for row counts and sha256). Reference export (2026-10-26):
  /Volumes/cdm_tmforum/copper_retirement/regulatory_source_docs/_app_gold_export/  (repo copy: data/app_gold/)
  SYNTHETIC: gold_copper_recovery_schedule, retirement_cost_per_wire_center, copper_risk_predictions,
             gold_wave_schedule, gold_contractor_assignment_plan, retirement_milestones,
             silver_budget_allocation, gold_commodity_price_forecast
  REAL     : copper_commodity_price_official (IMF PCOPPUSDM, https://fred.stlouisfed.org/series/PCOPPUSDM),
             roi_calculator_assumptions (cited ratios + labeled synthetic partner inputs)
  VIEW     : v_partner_value_wire_center (created last; reads the snapshots + seeded/pipeline inputs)

Definitions are copied from the reference workspace (cdm_tmforum.copper_retirement, 2026-10-25) with the
catalog/schema parameterized. Safety: existing objects are skipped unless --replace is passed, so running
this against the reference workspace does not rewrite curated objects.

Usage: python provision_app_objects.py --catalog <catalog> --schema <schema> [--snapshot-dir <dir>] [--replace] [--dry-run]
"""
import argparse
import os
import re

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

SILVER_DIG_SQL = """
CREATE OR REPLACE TABLE {fq}.silver_dig_incident_enriched
COMMENT 'SYNTHETIC DEMO DATA. Silver-layer enriched dig-safe incidents: one row per incident with H3 res8/res9 index, nearest copper device in the same state, copper devices within 50km, impacted services (silver_device_service_impact) and wire center (copper_plant_wire_center_jurisdiction). Read by the Dig Triage tab and the incident_lookup / proximity_search / reroute_suggest functions.'
AS
WITH incidents_h3 AS (
  SELECT d.*,
    h3_longlatash3(CAST(d.longitude AS DOUBLE), CAST(d.latitude AS DOUBLE), 8) AS incident_h3_res8,
    h3_longlatash3(CAST(d.longitude AS DOUBLE), CAST(d.latitude AS DOUBLE), 9) AS incident_h3_res9
  FROM {fq}.dig_safe_incident d
  WHERE d.latitude IS NOT NULL AND d.longitude IS NOT NULL
),
device_wire_center AS (
  SELECT DISTINCT physical_device_id,
    FIRST_VALUE(wire_center_id)   OVER (PARTITION BY physical_device_id ORDER BY wire_center_id) AS wire_center_id,
    FIRST_VALUE(wire_center_name) OVER (PARTITION BY physical_device_id ORDER BY wire_center_id) AS wire_center_name,
    FIRST_VALUE(clli_code)        OVER (PARTITION BY physical_device_id ORDER BY wire_center_id) AS clli_code,
    FIRST_VALUE(fiber_ready)      OVER (PARTITION BY physical_device_id ORDER BY wire_center_id) AS wc_fiber_ready
  FROM {fq}.copper_plant_wire_center_jurisdiction
),
device_wc_dedup AS (
  SELECT DISTINCT physical_device_id, wire_center_id, wire_center_name, clli_code, wc_fiber_ready FROM device_wire_center
),
incident_device_distance AS (
  SELECT ih.incident_id, cd.physical_device_id, cd.device_type, cd.device_status,
    cd.h3_res8 AS device_h3_res8, cd.addr_latitude AS device_latitude, cd.addr_longitude AS device_longitude,
    ROUND(111.32 * SQRT(
      POWER(CAST(ih.latitude AS DOUBLE) - CAST(cd.addr_latitude AS DOUBLE), 2) +
      POWER(COS(RADIANS(CAST(ih.latitude AS DOUBLE))) * (CAST(ih.longitude AS DOUBLE) - CAST(cd.addr_longitude AS DOUBLE)), 2)
    ), 3) AS distance_km
  FROM incidents_h3 ih
  JOIN {fq}.bronze_copper_devices cd ON ih.state = cd.state_code
),
ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY incident_id ORDER BY distance_km) AS rk FROM incident_device_distance),
nearest AS (SELECT * FROM ranked WHERE rk = 1),
nearby_counts AS (
  SELECT incident_id, COUNT(*) AS nearby_copper_device_count, COUNT(DISTINCT device_type) AS nearby_device_types
  FROM incident_device_distance WHERE distance_km <= 50 GROUP BY incident_id
),
impacted_svc AS (
  SELECT n.incident_id,
    COUNT(DISTINCT dsi.customer_facing_service_id) AS impacted_service_count,
    COUNT(DISTINCT dsi.customer_id) AS impacted_customer_count,
    CONCAT_WS(',', COLLECT_SET(dsi.service_type)) AS impacted_service_types_str
  FROM nearest n
  LEFT JOIN {fq}.silver_device_service_impact dsi ON n.physical_device_id = dsi.physical_device_id
  GROUP BY n.incident_id
)
SELECT
  d.incident_id, d.work_id, d.bp_agreement_id, d.geographic_address_id, d.network_route_id, d.state,
  d.latitude AS incident_latitude, d.longitude AS incident_longitude,
  d.incident_date, d.incident_timestamp, d.severity, d.cable_type, d.cable_damage_type, d.root_cause,
  d.contractor_at_fault, d.one_call_ticket_submitted, d.resolution_time_hours, d.reroute_required,
  d.service_interruption, d.affected_pair_count, d.repair_cost_amount, d.depth_of_cover_inches, d.recommended_action,
  ih.incident_h3_res8, ih.incident_h3_res9,
  n.physical_device_id AS nearest_device_id, n.device_type AS nearest_device_type, n.device_status AS nearest_device_status,
  n.device_h3_res8 AS nearest_device_h3, n.device_latitude AS nearest_device_lat, n.device_longitude AS nearest_device_lon,
  n.distance_km AS nearest_device_distance_km,
  COALESCE(nc.nearby_copper_device_count, 0) AS nearby_copper_device_count,
  COALESCE(nc.nearby_device_types, 0) AS nearby_device_types,
  COALESCE(isv.impacted_service_count, 0) AS impacted_service_count,
  COALESCE(isv.impacted_customer_count, 0) AS impacted_customer_count,
  isv.impacted_service_types_str AS impacted_service_types,
  dwc.wire_center_id, dwc.wire_center_name, dwc.clli_code AS wire_center_clli, dwc.wc_fiber_ready AS wire_center_fiber_ready,
  CASE
    WHEN d.severity = 'critical' AND d.service_interruption THEN 'P1'
    WHEN d.severity IN ('critical', 'major') AND d.reroute_required THEN 'P2'
    WHEN d.severity IN ('major', 'moderate') AND d.service_interruption THEN 'P3'
    ELSE 'P4'
  END AS triage_priority,
  current_timestamp() AS _enriched_at
FROM {fq}.dig_safe_incident d
JOIN incidents_h3 ih ON d.incident_id = ih.incident_id
LEFT JOIN nearest n ON d.incident_id = n.incident_id
LEFT JOIN nearby_counts nc ON d.incident_id = nc.incident_id
LEFT JOIN impacted_svc isv ON d.incident_id = isv.incident_id
LEFT JOIN device_wc_dedup dwc ON n.physical_device_id = dwc.physical_device_id
"""

INCIDENT_LOOKUP_SQL = """
CREATE OR REPLACE FUNCTION {fq}.incident_lookup(p_incident_id BIGINT COMMENT 'The unique incident ID to look up')
RETURNS TABLE (incident_id BIGINT, state STRING, incident_date DATE, incident_latitude DECIMAL(9,6), incident_longitude DECIMAL(9,6),
  severity STRING, cable_type STRING, cable_damage_type STRING, root_cause STRING, contractor_at_fault BOOLEAN,
  one_call_ticket_submitted BOOLEAN, resolution_time_hours DECIMAL(6,1), reroute_required BOOLEAN, service_interruption BOOLEAN,
  affected_pair_count INT, repair_cost_amount DECIMAL(10,2), recommended_action STRING, triage_priority STRING,
  nearest_device_id BIGINT, nearest_device_type STRING, nearest_device_distance_km DOUBLE, nearby_copper_device_count INT,
  impacted_service_count INT, impacted_customer_count INT, impacted_service_types STRING, wire_center_id STRING, wire_center_name STRING)
COMMENT 'Retrieves full enriched details for a specific dig-safe incident by ID from silver_dig_incident_enriched (SYNTHETIC). Used by the Dig Triage tab and triage agent.'
RETURN SELECT
    incident_id, state, incident_date, incident_latitude, incident_longitude,
    severity, cable_type, cable_damage_type, root_cause,
    contractor_at_fault, one_call_ticket_submitted, resolution_time_hours,
    reroute_required, service_interruption, affected_pair_count, repair_cost_amount,
    recommended_action, triage_priority,
    nearest_device_id, nearest_device_type, nearest_device_distance_km,
    CAST(nearby_copper_device_count AS INT), CAST(impacted_service_count AS INT),
    CAST(impacted_customer_count AS INT), impacted_service_types,
    wire_center_id, wire_center_name
  FROM {fq}.silver_dig_incident_enriched
  WHERE incident_id = p_incident_id
"""

PROXIMITY_SEARCH_SQL = """
CREATE OR REPLACE FUNCTION {fq}.proximity_search(
  p_latitude DOUBLE COMMENT 'WGS-84 latitude of search center',
  p_longitude DOUBLE COMMENT 'WGS-84 longitude of search center',
  p_radius_km DOUBLE COMMENT 'Search radius in kilometers (default: 25km if NULL)')
RETURNS TABLE (incident_id BIGINT, state STRING, incident_date DATE, severity STRING, cable_type STRING, root_cause STRING,
  service_interruption BOOLEAN, reroute_required BOOLEAN, recommended_action STRING, triage_priority STRING,
  incident_latitude DECIMAL(9,6), incident_longitude DECIMAL(9,6), distance_from_search_km DOUBLE, nearest_device_id BIGINT,
  nearest_device_type STRING, nearest_device_distance_km DOUBLE, nearby_copper_device_count INT, impacted_service_count INT,
  wire_center_id STRING)
COMMENT 'Finds dig-safe incidents (SYNTHETIC) within a radius of a lat/lon point, sorted by distance. Default radius 25km if NULL.'
RETURN SELECT
    incident_id, state, incident_date, severity, cable_type, root_cause,
    service_interruption, reroute_required, recommended_action, triage_priority,
    incident_latitude, incident_longitude,
    ROUND(111.32 * SQRT(
        POWER(CAST(incident_latitude AS DOUBLE) - p_latitude, 2) +
        POWER(COS(RADIANS(p_latitude)) * (CAST(incident_longitude AS DOUBLE) - p_longitude), 2)), 3) AS distance_from_search_km,
    nearest_device_id, nearest_device_type, nearest_device_distance_km,
    CAST(nearby_copper_device_count AS INT), CAST(impacted_service_count AS INT), wire_center_id
  FROM {fq}.silver_dig_incident_enriched
  WHERE 111.32 * SQRT(
      POWER(CAST(incident_latitude AS DOUBLE) - p_latitude, 2) +
      POWER(COS(RADIANS(p_latitude)) * (CAST(incident_longitude AS DOUBLE) - p_longitude), 2)) <= COALESCE(p_radius_km, 25.0)
  ORDER BY distance_from_search_km
"""

REROUTE_SUGGEST_SQL = """
CREATE OR REPLACE FUNCTION {fq}.reroute_suggest(p_incident_id BIGINT COMMENT 'The incident ID to generate reroute suggestions for')
RETURNS TABLE (incident_id BIGINT, incident_state STRING, incident_severity STRING, triage_priority STRING, reroute_required BOOLEAN,
  service_interruption BOOLEAN, recommended_action STRING, affected_pair_count INT, incident_latitude DECIMAL(9,6),
  incident_longitude DECIMAL(9,6), nearest_device_id BIGINT, nearest_device_type STRING, nearest_device_distance_km DOUBLE,
  wire_center_id STRING, wire_center_name STRING, wire_center_fiber_ready BOOLEAN, impacted_service_count INT,
  impacted_customer_count INT, impacted_service_types STRING, reroute_option STRING, reroute_rationale STRING)
COMMENT 'Rule-based reroute suggestion for a dig-safe incident (SYNTHETIC data) from severity, nearby copper, fiber readiness and impacted services.'
RETURN SELECT
    e.incident_id, e.state AS incident_state, e.severity AS incident_severity, e.triage_priority,
    e.reroute_required, e.service_interruption, e.recommended_action, e.affected_pair_count,
    e.incident_latitude, e.incident_longitude, e.nearest_device_id, e.nearest_device_type, e.nearest_device_distance_km,
    e.wire_center_id, e.wire_center_name, e.wire_center_fiber_ready,
    CAST(e.impacted_service_count AS INT), CAST(e.impacted_customer_count AS INT), e.impacted_service_types,
    CASE
      WHEN e.wire_center_fiber_ready = TRUE AND e.service_interruption THEN 'FIBER_MIGRATION'
      WHEN e.reroute_required AND e.nearby_copper_device_count > 2 THEN 'COPPER_REROUTE'
      WHEN e.severity = 'critical' AND e.service_interruption THEN 'EMERGENCY_RESTORE'
      WHEN e.reroute_required THEN 'TEMPORARY_BYPASS'
      WHEN e.service_interruption AND NOT e.reroute_required THEN 'REPAIR_IN_PLACE'
      ELSE 'MONITOR_ONLY'
    END AS reroute_option,
    CASE
      WHEN e.wire_center_fiber_ready = TRUE AND e.service_interruption
        THEN CONCAT('Wire center ', COALESCE(e.wire_center_name, 'unknown'), ' is fiber-ready. Recommend accelerated fiber migration for ', CAST(COALESCE(e.impacted_customer_count, 0) AS STRING), ' affected customers instead of copper repair.')
      WHEN e.reroute_required AND e.nearby_copper_device_count > 2
        THEN CONCAT('Reroute via alternate copper path. ', CAST(e.nearby_copper_device_count AS STRING), ' copper devices within 50km provide redundancy options.')
      WHEN e.severity = 'critical' AND e.service_interruption
        THEN CONCAT('Critical severity with service interruption. Emergency restoration required. ', CAST(COALESCE(e.impacted_service_count, 0) AS STRING), ' services affected.')
      WHEN e.reroute_required
        THEN 'Reroute required but limited nearby copper infrastructure. Deploy temporary bypass or mobile equipment.'
      WHEN e.service_interruption AND NOT e.reroute_required
        THEN CONCAT('Service interrupted but reroute not needed. Repair in place. Estimated resolution: ', CAST(COALESCE(e.resolution_time_hours, 0) AS STRING), ' hours.')
      ELSE 'No reroute needed. Monitor cable condition and schedule preventive maintenance.'
    END AS reroute_rationale
  FROM {fq}.silver_dig_incident_enriched e
  WHERE e.incident_id = p_incident_id
"""

# (object name, kind, DDL) in dependency order
OBJECTS = [
    ("silver_dig_incident_enriched", "table", SILVER_DIG_SQL),
    ("incident_lookup", "function", INCIDENT_LOOKUP_SQL),
    ("proximity_search", "function", PROXIMITY_SEARCH_SQL),
    ("reroute_suggest", "function", REROUTE_SUGGEST_SQL),
]

REQUIRED_INPUTS = ["dig_safe_incident", "copper_plant_wire_center_jurisdiction", "bronze_copper_devices", "silver_device_service_impact"]

# Snapshot-loaded tables (ACC-DE-FRESH-APP-GOLD), dependency order. View inputs first.
SNAPSHOT_TABLES = [
    "gold_copper_recovery_schedule", "retirement_cost_per_wire_center", "copper_commodity_price_official",
    "roi_calculator_assumptions", "retirement_milestones", "copper_risk_predictions", "gold_wave_schedule",
    "gold_contractor_assignment_plan", "silver_budget_allocation", "gold_commodity_price_forecast",
]
SNAPSHOT_VIEWS = ["v_partner_value_wire_center"]
DEFAULT_SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "app_gold")


def provision_snapshots(spark, a, fq):
    d = a.snapshot_dir
    if not os.path.isdir(d):
        raise SystemExit(f"Snapshot dir not found: {d}. Pass --snapshot-dir (see module docstring).")
    for name in SNAPSHOT_TABLES:
        target = f"{a.catalog}.{a.schema}.{name}"
        if spark.catalog.tableExists(target) and not a.replace:
            print(f"SKIP   table    {target} (exists; pass --replace to rebuild)")
            continue
        print(f"{'PLAN ' if a.dry_run else 'LOAD  '} table    {target} <- {name}.jsonl")
        if a.dry_run:
            continue
        with open(os.path.join(d, f"{name}.ddl.sql")) as f:
            ddl = f.read().format(fq=fq)
        if a.replace:
            spark.sql(f"DROP TABLE IF EXISTS {fq}.`{name}`")
        spark.sql(ddl)
        schema = spark.table(target).schema
        df = (spark.read.schema(schema)
              .option("timestampFormat", "yyyy-MM-dd HH:mm:ss[.SSSSSS][XXX]")
              .json(os.path.join(d, f"{name}.jsonl")))
        df.write.mode("overwrite").insertInto(target)
        spark.sql(f"ALTER TABLE {fq}.`{name}` SET TAGS ('telco_project' = 'copper-retirement')")
        print(f"       rows: {spark.table(target).count()}")
    for name in SNAPSHOT_VIEWS:
        target = f"{a.catalog}.{a.schema}.{name}"
        if spark.catalog.tableExists(target) and not a.replace:
            print(f"SKIP   view     {target} (exists; pass --replace to rebuild)")
            continue
        print(f"{'PLAN ' if a.dry_run else 'CREATE'} view     {target}")
        if not a.dry_run:
            with open(os.path.join(d, f"{name}.ddl.sql")) as f:
                spark.sql(f.read().format(fq=fq))
            spark.sql(f"ALTER VIEW {fq}.`{name}` SET TAGS ('telco_project' = 'copper-retirement')")


def exists(spark, catalog, schema, name, kind):
    if kind == "table":
        return spark.catalog.tableExists(f"{catalog}.{schema}.{name}")
    return spark.catalog.functionExists(f"{catalog}.{schema}.{name}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", default="copper_retirement")
    p.add_argument("--replace", action="store_true", help="Rebuild objects that already exist.")
    p.add_argument("--dry-run", action="store_true", help="Print the plan; create nothing.")
    p.add_argument("--snapshot-dir", default=DEFAULT_SNAPSHOT_DIR,
                   help="Dir with <name>.ddl.sql + <name>.jsonl snapshots (default: repo data/app_gold).")
    a = p.parse_args()
    for v in (a.catalog, a.schema):
        if not IDENT.match(v):
            raise SystemExit(f"Invalid identifier: {v!r}")

    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    fq = f"`{a.catalog}`.`{a.schema}`"

    missing = [t for t in REQUIRED_INPUTS if not spark.catalog.tableExists(f"{a.catalog}.{a.schema}.{t}")]
    if missing:
        raise SystemExit(f"Missing inputs in {a.catalog}.{a.schema}: {missing}. Run seed_synthetic_sources and refresh_pipeline first.")

    for name, kind, ddl in OBJECTS:
        if exists(spark, a.catalog, a.schema, name, kind) and not a.replace:
            print(f"SKIP   {kind:8s} {a.catalog}.{a.schema}.{name} (exists; pass --replace to rebuild)")
            continue
        print(f"{'PLAN ' if a.dry_run else 'CREATE'} {kind:8s} {a.catalog}.{a.schema}.{name}")
        if not a.dry_run:
            spark.sql(ddl.format(fq=fq))
            if kind == "table":
                spark.sql(f"ALTER TABLE {fq}.{name} SET TAGS ('telco_project' = 'copper-retirement')")

    provision_snapshots(spark, a, fq)

    if not a.dry_run:
        n = spark.table(f"{a.catalog}.{a.schema}.silver_dig_incident_enriched").count()
        print(f"silver_dig_incident_enriched rows: {n}")


if __name__ == "__main__":
    main()
