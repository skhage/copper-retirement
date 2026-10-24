# Databricks notebook source
# DBTITLE 1,Copper Retirement — Operational Runbook
# MAGIC %md
# MAGIC # Copper Retirement — Operational Runbook
# MAGIC
# MAGIC **Project:** Lakelink Fiber Copper Retirement  
# MAGIC **Catalog/Schema:** `<catalog>.<schema>` = bundle variables `catalog_name` / `schema_name` (set as widgets in Section 8)  
# MAGIC **Owner:** @data-engineer  
# MAGIC **Last Updated:** 2026-09-21  
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Infrastructure Inventory
# MAGIC
# MAGIC | Component | ID / Name | Status | Owner |
# MAGIC |---|---|---|---|
# MAGIC | **DLP Pipeline (active)** | `copper-retirement-pipeline` (`b52532a2-6398-44ed-b239-9e95cafb745c`) | IDLE / Healthy | @data-engineer |
# MAGIC | **Serving Endpoint** | `copper-retirement-risk` (V5 model) | READY | @ml-engineer |
# MAGIC | **Vector Search Endpoint** | `cmeg-demos-vs` (DEC-VS-ENDPOINT-ACTUAL) | ONLINE | @data-engineer |
# MAGIC | **Vector Search Index** | `<catalog>.<schema>.regulatory_doc_chunks_vs_index` (DELTA_SYNC, databricks-bge-large-en, PK chunk_id) | ONLINE | @data-engineer |
# MAGIC | **Lakebase Task Board** | `copper-task-board` (production branch) | Active | @pm |
# MAGIC | **Lakebase App Schema** | `copper_app` (11 tables) | Active | @data-engineer |
# MAGIC | **Demo Apps** | 5 apps (map, plan, triage, regulatory, commodity) | Scaffolded | @app-developer |
# MAGIC | **SQL Alerts** | 3 freshness alerts (MV, inference, MV-detail) | Active (12h cron) | @data-engineer |
# MAGIC | **Healthcheck** | `ops/pre_demo_healthcheck.py` (8 checks) | On-demand | @devops / @data-engineer |

# COMMAND ----------

# DBTITLE 1,Section 1: Active DLP Pipeline
# MAGIC %md
# MAGIC ## 1. Active DLP Pipeline (`copper-retirement-pipeline`)
# MAGIC
# MAGIC **Pipeline ID:** `b52532a2-6398-44ed-b239-9e95cafb745c`  
# MAGIC **Catalog/Schema:** `<catalog>.<schema>` (pipeline catalog/target from bundle variables; pipeline SQL uses unqualified names)  
# MAGIC **Mode:** Serverless, Development  
# MAGIC **DAG:** 8 materialized views (3 bronze → 2 silver → 3 gold)
# MAGIC
# MAGIC ### Source Files
# MAGIC | Layer | File | Description |
# MAGIC |---|---|---|
# MAGIC | Bronze | `pipeline/bronze_copper_devices.sql` | Physical devices with copper filter |
# MAGIC | Bronze | `pipeline/bronze_copper_services.sql` | Customer-facing services on copper |
# MAGIC | Bronze | `pipeline/bronze_dig_safe_incidents.sql` | Dig-safe incident records |
# MAGIC | Silver | `pipeline/silver_copper_plant_enriched.sql` | Enriched plant with geo + risk |
# MAGIC | Silver | `pipeline/silver_device_service_impact.sql` | Device ↔ service impact mapping |
# MAGIC | Gold | `pipeline/gold_wire_center_scorecard.sql` | Wire center retirement scorecard |
# MAGIC | Gold | `pipeline/gold_contractor_scorecard.sql` | Contractor performance scorecard |
# MAGIC | Gold | `pipeline/gold_retirement_executive_summary.sql` | Executive summary metrics |
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC 1. **Trigger refresh:** Databricks UI → Pipelines → `copper-retirement-pipeline` → Start
# MAGIC 2. **SDK trigger:** `w.pipelines.start_update('b52532a2-6398-44ed-b239-9e95cafb745c', full_refresh=False)`
# MAGIC 3. **Full refresh (schema change):** `w.pipelines.start_update('b52532a2-6398-44ed-b239-9e95cafb745c', full_refresh=True)`
# MAGIC 4. **Check status:** `w.pipelines.get('b52532a2-6398-44ed-b239-9e95cafb745c').state`
# MAGIC 5. **Last successful update:** Check `latest_updates` for `state='COMPLETED'`

# COMMAND ----------

# DBTITLE 1,Section 2: Metric Views
# MAGIC %md
# MAGIC ## 2. Metric Views
# MAGIC
# MAGIC **8 metric views** across two schemas:
# MAGIC
# MAGIC | Schema | Metric View | Description |
# MAGIC |---|---|---|
# MAGIC | `_metrics` | 4 views | Cross-domain aggregated KPIs |
# MAGIC | `copper_retirement` | 4 views | Copper-specific retirement metrics |
# MAGIC
# MAGIC ### Refresh Procedure
# MAGIC Metric views are backed by materialized views in the DLP pipeline. To refresh:
# MAGIC 1. Trigger the DLP pipeline (Section 1)
# MAGIC 2. Verify materialization: `DESCRIBE EXTENDED <catalog>.<schema>.<view_name>`
# MAGIC 3. Check freshness: Compare `last_altered` timestamp

# COMMAND ----------

# DBTITLE 1,Section 3: Lakebase Task Board
# MAGIC %md
# MAGIC ## 3. Lakebase Task Board (`copper-task-board`)
# MAGIC
# MAGIC **Project:** `copper-task-board`  
# MAGIC **Branch:** `production`  
# MAGIC **Endpoint:** `projects/copper-task-board/branches/production/endpoints/primary`  
# MAGIC **Host:** `ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com`  
# MAGIC **Tables:** `agent_tasks`, `status_updates`, `ceo_directives`, `decisions`
# MAGIC
# MAGIC ### Connection Pattern
# MAGIC ```python
# MAGIC import psycopg
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC w = WorkspaceClient()
# MAGIC endpoint_name = "projects/copper-task-board/branches/production/endpoints/primary"
# MAGIC host = "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
# MAGIC user = w.current_user.me().user_name
# MAGIC token = w.postgres.generate_database_credential(endpoint=endpoint_name).token
# MAGIC conn = psycopg.connect(host=host, dbname="databricks_postgres", user=user, password=token, sslmode="require")
# MAGIC conn.autocommit = True
# MAGIC cur = conn.cursor()
# MAGIC ```
# MAGIC
# MAGIC ### Manual Recovery
# MAGIC - **Token expired:** Re-generate with `w.postgres.generate_database_credential(endpoint=endpoint_name).token`
# MAGIC - **Connection refused:** Check endpoint status in Lakebase UI
# MAGIC - **Tables missing:** Task board schema is self-healing on next @pm run

# COMMAND ----------

# DBTITLE 1,Section 4: Serving Endpoint
# MAGIC %md
# MAGIC ## 4. Serving Endpoint (`copper-retirement-risk`)
# MAGIC
# MAGIC **Model:** V5 risk model (GBT/XGBoost)  
# MAGIC **Inference table logging:** Enabled  
# MAGIC **Status:** READY
# MAGIC
# MAGIC ### Health Check
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC w = WorkspaceClient()
# MAGIC ep = w.serving_endpoints.get('copper-retirement-risk')
# MAGIC print(f"State: {ep.state.ready}")
# MAGIC print(f"Config update: {ep.state.config_update}")
# MAGIC ```
# MAGIC
# MAGIC ### Rollback Procedure
# MAGIC 1. Check model versions: `w.model_registry.get_model_version_stages('copper-retirement-risk')`
# MAGIC 2. Roll back to previous version in Serving Endpoint UI → Edit configuration
# MAGIC 3. Verify inference table still logging: Check `<catalog>.<schema>.risk_model_inference_payload`

# COMMAND ----------

# DBTITLE 1,Section 5: Vector Search
# MAGIC %md
# MAGIC ## 5. Vector Search
# MAGIC
# MAGIC **Endpoint:** `cmeg-demos-vs` (the existing endpoint; see decision DEC-VS-ENDPOINT-ACTUAL)  
# MAGIC **Index:** `<catalog>.<schema>.regulatory_doc_chunks_vs_index` (source `regulatory_doc_chunks`; real chunks `is_synthetic=false`, legacy synthetic `is_synthetic=true`)  
# MAGIC **Embedding model:** `databricks-bge-large-en`
# MAGIC
# MAGIC ### Re-index Procedure
# MAGIC 1. Navigate to Vector Search UI → `cmeg-demos-vs`
# MAGIC 2. Select `regulatory_doc_chunks_vs_index`
# MAGIC 3. Click "Sync" to re-index from source table
# MAGIC 4. Monitor sync status until ONLINE

# COMMAND ----------

# DBTITLE 1,Section 6: Demo Apps
# MAGIC %md
# MAGIC ## 6. Databricks Apps (5 Demo Apps)
# MAGIC
# MAGIC | App | Purpose | Beat |
# MAGIC |---|---|---|
# MAGIC | Map App | Copper plant geospatial view | Beat 1 |
# MAGIC | Planning Dashboard | Wave schedule + contractor plan | Beat 2 |
# MAGIC | Triage App | Dig-safe incident triage | Beat 3 |
# MAGIC | Regulatory Assistant | VS-powered regulatory Q&A | Beat 4 |
# MAGIC | Commodity Dashboard | Copper price + EBITDA | Beat 5 |
# MAGIC
# MAGIC ### Restart Procedure
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC w = WorkspaceClient()
# MAGIC # List apps
# MAGIC apps = list(w.apps.list())
# MAGIC for app in apps:
# MAGIC     if 'copper' in app.name.lower() or 'lakelink' in app.name.lower():
# MAGIC         print(f"{app.name}: {app.status}")
# MAGIC # Restart a specific app
# MAGIC # w.apps.start('<app-name>')
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Section 7: Agent Automations
# MAGIC %md
# MAGIC ## 7. Agent Automations
# MAGIC
# MAGIC | Role | Task ID | Cadence |
# MAGIC |---|---|---|
# MAGIC | @data-planner | `b27c43599c28466498a1ce15a4487cca` | Daily |
# MAGIC | @data-engineer | `218f6f9ca64749ce901854ea973551f8` | Daily |
# MAGIC | @data-analyst | `14c120a93b9d408b9c840a467714745b` | Daily |
# MAGIC | @ml-engineer | `83814f8ee58042dbbbc5a137dac76824` | Daily |
# MAGIC | @pm | `f11e97a7c161400e80a06f3ac8fb0b4f` | Daily |
# MAGIC | @qa | `056bf86924174fe5be1636b4f4f214bc` | Daily |
# MAGIC | @devops | `cb363630d10b444f9a75bc1c8e10f661` | Daily |
# MAGIC | @app-developer | `d175baccbb80467595244fe07bb6fae4` | Daily |
# MAGIC | @designer | `f169a1fb28dc4cff948590d6bb2cc3d5` | Every 3 days |
# MAGIC
# MAGIC ### Monitoring Query (Lakebase)
# MAGIC ```sql
# MAGIC SELECT agent_role, 
# MAGIC   COUNT(*) FILTER (WHERE status='completed') as done,
# MAGIC   COUNT(*) FILTER (WHERE status IN ('open','in_progress')) as open_tasks,
# MAGIC   COUNT(*) as total
# MAGIC FROM agent_tasks GROUP BY agent_role ORDER BY agent_role
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Section 8: All-Systems Health Check
# All-Systems Health Check — run this cell to verify all subsystems
from databricks.sdk import WorkspaceClient
import psycopg

# Parameterized (ACC-DE-PARAMETERIZE): defaults match bundle variables
dbutils.widgets.text("catalog", "cdm_tmforum")
dbutils.widgets.text("schema", "copper_retirement")
dbutils.widgets.text("pipeline_name", "copper-retirement-pipeline")
CATALOG, SCHEMA = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")

w = WorkspaceClient()
results = {}

# 1. DLP Pipeline
try:
    _pname = dbutils.widgets.get("pipeline_name")
    _pid = next(x.pipeline_id for x in w.pipelines.list_pipelines(filter=f"name LIKE '{_pname}'") if x.name == _pname)
    p = w.pipelines.get(_pid)
    latest = p.latest_updates[0] if p.latest_updates else None
    results['DLP Pipeline'] = f"{p.state.value} | Last: {latest.state.value if latest else 'none'} @ {latest.creation_time if latest else 'n/a'}"
except Exception as e:
    results['DLP Pipeline'] = f"ERROR: {e}"

# 2. Serving Endpoint
try:
    ep = w.serving_endpoints.get('copper-retirement-risk')
    results['Serving Endpoint'] = f"{ep.state.ready}"
except Exception as e:
    results['Serving Endpoint'] = f"ERROR: {e}"

# 3. Lakebase
try:
    endpoint_name = "projects/copper-task-board/branches/production/endpoints/primary"
    host = "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
    user = w.current_user.me().user_name
    token = w.postgres.generate_database_credential(endpoint=endpoint_name).token
    conn = psycopg.connect(host=host, dbname="databricks_postgres", user=user, password=token, sslmode="require")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM agent_tasks")
    count = cur.fetchone()[0]
    results['Lakebase Task Board'] = f"CONNECTED | {count} tasks"
    conn.close()
except Exception as e:
    results['Lakebase Task Board'] = f"ERROR: {e}"

# 4. Key tables
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    for t in ['gold_wire_center_scorecard', 'gold_retirement_executive_summary', 'gold_device_risk_predictions']:
        try:
            cnt = spark.table(f'{CATALOG}.{SCHEMA}.{t}').count()
            results[f'Table: {t}'] = f"{cnt:,} rows"
        except Exception as e:
            results[f'Table: {t}'] = f"ERROR: {e}"
except Exception as e:
    results['Spark'] = f"ERROR: {e}"

print("=" * 60)
print("COPPER RETIREMENT — SYSTEM HEALTH CHECK")
print("=" * 60)
for k, v in results.items():
    status = "✅" if "ERROR" not in v else "❌"
    print(f"{status} {k}: {v}")
print("=" * 60)

# COMMAND ----------

# DBTITLE 1,Section 9: Escalation Contacts
# MAGIC %md
# MAGIC ## 9. Escalation Contacts
# MAGIC
# MAGIC | System | First Contact | Escalation |
# MAGIC |---|---|---|
# MAGIC | DLP Pipeline failure | @data-engineer | @pm → CEO |
# MAGIC | Metric view stale | @data-engineer | @data-planner |
# MAGIC | Serving endpoint down | @ml-engineer | @pm → CEO |
# MAGIC | Vector Search offline | @data-engineer | @pm → CEO |
# MAGIC | Lakebase unreachable | @data-engineer | @pm → CEO |
# MAGIC | App crash | @app-developer | @pm |
# MAGIC | Agent automation stuck | @pm | CEO |
# MAGIC | Data quality issue | @data-analyst | @data-planner → @data-engineer |
# MAGIC | Model drift detected | @ml-engineer | @data-engineer (features) |
# MAGIC | Security/access issue | @devops | CEO |

# COMMAND ----------

# DBTITLE 1,Section 11: Production Data Freshness Monitoring
# MAGIC %md
# MAGIC ## 11. Production Data Freshness Monitoring
# MAGIC
# MAGIC **Created:** 2026-09-21 by @data-engineer  
# MAGIC **Task:** DE-OPS-FRESHNESS-ALERTS-0921
# MAGIC
# MAGIC ### Overview
# MAGIC Three layers of freshness monitoring protect the demo from stale data:
# MAGIC
# MAGIC | Layer | What it checks | Cadence | Threshold |
# MAGIC |---|---|---|---|
# MAGIC | **SQL Alerts** | DLP MV age, inference table age | Every 12h (08:00 / 20:00 UTC) | MV > 24h, Inference > 48h |
# MAGIC | **Healthcheck** | MVs, inference, Lakebase sync, apps, endpoints | On-demand (`%run`) | Same thresholds |
# MAGIC | **DLP Pipeline** | Upstream source refresh | Scheduled by pipeline | Auto-refresh |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### SQL Alerts (Databricks SQL)
# MAGIC
# MAGIC | Alert | ID | Condition | Schedule |
# MAGIC |---|---|---|---|
# MAGIC | **DLP MV Freshness (Stale >24h)** | `2984097112457267` | `stale_mv_count > 0` (any of 8 MVs older than 24h) | `0 0 8,20 ? * * *` |
# MAGIC | **DLP MV Detail Freshness** | `2984097112457333` | `oldest_mv_hours > 24` (oldest MV refresh age) | `0 0 8,20 ? * * *` |
# MAGIC | **Inference Table Staleness** | `2984097112457300` | `hours_since_last_inference > 48` | `0 0 8,20 ? * * *` |
# MAGIC
# MAGIC **Alert SQL queries:**
# MAGIC
# MAGIC 1. **Stale MV count:**
# MAGIC ```sql
# MAGIC SELECT COUNT(*) as stale_mv_count
# MAGIC FROM <catalog>.information_schema.tables
# MAGIC WHERE table_schema = '<schema>'
# MAGIC   AND table_type = 'MATERIALIZED_VIEW'
# MAGIC   AND TIMESTAMPDIFF(HOUR, last_altered, current_timestamp()) > 24
# MAGIC ```
# MAGIC
# MAGIC 2. **Oldest MV age:**
# MAGIC ```sql
# MAGIC SELECT MAX(TIMESTAMPDIFF(HOUR, last_altered, current_timestamp())) as oldest_mv_hours
# MAGIC FROM <catalog>.information_schema.tables
# MAGIC WHERE table_schema = '<schema>'
# MAGIC   AND table_type = 'MATERIALIZED_VIEW'
# MAGIC ```
# MAGIC
# MAGIC 3. **Inference staleness:**
# MAGIC ```sql
# MAGIC SELECT COALESCE(
# MAGIC     TIMESTAMPDIFF(HOUR, MAX(request_time), current_timestamp()), 9999
# MAGIC ) as hours_since_last_inference
# MAGIC FROM <catalog>.<schema>.risk_model_inference_payload
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Pre-Demo Healthcheck Integration
# MAGIC
# MAGIC Three new checks added to `ops/pre_demo_healthcheck.py` (sections 6/8, 7/8, 8/8):
# MAGIC
# MAGIC | Check | Function | What it verifies |
# MAGIC |---|---|---|
# MAGIC | **6/8 MV Freshness** | `check_mv_freshness()` | All 8 DLP MVs refreshed within 24h |
# MAGIC | **7/8 Inference Table** | `check_inference_table()` | `risk_model_inference_payload` has recent entries (< 48h) |
# MAGIC | **8/8 Lakebase Sync** | `check_lakebase_sync()` | 8 `copper_app.*` tables match UC source row counts |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 8 DLP Materialized Views Monitored
# MAGIC
# MAGIC | MV Name | Layer | Max Age |
# MAGIC |---|---|---|
# MAGIC | `bronze_copper_devices` | Bronze | 24h |
# MAGIC | `bronze_copper_services` | Bronze | 24h |
# MAGIC | `bronze_dig_safe_incidents` | Bronze | 24h |
# MAGIC | `silver_copper_plant_enriched` | Silver | 24h |
# MAGIC | `silver_device_service_impact` | Silver | 24h |
# MAGIC | `gold_contractor_scorecard` | Gold | 24h |
# MAGIC | `gold_retirement_executive_summary` | Gold | 24h |
# MAGIC | `gold_wire_center_scorecard` | Gold | 24h |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Lakebase Sync Pairs (copper_app ↔ UC)
# MAGIC
# MAGIC | Lakebase Table | UC Source Table |
# MAGIC |---|---|
# MAGIC | `copper_app.wire_center_scorecard` | `copper_retirement.gold_wire_center_scorecard` |
# MAGIC | `copper_app.gold_wave_schedule` | `copper_retirement.gold_wave_schedule` |
# MAGIC | `copper_app.gold_contractor_assignment_plan` | `copper_retirement.gold_contractor_assignment_plan` |
# MAGIC | `copper_app.gold_copper_recovery_schedule` | `copper_retirement.gold_copper_recovery_schedule` |
# MAGIC | `copper_app.gold_reroute_options` | `copper_retirement.gold_reroute_options` |
# MAGIC | `copper_app.device_risk_map` | `copper_retirement.copper_risk_predictions` |
# MAGIC | `copper_app.executive_summary` | `copper_retirement.gold_retirement_executive_summary` |
# MAGIC | `copper_app.contractor_scorecard` | `copper_retirement.gold_contractor_scorecard` |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Remediation Playbook
# MAGIC
# MAGIC | Symptom | Cause | Fix |
# MAGIC |---|---|---|
# MAGIC | MV stale > 24h | DLP pipeline didn't run | Trigger `copper-retirement-pipeline` manually |
# MAGIC | Inference table > 48h | No recent model calls | Score a batch via serving endpoint |
# MAGIC | Lakebase sync drift | ETL sync job missed | Re-run copper_app sync notebook |
# MAGIC | Lakebase table empty | Initial sync never ran | Backfill from UC source |