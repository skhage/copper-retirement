"""data.py — Live data layer for Copper Prioritization Map (P7-MAP)

Queries cdm_tmforum catalog tables via SQL warehouse.
Uses pre-populated h3_res8 columns (populated 2026-09-12) with
h3_toparent() for coarser resolutions. No more on-the-fly H3
computation from raw lat/lon.

@app-developer 2026-09-12 — UPGRADE-COPPER-MAP-LIVE-DATA
@app-developer 2026-09-13 — P7-MAP-LIVE-DATA-PREP: switched to
  pre-populated h3_res8 columns via h3_toparent() for performance.
  Added h3_h3tostring() for human-readable hex IDs.
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
