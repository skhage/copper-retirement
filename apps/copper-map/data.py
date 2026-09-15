"""data.py — Live data layer for Copper Prioritization Map (P7-MAP)

Queries cdm_tmforum catalog tables via SQL warehouse.
Uses pre-populated h3_res8 columns (populated 2026-09-12) with
h3_toparent() for coarser resolutions. No more on-the-fly H3
computation from raw lat/lon.

@app-developer 2026-09-12 — UPGRADE-COPPER-MAP-LIVE-DATA
@app-developer 2026-09-13 — P7-MAP-LIVE-DATA-PREP: switched to
  pre-populated h3_res8 columns via h3_toparent() for performance.
  Added h3_h3tostring() for human-readable hex IDs.
@app-developer 2026-09-14 — P7-MAP-GOLD-INTEGRATION: added gold table
  queries (gold_wire_center_scorecard, gold_retirement_executive_summary)
  as primary data source. Raw base-table queries retained as fallback.
  New functions: load_gold_wire_centers(), load_gold_kpis(),
  load_gold_executive_summary(). Gold data provides retirement_readiness_score,
  retirement_priority_rank, and pre-aggregated risk/service/regulatory metrics.
"""
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "7b65956f30d66feb")
H3_RES = int(os.environ.get("H3_RESOLUTION", "4"))  # res 4 for US-wide view

# ── SQL Queries ────────────────────────────────────────────────────────────────

QUERY_HEX_RISK = """
SELECT
  h3_h3tostring(h3_toparent(ga.h3_res8, {h3_res})) AS h3_cell,
  AVG(CAST(ga.latitude AS DOUBLE))   AS center_lat,
  AVG(CAST(ga.longitude AS DOUBLE))  AS center_lon,
  ga.state_or_province               AS state,
  COUNT(DISTINCT pd.physical_device_id) AS copper_devices,
  COUNT(DISTINCT a.alarm_id)         AS active_alarms,
  SUM(CASE WHEN a.perceived_severity = 'critical' THEN 1 ELSE 0 END) AS critical_alarms,
  SUM(CASE WHEN a.perceived_severity = 'major' THEN 1 ELSE 0 END)    AS major_alarms,
  -- Risk proxy: alarm-density score (0-100), replaced by P4-RISK model later
  LEAST(100, ROUND(
    COUNT(DISTINCT a.alarm_id) * 100.0
    / NULLIF(COUNT(DISTINCT pd.physical_device_id), 0) / 3.0
  )) AS risk_score
FROM cdm_tmforum.tmf_shared.geographic_address ga
INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
  ON pd.geographic_address_id = ga.geographic_address_id
  AND pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
LEFT JOIN cdm_tmforum.tmf_resource.alarm a
  ON a.physical_resource_id = pd.physical_device_id
WHERE ga.h3_res8 IS NOT NULL
  AND ('{state_filter}' = '' OR ga.state_or_province = '{state_filter}')
GROUP BY
  h3_toparent(ga.h3_res8, {h3_res}),
  ga.state_or_province
ORDER BY copper_devices DESC
LIMIT 500
"""

QUERY_KPI = """
WITH copper_devices AS (
  SELECT
    pd.device_type,
    COUNT(*) AS cnt
  FROM cdm_tmforum.tmf_enterprise.physical_device pd
  WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  GROUP BY pd.device_type
),
copper_alarms AS (
  SELECT
    COUNT(DISTINCT a.alarm_id) AS total_alarms,
    SUM(CASE WHEN a.perceived_severity = 'critical' THEN 1 ELSE 0 END) AS crit_alarms
  FROM cdm_tmforum.tmf_resource.alarm a
  INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
    ON pd.physical_device_id = a.physical_resource_id
    AND pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
),
copper_services AS (
  SELECT
    SUM(CASE
      WHEN cfs.service_type = 'voice' THEN 45
      WHEN cfs.service_type = 'broadband' THEN 75
      WHEN cfs.service_type = 'fixed_line' THEN 35
      ELSE 0
    END) AS revenue_at_risk_mrr,
    COUNT(DISTINCT cfs.customer_id) AS customers_on_copper,
    COUNT(DISTINCT cfs.customer_facing_service_id) AS services_affected
  FROM cdm_tmforum.tmf_service.customer_facing_service cfs
  WHERE cfs.service_type IN ('voice', 'fixed_line', 'broadband')
    AND cfs.status IN ('active', 'feasibility_checked', 'designed')
),
copper_states AS (
  SELECT COUNT(DISTINCT ga.state_or_province) AS state_count
  FROM cdm_tmforum.tmf_shared.geographic_address ga
  INNER JOIN cdm_tmforum.tmf_enterprise.physical_device pd
    ON pd.geographic_address_id = ga.geographic_address_id
    AND pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  WHERE ga.state_or_province IS NOT NULL
)
SELECT
  (SELECT SUM(cnt) FROM copper_devices) AS total_devices,
  (SELECT cnt FROM copper_devices WHERE device_type = 'cpe') AS cpe,
  (SELECT cnt FROM copper_devices WHERE device_type = 'ont') AS ont,
  (SELECT cnt FROM copper_devices WHERE device_type = 'olt') AS olt,
  (SELECT cnt FROM copper_devices WHERE device_type = 'patch_panel') AS pp,
  ca.total_alarms,
  ca.crit_alarms,
  ROUND(ca.crit_alarms * 100.0 / NULLIF(ca.total_alarms, 0), 1) AS pct_crit,
  cs2.state_count AS states,
  cs.revenue_at_risk_mrr,
  cs.customers_on_copper,
  cs.services_affected
FROM copper_alarms ca
CROSS JOIN copper_services cs
CROSS JOIN copper_states cs2
"""

QUERY_DEVICES = """
SELECT
  pd.physical_device_id               AS id,
  pd.device_type                      AS type,
  pd.serial_number                    AS serial,
  pd.status,
  pd.installation_date                AS installed,
  ga.state_or_province                AS state,
  ga.locality                         AS city,
  COUNT(DISTINCT a.alarm_id)          AS alarms,
  SUM(CASE WHEN a.perceived_severity = 'critical' THEN 1 ELSE 0 END) AS crit,
  -- Risk proxy until P4-RISK model
  LEAST(100, ROUND(
    COUNT(DISTINCT a.alarm_id) * 100.0 / 3.0
  )) AS risk
FROM cdm_tmforum.tmf_enterprise.physical_device pd
INNER JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON ga.geographic_address_id = pd.geographic_address_id
LEFT JOIN cdm_tmforum.tmf_resource.alarm a
  ON a.physical_resource_id = pd.physical_device_id
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  AND ('{state_filter}' = '' OR ga.state_or_province = '{state_filter}')
  AND ('{device_type}' = '' OR pd.device_type = '{device_type}')
GROUP BY
  pd.physical_device_id, pd.device_type, pd.serial_number,
  pd.status, pd.installation_date,
  ga.state_or_province, ga.locality
ORDER BY crit DESC, alarms DESC
LIMIT 100
"""

QUERY_FILTER_OPTIONS = """
SELECT
  'state' AS filter_type,
  ga.state_or_province AS filter_value,
  COUNT(DISTINCT pd.physical_device_id) AS device_count
FROM cdm_tmforum.tmf_enterprise.physical_device pd
INNER JOIN cdm_tmforum.tmf_shared.geographic_address ga
  ON ga.geographic_address_id = pd.geographic_address_id
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
  AND ga.state_or_province IS NOT NULL
GROUP BY ga.state_or_province

UNION ALL

SELECT
  'device_type' AS filter_type,
  pd.device_type AS filter_value,
  COUNT(DISTINCT pd.physical_device_id) AS device_count
FROM cdm_tmforum.tmf_enterprise.physical_device pd
WHERE pd.device_type IN ('cpe', 'ont', 'olt', 'patch_panel')
GROUP BY pd.device_type

ORDER BY filter_type, device_count DESC
"""


# ── Gold Table Queries (primary data source) ───────────────────────────────────

QUERY_GOLD_WIRE_CENTERS = """
SELECT
  wire_center_id,
  wire_center_name,
  clli_code,
  state_code,
  fiber_ready,
  puc_filing_required,
  annual_retire_priority,
  puc_name,
  copper_device_count,
  active_device_count,
  avg_alarm_count,
  CAST(avg_critical_alarm_rate AS DOUBLE) AS avg_critical_alarm_rate,
  CAST(avg_sla_breach_rate AS DOUBLE) AS avg_sla_breach_rate,
  critical_risk_devices,
  high_risk_devices,
  CAST(bbox_min_lat AS DOUBLE) AS bbox_min_lat,
  CAST(bbox_max_lat AS DOUBLE) AS bbox_max_lat,
  CAST(bbox_min_lon AS DOUBLE) AS bbox_min_lon,
  CAST(bbox_max_lon AS DOUBLE) AS bbox_max_lon,
  (CAST(bbox_min_lat AS DOUBLE) + CAST(bbox_max_lat AS DOUBLE)) / 2.0 AS center_lat,
  (CAST(bbox_min_lon AS DOUBLE) + CAST(bbox_max_lon AS DOUBLE)) / 2.0 AS center_lon,
  affected_service_count,
  affected_customer_count,
  voice_services,
  broadband_services,
  fixed_line_services,
  CAST(retirement_readiness_score AS DOUBLE) AS retirement_readiness_score,
  retirement_priority_rank
FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard
WHERE 1=1
  AND ('{state_filter}' = '' OR state_code = '{state_filter}')
ORDER BY retirement_priority_rank ASC
LIMIT 500
"""

QUERY_GOLD_KPI = """
SELECT
  SUM(total_copper_devices) AS total_devices,
  SUM(active_devices) AS active_devices,
  SUM(critical_risk_count) AS critical_risk_total,
  SUM(high_risk_count) AS high_risk_total,
  SUM(wire_center_count) AS wire_center_count,
  SUM(fiber_ready_devices) AS fiber_ready_devices,
  ROUND(SUM(fiber_ready_devices) * 100.0 / NULLIF(SUM(total_copper_devices), 0), 1) AS fiber_ready_pct,
  SUM(total_affected_services) AS services_affected,
  SUM(total_affected_customers) AS customers_affected,
  SUM(voice_services_at_risk) AS voice_at_risk,
  SUM(broadband_services_at_risk) AS broadband_at_risk,
  SUM(total_dig_incidents) AS dig_incidents,
  SUM(regulatory_violations) AS regulatory_violations,
  SUM(CAST(total_repair_cost AS DOUBLE)) AS total_repair_cost,
  SUM(available_contractors) AS available_contractors,
  SUM(total_crew_capacity) AS crew_capacity,
  COUNT(DISTINCT state_code) AS state_count,
  ROUND(SUM(critical_risk_count) * 100.0 / NULLIF(SUM(total_copper_devices), 0), 1) AS critical_risk_pct
FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
WHERE state_code IN ('CO', 'MN', 'WA', 'OR', 'ID', 'AZ')
"""

QUERY_GOLD_EXECUTIVE_SUMMARY = """
SELECT
  state_code,
  total_copper_devices,
  active_devices,
  critical_risk_count,
  high_risk_count,
  wire_center_count,
  fiber_ready_devices,
  CAST(fiber_ready_pct AS DOUBLE) AS fiber_ready_pct,
  total_affected_services,
  total_affected_customers,
  voice_services_at_risk,
  broadband_services_at_risk,
  total_dig_incidents,
  regulatory_violations,
  CAST(total_repair_cost AS DOUBLE) AS total_repair_cost,
  CAST(avg_resolution_hours AS DOUBLE) AS avg_resolution_hours,
  available_contractors,
  CAST(avg_contractor_rating AS DOUBLE) AS avg_contractor_rating,
  total_crew_capacity,
  preferred_contractors,
  program_health_status
FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
WHERE state_code IN ('CO', 'MN', 'WA', 'OR', 'ID', 'AZ')
ORDER BY total_copper_devices DESC
"""


# ── SQL Connection ─────────────────────────────────────────────────────────────

def _get_connection():
    """Get a Databricks SQL connection using app OAuth credentials."""
    from databricks.sdk import WorkspaceClient
    from databricks import sql as dbsql

    w = WorkspaceClient()
    return dbsql.connect(
        server_hostname=w.config.host.replace("https://", ""),
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: w.config.authenticate,
    )


def _run_query(query: str) -> list[dict[str, Any]]:
    """Execute a SQL query and return results as list of dicts."""
    conn = _get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


# ── Risk tier assignment ───────────────────────────────────────────────────────

def _assign_tier(risk_score: float) -> str:
    """Assign risk tier from score."""
    if risk_score >= 75:
        return "critical"
    if risk_score >= 50:
        return "high"
    if risk_score >= 25:
        return "medium"
    return "low"


# ── Public API ─────────────────────────────────────────────────────────────────

def load_hex_cells(state_filter: str = "") -> list[dict]:
    """Load H3 hex cell risk data from live catalog."""
    query = QUERY_HEX_RISK.format(
        h3_res=H3_RES,
        state_filter=state_filter or "",
    )
    rows = _run_query(query)
    for row in rows:
        row["lat"] = row.pop("center_lat", 0)
        row["lon"] = row.pop("center_lon", 0)
        row["devices"] = row.pop("copper_devices", 0)
        row["risk"] = row.pop("risk_score", 50)
        row["alarms"] = row.pop("active_alarms", 0)
        row["crit"] = row.pop("critical_alarms", 0)
        row["tier"] = _assign_tier(row["risk"])
    return rows


def load_kpis() -> dict:
    """Load KPI summary from live catalog."""
    rows = _run_query(QUERY_KPI)
    if not rows:
        return {}
    r = rows[0]
    devices = r.get("total_devices", 0) or 0
    pct_crit = float(r.get("pct_crit", 0) or 0)
    return {
        "devices": devices,
        "copper_devices": devices,  # alias for app.py KPI display
        "cpe": r.get("cpe", 0) or 0,
        "ont": r.get("ont", 0) or 0,
        "olt": r.get("olt", 0) or 0,
        "pp": r.get("pp", 0) or 0,
        "alarms": r.get("total_alarms", 0) or 0,
        "crit_alarms": r.get("crit_alarms", 0) or 0,
        "pct_crit": pct_crit,
        "critical_risk_pct": pct_crit,  # alias for app.py KPI display
        "states": r.get("states", 0) or 0,
        "revenue_at_risk_mrr": r.get("revenue_at_risk_mrr", 0) or 0,
        "customers_on_copper": r.get("customers_on_copper", 0) or 0,
        "services_affected": r.get("services_affected", 0) or 0,
    }


def load_devices(state_filter: str = "", device_type: str = "") -> list[dict]:
    """Load device detail from live catalog."""
    query = QUERY_DEVICES.format(
        state_filter=state_filter or "",
        device_type=device_type or "",
    )
    return _run_query(query)


def load_filter_options() -> dict[str, list[str]]:
    """Load distinct filter values from live catalog."""
    rows = _run_query(QUERY_FILTER_OPTIONS)
    result: dict[str, list[str]] = {"state": [], "device_type": []}
    for row in rows:
        ft = row.get("filter_type", "")
        fv = row.get("filter_value", "")
        if ft in result and fv:
            result[ft].append(fv)
    return result


# ── Gold Table API (P7-MAP-GOLD-INTEGRATION) ───────────────────────────────

def load_gold_wire_centers(state_filter: str = "") -> list[dict]:
    """Load wire center scorecard data from gold table.

    Returns wire centers with pre-aggregated risk, service, and
    retirement readiness metrics. Each row includes center_lat/lon
    computed from bounding box for map plotting.
    """
    query = QUERY_GOLD_WIRE_CENTERS.format(state_filter=state_filter or "")
    rows = _run_query(query)
    for row in rows:
        # Normalize for map compatibility
        row["lat"] = float(row.get("center_lat") or 0)
        row["lon"] = float(row.get("center_lon") or 0)
        row["devices"] = int(row.get("copper_device_count") or 0)
        readiness = float(row.get("retirement_readiness_score") or 50)
        # Invert readiness to risk: high readiness = low risk
        row["risk"] = max(0, min(100, 100 - readiness))
        row["alarms"] = int(row.get("avg_alarm_count") or 0) * row["devices"]
        crit_rate = float(row.get("avg_critical_alarm_rate") or 0)
        row["crit"] = int(row["alarms"] * crit_rate)
        row["tier"] = _assign_tier(row["risk"])
        row["state"] = row.get("state_code", "")
        row["h3"] = row.get("wire_center_id", "")  # use wire_center_id as cell key
        # Extra fields for wire center detail
        row["wire_center"] = row.get("wire_center_name", "")
        row["clli"] = row.get("clli_code", "")
        row["fiber_ready"] = bool(row.get("fiber_ready"))
        row["services"] = int(row.get("affected_service_count") or 0)
        row["customers"] = int(row.get("affected_customer_count") or 0)
        row["priority_rank"] = int(row.get("retirement_priority_rank") or 999)
        row["readiness"] = readiness
    return rows


def load_gold_kpis() -> dict:
    """Load KPI summary from gold executive summary table.

    Aggregates across all states. Provides richer metrics than
    the base-table KPI query (includes fiber readiness, contractor
    capacity, dig incidents, regulatory violations).
    """
    rows = _run_query(QUERY_GOLD_KPI)
    if not rows:
        return {}
    r = rows[0]
    devices = int(r.get("total_devices") or 0)
    critical = int(r.get("critical_risk_total") or 0)
    high = int(r.get("high_risk_total") or 0)
    crit_pct = float(r.get("critical_risk_pct") or 0)
    services = int(r.get("services_affected") or 0)
    customers = int(r.get("customers_affected") or 0)
    # Estimate MRR from service mix (voice $45, broadband $75, fixed $35)
    voice = int(r.get("voice_at_risk") or 0)
    broadband = int(r.get("broadband_at_risk") or 0)
    other_services = services - voice - broadband
    est_mrr = voice * 45 + broadband * 75 + other_services * 35
    return {
        "devices": devices,
        "copper_devices": devices,
        "active_devices": int(r.get("active_devices") or 0),
        "critical_risk_devices": critical,
        "high_risk_devices": high,
        "critical_risk_pct": crit_pct,
        "pct_crit": crit_pct,
        "states": int(r.get("state_count") or 0),
        "wire_centers": int(r.get("wire_center_count") or 0),
        "fiber_ready_devices": int(r.get("fiber_ready_devices") or 0),
        "fiber_ready_pct": float(r.get("fiber_ready_pct") or 0),
        "services_affected": services,
        "customers_on_copper": customers,
        "revenue_at_risk_mrr": est_mrr,
        "voice_at_risk": voice,
        "broadband_at_risk": broadband,
        "dig_incidents": int(r.get("dig_incidents") or 0),
        "regulatory_violations": int(r.get("regulatory_violations") or 0),
        "total_repair_cost": float(r.get("total_repair_cost") or 0),
        "available_contractors": int(r.get("available_contractors") or 0),
        "crew_capacity": int(r.get("crew_capacity") or 0),
        # Keep legacy aliases
        "alarms": 0,
        "crit_alarms": critical,
    }


def load_gold_executive_summary() -> list[dict]:
    """Load per-state executive summary from gold table.

    Returns one row per state with program health status and
    comprehensive metrics for the state-level breakdown panel.
    """
    return _run_query(QUERY_GOLD_EXECUTIVE_SUMMARY)
