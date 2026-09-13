# DLP Pipeline Interactive Runbook

**Author:** @devops | **Date:** 2026-09-13 | **Status:** Active  
**Task:** DEVOPS-DLP-INTERACTIVE-RUNBOOK

This runbook documents the step-by-step procedure for manually configuring and
running the copper-retirement Lakeflow Spark Declarative Pipeline (SDP). Automated
configuration via the SDK, REST API, and CLI is blocked by safety guardrails in
scheduled agent contexts. These steps must be performed in an **interactive session**
(human or interactive agent).

---

## Table of Contents

1. [Current State Summary](#1-current-state-summary)
2. [Pre-Flight Checklist](#2-pre-flight-checklist)
3. [Step 1: Add Missing SQL Files to Pipeline](#3-step-1-add-missing-sql-files)
4. [Step 2: Verify Pipeline Settings](#4-step-2-verify-pipeline-settings)
5. [Step 3: Trigger Full Refresh](#5-step-3-trigger-full-refresh)
6. [Step 4: Validate Pipeline Output](#6-step-4-validate-pipeline-output)
7. [Step 5: Decommission Old Pipeline](#7-step-5-decommission-old-pipeline)
8. [Rollback Plan](#8-rollback-plan)
9. [Known Issues & Fixes](#9-known-issues--fixes)

---

## 1. Current State Summary

### Two Pipelines Exist

| Pipeline | ID | Catalog | Schema | Status | Verdict |
|---|---|---|---|---|---|
| copper-retirement-pipeline | `b52532a2-6398-44ed-b239-9e95cafb745c` | cdm_tmforum | copper_retirement | IDLE (1 failed run) | **ACTIVE — configure this one** |
| copper-retirement-dlp | `3d0576c0-5881-4c79-bd54-cdf2e57ad207` | cmegdemos_catalog | default | IDLE (never run) | **SUPERSEDED — decommission** |

### Workaround Tables (Already Exist)

@data-engineer materialized all 10 pipeline tables as **regular Delta tables**
in `cdm_tmforum.copper_retirement` (bypassing the blocked pipeline). These are
production-ready and serving the apps. When the DLP pipeline runs successfully,
its materialized views will supersede these tables via `CREATE OR REFRESH`.

| Table | Rows | Layer |
|---|---|---|
| bronze_copper_services | 17,655 | Bronze |
| bronze_copper_devices | 2,672 | Bronze |
| bronze_dig_safe_incidents | 5,000 | Bronze |
| silver_copper_plant_enriched | 2,672 | Silver |
| silver_device_service_impact | 440 | Silver |
| silver_contract_constraints | 249 | Silver |
| gold_wire_center_scorecard | 103 | Gold |
| gold_contractor_scorecard | 10,000 | Gold |
| gold_circuit_revenue_at_risk | 14,777 | Gold |
| gold_retirement_executive_summary | 50 | Gold |

### Pipeline SQL Files (11 in directory, 8 attached)

Directory: `/Users/stephen.hage@databricks.com/copper-retirement/pipeline/`

| File | In Pipeline? | Layer |
|---|---|---|
| bronze_copper_devices.sql | Yes | Bronze |
| bronze_copper_services.sql | Yes | Bronze |
| bronze_dig_safe_incidents.sql | Yes | Bronze |
| silver_copper_plant_enriched.sql | Yes | Silver |
| silver_device_service_impact.sql | Yes | Silver |
| silver_contract_constraints.sql | **NO — must add** | Silver |
| silver_revenue_recognition_constraints.sql | **NO — must add** | Silver |
| gold_wire_center_scorecard.sql | Yes | Gold |
| gold_contractor_scorecard.sql | Yes | Gold |
| gold_circuit_revenue_at_risk.sql | **NO — must add** | Gold |
| gold_retirement_executive_summary.sql | Yes | Gold |

---

## 2. Pre-Flight Checklist

Before proceeding, verify:

- [ ] You are in an **interactive session** (not a scheduled agent run)
- [ ] Catalog `cdm_tmforum` exists and you have `USE CATALOG` privilege
- [ ] Schema `cdm_tmforum.copper_retirement` exists
- [ ] All 11 SQL files exist in the pipeline directory:
  ```sql
  -- Run in a SQL cell or notebook
  SELECT * FROM list('/Workspace/Users/stephen.hage@databricks.com/copper-retirement/pipeline/');
  ```
- [ ] Upstream source tables are populated (spot-check):
  ```sql
  SELECT 'customer_facing_service' AS tbl, COUNT(*) AS cnt FROM cdm_tmforum.tmf_service.customer_facing_service
  UNION ALL SELECT 'physical_device', COUNT(*) FROM cdm_tmforum.tmf_enterprise.physical_device
  UNION ALL SELECT 'geographic_address', COUNT(*) FROM cdm_tmforum.tmf_shared.geographic_address;
  ```
  Expected: ~100K, ~10K, ~10K respectively.

---

## 3. Step 1: Add Missing SQL Files

Three SQL files must be added to pipeline `b52532a2-6398-44ed-b239-9e95cafb745c`.

### Option A: Pipeline Editor UI (Recommended)

1. Navigate to the pipeline editor:
   - URL: `https://fevm-cmegdemos.cloud.databricks.com/#joblist/pipelines/b52532a2-6398-44ed-b239-9e95cafb745c`
   - Or use: `openAsset(assetType="pipeline-editor", assetId="b52532a2-6398-44ed-b239-9e95cafb745c")`
2. Click **Settings** (gear icon) → **Libraries** section.
3. Click **Add library** (or **Add source code**) and add each missing file:
   - `/Users/stephen.hage@databricks.com/copper-retirement/pipeline/silver_contract_constraints.sql`
   - `/Users/stephen.hage@databricks.com/copper-retirement/pipeline/silver_revenue_recognition_constraints.sql`
   - `/Users/stephen.hage@databricks.com/copper-retirement/pipeline/gold_circuit_revenue_at_risk.sql`
4. Click **Save**.

### Option B: REST API (Interactive Python Session)

```python
import requests
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.config.host
token = w.config.token  # or use w.api_client

pipeline_id = "b52532a2-6398-44ed-b239-9e95cafb745c"

# Current libraries (8 files)
current_libraries = [
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/bronze_copper_devices.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/bronze_copper_services.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/bronze_dig_safe_incidents.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/silver_copper_plant_enriched.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/silver_device_service_impact.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/gold_wire_center_scorecard.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/gold_contractor_scorecard.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/gold_retirement_executive_summary.sql"}},
    # === ADD THESE THREE ===
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/silver_contract_constraints.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/silver_revenue_recognition_constraints.sql"}},
    {"file": {"path": "/Users/stephen.hage@databricks.com/copper-retirement/pipeline/gold_circuit_revenue_at_risk.sql"}},
]

response = requests.put(
    f"{host}/api/2.0/pipelines/{pipeline_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={"libraries": current_libraries}
)
print(response.status_code, response.json())
```

### Verification

After adding, confirm the pipeline shows 11 libraries:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
p = w.pipelines.get(pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c")
print(f"Libraries: {len(p.spec.libraries)}")
for lib in p.spec.libraries:
    print(f"  {lib.file.path if lib.file else lib.notebook.path if lib.notebook else 'unknown'}")
```
Expected: 11 files.

---

## 4. Step 2: Verify Pipeline Settings

Confirm these settings in the pipeline editor (Settings panel):

| Setting | Expected Value | Notes |
|---|---|---|
| Pipeline name | `copper-retirement-pipeline` | |
| Product edition | Advanced | Default for serverless |
| Catalog | `cdm_tmforum` | **Critical — must NOT be cmegdemos_catalog** |
| Target schema | `copper_retirement` | **Critical — must NOT be default** |
| Development mode | ON (checked) | For initial testing; disable for production |
| Serverless | ON | Required for `h3_longlatash3` function |
| Channel | Current | |
| Libraries | 11 files | See Step 1 |

If any setting is wrong, correct it in the Settings panel and Save.

---

## 5. Step 3: Trigger Full Refresh

### Option A: Pipeline Editor UI (Recommended)

1. In the pipeline editor, click the **Start** button.
2. Select **Full refresh all** from the dropdown (not "Start").
   - Full refresh is needed because the workaround Delta tables already occupy
     the target schema. The pipeline needs to CREATE OR REFRESH all objects.
3. Monitor the pipeline graph for progress.

### Option B: REST API

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

update = w.pipelines.start_update(
    pipeline_id="b52532a2-6398-44ed-b239-9e95cafb745c",
    full_refresh=True
)
print(f"Update started: {update.update_id}")
```

### Option C: CLI

```bash
databricks pipelines start \
  --pipeline-id b52532a2-6398-44ed-b239-9e95cafb745c \
  --full-refresh
```

### Expected Duration

- Development mode + serverless: ~5-15 minutes for the full graph.
- Bronze layer reads from source tables (100K+ rows each).
- Silver layer enriches with spatial joins (H3).
- Gold layer aggregates into scorecards and summaries.

### Monitoring

Watch for:
- **Green checkmarks** on each dataset node in the pipeline graph.
- **COMPLETED** state in the update history.
- Any **FAILED** nodes — check the error message (see Known Issues below).

---

## 6. Step 4: Validate Pipeline Output

After a successful run, validate the output tables:

```sql
-- Row count validation
SELECT 'bronze_copper_services' AS tbl, COUNT(*) AS cnt FROM cdm_tmforum.copper_retirement.bronze_copper_services
UNION ALL SELECT 'bronze_copper_devices', COUNT(*) FROM cdm_tmforum.copper_retirement.bronze_copper_devices
UNION ALL SELECT 'bronze_dig_safe_incidents', COUNT(*) FROM cdm_tmforum.copper_retirement.bronze_dig_safe_incidents
UNION ALL SELECT 'silver_copper_plant_enriched', COUNT(*) FROM cdm_tmforum.copper_retirement.silver_copper_plant_enriched
UNION ALL SELECT 'silver_device_service_impact', COUNT(*) FROM cdm_tmforum.copper_retirement.silver_device_service_impact
UNION ALL SELECT 'silver_contract_constraints', COUNT(*) FROM cdm_tmforum.copper_retirement.silver_contract_constraints
UNION ALL SELECT 'gold_wire_center_scorecard', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_wire_center_scorecard
UNION ALL SELECT 'gold_contractor_scorecard', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_contractor_scorecard
UNION ALL SELECT 'gold_circuit_revenue_at_risk', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_circuit_revenue_at_risk
UNION ALL SELECT 'gold_retirement_executive_summary', COUNT(*) FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
ORDER BY tbl;
```

**Expected row counts** (should match or exceed workaround table counts):

| Table | Min Expected |
|---|---|
| bronze_copper_services | 17,655 |
| bronze_copper_devices | 2,672 |
| bronze_dig_safe_incidents | 5,000 |
| silver_copper_plant_enriched | 2,672 |
| silver_device_service_impact | 440 |
| silver_contract_constraints | 249 |
| gold_wire_center_scorecard | 100+ |
| gold_contractor_scorecard | 10,000 |
| gold_circuit_revenue_at_risk | 14,000+ |
| gold_retirement_executive_summary | 50 |

Also validate the two new tables (from the files not yet in the pipeline):
```sql
-- These may be new if not yet materialized by workaround
SELECT 'silver_revenue_recognition_constraints' AS tbl, COUNT(*) AS cnt 
FROM cdm_tmforum.copper_retirement.silver_revenue_recognition_constraints;
```

**Spot-check data quality:**
```sql
-- Gold executive summary should cover 6 legacy states
SELECT state, retirement_readiness_score 
FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
WHERE retirement_readiness_score IS NOT NULL
ORDER BY retirement_readiness_score DESC
LIMIT 10;

-- Revenue at risk should have non-null amounts
SELECT COUNT(*) AS total, 
       COUNT(annual_revenue_at_risk) AS with_revenue,
       SUM(annual_revenue_at_risk) AS total_revenue_at_risk
FROM cdm_tmforum.copper_retirement.gold_circuit_revenue_at_risk;
```

---

## 7. Step 5: Decommission Old Pipeline

After the new pipeline runs successfully, decommission the old one.

### Old Pipeline Details
- **Name:** copper-retirement-dlp
- **ID:** `3d0576c0-5881-4c79-bd54-cdf2e57ad207`
- **Problem:** Points to wrong catalog (`cmegdemos_catalog`) and wrong schema (`default`)
- **Libraries:** Glob to non-existent directory
- **Status:** Never successfully ran

### Decommission Steps

1. **Verify** the new pipeline (`b52532a2`) ran successfully first.
2. **Delete** the old pipeline:
   ```python
   from databricks.sdk import WorkspaceClient
   w = WorkspaceClient()
   w.pipelines.delete(pipeline_id="3d0576c0-5881-4c79-bd54-cdf2e57ad207")
   print("Old pipeline deleted.")
   ```
3. **Or via CLI:**
   ```bash
   databricks pipelines delete --pipeline-id 3d0576c0-5881-4c79-bd54-cdf2e57ad207
   ```
4. **Clean up** the old pipeline source directory (if it still exists):
   `/Users/stephen.hage@databricks.com/copper-retirement-dlp_0f9cfbfe/`
   This was the auto-generated directory from the old pipeline creation wizard.

---

## 8. Rollback Plan

If the pipeline run fails and cannot be immediately fixed:

1. **The workaround Delta tables are still in place.** They serve the apps
   and dashboards. No data loss occurs from a failed pipeline run.
2. **Do not delete the workaround tables** until the pipeline has run
   successfully at least once.
3. **To revert to workaround mode:** No action needed — the apps already
   read from `cdm_tmforum.copper_retirement.*`, which is where the
   workaround tables live.
4. **If the pipeline created partial/corrupted tables:** Drop only the
   affected materialized views and re-run the @data-engineer workaround
   notebooks to recreate the Delta tables.

---

## 9. Known Issues & Fixes

### Issue 1: CLUSTER BY Column Not Found
**Error:** `DELTA_COLUMN_NOT_FOUND_IN_SCHEMA`  
**Cause:** `bronze_copper_services.sql` originally had `CLUSTER BY (status)` but
the column is named `service_status`.  
**Fix:** Already applied by @pm (2026-09-13). The SQL file now uses
`CLUSTER BY (service_status)`.  
**Verify:** `grep 'CLUSTER BY' /Workspace/Users/stephen.hage@databricks.com/copper-retirement/pipeline/bronze_copper_services.sql`

### Issue 2: H3 Function Name
**Error:** `function h3_latlng_to_cell not found`  
**Cause:** Serverless compute uses `h3_longlatash3(lon, lat, resolution)`, not
`h3_latlng_to_cell(lat, lon, resolution)`. Note argument order is also different.  
**Fix:** All pipeline SQL files should use `h3_longlatash3`. Verify with:
```bash
grep -r 'h3_latlng_to_cell' /Workspace/Users/stephen.hage@databricks.com/copper-retirement/pipeline/
```
Expected: no matches.

### Issue 3: Pipeline Config Blocked in Scheduled Context
**Error:** SDK, REST API, and CLI `pipelines update` calls fail with safety guardrails.  
**Cause:** Scheduled agent execution contexts restrict pipeline mutations.  
**Workaround:** This entire runbook exists because of this issue. All configuration
must happen in an interactive session.

### Issue 4: Existing Delta Tables vs. Materialized Views
**Concern:** The workaround Delta tables share names with the pipeline's MV targets.  
**Resolution:** SDP `CREATE OR REFRESH STREAMING TABLE` / `MATERIALIZED VIEW`
will overwrite existing tables. No manual DROP needed.
**Exception:** If a table was created as a regular table and the pipeline tries
to create it as a streaming table (or vice versa), you may get a type conflict.
In that case, DROP the conflicting table first:
```sql
DROP TABLE IF EXISTS cdm_tmforum.copper_retirement.<table_name>;
```
Then re-run the pipeline.

---

## Appendix: Quick Command Reference

```bash
# Check pipeline status
databricks pipelines get --pipeline-id b52532a2-6398-44ed-b239-9e95cafb745c

# List pipeline updates (run history)
databricks pipelines list-updates --pipeline-id b52532a2-6398-44ed-b239-9e95cafb745c

# Get update details (replace UPDATE_ID)
databricks pipelines get-update --pipeline-id b52532a2-6398-44ed-b239-9e95cafb745c --update-id <UPDATE_ID>

# Navigate to pipeline monitoring
# URL: https://fevm-cmegdemos.cloud.databricks.com/#joblist/pipelines/b52532a2-6398-44ed-b239-9e95cafb745c

# Navigate to pipeline editor
# openAsset(assetType="pipeline-editor", assetId="b52532a2-6398-44ed-b239-9e95cafb745c")
```
