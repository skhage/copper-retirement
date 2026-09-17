# Databricks notebook source
# DBTITLE 1,Header
# MAGIC %md
# MAGIC # Copper Risk Model — Monitoring & Drift Activation
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC **Purpose:** Verify and activate Lakehouse Monitoring for the V5 copper-retirement-risk model.  
# MAGIC **Run this notebook** after CEO enables auto-capture on the serving endpoint.  
# MAGIC **Monitor target:** `cdm_tmforum.copper_retirement.risk_inference_unpacked`  
# MAGIC **Baseline reference:** `copper-retirement/resources/monitoring_baseline.md`  
# MAGIC **MLflow experiment:** `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier`

# COMMAND ----------

# DBTITLE 1,Step 1: Verify auto-capture is enabled
# Step 1: Verify auto-capture is enabled on the serving endpoint
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ep = w.serving_endpoints.get("copper-retirement-risk")

print(f"Endpoint: {ep.name}")
print(f"State:    {ep.state.ready}")

ac = ep.config.auto_capture_config if ep.config else None
if ac and ac.enabled:
    print(f"\n✅ AUTO-CAPTURE ENABLED")
    print(f"   Catalog:  {ac.catalog_name}")
    print(f"   Schema:   {ac.schema_name}")
    print(f"   Prefix:   {ac.table_name_prefix}")
else:
    print(f"\n❌ AUTO-CAPTURE NOT ENABLED — Stop here, CEO must enable via Serving UI.")
    print(f"   Go to: Serving > copper-retirement-risk > Inference table")
    print(f"   Set: catalog=cdm_tmforum, schema=copper_retirement, prefix=risk_model_inference")

# Check tags
if ep.tags:
    tag_dict = {t.key: t.value for t in ep.tags}
    print(f"\nTags: {tag_dict}")
    if 'project' in tag_dict and 'telco_project' not in tag_dict:
        print("⚠️  Tag uses old 'project' key — should be 'telco_project' per CEO TAG RENAME directive")

# COMMAND ----------

# DBTITLE 1,Step 2: Check inference table growth
# Step 2: Check inference table is receiving live predictions
df_inf = spark.sql("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT DATE(request_time)) as distinct_days,
        MIN(request_time) as earliest,
        MAX(request_time) as latest,
        DATEDIFF(MAX(request_time), MIN(request_time)) as span_days
    FROM cdm_tmforum.copper_retirement.risk_model_inference_payload
""")
df_inf.show(truncate=False)

row = df_inf.collect()[0]
if row['total_rows'] > 20:
    print(f"✅ Inference table has {row['total_rows']} rows across {row['distinct_days']} days")
else:
    print(f"⚠️  Only {row['total_rows']} rows — may still be test data. Wait for production batch scoring.")
    print(f"   Run batch_score_copper_risk notebook to generate predictions.")

# COMMAND ----------

# DBTITLE 1,Step 3: Check unpacked view row count
# Step 3: Verify unpacked view is working
df_unpacked = spark.sql("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT prediction) as distinct_predictions,
        COUNT(DISTINCT model_id) as model_versions
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
""")
df_unpacked.show(truncate=False)

row = df_unpacked.collect()[0]
print(f"Unpacked view: {row['total_rows']} scored devices, {row['distinct_predictions']} risk tiers, {row['model_versions']} model version(s)")

# COMMAND ----------

# DBTITLE 1,Step 4: Trigger monitor refresh
# Step 4: Trigger a Lakehouse Monitor refresh to compute fresh drift metrics
import requests, json

host = w.config.host.rstrip('/')
token = w.config.token

table_name = "cdm_tmforum.copper_retirement.risk_inference_unpacked"

# Trigger refresh
resp = requests.post(
    f"{host}/api/2.1/unity-catalog/tables/{table_name}/monitor/run",
    headers={"Authorization": f"Bearer {token}"},
    json={}
)
print(f"Monitor refresh trigger: {resp.status_code}")
if resp.status_code == 200:
    run_info = resp.json()
    print(f"✅ Refresh triggered: {json.dumps(run_info, indent=2)[:500]}")
else:
    print(f"Response: {resp.text[:500]}")
    print("\nIf 404: monitor may need to be re-created.")
    print("If 400: monitor may already be refreshing.")

# COMMAND ----------

# DBTITLE 1,Step 5: Check profile metrics (feature distributions)
# Step 5: Inspect profile metrics — feature distributions from the latest monitor window
df_profile = spark.sql("""
    SELECT 
        column_name,
        count,
        num_nulls,
        ROUND(avg, 4) as avg_value,
        ROUND(min, 4) as min_value,
        ROUND(max, 4) as max_value,
        ROUND(stddev, 4) as stddev_value,
        data_type
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked_profile_metrics
    WHERE column_name NOT IN (':table')
    ORDER BY column_name
""")
print(f"Profile metrics: {df_profile.count()} rows")
df_profile.show(50, truncate=False)

# COMMAND ----------

# DBTITLE 1,Step 6: Check drift metrics (PSI scores)
# Step 6: Inspect drift metrics — PSI scores comparing current vs baseline
df_drift = spark.sql("""
    SELECT *
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked_drift_metrics
    ORDER BY column_name
""")
print(f"Drift metrics: {df_drift.count()} rows")

if df_drift.count() > 0:
    df_drift.show(50, truncate=False)
    
    # Check for PSI > 0.2 threshold breaches
    try:
        alerts = spark.sql("""
            SELECT column_name, drift_type, statistic, value
            FROM cdm_tmforum.copper_retirement.risk_inference_unpacked_drift_metrics
            WHERE statistic = 'psi' AND value > 0.2
        """)
        if alerts.count() > 0:
            print("\n🚨 DRIFT ALERTS — PSI > 0.2 threshold breached:")
            alerts.show(truncate=False)
        else:
            print("\n✅ No drift alerts — all PSI values within threshold (<0.2)")
    except Exception as e:
        print(f"Drift alert check note: {e}")
else:
    print("\n⚠️  No drift metrics yet — need 2+ monitoring windows (wait for next day's refresh).")
    print("   Drift = comparison of current window vs baseline/previous window.")
    print("   Once auto-capture is live and batch scoring runs daily, drift will populate.")

# COMMAND ----------

# DBTITLE 1,Step 7: Monitoring health summary
# Step 7: End-to-end monitoring health summary
print("=" * 70)
print("COPPER RISK MODEL — MONITORING HEALTH SUMMARY")
print("=" * 70)

# Endpoint
ep = w.serving_endpoints.get("copper-retirement-risk")
ac = ep.config.auto_capture_config if ep.config else None
auto_capture_ok = bool(ac and ac.enabled)
print(f"\n1. Endpoint:       {'✅ READY' if str(ep.state.ready) == 'EndpointStateReady.READY' else '❌ NOT READY'}")
print(f"2. Auto-capture:   {'✅ ENABLED' if auto_capture_ok else '❌ NOT ENABLED (blocker)'}")

# Inference table
inf_count = spark.sql("SELECT COUNT(*) as c FROM cdm_tmforum.copper_retirement.risk_model_inference_payload").collect()[0]['c']
print(f"3. Inference rows:  {inf_count} {'✅' if inf_count > 20 else '⚠️  (low — need production traffic)'}")

# Unpacked view
unpacked_count = spark.sql("SELECT COUNT(*) as c FROM cdm_tmforum.copper_retirement.risk_inference_unpacked").collect()[0]['c']
print(f"4. Unpacked view:   {unpacked_count} rows {'✅' if unpacked_count > 0 else '❌'}")

# Profile metrics
profile_count = spark.sql("SELECT COUNT(*) as c FROM cdm_tmforum.copper_retirement.risk_inference_unpacked_profile_metrics").collect()[0]['c']
print(f"5. Profile metrics: {profile_count} rows {'✅' if profile_count > 0 else '⚠️  (pending refresh)'}")

# Drift metrics
drift_count = spark.sql("SELECT COUNT(*) as c FROM cdm_tmforum.copper_retirement.risk_inference_unpacked_drift_metrics").collect()[0]['c']
print(f"6. Drift metrics:   {drift_count} rows {'✅' if drift_count > 0 else '⚠️  (need 2+ windows)'}")

# Baseline doc
try:
    import os
    baseline_path = "/Workspace/Users/stephen.hage@databricks.com/copper-retirement/resources/monitoring_baseline.md"
    baseline_exists = os.path.exists(baseline_path)
    print(f"7. Baseline doc:    {'✅ EXISTS' if baseline_exists else '❌ MISSING'}")
except:
    print(f"7. Baseline doc:    ⚠️  (could not verify)")

print(f"\n{'=' * 70}")
if auto_capture_ok and inf_count > 20 and drift_count > 0:
    print("STATUS: ✅ FULLY OPERATIONAL — monitoring pipeline is live.")
elif auto_capture_ok and inf_count <= 20:
    print("STATUS: ⚠️  AUTO-CAPTURE ON, but low inference volume. Run batch scoring.")
else:
    print("STATUS: ⏳ SETUP COMPLETE — waiting for auto-capture enablement (CEO action).")
    print("\nACTION ITEMS:")
    print("  1. CEO: Enable inference table logging on copper-retirement-risk endpoint")
    print("  2. CEO: Update endpoint tag from 'project' to 'telco_project'")
    print("  3. Run batch_score_copper_risk to generate prediction volume")
    print("  4. Re-run this notebook to verify end-to-end pipeline")
print(f"{'=' * 70}")

# COMMAND ----------

# DBTITLE 1,Step 8: Latency SLA Monitoring
# Step 8: Latency SLA Monitoring
# SLA targets from model card: p50<200ms, p99<1000ms (single request)

df_latency = spark.sql("""
    WITH daily_latency AS (
        SELECT
            request_date,
            COUNT(*) as request_count,
            ROUND(AVG(execution_duration_ms), 1) as avg_ms,
            ROUND(PERCENTILE(execution_duration_ms, 0.50), 1) as p50_ms,
            ROUND(PERCENTILE(execution_duration_ms, 0.95), 1) as p95_ms,
            ROUND(PERCENTILE(execution_duration_ms, 0.99), 1) as p99_ms,
            ROUND(MIN(execution_duration_ms), 1) as min_ms,
            ROUND(MAX(execution_duration_ms), 1) as max_ms
        FROM cdm_tmforum.copper_retirement.risk_model_inference_payload
        WHERE status_code = 200
        GROUP BY request_date
        ORDER BY request_date
    )
    SELECT *,
        CASE WHEN p50_ms < 200 THEN '✅' ELSE '🚨 BREACH' END as p50_sla,
        CASE WHEN p99_ms < 1000 THEN '✅' ELSE '🚨 BREACH' END as p99_sla
    FROM daily_latency
""")

print("=== LATENCY SLA MONITORING ===")
print("SLA targets: p50 < 200ms, p99 < 1000ms (per model card V5)")
print()
df_latency.show(30, truncate=False)

# Overall summary
df_overall = spark.sql("""
    SELECT
        COUNT(*) as total_requests,
        COUNT(CASE WHEN status_code != 200 THEN 1 END) as error_count,
        ROUND(100.0 * COUNT(CASE WHEN status_code = 200 THEN 1 END) / COUNT(*), 2) as success_rate_pct,
        ROUND(AVG(execution_duration_ms), 1) as overall_avg_ms,
        ROUND(PERCENTILE(execution_duration_ms, 0.50), 1) as overall_p50_ms,
        ROUND(PERCENTILE(execution_duration_ms, 0.95), 1) as overall_p95_ms,
        ROUND(PERCENTILE(execution_duration_ms, 0.99), 1) as overall_p99_ms
    FROM cdm_tmforum.copper_retirement.risk_model_inference_payload
""")
print("\n=== OVERALL LATENCY ===")
df_overall.show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Step 9: Prediction Distribution vs Baseline
# Step 9: Prediction Distribution vs Baseline
# Baseline from monitoring_baseline.md (V5 batch scoring, 2,672 copper devices):
#   low=20.0%, medium=39.7%, high=30.3%, critical=10.0%

BASELINE = {0: ('low', 20.0), 1: ('medium', 39.7), 2: ('high', 30.3), 3: ('critical', 10.0)}

df_pred = spark.sql("""
    SELECT
        prediction as risk_tier_code,
        CASE prediction
            WHEN 0 THEN 'low'
            WHEN 1 THEN 'medium'
            WHEN 2 THEN 'high'
            WHEN 3 THEN 'critical'
            ELSE 'unknown'
        END as risk_tier,
        COUNT(*) as count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    GROUP BY prediction
    ORDER BY prediction
""")

print("=== PREDICTION DISTRIBUTION: LIVE vs BASELINE ===")
print(f"{'Tier':<12} {'Live %':>8} {'Baseline %':>12} {'Delta':>8} {'Status':>8}")
print("-" * 52)

rows = df_pred.collect()
for row in rows:
    code = row['risk_tier_code']
    live_pct = row['pct']
    if code in BASELINE:
        tier_name, base_pct = BASELINE[code]
        delta = live_pct - base_pct
        # Flag if drift > 5 percentage points
        status = '🚨' if abs(delta) > 5.0 else '✅'
        print(f"{tier_name:<12} {live_pct:>7.1f}% {base_pct:>11.1f}% {delta:>+7.1f}% {status:>8}")
    else:
        print(f"{'unknown':<12} {live_pct:>7.1f}% {'N/A':>12} {'N/A':>8} {'⚠️':>8}")

print(f"\nTotal live predictions: {sum(r['count'] for r in rows)}")
print("\nAlert thresholds:")
print("  - Tier drift > ±5 pp  → prediction distribution shift")
print("  - Tier drift > ±10 pp → potential concept drift, retrain recommended")
print("  - PSI > 0.2 on any feature → feature drift (check Step 6)")

# COMMAND ----------

# DBTITLE 1,Step 10: Time-Series Monitoring Queries (reusable SQL)
# Step 10: Reusable monitoring queries — save as views or run ad-hoc
# These queries are designed for daily operational monitoring once auto-capture is live.

# Query A: Daily prediction volume + distribution trend
df_daily_dist = spark.sql("""
    SELECT
        request_date,
        COUNT(*) as total_predictions,
        COUNT(CASE WHEN prediction = 0 THEN 1 END) as low_count,
        COUNT(CASE WHEN prediction = 1 THEN 1 END) as medium_count,
        COUNT(CASE WHEN prediction = 2 THEN 1 END) as high_count,
        COUNT(CASE WHEN prediction = 3 THEN 1 END) as critical_count,
        ROUND(100.0 * COUNT(CASE WHEN prediction = 3 THEN 1 END) / COUNT(*), 1) as critical_pct
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    GROUP BY request_date
    ORDER BY request_date
""")
print("=== DAILY PREDICTION DISTRIBUTION TREND ===")
df_daily_dist.show(30, truncate=False)

# Query B: Feature value drift signals — top features by importance
print("\n=== TOP FEATURE VALUE RANGES (current vs expected) ===")
df_features = spark.sql("""
    SELECT
        'alarm_count' as feature,
        ROUND(AVG(alarm_count), 2) as live_mean,
        ROUND(STDDEV(alarm_count), 2) as live_std,
        ROUND(MIN(alarm_count), 2) as live_min,
        ROUND(MAX(alarm_count), 2) as live_max
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    UNION ALL
    SELECT 'test_fail_rate', ROUND(AVG(test_fail_rate), 2), ROUND(STDDEV(test_fail_rate), 2), ROUND(MIN(test_fail_rate), 2), ROUND(MAX(test_fail_rate), 2)
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    UNION ALL
    SELECT 'sla_breach_count', ROUND(AVG(sla_breach_count), 2), ROUND(STDDEV(sla_breach_count), 2), ROUND(MIN(sla_breach_count), 2), ROUND(MAX(sla_breach_count), 2)
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    UNION ALL
    SELECT 'problem_count', ROUND(AVG(problem_count), 2), ROUND(STDDEV(problem_count), 2), ROUND(MIN(problem_count), 2), ROUND(MAX(problem_count), 2)
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    UNION ALL
    SELECT 'device_age_days', ROUND(AVG(device_age_days), 2), ROUND(STDDEV(device_age_days), 2), ROUND(MIN(device_age_days), 2), ROUND(MAX(device_age_days), 2)
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
    UNION ALL
    SELECT 'firmware_obsolescence_score', ROUND(AVG(firmware_obsolescence_score), 2), ROUND(STDDEV(firmware_obsolescence_score), 2), ROUND(MIN(firmware_obsolescence_score), 2), ROUND(MAX(firmware_obsolescence_score), 2)
    FROM cdm_tmforum.copper_retirement.risk_inference_unpacked
""")
df_features.show(truncate=False)

# Query C: Anomalous predictions — requests with unexpected latency or error codes
print("\n=== ANOMALOUS REQUESTS (errors or high latency) ===")
df_anomalies = spark.sql("""
    SELECT
        databricks_request_id,
        request_time,
        status_code,
        execution_duration_ms,
        CASE
            WHEN status_code != 200 THEN 'HTTP_ERROR'
            WHEN execution_duration_ms > 1000 THEN 'HIGH_LATENCY'
            ELSE 'NORMAL'
        END as anomaly_type
    FROM cdm_tmforum.copper_retirement.risk_model_inference_payload
    WHERE status_code != 200 OR execution_duration_ms > 1000
    ORDER BY request_time DESC
""")
count = df_anomalies.count()
if count > 0:
    print(f"🚨 {count} anomalous requests found:")
    df_anomalies.show(20, truncate=False)
else:
    print("✅ No anomalous requests (all 200 OK, all < 1000ms)")

print("\n=== MONITORING QUERIES READY ===")
print("These queries run against live inference data.")
print("Once auto-capture is enabled and batch scoring runs daily:")
print("  - Query A monitors prediction volume + tier distribution drift")
print("  - Query B tracks top feature value ranges for input drift")
print("  - Query C flags errors and latency SLA breaches")
print("  - Steps 5-6 (profile/drift metrics) give Lakehouse Monitor PSI scores")
print("  - Step 8 gives latency SLA compliance report")
print("  - Step 9 compares live predictions to V5 baseline")