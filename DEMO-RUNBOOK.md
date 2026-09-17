# Copper Retirement — Demo-Day Runbook v2

**Author:** @devops | **Created:** 2026-09-16  
**Project:** Lakelink Fiber Copper Retirement  
**Scope:** Beat 1 (Copper Map) + Beat 4 (Regulatory Assistant)  
**Workspace:** `fevm-cmegdemos.cloud.databricks.com`

---

## 1. Pre-Flight Checklist

Run these checks **30 minutes before demo**. Every item must show **PASS** before proceeding.

### 1.1 SQL Warehouse

| Check | Expected | How to verify |
| --- | --- | --- |
| Warehouse `Serverless Starter Warehouse` state | `RUNNING` | Workspace UI → SQL Warehouses → ID `7b65956f30d66feb` |
| Query latency | < 5s on simple SELECT | Run: `SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard` |

**If STOPPED:** The warehouse auto-starts on first query. Issue a warm-up query 5 minutes before demo:
```sql
SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions;
SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard;
SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.gold_circuit_revenue_at_risk;
```

### 1.2 Model Serving Endpoint

| Check | Expected | How to verify |
| --- | --- | --- |
| Endpoint `copper-retirement-risk` | State: `READY` | Workspace UI → Serving → `copper-retirement-risk` |
| Model | `cdm_tmforum.ml_models.copper_retirement_risk` (V5) | Serving endpoint config tab |
| Inference table logging | Enabled | Serving endpoint config tab |

**If NOT READY:** The endpoint may be scaled to zero. It auto-wakes on first request (~60-90s cold start). Send a warm-up request 5 min before demo:
```python
import mlflow.deployments
client = mlflow.deployments.get_deploy_client("databricks")
# V5 model requires all 39 input features
warm_up_record = {
    "alarm_count": 25.0, "critical_alarm_rate": 0.15, "service_affecting_rate": 0.08,
    "sla_breach_count": 5.0, "sla_breach_rate": 0.2, "test_fail_rate": 0.35,
    "problem_count": 8.0, "recurring_problem_rate": 0.25,
    "dispute_count": 3.0, "escalated_dispute_count": 1.0,
    "sla_breach_dispute_count": 2.0, "months_since_last_dispute": 2.0,
    "complaint_count": 12.0, "complaint_rate_per_month": 1.0,
    "escalated_complaint_count": 3.0, "high_severity_complaint_count": 4.0,
    "complaint_avg_resolution_hours": 48.0,
    "active_months": 60.0, "avg_monthly_usage": 500000.0, "avg_monthly_revenue": 85.0,
    "device_age_days": 2500.0, "firmware_obsolescence_score": 0.8,
    "days_since_last_patch": 800.0, "days_past_eol": 400.0,
    "days_past_support_expiry": 200.0, "is_past_eol": 1.0, "is_support_expired": 1.0,
    "has_vulnerabilities": 1.0, "has_upgrade_blocked": 0.0, "has_upgrade_ineligible": 1.0,
    "installed_software_count": 3.0, "has_software_data": 1.0,
    "plant_pair_count": 4.0, "avg_loop_length_ft": 12000.0, "avg_splice_count": 8.0,
    "avg_cable_vintage_year": 1985.0, "avg_db_loss": 28.0, "moisture_rate": 0.3,
    "device_type_encoded": 0.0
}
result = client.predict(
    endpoint="copper-retirement-risk",
    inputs={"dataframe_records": [warm_up_record]}
)
print(result)  # Should return risk tier + class probabilities
```

### 1.3 Vector Search

| Check | Expected | How to verify |
| --- | --- | --- |
| VS Endpoint `demo_telco_vs_endpoint` | `ONLINE` | Workspace UI → Compute → Vector Search Endpoints |
| VS Index `cdm_tmforum.copper_retirement.regulatory_doc_vs_index` | `ready: True`, 528 docs indexed | Catalog Explorer → `copper_retirement` → `regulatory_doc_vs_index` |

**If index not ready:** Vector Search indexes are persistent — if the endpoint is ONLINE, the index should be available. If the index shows 0 docs, check the source table `cdm_tmforum.copper_retirement.regulatory_doc_chunks` for data.

### 1.4 DLP Pipeline

| Check | Expected | How to verify |
| --- | --- | --- |
| Pipeline `copper-retirement-dlp` | `IDLE` (last run succeeded) | Workspace UI → Pipelines → ID `b52532a2-6398-44ed-b239-9e95cafb745c` |
| 8 Materialized Views populated | All have rows > 0 | See §3 Data Freshness Queries |

**Materialized Views (expected counts):**

| MV | Expected Rows |
| --- | --- |
| `bronze_copper_devices` | ~2,672 |
| `bronze_copper_services` | ~17,655 |
| `bronze_dig_safe_incidents` | > 0 |
| `silver_copper_plant_enriched` | > 0 |
| `silver_device_service_impact` | > 0 |
| `gold_wire_center_scorecard` | 103 |
| `gold_contractor_scorecard` | 10,000 |
| `gold_retirement_executive_summary` | 6 |

### 1.5 Databricks Apps

| App | Expected State | URL |
| --- | --- | --- |
| `copper-map` | `ACTIVE` | https://copper-map-7474656585748611.aws.databricksapps.com |
| `regulatory-assistant` | `ACTIVE` | https://regulatory-assistant-7474656585748611.aws.databricksapps.com |

**If STOPPED:** Apps auto-start on first HTTP request. Open the URL in a browser 2-3 minutes before demo to warm up.

### 1.6 Lakebase Task Board (optional — for multi-agent coordination demo)

| Check | Expected | How to verify |
| --- | --- | --- |
| Lakebase project `copper-task-board` | Endpoint reachable | Run Lakebase connection snippet (see §5) |
| `agent_tasks` table | > 240 rows | `SELECT COUNT(*) FROM agent_tasks` |

---

## 2. Startup Sequence

Follow this exact order to ensure all dependencies are warm before the demo begins.

### Step 1: Warm the SQL Warehouse (T-10 min)
```sql
-- Run in SQL Editor against warehouse 7b65956f30d66feb
SELECT 'warehouse_warm' AS check_name, COUNT(*) AS row_count 
FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard
UNION ALL
SELECT 'risk_predictions', COUNT(*) 
FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions
UNION ALL
SELECT 'revenue_at_risk', COUNT(*) 
FROM cdm_tmforum.copper_retirement.gold_circuit_revenue_at_risk;
```

### Step 2: Warm the Serving Endpoint (T-5 min)
```python
import mlflow.deployments
client = mlflow.deployments.get_deploy_client("databricks")
# V5 model requires all 39 input features
warm_up_record = {
    "alarm_count": 25.0, "critical_alarm_rate": 0.15, "service_affecting_rate": 0.08,
    "sla_breach_count": 5.0, "sla_breach_rate": 0.2, "test_fail_rate": 0.35,
    "problem_count": 8.0, "recurring_problem_rate": 0.25,
    "dispute_count": 3.0, "escalated_dispute_count": 1.0,
    "sla_breach_dispute_count": 2.0, "months_since_last_dispute": 2.0,
    "complaint_count": 12.0, "complaint_rate_per_month": 1.0,
    "escalated_complaint_count": 3.0, "high_severity_complaint_count": 4.0,
    "complaint_avg_resolution_hours": 48.0,
    "active_months": 60.0, "avg_monthly_usage": 500000.0, "avg_monthly_revenue": 85.0,
    "device_age_days": 2500.0, "firmware_obsolescence_score": 0.8,
    "days_since_last_patch": 800.0, "days_past_eol": 400.0,
    "days_past_support_expiry": 200.0, "is_past_eol": 1.0, "is_support_expired": 1.0,
    "has_vulnerabilities": 1.0, "has_upgrade_blocked": 0.0, "has_upgrade_ineligible": 1.0,
    "installed_software_count": 3.0, "has_software_data": 1.0,
    "plant_pair_count": 4.0, "avg_loop_length_ft": 12000.0, "avg_splice_count": 8.0,
    "avg_cable_vintage_year": 1985.0, "avg_db_loss": 28.0, "moisture_rate": 0.3,
    "device_type_encoded": 0.0
}
result = client.predict(
    endpoint="copper-retirement-risk",
    inputs={"dataframe_records": [warm_up_record]}
)
assert "predictions" in result or isinstance(result, dict), f"Unexpected response: {result}"
print("Serving endpoint WARM")
```

### Step 3: Open Beat 1 App — Copper Map (T-3 min)
1. Open https://copper-map-7474656585748611.aws.databricksapps.com in browser
2. Verify the map loads with H3 hexagons colored by risk score
3. Click a hexagon — verify the popover shows device count, risk score, customer count
4. Toggle filters (state, risk tier) — verify map updates

### Step 4: Open Beat 4 App — Regulatory Assistant (T-2 min)
1. Open https://regulatory-assistant-7474656585748611.aws.databricksapps.com in browser
2. Verify the chat interface loads
3. Send a test query: "What are the FCC copper retirement notice requirements?"
4. Verify response includes citations from indexed regulatory documents

### Step 5: Final Sanity Check (T-1 min)
- [ ] SQL Warehouse: RUNNING
- [ ] Serving Endpoint: READY
- [ ] VS Index: 528 docs
- [ ] Copper Map app: Rendering correctly
- [ ] Regulatory Assistant app: Responding with citations
- [ ] Browser tabs arranged: Map | Regulatory Assistant | Workspace (for live queries)

---

## 3. Data Freshness Queries

Run these to confirm data is current and complete. All queries target `cdm_tmforum.copper_retirement`.

### 3.1 Gold Table Health Check
```sql
SELECT 
  'gold_wire_center_scorecard' AS table_name, COUNT(*) AS row_count FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard
UNION ALL SELECT 
  'gold_circuit_revenue_at_risk', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_circuit_revenue_at_risk
UNION ALL SELECT 
  'gold_retirement_executive_summary', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
UNION ALL SELECT 
  'gold_contractor_scorecard', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_contractor_scorecard
UNION ALL SELECT 
  'gold_device_risk_predictions', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions;
```

**Expected:**

| Table | Min Rows |
| --- | --- |
| gold_wire_center_scorecard | 103 |
| gold_circuit_revenue_at_risk | 14,777 |
| gold_retirement_executive_summary | 6 |
| gold_contractor_scorecard | 10,000 |
| gold_device_risk_predictions | 2,672 |

### 3.2 Bronze/Silver Pipeline Freshness
```sql
SELECT 
  'bronze_copper_devices' AS table_name, COUNT(*) AS row_count FROM cdm_tmforum.copper_retirement.bronze_copper_devices
UNION ALL SELECT 
  'bronze_copper_services', COUNT(*) FROM cdm_tmforum.copper_retirement.bronze_copper_services
UNION ALL SELECT 
  'silver_copper_plant_enriched', COUNT(*) FROM cdm_tmforum.copper_retirement.silver_copper_plant_enriched
UNION ALL SELECT 
  'silver_device_service_impact', COUNT(*) FROM cdm_tmforum.copper_retirement.silver_device_service_impact;
```

### 3.3 Risk Model Inference Table
```sql
-- Check the serving endpoint inference log
SELECT COUNT(*) AS total_inferences,
       MAX(request_time) AS latest_inference
FROM cdm_tmforum.copper_retirement.risk_inference_unpacked;
```

### 3.4 Lakebase App Tables (Beat 1 map data)
```python
# Run from notebook with Lakebase connection
cur.execute("""
    SELECT table_name, 
           (xpath(table_stats, '/row_count/text()'))[1]::int AS approx_rows
    FROM (
        SELECT tablename AS table_name, 
               pg_stat_get_live_tuples(c.oid)::text AS table_stats
        FROM pg_tables t
        JOIN pg_class c ON c.relname = t.tablename
        WHERE schemaname = 'copper_app'
    ) sub
    ORDER BY table_name;
""")
-- Or simpler:
cur.execute("SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname='copper_app' ORDER BY relname")
for r in cur.fetchall():
    print(f"  {r[0]}: ~{r[1]} rows")
```

---

## 4. Rollback Procedures

### 4.1 App Not Loading / Crashing

**Symptom:** App URL returns 502/503 or blank page.  
**Fix:**
1. Check app logs: Workspace UI → Apps → `copper-map` or `regulatory-assistant` → Logs tab
2. Restart the app:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.apps.stop("copper-map")    # or "regulatory-assistant"
# Wait 10 seconds
w.apps.start("copper-map")
```
3. If persistent: check `app.yaml` env vars — ensure `DATABRICKS_WAREHOUSE_ID=7b65956f30d66feb` is set.

### 4.2 Serving Endpoint Returning Errors

**Symptom:** Risk scores not rendering on map, or 4xx/5xx from endpoint.  
**Fix:**
1. Check endpoint state: Workspace UI → Serving → `copper-retirement-risk`
2. If state is `NOT_READY` or `FAILED`:
   - Check events log for error details
   - Model entity: `cdm_tmforum.ml_models.copper_retirement_risk`
   - Last known good version: V5
3. **Fallback:** The copper-map app has a `LIVE_DATA=false` env var. Set it to `"false"` to use mock risk scores:
```python
# In copper-map/app.yaml, change:
# value: "true"  →  value: "false"
# Then redeploy the app
```

### 4.3 SQL Warehouse Unavailable

**Symptom:** Queries timing out or warehouse not starting.  
**Fix:**
1. Try a different warehouse — `telco-builders` (ID: `da0dbcd5676d37eb`) is a backup.
2. Update app env vars to point to the backup warehouse ID.
3. For live SQL demos, switch to serverless compute in a notebook.

### 4.4 Vector Search Not Responding

**Symptom:** Regulatory assistant returns no results or generic responses.  
**Fix:**
1. Check VS endpoint `demo_telco_vs_endpoint` is ONLINE
2. Test index directly:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
results = w.vector_search_indexes.query_index(
    index_name="cdm_tmforum.copper_retirement.regulatory_doc_vs_index",
    columns=["embedding_text", "title", "docket_number"],
    query_text="FCC copper retirement notice requirements",
    num_results=3
)
print(results)
```
3. **Fallback:** If VS is down, the regulatory-assistant app should fall back to mock responses (check `REG_AGENT_ENDPOINT` env var — if unset or unreachable, app uses mock data).

### 4.5 DLP Pipeline Data Stale or Missing

**Symptom:** Gold tables have 0 rows or unexpected counts.  
**Fix:**
1. Trigger a pipeline refresh:
   - Workspace UI → Pipelines → `copper-retirement-dlp` (ID: `b52532a2-6398-44ed-b239-9e95cafb745c`) → Start
   - Pipeline runs take ~5-10 minutes
2. Verify MVs repopulate with §3.1 query
3. **Do NOT drop managed tables** — the DLP table conflict was already resolved by CEO.

### 4.6 Lakebase Connection Failure

**Symptom:** Task board or app data queries fail with connection refused.  
**Fix:**
1. Regenerate credential token (tokens expire):
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
token = w.postgres.generate_database_credential(
    endpoint="projects/copper-task-board/branches/production/endpoints/primary"
).token
print(f"New token generated (expires in ~1hr)")
```
2. Reconnect with fresh token.
3. If endpoint is unreachable, check Lakebase project status in workspace.

---

## 5. Reference: Connection Snippets

### Lakebase (Task Board)
```python
import psycopg
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
endpoint_name = "projects/copper-task-board/branches/production/endpoints/primary"
host = "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
user = w.current_user.me().user_name
token = w.postgres.generate_database_credential(endpoint=endpoint_name).token
conn = psycopg.connect(host=host, dbname="databricks_postgres", user=user, password=token, sslmode="require")
conn.autocommit = True
cur = conn.cursor()
```

### Key Resource IDs

| Resource | ID / Name |
| --- | --- |
| SQL Warehouse (primary) | `7b65956f30d66feb` (Serverless Starter Warehouse) |
| SQL Warehouse (backup) | `da0dbcd5676d37eb` (telco-builders) |
| Serving Endpoint | `copper-retirement-risk` |
| Model | `cdm_tmforum.ml_models.copper_retirement_risk` (V5) |
| VS Endpoint | `demo_telco_vs_endpoint` |
| VS Index | `cdm_tmforum.copper_retirement.regulatory_doc_vs_index` (528 docs) |
| DLP Pipeline | `b52532a2-6398-44ed-b239-9e95cafb745c` (copper-retirement-pipeline) |
| Copper Map App | `copper-map` → https://copper-map-7474656585748611.aws.databricksapps.com |
| Regulatory Assistant App | `regulatory-assistant` → https://regulatory-assistant-7474656585748611.aws.databricksapps.com |
| Task Board App | `copper-task-board` → https://copper-task-board-7474656585748611.aws.databricksapps.com |
| Lakebase Endpoint | `ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com` |
| Catalog | `cdm_tmforum` |
| Schema | `copper_retirement` |
| Lakebase Schema | `copper_app` (14 tables) |

---

## 6. Demo Flow Quick Reference

### Beat 1: "Where is our copper / risk of touching it?"
1. Open **Copper Map** app
2. Show US-wide view — H3 hexagons colored by risk
3. Zoom into a region — show device density
4. Click a hexagon — show device details, risk score, customer impact
5. Use filters — filter by risk tier (critical), show only high-risk areas
6. **Talking point:** "2,672 copper devices scored in real-time by our ML model, 14,777 circuits with revenue-at-risk calculated"

### Beat 4: "Are we clear on regs everywhere we touch?"
1. Open **Regulatory Assistant** app
2. Ask: "What are the FCC copper retirement requirements for ILEC networks?"
3. Show citations from indexed regulatory documents (528 docs)
4. Ask: "What notice period is required for copper retirement in California?"
5. Show jurisdiction-specific compliance details
6. **Talking point:** "528 regulatory documents indexed with vector search, instant retrieval with source citations"

---

## 7. Emergency Contacts

| Role | Who | Escalation Path |
| --- | --- | --- |
| CEO / Project Owner | Stephen Hage | Direct — final escalation for all blockers |
| @devops | Scheduled automation | Git, DAB, infrastructure issues |
| @pm | Scheduled automation | Task coordination, priority conflicts |
| @app-developer | Scheduled automation | App code issues, UI bugs |

---

*Last verified: 2026-09-17 by @devops automated run*  
*Next review: Before each demo day*
