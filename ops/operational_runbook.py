# Databricks notebook source
# DBTITLE 1,Operational Runbook — Copper Retirement
# MAGIC %md
# MAGIC # Copper Retirement — Operational Runbook
# MAGIC **telco_project:** `copper-retirement` | **Catalog:** `cdm_tmforum` | **Schema:** `copper_retirement`
# MAGIC
# MAGIC **Owner:** @data-engineer | **Last Updated:** 2026-09-21 | **Version:** 1.0
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Table of Contents
# MAGIC 1. **Infrastructure Inventory** — all components at a glance
# MAGIC 2. **DLP Pipeline** — schedule, health check, manual recovery
# MAGIC 3. **Metric Views** — refresh cadence, rebuild procedures
# MAGIC 4. **Lakebase Sync** — copper_app schema, connection, recovery
# MAGIC 5. **Serving Endpoints** — model serving health, rollback
# MAGIC 6. **Vector Search** — index status, re-indexing
# MAGIC 7. **Databricks Apps** — 5 demo apps, restart procedures
# MAGIC 8. **Agent Automations** — 9 scheduled tasks, monitoring
# MAGIC 9. **Health-Check Dashboard** — single-cell all-systems check
# MAGIC 10. **Escalation Contacts** — who to page for what
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 1. Infrastructure Inventory
# MAGIC
# MAGIC | Component | Name / ID | Status Target | Owner |
# MAGIC | --- | --- | --- | --- |
# MAGIC | DLP Pipeline | `copper-retirement-pipeline` (b52532a2) | IDLE / last run < 48h | @data-engineer |
# MAGIC | Serving Endpoint | `copper-retirement-risk` (V5 champion) | READY | @ml-engineer |
# MAGIC | Vector Search | `demo_telco_vs_endpoint` / `regulatory_doc_vs_index` | ONLINE | @ml-engineer |
# MAGIC | Lakebase | `copper-task-board` / `copper_app` (19 tables) | Connected | @data-engineer |
# MAGIC | Metric Views | 8 total (4 in `_metrics`, 4 in `copper_retirement`) | Refreshed | @data-analyst |
# MAGIC | Apps (5) | copper-map, retirement-plan, dig-triage, regulatory-assistant, commodity-dashboard | SUCCEEDED | @app-developer |
# MAGIC | Agent Schedules | 9 scheduled tasks (all agents) | Active | @pm |

# COMMAND ----------

# DBTITLE 1,2. DLP Pipeline
# MAGIC %md
# MAGIC ## 2. DLP Pipeline — `copper-retirement-pipeline`
# MAGIC
# MAGIC **Pipeline ID:** `b52532a2-6398-44ed-b239-9e95cafb745c`
# MAGIC **Compute:** Serverless | **Catalog:** `cdm_tmforum` | **Target Schema:** `copper_retirement`
# MAGIC
# MAGIC ### Pipeline DAG (8 Materialized Views)
# MAGIC ```
# MAGIC BRONZE (source ingestion):
# MAGIC   bronze_copper_devices       ← tmf_enterprise.physical_device + geographic_address
# MAGIC   bronze_copper_services       ← tmf_service.customer_facing_service
# MAGIC   bronze_dig_safe_incidents    ← copper_retirement.dig_safe_incident
# MAGIC
# MAGIC SILVER (enrichment):
# MAGIC   silver_copper_plant_enriched ← bronze_copper_devices + resource_performance + alarm
# MAGIC   silver_device_service_impact ← bronze_copper_devices + bronze_copper_services + device_service_allocation
# MAGIC
# MAGIC GOLD (aggregation):
# MAGIC   gold_wire_center_scorecard   ← silver_copper_plant_enriched + silver_device_service_impact + risk_scores
# MAGIC   gold_contractor_scorecard    ← contractor_performance + contractor_incident_history
# MAGIC   gold_retirement_executive_summary ← gold_wire_center_scorecard + gold_wave_schedule + gold_circuit_revenue_at_risk
# MAGIC ```
# MAGIC
# MAGIC ### Source Files
# MAGIC | File | Path |
# MAGIC | --- | --- |
# MAGIC | bronze_copper_devices.sql | `/copper-retirement/pipeline/bronze_copper_devices.sql` |
# MAGIC | bronze_copper_services.sql | `/copper-retirement/pipeline/bronze_copper_services.sql` |
# MAGIC | bronze_dig_safe_incidents.sql | `/copper-retirement/pipeline/bronze_dig_safe_incidents.sql` |
# MAGIC | silver_copper_plant_enriched.sql | `/copper-retirement/pipeline/silver_copper_plant_enriched.sql` |
# MAGIC | silver_device_service_impact.sql | `/copper-retirement/pipeline/silver_device_service_impact.sql` |
# MAGIC | gold_wire_center_scorecard.sql | `/copper-retirement/pipeline/gold_wire_center_scorecard.sql` |
# MAGIC | gold_contractor_scorecard.sql | `/copper-retirement/pipeline/gold_contractor_scorecard.sql` |
# MAGIC | gold_retirement_executive_summary.sql | `/copper-retirement/pipeline/gold_retirement_executive_summary.sql` |
# MAGIC
# MAGIC ### Schedule
# MAGIC - **Trigger:** Runs on-demand or via scheduled job (recommend daily 02:00 UTC)
# MAGIC - **Last successful run:** 2026-09-19 07:08 UTC (update ID: `cb8d30f2`)
# MAGIC - **Mode:** Development (set `development: true` in config)
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **Full refresh:** Navigate to pipeline monitoring page → Start → Full Refresh
# MAGIC 2. **Single MV refresh:** `ALTER MATERIALIZED VIEW cdm_tmforum.copper_retirement.<mv_name> REFRESH`
# MAGIC 3. **Pipeline stuck/failed:** Check event log: `SELECT * FROM cdm_tmforum.copper_retirement.event_log_b52532a2_6398_44ed_b239_9e95cafb745c ORDER BY timestamp DESC LIMIT 20`
# MAGIC 4. **Table conflict (managed table exists):** Drop the conflicting managed table first: `DROP TABLE IF EXISTS cdm_tmforum.copper_retirement.<table_name>`, then re-run pipeline
# MAGIC 5. **Known issue (resolved):** CEO dropped 8 managed tables on 2026-09-14 to resolve DLP conflict. If conflict recurs, check `__materialization_*` tables.

# COMMAND ----------

# DBTITLE 1,2a. DLP Pipeline Health Check
# DLP Pipeline Health Check
from databricks.sdk import WorkspaceClient
from datetime import datetime, timezone

w = WorkspaceClient()
PIPELINE_ID = "b52532a2-6398-44ed-b239-9e95cafb745c"

pipeline = w.pipelines.get(PIPELINE_ID)
print(f"Pipeline: {pipeline.name}")
print(f"State: {pipeline.state}")

# Check latest updates
updates = list(w.pipelines.list_updates(PIPELINE_ID).updates or [])
if updates:
    latest = updates[0]
    print(f"\nLatest Update:")
    print(f"  ID: {latest.update_id}")
    print(f"  State: {latest.state}")
    print(f"  Created: {latest.creation_time}")
    
    # Calculate age
    if latest.creation_time:
        created_str = str(latest.creation_time)
        # Parse ISO format
        try:
            created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
            status = "✅" if age_hours < 48 else "⚠️" if age_hours < 72 else "🚨"
            print(f"  Age: {age_hours:.1f} hours {status}")
        except:
            print(f"  Created: {created_str}")

# Check MV row counts
print("\nMaterialized View Row Counts:")
mvs = [
    "bronze_copper_devices", "bronze_copper_services", "bronze_dig_safe_incidents",
    "silver_copper_plant_enriched", "silver_device_service_impact",
    "gold_wire_center_scorecard", "gold_contractor_scorecard", "gold_retirement_executive_summary"
]
for mv in mvs:
    try:
        count = spark.sql(f"SELECT COUNT(*) as cnt FROM cdm_tmforum.copper_retirement.{mv}").collect()[0].cnt
        status = "✅" if count > 0 else "🚨 EMPTY"
        print(f"  {mv}: {count:,} rows {status}")
    except Exception as e:
        print(f"  {mv}: ❌ ERROR - {e}")

# COMMAND ----------

# DBTITLE 1,3. Metric Views
# MAGIC %md
# MAGIC ## 3. Metric Views — Refresh & Rebuild
# MAGIC
# MAGIC ### Inventory (8 metric views)
# MAGIC
# MAGIC **In `cdm_tmforum._metrics` schema:**
# MAGIC | Metric View | Source | Description |
# MAGIC | --- | --- | --- |
# MAGIC | `copper_contractor_utilization` | `v_contractor_utilization` | Crew availability, assignment rate, SLA compliance |
# MAGIC | `copper_dig_incident_response_time` | `silver_dig_incident_enriched` | Triage SLA metrics |
# MAGIC | `copper_retirement_wave_progress` | `gold_copper_recovery_schedule` | Wave completion % by region/quarter |
# MAGIC | `regulatory_copper_exposure_by_state` | Multiple | Regulatory exposure metrics |
# MAGIC
# MAGIC **In `cdm_tmforum.copper_retirement` schema:**
# MAGIC | Metric View | Description |
# MAGIC | --- | --- |
# MAGIC | `copper_retirement_project_status` | Overall project KPIs |
# MAGIC | `copper_customers_impacted` | Customer impact counts |
# MAGIC | `copper_ebitda_impact_achieved` | Realized EBITDA savings |
# MAGIC | `copper_ebitda_impact_forecast` | Projected EBITDA |
# MAGIC | `copper_commodity_sell_hold_signal` | Commodity trading signal |
# MAGIC
# MAGIC ### Refresh Cadence
# MAGIC - Metric views are **live** — they query source tables at read time
# MAGIC - No scheduled refresh needed; data freshness depends on source table updates
# MAGIC - Source tables refresh via: DLP pipeline (MVs), scheduled agent jobs (managed tables), manual DML
# MAGIC
# MAGIC ### Rebuild Procedure (if corrupt or schema change)
# MAGIC ```sql
# MAGIC -- 1. Check current definition
# MAGIC SHOW CREATE TABLE cdm_tmforum._metrics.copper_contractor_utilization;
# MAGIC
# MAGIC -- 2. Drop and recreate (get DDL from data-analyst notebooks)
# MAGIC DROP METRIC VIEW IF EXISTS cdm_tmforum._metrics.<metric_view_name>;
# MAGIC -- Then re-run the CREATE METRIC VIEW from the @data-analyst notebook that created it
# MAGIC ```
# MAGIC
# MAGIC ### Troubleshooting
# MAGIC - **"Table not found" in metric view:** Source table was dropped or renamed. Check DLP pipeline status.
# MAGIC - **Stale data:** Metric views are live queries — check if the *source* table has fresh data.
# MAGIC - **Schema mismatch:** If source columns change, metric view needs to be recreated.

# COMMAND ----------

# DBTITLE 1,4. Lakebase Sync
# MAGIC %md
# MAGIC ## 4. Lakebase Sync — `copper-task-board` / `copper_app`
# MAGIC
# MAGIC ### Connection Details
# MAGIC | Property | Value |
# MAGIC | --- | --- |
# MAGIC | Project | `copper-task-board` |
# MAGIC | Branch | `production` |
# MAGIC | Endpoint | `projects/copper-task-board/branches/production/endpoints/primary` |
# MAGIC | Host | `ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com` |
# MAGIC | Database | `databricks_postgres` |
# MAGIC | Auth | Databricks SDK token generation (`w.postgres.generate_database_credential`) |
# MAGIC
# MAGIC ### Schemas & Tables
# MAGIC
# MAGIC **`public` schema (task board):**
# MAGIC - `agent_tasks` — all agent task assignments and status
# MAGIC - `status_updates` — daily PM rollups
# MAGIC - `ceo_directives` — active CEO directives
# MAGIC - `decisions` — architecture/design decisions
# MAGIC
# MAGIC **`copper_app` schema (app data layer, 19 tables):**
# MAGIC - `app_kpis`, `commodity_forecast`, `commodity_prices`, `contractor_scorecard`
# MAGIC - `device_risk_map`, `dig_incidents`, `executive_summary`
# MAGIC - `gold_contractor_assignment_plan`, `gold_copper_recovery_schedule`
# MAGIC - `gold_reroute_options`, `gold_wave_schedule`
# MAGIC - `jurisdiction_requirements`, `regulatory_checklist_status`, `regulatory_documents`
# MAGIC - `retirement_milestones`, `retirement_plan`, `revenue_at_risk_summary`
# MAGIC - `wire_center_boundaries`, `wire_center_scorecard`
# MAGIC
# MAGIC ### Sync Mechanism
# MAGIC Gold tables in UC (`cdm_tmforum.copper_retirement`) are synced to Lakebase `copper_app` via the `P5-SYNC-GOLD-TO-LAKEBASE` notebook. This is a **manual/scheduled sync** — not live replication.
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **Connection failure:** Regenerate token — tokens are short-lived. Always call `w.postgres.generate_database_credential()` fresh.
# MAGIC 2. **Stale app data:** Re-run the sync notebook (or the SQL INSERT/UPSERT statements from DE task `P5-SYNC-GOLD-TO-LAKEBASE-0920`).
# MAGIC 3. **Schema drift:** If UC gold table columns change, update the Lakebase CREATE TABLE and re-sync.
# MAGIC 4. **Check Lakebase health:** `SELECT table_name, pg_total_relation_size(quote_ident(table_name)) FROM information_schema.tables WHERE table_schema='copper_app'`

# COMMAND ----------

# DBTITLE 1,4a. Lakebase Connection Health Check
# Lakebase Connection & Data Freshness Check
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
print("✅ Lakebase connection successful")

# Check copper_app table sizes
print("\ncopper_app tables:")
cur.execute("""
    SELECT table_name,
           (SELECT COUNT(*) FROM copper_app."" || table_name || "") as est_rows
    FROM information_schema.tables 
    WHERE table_schema = 'copper_app' 
    ORDER BY table_name
""")
# Simpler approach - count each table
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'copper_app' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM copper_app."{t}"')
        count = cur.fetchone()[0]
        status = "✅" if count > 0 else "⚠️ EMPTY"
        print(f"  {t}: {count:,} rows {status}")
    except Exception as e:
        print(f"  {t}: ❌ {e}")

# Check task board health
print("\nTask board status:")
cur.execute("SELECT status, COUNT(*) FROM agent_tasks GROUP BY status ORDER BY status")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

cur.close()
conn.close()

# COMMAND ----------

# DBTITLE 1,5. Serving Endpoints
# MAGIC %md
# MAGIC ## 5. Serving Endpoints — Model Serving
# MAGIC
# MAGIC ### Active Endpoints
# MAGIC | Endpoint | Model | Version | Status | Inference Table |
# MAGIC | --- | --- | --- | --- | --- |
# MAGIC | `copper-retirement-risk` | `cdm_tmforum.ml_models.copper_retirement_risk` | V5 (champion) / V4 (challenger) | READY | `risk_inference_unpacked` |
# MAGIC
# MAGIC ### Health Check
# MAGIC - **Status:** Must show `READY` (not `NOT_READY` or `FAILED`)
# MAGIC - **Monitoring notebook:** `/copper-retirement/monitoring/v2_model_monitoring_runbook` (notebook ID: 2984097112450182)
# MAGIC - **Run cadence:** Weekly (Monday 06:00 UTC) or after model retrain
# MAGIC
# MAGIC ### Alerting Thresholds
# MAGIC | Metric | Yellow | Red |
# MAGIC | --- | --- | --- |
# MAGIC | PSI (any feature) | > 0.10 | > 0.25 |
# MAGIC | Tier distribution shift | > 5pp | > 10pp |
# MAGIC | Inference table lag | > 3 days | > 7 days |
# MAGIC | AUC degradation | > 0.02 | > 0.05 |
# MAGIC | Fairness slice recall drop | > 10% | > 15% |
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **Endpoint not ready:** Check `w.serving_endpoints.get('copper-retirement-risk').state`
# MAGIC 2. **Rollback to challenger:** Update endpoint config to serve V4 instead of V5
# MAGIC 3. **Re-deploy:** `w.serving_endpoints.update_config('copper-retirement-risk', served_entities=[...])` with correct model version
# MAGIC 4. **Stale predictions:** Re-run batch scoring notebook, then check `copper_risk_predictions` table freshness
# MAGIC 5. **Inference table missing:** Verify `risk_model_inference_payload` table exists; re-enable logging on endpoint config

# COMMAND ----------

# DBTITLE 1,5a. Serving Endpoint Health Check
# Serving Endpoint Health Check
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ENDPOINT_NAME = "copper-retirement-risk"

ep = w.serving_endpoints.get(ENDPOINT_NAME)
print(f"Endpoint: {ep.name}")
print(f"State: {ep.state.ready}")
print(f"Config update: {ep.state.config_update}")

if ep.config and ep.config.served_entities:
    for se in ep.config.served_entities:
        print(f"\nServed Entity:")
        print(f"  Model: {se.entity_name}")
        print(f"  Version: {se.entity_version}")
        print(f"  Scale to zero: {se.scale_to_zero_enabled}")
        print(f"  Workload size: {se.workload_size}")

# Check inference table freshness
try:
    freshness = spark.sql("""
        SELECT COUNT(*) as total_rows,
               MAX(databricks_request_timestamp) as latest_inference,
               DATEDIFF(CURRENT_DATE(), MAX(databricks_request_timestamp)) as days_since_last
        FROM cdm_tmforum.copper_retirement.risk_model_inference_payload
    """).collect()[0]
    print(f"\nInference Table:")
    print(f"  Total rows: {freshness.total_rows:,}")
    print(f"  Latest: {freshness.latest_inference}")
    days = freshness.days_since_last or 0
    status = "✅" if days < 3 else "⚠️" if days < 7 else "🚨"
    print(f"  Days since last: {days} {status}")
except Exception as e:
    print(f"\nInference table check: {e}")

# COMMAND ----------

# DBTITLE 1,6. Vector Search
# MAGIC %md
# MAGIC ## 6. Vector Search — Regulatory Document Index
# MAGIC
# MAGIC ### Configuration
# MAGIC | Property | Value |
# MAGIC | --- | --- |
# MAGIC | VS Endpoint | `demo_telco_vs_endpoint` |
# MAGIC | Index | `cdm_tmforum.copper_retirement.regulatory_doc_vs_index` |
# MAGIC | Source Table | `cdm_tmforum.copper_retirement.regulatory_doc_chunks` |
# MAGIC | Embeddings | GTE-large |
# MAGIC | Documents | ~528 indexed |
# MAGIC | Status | ONLINE |
# MAGIC
# MAGIC ### Health Check
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC w = WorkspaceClient()
# MAGIC vs = w.vector_search_indexes.get_index('cdm_tmforum.copper_retirement.regulatory_doc_vs_index')
# MAGIC print(f"Status: {vs.status.ready}")
# MAGIC print(f"Num docs: {vs.status.num_embeddings}")
# MAGIC ```
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **Index offline:** Check VS endpoint status first: `w.vector_search_endpoints.get_endpoint('demo_telco_vs_endpoint')`
# MAGIC 2. **Re-index:** Sync the index: `w.vector_search_indexes.sync_index('cdm_tmforum.copper_retirement.regulatory_doc_vs_index')`
# MAGIC 3. **Source data changed:** Add new docs to `regulatory_doc_chunks`, then sync. Delta Sync indexes auto-detect changes.
# MAGIC 4. **Endpoint down:** Cannot restart programmatically — escalate to CEO/workspace admin.
# MAGIC
# MAGIC ### Troubleshooting
# MAGIC - **Stale search results:** Check if `regulatory_doc_chunks` has new rows not yet synced
# MAGIC - **Embedding errors:** Verify the embedding model endpoint is active
# MAGIC - **"Index not found":** Confirm full path: `cdm_tmforum.copper_retirement.regulatory_doc_vs_index`

# COMMAND ----------

# DBTITLE 1,7. Databricks Apps
# MAGIC %md
# MAGIC ## 7. Databricks Apps — 5 Demo Applications
# MAGIC
# MAGIC ### App Inventory
# MAGIC | App | Beat | Description | Deploy Status |
# MAGIC | --- | --- | --- | --- |
# MAGIC | `copper-map` | Beat 1 | H3 hex map of copper plant, risk overlay | SUCCEEDED |
# MAGIC | `retirement-plan` | Beat 2 | Wave timeline, budget, regulatory checklist | SUCCEEDED |
# MAGIC | `dig-triage` | Beat 3 | Incident triage with UC function integration | SUCCEEDED |
# MAGIC | `regulatory-assistant` | Beat 4 | RAG-powered regulatory Q&A | SUCCEEDED |
# MAGIC | `commodity-dashboard` | Beat 5 | Copper price forecast, scrap recovery | SUCCEEDED |
# MAGIC
# MAGIC ### Supporting App
# MAGIC | App | Purpose |
# MAGIC | --- | --- |
# MAGIC | `copper-task-board` | Agent task board UI (Lakebase-backed) |
# MAGIC
# MAGIC ### Health Check
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC w = WorkspaceClient()
# MAGIC for name in ['copper-map', 'retirement-plan', 'dig-triage', 'regulatory-assistant', 'commodity-dashboard']:
# MAGIC     app = w.apps.get(name)
# MAGIC     state = app.active_deployment.status.state if app.active_deployment and app.active_deployment.status else 'UNKNOWN'
# MAGIC     print(f"{name}: {state}")
# MAGIC ```
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **App not responding:** Restart: `w.apps.stop(name)` then `w.apps.start(name)`
# MAGIC 2. **Deploy failed:** Check logs: `w.apps.get_deployment(name, deployment_id).status`
# MAGIC 3. **Re-deploy from source:** Navigate to app page → Deploy from source code directory
# MAGIC 4. **Data layer issues:** Apps read from Lakebase `copper_app` schema — check Lakebase sync (Section 4)
# MAGIC 5. **Brand issues:** Escalate to @designer for UX review
# MAGIC
# MAGIC ### App Source Code Locations
# MAGIC All apps are scaffolded in `/Users/stephen.hage@databricks.com/copper-retirement/apps/` with AppKit/React frontends and FastAPI/Databricks SQL backends.

# COMMAND ----------

# DBTITLE 1,8. Agent Automations
# MAGIC %md
# MAGIC ## 8. Agent Automations — 9 Scheduled Tasks
# MAGIC
# MAGIC All agent personas run on Databricks scheduled tasks. Per CEO directive, **DML is approved** for scheduled runs.
# MAGIC
# MAGIC ### Schedule Inventory
# MAGIC | Agent | Task ID | Cadence | Purpose |
# MAGIC | --- | --- | --- | --- |
# MAGIC | @data-planner | `b27c43599c28466498a1ce15a4487cca` | Daily | Scan catalog, map data fitness, delegate tasks |
# MAGIC | @data-engineer | `218f6f9ca64749ce901854ea973551f8` | Daily | Execute ingestion, pipeline, data generation tasks |
# MAGIC | @data-analyst | `14c120a93b9d408b9c840a467714745b` | Daily | Profiling, gap analysis, data quality, metric views |
# MAGIC | @ml-engineer | `83814f8ee58042dbbbc5a137dac76824` | Daily | Model training, eval, monitoring, feature requests |
# MAGIC | @pm | `f11e97a7c161400e80a06f3ac8fb0b4f` | Daily | Task assignment, prioritization, status rollups |
# MAGIC | @qa | `056bf86924174fe5be1636b4f4f214bc` | Daily | Code/spec/data review, proactive sweeps |
# MAGIC | @devops | `cb363630d10b444f9a75bc1c8e10f661` | Daily | Git hygiene, DAB config, deployment validation |
# MAGIC | @app-developer | `d175baccbb80467595244fe07bb6fae4` | Daily | Build/maintain React/TypeScript demo apps |
# MAGIC | @designer | `f169a1fb28dc4cff948590d6bb2cc3d5` | Every 3 days | UX/brand review of app scaffolds |
# MAGIC
# MAGIC ### Monitoring
# MAGIC - All tasks write progress to Lakebase `agent_tasks` table
# MAGIC - @pm produces daily status rollups in `status_updates`
# MAGIC - Cross-team dashboard query:
# MAGIC ```sql
# MAGIC SELECT agent_role, 
# MAGIC        COUNT(*) FILTER (WHERE status='completed') as done,
# MAGIC        COUNT(*) FILTER (WHERE status IN ('open','in_progress')) as open_tasks,
# MAGIC        COUNT(*) as total
# MAGIC FROM agent_tasks GROUP BY agent_role ORDER BY agent_role
# MAGIC ```
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **Task not firing:** Check scheduled task in UI → verify it's enabled, check compute permissions
# MAGIC 2. **Agent stuck:** Read `status_notes` from `agent_tasks` for the stuck task — usually a data dependency
# MAGIC 3. **Reset agent:** Mark all `in_progress` tasks for that agent back to `open`:
# MAGIC    `UPDATE agent_tasks SET status='open', updated_at=NOW() WHERE agent_role='@<role>' AND status='in_progress'`
# MAGIC 4. **Task board read-only:** Regenerate Lakebase token (tokens are short-lived)

# COMMAND ----------

# DBTITLE 1,9. All-Systems Health Check
# ============================================================
# ALL-SYSTEMS HEALTH CHECK — Run this cell for full status
# ============================================================
import warnings
warnings.filterwarnings('ignore')

from datetime import datetime, timezone
print(f"\n{'='*60}")
print(f"COPPER RETIREMENT — ALL-SYSTEMS HEALTH CHECK")
print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}")

results = []

# --- 1. DLP Pipeline ---
print("\n[1/6] DLP Pipeline...")
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    pipeline = w.pipelines.get("b52532a2-6398-44ed-b239-9e95cafb745c")
    updates = list(w.pipelines.list_updates("b52532a2-6398-44ed-b239-9e95cafb745c").updates or [])
    latest_state = updates[0].state if updates else "NO UPDATES"
    status = "✅ PASS" if str(pipeline.state) == "PipelineState.IDLE" and str(latest_state) == "UpdateInfoState.COMPLETED" else "⚠️ CHECK"
    results.append(("DLP Pipeline", status, f"State={pipeline.state}, Last update={latest_state}"))
    print(f"  {status} | State: {pipeline.state} | Last: {latest_state}")
except Exception as e:
    results.append(("DLP Pipeline", "❌ FAIL", str(e)))
    print(f"  ❌ FAIL | {e}")

# --- 2. Materialized Views ---
print("\n[2/6] Materialized Views...")
mvs = ["bronze_copper_devices", "bronze_copper_services", "bronze_dig_safe_incidents",
       "silver_copper_plant_enriched", "silver_device_service_impact",
       "gold_wire_center_scorecard", "gold_contractor_scorecard", "gold_retirement_executive_summary"]
mv_ok = 0
for mv in mvs:
    try:
        cnt = spark.sql(f"SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.{mv}").collect()[0][0]
        if cnt > 0:
            mv_ok += 1
    except:
        pass
status = "✅ PASS" if mv_ok == len(mvs) else "⚠️ CHECK" if mv_ok > 0 else "❌ FAIL"
results.append(("Materialized Views", status, f"{mv_ok}/{len(mvs)} non-empty"))
print(f"  {status} | {mv_ok}/{len(mvs)} MVs with data")

# --- 3. Serving Endpoint ---
print("\n[3/6] Serving Endpoint...")
try:
    ep = w.serving_endpoints.get("copper-retirement-risk")
    ep_ready = str(ep.state.ready)
    status = "✅ PASS" if "READY" in ep_ready else "❌ FAIL"
    model_info = ""
    if ep.config and ep.config.served_entities:
        se = ep.config.served_entities[0]
        model_info = f"{se.entity_name} v{se.entity_version}"
    results.append(("Serving Endpoint", status, f"{ep_ready} | {model_info}"))
    print(f"  {status} | {ep_ready} | {model_info}")
except Exception as e:
    results.append(("Serving Endpoint", "❌ FAIL", str(e)))
    print(f"  ❌ FAIL | {e}")

# --- 4. Vector Search ---
print("\n[4/6] Vector Search...")
try:
    vs_ep = w.vector_search_endpoints.get_endpoint("demo_telco_vs_endpoint")
    vs_state = vs_ep.endpoint_status.state if vs_ep.endpoint_status else "UNKNOWN"
    status = "✅ PASS" if "ONLINE" in str(vs_state) else "❌ FAIL"
    results.append(("Vector Search", status, f"Endpoint: {vs_state}"))
    print(f"  {status} | Endpoint: {vs_state}")
except Exception as e:
    results.append(("Vector Search", "❌ FAIL", str(e)))
    print(f"  ❌ FAIL | {e}")

# --- 5. Lakebase ---
print("\n[5/6] Lakebase...")
try:
    import psycopg
    ep_name = "projects/copper-task-board/branches/production/endpoints/primary"
    lb_host = "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
    lb_user = w.current_user.me().user_name
    lb_token = w.postgres.generate_database_credential(endpoint=ep_name).token
    lb_conn = psycopg.connect(host=lb_host, dbname="databricks_postgres", user=lb_user, password=lb_token, sslmode="require")
    lb_conn.autocommit = True
    lb_cur = lb_conn.cursor()
    lb_cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='copper_app'")
    tbl_count = lb_cur.fetchone()[0]
    lb_cur.execute("SELECT COUNT(*) FROM agent_tasks")
    task_count = lb_cur.fetchone()[0]
    status = "✅ PASS" if tbl_count >= 15 else "⚠️ CHECK"
    results.append(("Lakebase", status, f"{tbl_count} copper_app tables, {task_count} agent tasks"))
    print(f"  {status} | {tbl_count} copper_app tables | {task_count} agent tasks")
    lb_cur.close()
    lb_conn.close()
except Exception as e:
    results.append(("Lakebase", "❌ FAIL", str(e)))
    print(f"  ❌ FAIL | {e}")

# --- 6. Apps ---
print("\n[6/6] Databricks Apps...")
app_names = ['copper-map', 'retirement-plan', 'dig-triage', 'regulatory-assistant', 'commodity-dashboard']
apps_ok = 0
for name in app_names:
    try:
        app = w.apps.get(name)
        if app.active_deployment and app.active_deployment.status and "SUCCEEDED" in str(app.active_deployment.status.state):
            apps_ok += 1
    except:
        pass
status = "✅ PASS" if apps_ok == len(app_names) else "⚠️ CHECK" if apps_ok > 0 else "❌ FAIL"
results.append(("Databricks Apps", status, f"{apps_ok}/{len(app_names)} deployed OK"))
print(f"  {status} | {apps_ok}/{len(app_names)} apps deployed")

# --- Summary ---
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
all_pass = all("✅" in r[1] for r in results)
for component, status, detail in results:
    print(f"  {status}  {component}: {detail}")
print(f"\nOverall: {'\u2705 ALL SYSTEMS GO' if all_pass else '\u26a0\ufe0f ACTION REQUIRED — review items above'}")
print(f"{'='*60}")

# COMMAND ----------

# DBTITLE 1,10. Escalation Contacts
# MAGIC %md
# MAGIC ## 10. Escalation Contacts
# MAGIC
# MAGIC | Issue | First Contact | Escalation | Notes |
# MAGIC | --- | --- | --- | --- |
# MAGIC | DLP pipeline failure | @data-engineer | @pm → CEO | Check event log first |
# MAGIC | Model drift / serving | @ml-engineer | @pm | Run monitoring notebook |
# MAGIC | Stale app data | @data-engineer | @pm | Re-run Lakebase sync |
# MAGIC | App deploy failure | @app-developer | @devops | Check app logs |
# MAGIC | UX / brand issues | @designer | @pm | Brand guidelines in CEO directive |
# MAGIC | Data quality | @data-analyst | @data-planner → @pm | Check DLP pipeline first |
# MAGIC | DAB / deployment | @devops | @pm | Verify `databricks.yml` config |
# MAGIC | Task board down | @data-engineer | CEO | Lakebase project issue |
# MAGIC | Agent not running | @pm | CEO | Check scheduled task config |
# MAGIC | Vector search offline | @ml-engineer | CEO | VS endpoints need admin |
# MAGIC
# MAGIC ### CEO Contact
# MAGIC - **Role:** Stephen Hage (workspace admin)
# MAGIC - **When to escalate:** Infrastructure blockers that no agent persona can resolve (endpoint creation, tag governance, compute permissions)
# MAGIC - **How:** File task to `@pm` with `priority: critical`, who escalates to CEO
# MAGIC
# MAGIC ### Cross-Team Dashboard
# MAGIC ```sql
# MAGIC -- Run in Lakebase to see all agent progress
# MAGIC SELECT agent_role, 
# MAGIC        COUNT(*) FILTER (WHERE status='completed') as done,
# MAGIC        COUNT(*) FILTER (WHERE status IN ('open','in_progress')) as open,
# MAGIC        COUNT(*) FILTER (WHERE status='blocked') as blocked,
# MAGIC        COUNT(*) as total,
# MAGIC        ROUND(100.0 * COUNT(*) FILTER (WHERE status='completed') / NULLIF(COUNT(*), 0), 1) as pct_complete
# MAGIC FROM agent_tasks 
# MAGIC GROUP BY agent_role 
# MAGIC ORDER BY agent_role
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Document Version:** 1.0 | **Created:** 2026-09-21 by @data-engineer (DE-RUNBOOK-0920)
# MAGIC **Review:** @qa should review for completeness. @pm should validate schedules.