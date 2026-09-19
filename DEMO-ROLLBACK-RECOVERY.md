# Copper Retirement — Demo Rollback & Recovery Procedure

**Author:** @devops | **Created:** 2026-09-19  
**Project:** Lakelink Fiber Copper Retirement  
**Git Tag:** `v1.0-demo` (commit `43b0a74`)  
**Workspace:** `fevm-cmegdemos.cloud.databricks.com`  
**Scope:** Standalone recovery runbook for all demo-critical services

> **Purpose:** If any component fails during or before a live demo, this document provides
> copy-paste-ready commands to restore the demo to a known-good state.
> Organized as a rapid-triage decision tree — find your symptom, follow the steps.

---

## Quick Reference — Demo Infrastructure

| Component | Identifier | Known-Good State |
| --- | --- | --- |
| SQL Warehouse | `7b65956f30d66feb` (Serverless Starter) | RUNNING |
| Serving Endpoint | `copper-retirement-risk` | READY (V5 model) |
| VS Endpoint | `demo_telco_vs_endpoint` | ONLINE |
| VS Index | `cdm_tmforum.copper_retirement.regulatory_doc_vs_index` | 528 docs |
| DLP Pipeline | `b52532a2-6398-44ed-b239-9e95cafb745c` | IDLE, last run COMPLETED |
| App: Copper Map | `copper-map` | ACTIVE, SNAPSHOT deployed |
| App: Regulatory Assistant | `regulatory-assistant` | ACTIVE |
| App: Retirement Plan | `retirement-plan` | ACTIVE, SNAPSHOT deployed |
| App: Task Board | `copper-task-board` | ACTIVE, SNAPSHOT deployed |
| Lakebase Project | `copper-task-board` | Endpoint reachable, 516 tasks |
| Git Tag | `v1.0-demo` | HEAD (43b0a74), 222 files |

---

## Baseline Row Counts (v1.0-demo snapshot)

### Unity Catalog (`cdm_tmforum.copper_retirement`)

| Table | Expected Rows |
| --- | --- |
| `bronze_copper_devices` | 2,672 |
| `bronze_copper_services` | 17,655 |
| `silver_copper_plant_enriched` | 2,672 |
| `silver_device_service_impact` | 440 |
| `gold_wire_center_scorecard` | 103 |
| `gold_circuit_revenue_at_risk` | 14,777 |
| `gold_contractor_scorecard` | 10,000 |
| `gold_retirement_executive_summary` | 6 |
| `gold_device_risk_predictions` | 2,672 |
| `regulatory_doc_chunks` | 528 |

### Lakebase (`copper_app` schema)

| Table | Expected Rows |
| --- | --- |
| `device_risk_map` | 2,672 |
| `wire_center_scorecard` | 103 |
| `wire_center_boundaries` | 1,699 |
| `contractor_scorecard` | 10,000 |
| `revenue_at_risk_summary` | 1,442 |
| `executive_summary` | 50 |
| `retirement_plan` | 200 |
| `retirement_milestones` | 927 |
| `dig_incidents` | 5,000 |
| `regulatory_documents` | 297 |
| `jurisdiction_requirements` | 56 |
| `commodity_prices` | 10,482 |
| `commodity_forecast` | 72 |
| `app_kpis` | 20 |

---

## 1. Rapid Triage Decision Tree

During a live demo, identify the failing component and jump directly to the numbered section:

```
PROBLEM?
│
├── App not loading / 502 / blank ───────── → §2 App Recovery
│   ├── copper-map specifically ─────────── → §2.1
│   ├── regulatory-assistant specifically ── → §2.2
│   └── any app ─────────────────────────── → §2.3 Generic App Restart
│
├── Risk scores missing / map no colors ──── → §3 Serving Endpoint Recovery
│   ├── Endpoint NOT_READY ──────────────── → §3.1 Warm-up / Wait
│   ├── Endpoint FAILED ─────────────────── → §3.2 Model Version Rollback
│   └── Predictions look wrong ──────────── → §3.3 Model Fallback to V4
│
├── Regulatory search returns nothing ────── → §4 Vector Search Recovery
│   ├── VS endpoint OFFLINE ─────────────── → §4.1 Escalate to Admin
│   ├── Index 0 docs ────────────────────── → §4.2 Trigger Re-sync
│   └── Stale / wrong results ───────────── → §4.3 Source Table Check
│
├── Gold tables empty / stale ───────────── → §5 Pipeline Recovery
│   ├── Pipeline FAILED ─────────────────── → §5.1 Manual Refresh
│   └── SQL source files corrupted ──────── → §5.2 Git Restore
│
├── SQL Warehouse down ──────────────────── → §6 Warehouse Failover
│
├── Lakebase unreachable ────────────────── → §7 Lakebase Recovery
│
└── Full environment corrupted ──────────── → §8 Nuclear Option: Full Restore
```

---

## 2. App Recovery

### 2.1 Copper Map Not Loading

**URL:** `https://copper-map-7474656585748611.aws.databricksapps.com`  
**Source:** `/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/copper-map`

**Step 1 — Restart (90% of issues):**
```python
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient()
w.apps.stop("copper-map")
time.sleep(10)
w.apps.start("copper-map")
print("copper-map restarting — allow 60-90s for warm-up")
```

**Step 2 — If restart fails, redeploy from SNAPSHOT source:**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.apps.deploy(
    "copper-map",
    source_code_path="/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/copper-map",
    mode="SNAPSHOT"
).result()  # Blocks until deployed
print("copper-map redeployed")
```

**Step 3 — If map renders but risk colors are missing:**
- This is a serving endpoint issue → jump to §3
- **Fallback:** Set `LIVE_DATA=false` in `copper-map/app.yaml` to use mock risk scores, then redeploy

### 2.2 Regulatory Assistant Not Loading

**URL:** `https://regulatory-assistant-7474656585748611.aws.databricksapps.com`  
**Source:** `/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/regulatory-assistant`

**Step 1 — Restart:**
```python
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient()
w.apps.stop("regulatory-assistant")
time.sleep(10)
w.apps.start("regulatory-assistant")
print("regulatory-assistant restarting")
```

**Step 2 — If search returns no results:**
- This is a Vector Search issue → jump to §4
- Check `REG_AGENT_ENDPOINT` env var — if unset, app should fall back to mock data

### 2.3 Generic App Restart (any app)

Replace `<APP_NAME>` with: `copper-map`, `regulatory-assistant`, `retirement-plan`, `copper-task-board`

```python
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient()

app_name = "<APP_NAME>"  # Change this

# Check current state
app = w.apps.get(app_name)
print(f"{app_name}: compute={app.compute_status.state}, deploy={app.active_deployment.status.state if app.active_deployment else 'NONE'}")

# Restart
w.apps.stop(app_name)
time.sleep(10)
w.apps.start(app_name)
print(f"{app_name} restarting")
```

**Recovery time:** 1-2 minutes per app

---

## 3. Serving Endpoint Recovery

**Endpoint:** `copper-retirement-risk`  
**Model:** `cdm_tmforum.ml_models.copper_retirement_risk`  
**Champion:** V5 (LightGBM, AUC 0.986)  
**Fallback:** V4

### 3.1 Endpoint NOT_READY (Scale-to-Zero Wake-up)

The endpoint has scale-to-zero enabled. First request after idle triggers a cold start.

**Fix:** Send a warm-up inference request and wait 60-90 seconds:
```python
import mlflow.deployments
client = mlflow.deployments.get_deploy_client("databricks")
warm_up = {
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
result = client.predict(endpoint="copper-retirement-risk", inputs={"dataframe_records": [warm_up]})
print(f"Endpoint WARM — response: {result}")
```

### 3.2 Endpoint FAILED — Recreate

If the endpoint enters a failed state, recreate it:

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput, ServedEntityInput, AutoCaptureConfigInput
)
w = WorkspaceClient()

# Delete broken endpoint
try:
    w.serving_endpoints.delete("copper-retirement-risk")
    print("Deleted broken endpoint")
except Exception as e:
    print(f"Delete failed (may already be gone): {e}")

import time
time.sleep(10)

# Recreate with V5 config
w.serving_endpoints.create(
    name="copper-retirement-risk",
    config=EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name="cdm_tmforum.ml_models.copper_retirement_risk",
                entity_version="5",
                workload_size="Small",
                scale_to_zero_enabled=True
            )
        ],
        auto_capture_config=AutoCaptureConfigInput(
            catalog_name="cdm_tmforum",
            schema_name="copper_retirement",
            table_name_prefix="risk_model_inference",
            enabled=True
        )
    )
).result()  # Blocks until READY
print("Endpoint recreated and READY")
```

**Recovery time:** 5-10 minutes

### 3.3 Model Fallback — Roll Back to V4

If V5 predictions look wrong, fall back to V4:

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput
w = WorkspaceClient()

w.serving_endpoints.update_config(
    name="copper-retirement-risk",
    served_entities=[
        ServedEntityInput(
            entity_name="cdm_tmforum.ml_models.copper_retirement_risk",
            entity_version="4",  # Fallback version
            workload_size="Small",
            scale_to_zero_enabled=True
        )
    ]
).result()
print("Rolled back to V4")
```

**Recovery time:** 3-5 minutes

---

## 4. Vector Search Recovery

**VS Endpoint:** `demo_telco_vs_endpoint`  
**VS Index:** `cdm_tmforum.copper_retirement.regulatory_doc_vs_index`  
**Source Table:** `cdm_tmforum.copper_retirement.regulatory_doc_chunks` (528 rows)

### 4.1 VS Endpoint OFFLINE

Vector Search endpoints cannot be self-service recreated. **Escalate to workspace admin.**

While waiting, switch the regulatory-assistant app to mock mode:
- Set env var `VS_FALLBACK=true` in app.yaml (if implemented)
- Redeploy with §2.2 steps

### 4.2 Index Shows 0 Documents — Trigger Re-sync

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Verify source data exists
result = w.vector_search_indexes.get_index("cdm_tmforum.copper_retirement.regulatory_doc_vs_index")
print(f"Index status: ready={result.status.ready}, docs={result.status.indexed_row_count}")

# Trigger manual sync (TRIGGERED pipeline)
w.vector_search_indexes.sync_index("cdm_tmforum.copper_retirement.regulatory_doc_vs_index")
print("Sync triggered — allow 5-15 minutes")
```

### 4.3 Source Table Check

```sql
SELECT COUNT(*) AS total_chunks,
       COUNT(DISTINCT title) AS distinct_docs,
       COUNT(DISTINCT docket_number) AS distinct_dockets
FROM cdm_tmforum.copper_retirement.regulatory_doc_chunks;
-- Expected: 528 chunks, ~30+ distinct docs
```

### 4.4 Test Search (Verification)

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
results = w.vector_search_indexes.query_index(
    index_name="cdm_tmforum.copper_retirement.regulatory_doc_vs_index",
    columns=["embedding_text", "title", "docket_number"],
    query_text="FCC copper retirement notice requirements",
    num_results=3
)
for doc in results.result.data_array:
    print(f"  {doc[1]} ({doc[2]}): {doc[0][:100]}...")
```

**Recovery time:** 5-15 minutes (sync latency)

---

## 5. Pipeline Recovery

**Pipeline:** `copper-retirement-pipeline`  
**Pipeline ID:** `b52532a2-6398-44ed-b239-9e95cafb745c`  
**8 Materialized Views** in `cdm_tmforum.copper_retirement`

### 5.1 Pipeline FAILED — Manual Full Refresh

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Check current state
pipeline = w.pipelines.get("b52532a2-6398-44ed-b239-9e95cafb745c")
print(f"State: {pipeline.state}, Last update: {pipeline.latest_updates[0].state if pipeline.latest_updates else 'NONE'}")

# Trigger full refresh
w.pipelines.start_update(
    pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c",
    full_refresh=True
)
print("Full refresh triggered — allow 5-10 minutes")
```

**Verify after refresh:**
```sql
SELECT 'bronze_copper_devices' AS t, COUNT(*) AS n FROM cdm_tmforum.copper_retirement.bronze_copper_devices
UNION ALL SELECT 'gold_wire_center_scorecard', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard
UNION ALL SELECT 'gold_device_risk_predictions', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions;
```

### 5.2 SQL Source Files Corrupted — Git Restore

If pipeline SQL files were accidentally edited:

```bash
cd /Workspace/Users/stephen.hage@databricks.com/copper-retirement

# Restore all pipeline SQL files from v1.0-demo tag
git checkout v1.0-demo -- pipeline/

# Verify
git diff HEAD -- pipeline/
# Should show no changes (v1.0-demo = HEAD currently)
```

Then trigger a pipeline refresh per §5.1.

**Recovery time:** 5-10 minutes (serverless pipeline)

---

## 6. SQL Warehouse Failover

**Primary:** `Serverless Starter Warehouse` (ID: `7b65956f30d66feb`)  
**Backup:** `telco-builders` (ID: `da0dbcd5676d37eb`)

### 6.1 Primary Warehouse Unavailable

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Check primary
primary = w.warehouses.get("7b65956f30d66feb")
print(f"Primary state: {primary.state}")

# If STOPPED, try starting
if str(primary.state) != "RUNNING":
    w.warehouses.start("7b65956f30d66feb")
    print("Starting primary warehouse — allow 1-2 minutes")
```

### 6.2 Failover to Backup Warehouse

If primary is unrecoverable:
1. Update app `DATABRICKS_WAREHOUSE_ID` env var to `da0dbcd5676d37eb`
2. Redeploy affected apps per §2.3
3. For live SQL demos, switch to a notebook using serverless compute

**Recovery time:** 1-3 minutes

---

## 7. Lakebase Recovery

**Project:** `copper-task-board`  
**Host:** `ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com`

### 7.1 Connection Refused / Token Expired

```python
import psycopg
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Regenerate credential (tokens expire ~1hr)
token = w.postgres.generate_database_credential(
    endpoint="projects/copper-task-board/branches/production/endpoints/primary"
).token
print(f"New token generated")

# Reconnect
conn = psycopg.connect(
    host="ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com",
    dbname="databricks_postgres",
    user=w.current_user.me().user_name,
    password=token,
    sslmode="require"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM agent_tasks")
print(f"Connection OK — {cur.fetchone()[0]} tasks")
```

### 7.2 Project Suspended (24hr idle timeout)

Lakebase projects auto-suspend after 24h of inactivity. **Any query auto-resumes the project.**
Simply run the connection snippet above — the first query will trigger wake-up (30-60 seconds).

Data is fully durable — no data loss from suspension.

**Recovery time:** 30-60 seconds

---

## 8. Nuclear Option: Full Environment Restore from v1.0-demo

If multiple components are corrupted or the repo is in an unknown state:

### 8.1 Git Restore — Repo Files

```bash
cd /Workspace/Users/stephen.hage@databricks.com/copper-retirement

# Stash any uncommitted work
git stash

# Hard reset to v1.0-demo tag
git checkout v1.0-demo

# Verify
git log --oneline -1
# Expected: 43b0a74 chore(demo): finalize regulatory-assistant app.yaml for v1.0-demo tag
```

**What this restores:**
- All 222 tracked files: app source code, pipeline SQL, DAB config, notebooks, scripts
- Does NOT restore: UC table data, serving endpoints, VS indexes, Lakebase data

### 8.2 Pipeline Data Restore

After Git restore, re-run the DLP pipeline to repopulate all 8 materialized views:

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.pipelines.start_update(
    pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c",
    full_refresh=True
)
print("Pipeline full refresh started — 5-10 min")
```

### 8.3 Serving Endpoint Restore

Follow §3.2 to recreate the serving endpoint with V5 model config.

### 8.4 Vector Search Verify

The VS index is persistent and delta-synced. After confirming the source table has 528 rows, trigger a sync per §4.2.

### 8.5 App Redeploy (All 4 Apps)

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

apps = {
    "copper-map": "/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/copper-map",
    "retirement-plan": "/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/retirement-plan",
    "regulatory-assistant": "/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/regulatory-assistant",
    "copper-task-board": "/Workspace/Users/stephen.hage@databricks.com/copper-task-board-src"
}

for name, path in apps.items():
    try:
        w.apps.deploy(name, source_code_path=path, mode="SNAPSHOT").result()
        print(f"{name}: redeployed OK")
    except Exception as e:
        print(f"{name}: FAILED — {e}")
```

### 8.6 Lakebase Data Verify

Lakebase data is durable and independent of Git. Verify:
```python
cur.execute("SELECT COUNT(*) FROM agent_tasks")
print(f"agent_tasks: {cur.fetchone()[0]} (expected 516+)")
cur.execute("SELECT COUNT(*) FROM copper_app.device_risk_map")
print(f"device_risk_map: {cur.fetchone()[0]} (expected 2672)")
```

### 8.7 Full Recovery Sequence (Copy-Paste Checklist)

```
1. [ ] Git: git checkout v1.0-demo
2. [ ] Pipeline: start_update(full_refresh=True) — wait 10 min
3. [ ] Serving: recreate endpoint with V5 — wait 5 min
4. [ ] VS: verify index ready, sync if needed — wait 5 min
5. [ ] Apps: redeploy all 4 from SNAPSHOT source — wait 3 min
6. [ ] Lakebase: regenerate token, verify 516+ tasks
7. [ ] SQL Warehouse: warm-up query
8. [ ] Smoke test: open each app URL, run test queries
```

**Total recovery time: ~25-30 minutes**

---

## 9. Git Tag Inventory

Available rollback points, newest first:

| Tag | Commit | Date | Description |
| --- | --- | --- | --- |
| `v1.0-demo` | `43b0a74` | 2026-09-18 | **CURRENT** — Final demo-ready release |
| `v1.0-demo-rc4` | `467f329` | 2026-09-17 | RC4 — env freeze, 24 artifacts committed |
| `v1.0-demo-rc3` | (earlier) | 2026-09-17 | RC3 |
| `v1.0-demo-rc2` | (earlier) | 2026-09-16 | RC2 |
| `rc-demo-2026-09-16` | (earlier) | 2026-09-16 | First release candidate |

If `v1.0-demo` is itself broken, fall back to `v1.0-demo-rc4`:
```bash
git checkout v1.0-demo-rc4
```

---

## 10. Emergency Contacts & Escalation

| Severity | Action | Who |
| --- | --- | --- |
| App restart / warm-up | Self-service (this runbook) | @devops |
| Endpoint / pipeline issue | Self-service (this runbook) | @devops, @ml-engineer |
| VS endpoint OFFLINE | Cannot self-service | **Workspace admin** |
| Data corruption | Lakebase + pipeline restore | @data-engineer, @devops |
| Multiple component failure | Full restore §8 | @devops + CEO approval |
| Workspace-level outage | Databricks support | CEO |

---

**Document owner:** @devops  
**Companion docs:** `DEMO-RUNBOOK.md` (pre-flight + startup), `DEMO-ENV-FREEZE-CHECKLIST.md` (inventory)  
**Last verified:** 2026-09-19 (all baselines current)