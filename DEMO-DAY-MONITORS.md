# 🎯 Demo-Day Monitoring Checklist

**Project:** Copper Retirement — LakeLink Fiber  
**Generated:** 2026-09-18 by @devops  
**Purpose:** Pre-demo verification of all infrastructure components. Run through each section T-60 min before demo start.

---

## 1. Databricks Apps Health

All 7 apps must show **Compute: ACTIVE** and **Deployment: SUCCEEDED**.

| # | App Name | URL | Expected State |
|---|----------|-----|----------------|
| 1 | copper-map | https://copper-map-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| 2 | commodity-dashboard | https://commodity-dashboard-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| 3 | regulatory-assistant | https://regulatory-assistant-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| 4 | retirement-plan | https://retirement-plan-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| 5 | fiber-planner-v2 | https://fiber-planner-v2-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| 6 | lakelink-ra-review | https://lakelink-ra-review-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| 7 | copper-task-board | https://copper-task-board-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |

**Verification steps:**
1. Open each URL in a browser tab — confirm the page loads without errors.
2. In the Databricks workspace: **Apps** → filter by name → confirm "Running" status.
3. If an app shows "Stopped" or "Error", use `databricks apps start <app-name>` to restart. Allow 2-3 min for warm-up.

**CLI quick-check (run from any terminal):**
```bash
for app in copper-map commodity-dashboard regulatory-assistant retirement-plan fiber-planner-v2 lakelink-ra-review copper-task-board; do
  echo "--- $app ---"
  databricks apps get $app --output JSON | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Compute: {d.get(\"compute_status\",{}).get(\"state\",\"??\")}  Deploy: {d.get(\"active_deployment\",{}).get(\"status\",{}).get(\"state\",\"??\")}')" 2>/dev/null || echo "  FAILED TO QUERY"
done
```

**SDK quick-check (Python):**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
apps = ['copper-map','commodity-dashboard','regulatory-assistant','retirement-plan','fiber-planner-v2','lakelink-ra-review','copper-task-board']
for name in apps:
    a = w.apps.get(name)
    cs = a.compute_status.state.value if a.compute_status else 'UNKNOWN'
    ds = a.active_deployment.status.state.value if a.active_deployment and a.active_deployment.status else 'UNKNOWN'
    flag = '✅' if cs == 'ACTIVE' and ds == 'SUCCEEDED' else '❌'
    print(f"{flag} {name}: compute={cs}, deploy={ds}")
```

---

## 2. Model Serving Endpoint — Risk Scoring

| Property | Expected Value |
|----------|----------------|
| **Endpoint name** | `copper-retirement-risk` |
| **State** | `READY` |
| **Config update** | `NOT_UPDATING` |
| **Served model** | `cdm_tmforum.ml_models.copper_retirement_risk` (version 5) |
| **Workload** | CPU / Small / Scale-to-zero enabled |
| **Deployment** | `DEPLOYMENT_READY` |

**Verification steps:**
1. Workspace → **Serving** → `copper-retirement-risk` → confirm green "Ready" badge.
2. If scaled to zero, the first inference call will take ~30-60s cold start. **Warm it up T-10 min before demo:**

```python
import mlflow
from mlflow.deployments import get_deploy_client
client = get_deploy_client("databricks")

# Warm-up call — use a sample record
response = client.predict(
    endpoint="copper-retirement-risk",
    inputs={"dataframe_records": [{"physical_device_id": "PD-00001"}]}
)
print(f"Warm-up response: {response}")
```

**Latency baseline:**
- Cold start (from zero): 30-60 seconds
- Warm inference: < 500ms
- If latency exceeds 2s warm, check endpoint logs.

---

## 3. Vector Search — Regulatory Documents

| Property | Expected Value |
|----------|----------------|
| **VS Endpoint** | `demo_telco_vs_endpoint` |
| **Endpoint status** | `ONLINE` |
| **Index** | `cdm_tmforum.copper_retirement.regulatory_doc_vs_index` |
| **Index status** | `ready = True` |
| **Indexed rows** | 528 documents |
| **Embedding model** | GTE-large |

**Verification steps:**
1. Workspace → **Compute** → **Vector Search** → `demo_telco_vs_endpoint` → confirm "Online".
2. Click into the index → confirm 528 indexed rows.
3. Test a query:

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

results = w.vector_search_indexes.query_index(
    index_name="cdm_tmforum.copper_retirement.regulatory_doc_vs_index",
    columns=["doc_title", "chunk_text"],
    query_text="FCC copper retirement obligations notice requirements",
    num_results=3
)
for r in results.result.data_array:
    print(f"  {r[0]}: {r[1][:100]}...")
```

**Latency baseline:**
- Query response: < 200ms (p50), < 500ms (p99)
- If index shows "PROVISIONING" or row count = 0, escalate to @pm.

---

## 4. DLP Pipeline — Data Freshness

| Property | Expected Value |
|----------|----------------|
| **Primary pipeline** | `copper-retirement-pipeline` |
| **Pipeline ID** | `b52532a2-6398-44ed-b239-9e95cafb745c` |
| **State** | `IDLE` (healthy — means not currently running) |
| **Last successful update** | 2026-09-17T03:11:02Z |
| **Materialized views** | 8 MVs + 1 VIEW (9 total) |

⚠️ **Note:** `copper-retirement-dlp` (ID: `3d0576c0`) has FAILED updates from Sep 15 — this is the **old pipeline**. Ignore it. Only monitor `copper-retirement-pipeline`.

**Materialized views freshness (all should show last_altered ≥ 2026-09-17):**

| Layer | Table | Type | Last Refreshed |
|-------|-------|------|----------------|
| Bronze | `bronze_copper_devices` | MV | 2026-09-17 |
| Bronze | `bronze_copper_services` | MV | 2026-09-17 |
| Bronze | `bronze_dig_safe_incidents` | MV | 2026-09-17 |
| Silver | `silver_copper_plant_enriched` | MV | 2026-09-17 |
| Silver | `silver_device_service_impact` | MV | 2026-09-17 |
| Gold | `gold_contractor_scorecard` | MV | 2026-09-17 |
| Gold | `gold_retirement_executive_summary` | MV | 2026-09-17 |
| Gold | `gold_wire_center_scorecard` | MV | 2026-09-17 |
| Risk | `risk_inference_unpacked` | VIEW | 2026-09-16 |

**Verification SQL (run in any SQL warehouse):**
```sql
SELECT table_name, table_type, last_altered,
  CASE WHEN last_altered >= CURRENT_DATE - INTERVAL 2 DAYS THEN '✅ FRESH' ELSE '❌ STALE' END AS status
FROM cdm_tmforum.information_schema.tables
WHERE table_schema = 'copper_retirement'
  AND table_type IN ('MATERIALIZED_VIEW', 'VIEW')
ORDER BY table_name
```

**If data is stale (> 48h old):**
1. Navigate to pipeline `copper-retirement-pipeline` in the workspace.
2. Click **Start** to trigger a manual refresh.
3. Wait ~5 min for completion. All 8 MVs should update atomically.

---

## 5. Lakebase — Task Board Database

| Property | Expected Value |
|----------|----------------|
| **Project** | `copper-task-board` |
| **Branch** | `production` |
| **Host** | `ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com` |
| **Tables** | `agent_tasks`, `status_updates`, `ceo_directives`, `decisions` |

**Verification (Python):**
```python
import psycopg
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
token = w.postgres.generate_database_credential(
    endpoint="projects/copper-task-board/branches/production/endpoints/primary"
).token
conn = psycopg.connect(
    host="ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com",
    dbname="databricks_postgres",
    user=w.current_user.me().user_name,
    password=token, sslmode="require"
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM agent_tasks")
print(f"✅ Lakebase connected — {cur.fetchone()[0]} tasks")
```

---

## 6. Pre-Demo Warm-Up Sequence (T-10 min)

Run this in order to ensure no cold-start delays during the demo:

1. **Open all app URLs** in browser tabs — this wakes up any idle compute.
2. **Hit the serving endpoint** with a warm-up inference call (see Section 2).
3. **Run a VS query** to warm the vector search cache (see Section 3).
4. **Run a quick SQL query** against the gold tables to warm the SQL warehouse:
   ```sql
   SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
   ```
5. **Verify Lakebase** responds with the connection test (see Section 5).

---

## 7. Escalation Contacts

| Issue | Escalation |
|-------|------------|
| App won't start | @app-developer, then CEO |
| Serving endpoint stuck UPDATING | CEO (interactive fix) |
| VS index row count = 0 | @data-engineer, then CEO |
| DLP pipeline FAILED | @data-engineer (check pipeline logs) |
| Lakebase unreachable | CEO (Lakebase project owner) |
| SQL warehouse unavailable | CEO (workspace admin) |

---

## 8. Known Issues & Workarounds

| Issue | Workaround |
|-------|------------|
| `copper-retirement-dlp` pipeline shows FAILED | Ignore — this is the **deprecated** pipeline. Only `copper-retirement-pipeline` matters. |
| Serving endpoint scaled to zero | Expected behavior. Warm-up call triggers scale-up in 30-60s. Do this before demo. |
| App loads slowly on first visit | Databricks Apps auto-sleep after inactivity. First load may take 10-15s. Pre-open all tabs. |

---

*Last verified: 2026-09-18 by @devops (DEVOPS-DEMO-DAY-MONITOR-0918)*
