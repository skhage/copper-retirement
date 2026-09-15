# Demo Deployment Runbook — Copper Retirement

**Author:** @devops | **Date:** 2026-09-15 | **Status:** Active  
**Project:** `/Users/stephen.hage@databricks.com/copper-retirement`  
**Catalog:** `cdm_tmforum` | **Schema:** `copper_retirement`

This runbook covers the startup, health-check, and troubleshooting procedures for
running the Copper Retirement demo. For initial workspace setup and data generation,
see `MANUAL_RUNBOOK.md`. For DLP pipeline configuration, see `DLP_PIPELINE_RUNBOOK.md`.

---

## Table of Contents

1. [App URLs & Health Endpoints](#1-app-urls--health-endpoints)
2. [Startup Sequence](#2-startup-sequence)
3. [DLP Pipeline Refresh](#3-dlp-pipeline-refresh)
4. [Model Serving Endpoint Check](#4-model-serving-endpoint-check)
5. [Vector Search Index Check](#5-vector-search-index-check)
6. [Lakebase Task Board Check](#6-lakebase-task-board-check)
7. [Known Limitations](#7-known-limitations)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. App URLs & Health Endpoints

All apps run on Databricks Apps. Workspace ID: `7474656585748611`.

| App | URL | Purpose | Beat |
|-----|-----|---------|------|
| **Copper Map** | `https://copper-map-7474656585748611.aws.databricksapps.com` | Interactive H3 hex map showing copper plant locations, risk scores, retirement readiness | Beat 1 |
| **Retirement Plan** | `https://retirement-plan-7474656585748611.aws.databricksapps.com` | Planning dashboard — executive summary, wire center scorecards, milestones | Beat 1 |
| **Dig Triage** | `https://dig-triage-7474656585748611.aws.databricksapps.com` | Dig-safe incident triage with geospatial context | Beat 2 |
| **Regulatory Assistant** | `https://regulatory-assistant-7474656585748611.aws.databricksapps.com` | RAG-powered regulatory Q&A, jurisdiction map, compliance checklist | Beat 4 |
| **Commodity Dashboard** | `https://commodity-dashboard-7474656585748611.aws.databricksapps.com` | Copper commodity pricing, forecasts, EBITDA impact | Beat 3 |

**Additional operational apps:**

| App | URL | Purpose |
|-----|-----|---------|
| **Task Board** | `https://copper-task-board-7474656585748611.aws.databricksapps.com` | Multi-agent task board UI (reads from Lakebase) |
| **Lakelink RA Review** | `https://lakelink-ra-review-7474656585748611.aws.databricksapps.com` | Revenue assurance review dashboard |

**Health check (all apps):**

Apps should show `ACTIVE` compute status. Verify via CLI:
```bash
databricks apps list | grep -E 'copper|regulatory|commodity|retirement|dig-triage'
```

Or via SDK:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
for name in ['copper-map', 'retirement-plan', 'dig-triage', 'regulatory-assistant', 'commodity-dashboard']:
    app = w.apps.get(name)
    print(f"{name}: {app.compute_status.state}")
```

Expected: all should return `ComputeState.ACTIVE`.

---

## 2. Startup Sequence

**Before the demo, verify these in order:**

### Step 1: DLP Pipeline is IDLE (not FAILED)
```python
p = w.pipelines.get(pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c")
assert p.state.name == 'IDLE', f"Pipeline state: {p.state}"
print(f"Pipeline: {p.name} — {p.state} ✓")
```

### Step 2: Model Serving Endpoint is READY
```python
ep = w.serving_endpoints.get(name="copper-retirement-risk")
assert ep.state.ready.name == 'READY', f"Endpoint state: {ep.state}"
print(f"Endpoint: copper-retirement-risk — READY ✓")
```

### Step 3: Vector Search Index is ONLINE
```python
idx = w.vector_search_indexes.get_index(index_name="cdm_tmforum.copper_retirement.regulatory_doc_vs_index")
print(f"VS Index: {idx.name} — {idx.status} ✓")
```

### Step 4: Apps are ACTIVE
See health check in Section 1.

### Step 5: Lakebase Task Board is connected
```python
import psycopg
endpoint_name = "projects/copper-task-board/branches/production/endpoints/primary"
host = "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
user = w.current_user.me().user_name
token = w.postgres.generate_database_credential(endpoint=endpoint_name).token
conn = psycopg.connect(host=host, dbname="databricks_postgres", user=user, password=token, sslmode="require")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM agent_tasks")
count = cur.fetchone()[0]
print(f"Lakebase: {count} tasks in agent_tasks ✓")
conn.close()
```

### Step 6: Key tables are populated
```sql
-- Core DLP materialized views (should be non-empty)
SELECT 'bronze_copper_devices' AS tbl, COUNT(*) AS cnt FROM cdm_tmforum.copper_retirement.bronze_copper_devices
UNION ALL
SELECT 'bronze_copper_services', COUNT(*) FROM cdm_tmforum.copper_retirement.bronze_copper_services
UNION ALL
SELECT 'gold_device_risk_predictions', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions
UNION ALL
SELECT 'gold_wire_center_scorecard', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard
UNION ALL
SELECT 'gold_retirement_executive_summary', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
UNION ALL
SELECT 'regulatory_doc_chunks', COUNT(*) FROM cdm_tmforum.copper_retirement.regulatory_doc_chunks
UNION ALL
SELECT 'state_puc_jurisdiction_requirements', COUNT(*) FROM cdm_tmforum.copper_retirement.state_puc_jurisdiction_requirements;
```

---

## 3. DLP Pipeline Refresh

**Active pipeline:** `copper-retirement-pipeline`  
**Pipeline ID:** `b52532a2-6398-44ed-b239-9e95cafb745c`  
**Catalog:** `cdm_tmforum` | **Target schema:** `copper_retirement`  
**State:** Should be `IDLE` (runs on-demand, not continuous)

**Legacy pipeline (do NOT use):** `copper-retirement-dlp` (`3d0576c0`) — wrong catalog (cmegdemos_catalog.default). Superseded.

**To trigger a full refresh:**
```python
update = w.pipelines.start_update(
    pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c",
    full_refresh=True
)
print(f"Update started: {update.update_id}")
```

**To check update status:**
```python
p = w.pipelines.get(pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c")
print(f"State: {p.state}")
if p.latest_updates:
    latest = p.latest_updates[0]
    print(f"Latest update: {latest.update_id} — {latest.state}")
```

**Materialized views (46 tables):** See `cdm_tmforum.copper_retirement` schema.
Key MVs: `bronze_copper_devices`, `bronze_copper_services`, `silver_copper_plant_enriched`,
`gold_device_risk_predictions`, `gold_wire_center_scorecard`, `gold_retirement_executive_summary`,
`gold_circuit_revenue_at_risk`, `gold_ebitda_forecast`.

---

## 4. Model Serving Endpoint Check

**Endpoint:** `copper-retirement-risk`  
**Model:** V5 risk model (GBT classifier)  
**State:** Should be `READY` with `NOT_UPDATING` config

**Health check:**
```python
ep = w.serving_endpoints.get(name="copper-retirement-risk")
print(f"Ready: {ep.state.ready}")
print(f"Config update: {ep.state.config_update}")
```

**Test inference:**
```python
import json
response = w.serving_endpoints.query(
    name="copper-retirement-risk",
    dataframe_records=[{
        "device_age_years": 15.0,
        "alarm_rate_30d": 0.8,
        "complaint_rate_90d": 0.5,
        "firmware_age_months": 60,
        "revenue_at_risk": 150.0
    }]
)
print(json.dumps(response.as_dict(), indent=2))
```

**Inference table logging:** Enabled — logs to `cdm_tmforum.copper_retirement.risk_model_inference_payload`.

---

## 5. Vector Search Index Check

**VS Endpoint:** `demo_telco_vs_endpoint` (ONLINE)  
**Index:** `cdm_tmforum.copper_retirement.regulatory_doc_vs_index`  
**Type:** DELTA_SYNC (auto-syncs from `regulatory_doc_chunks` table)  
**Primary key:** `chunk_id`  
**Embeddings:** GTE-large  
**Doc count:** ~528 documents indexed

**Health check:**
```python
idx = w.vector_search_indexes.get_index(
    index_name="cdm_tmforum.copper_retirement.regulatory_doc_vs_index"
)
print(f"Status: {idx.status}")
print(f"Num docs: {idx.num_docs if hasattr(idx, 'num_docs') else 'N/A'}")
```

**Test similarity search:**
```python
results = w.vector_search_indexes.query_index(
    index_name="cdm_tmforum.copper_retirement.regulatory_doc_vs_index",
    columns=["chunk_id", "document_title", "chunk_text"],
    query_text="What are the FCC requirements for copper retirement notification?",
    num_results=3
)
for r in results.result.data_array:
    print(f"  {r[1]}: {r[2][:100]}...")
```

---

## 6. Lakebase Task Board Check

**Project:** `copper-task-board`  
**Branch:** `production`  
**Endpoint:** `ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com`  
**Database:** `databricks_postgres`

**Cross-team dashboard query:**
```sql
SELECT agent_role,
    COUNT(*) FILTER (WHERE status='completed') AS done,
    COUNT(*) FILTER (WHERE status IN ('open','in_progress')) AS open,
    COUNT(*) FILTER (WHERE status='blocked') AS blocked,
    COUNT(*) AS total
FROM agent_tasks
GROUP BY agent_role
ORDER BY agent_role;
```

**Expected:** 250+ tasks across 9 agent roles, 98%+ completion rate.

---

## 7. Known Limitations

### Vector Search — Column Descriptions
The VS index (`regulatory_doc_vs_index`) does not expose column-level descriptions
in the Delta Sync configuration. Document column semantics are recorded in the
source table (`regulatory_doc_chunks`) COMMENT metadata instead.

### Metric View SQL Scaffolds
Four metric view SQL files are committed as empty scaffolds (per CEO Semantic
Modeling Mandate, 2026-09-14). They need @data-analyst to populate:
- `src/metric_views/copper_customers_impacted.sql`
- `src/metric_views/copper_ebitda_impact_achieved.sql`
- `src/metric_views/copper_ebitda_impact_forecast.sql`
- `src/metric_views/copper_retirement_project_status.sql`

### DLP Pipeline — No Continuous Mode
The pipeline runs on-demand (IDLE state). It does NOT continuously process.
Trigger a full refresh before the demo if source data has changed.

### Legacy Pipeline
`copper-retirement-dlp` (3d0576c0) points to wrong catalog (`cmegdemos_catalog.default`).
Do NOT use it. The correct pipeline is `copper-retirement-pipeline` (b52532a2).

### Git Credential
The default GitHub PAT credential (`GitHub credential`, ID 696558001589676, user
stephen-hage_data) is expired/invalid. All Git pushes must use the **skhage-github**
OAuth credential (ID 358347682222830, user skhage). Pass `gitCredentialId=358347682222830`
explicitly on every `runGit` commit_and_push call.

### Model Serving — Feature Columns
The V5 risk model expects specific feature columns. If the feature engineering
tables are refreshed, verify column names match the model signature before
re-scoring.

### Synthetic Data — FK Compliance
All synthetic data must draw FK values from existing parent tables
(`tmf_customer.customer`, `tmf_shared.geographic_address`, etc.). Never generate
orphan FK values.

---

## 8. Troubleshooting

### App shows blank page or 502
1. Check app compute status: `databricks apps get <app-name>`
2. If compute is `STOPPED`, restart: `databricks apps start <app-name>`
3. Check app logs: `databricks apps logs <app-name>`
4. Verify the app's `app.yaml` SQL warehouse reference is valid.

### DLP Pipeline fails with table conflict
**Symptom:** `TABLE_OR_VIEW_ALREADY_EXISTS`  
**Cause:** A managed table with the same name exists outside the pipeline.  
**Fix:**
1. Identify the conflicting table: `DESCRIBE EXTENDED cdm_tmforum.copper_retirement.<table>`
2. Drop the managed table: `DROP TABLE cdm_tmforum.copper_retirement.<table>`
3. Re-run the pipeline with full refresh.

*Reference: This was the DLP table conflict resolved by CEO on 2026-09-14.*

### Model serving endpoint stuck in UPDATING
1. Check config update state: `w.serving_endpoints.get(name="copper-retirement-risk").state`
2. If stuck > 30 min, the model artifact may be invalid.
3. Check MLflow model registry for the latest version.
4. Re-deploy with: `w.serving_endpoints.update_config(name=..., served_entities=[...])`

### Vector Search index not returning results
1. Verify index status is ONLINE (not PROVISIONING).
2. Check source table has data: `SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.regulatory_doc_chunks`
3. If index shows 0 docs, trigger a sync: the DELTA_SYNC index auto-syncs, but
   changes may take 5-10 minutes to propagate.

### Lakebase connection timeout
1. Verify the endpoint is active — Lakebase endpoints scale to zero after inactivity.
2. First connection after cold start may take 10-30 seconds.
3. Retry once — the second attempt usually succeeds after wake-up.
4. If persistent, check that the SDK version supports `w.postgres.generate_database_credential`
   (requires `databricks-sdk >= 0.118.0`).

### Git push fails with authentication error
1. Run `runGit(list_credentials)` to see available credentials.
2. Use `skhage-github` (ID 358347682222830) — the only working credential.
3. Pass `gitCredentialId=358347682222830` explicitly.
4. If OAuth token is expired, re-authenticate via Linked Accounts:
   `https://fevm-cmegdemos.cloud.databricks.com/settings/user/linked-accounts?o=7474656585748611`

### H3 function errors on serverless
Serverless uses `h3_longlatash3(lon, lat, resolution)`, NOT `h3_latlng_to_cell(lat, lon, res)`.
Note the argument order: **longitude first**, then latitude.

---

*Last updated: 2026-09-15 by @devops*
