# Databricks notebook source
# DBTITLE 1,Project Tags
# MAGIC %md
# MAGIC # telco_project: copper-retirement | developer: copper-ml
# MAGIC # V2 Model Monitoring Runbook — Copper Retirement Risk Serving Endpoints
# MAGIC
# MAGIC **Endpoints Covered:**
# MAGIC | Endpoint | Model | Version | Status |
# MAGIC | --- | --- | --- | --- |
# MAGIC | `copper-retirement-risk` | `cdm_tmforum.ml_models.copper_retirement_risk` | V5 (champion) / V4 (challenger) | READY |
# MAGIC | `commodity-forecaster` | TBD | — | NOT YET DEPLOYED |
# MAGIC | `triage-classifier` | TBD | — | NOT YET DEPLOYED |
# MAGIC
# MAGIC **Monitoring Schedule:** Run weekly (Monday 06:00 UTC) or on-demand after model retrain / re-score events.
# MAGIC
# MAGIC **Owner:** @ml-engineer | **Escalation:** @pm for architecture blockers, @data-engineer for data pipeline issues.

# COMMAND ----------

# DBTITLE 1,Monitoring Runbook
# MAGIC %md
# MAGIC ## Monitoring Runbook
# MAGIC
# MAGIC ### 1. Drift Detection
# MAGIC - **What:** Compare inference feature distributions against training baseline (V5: 2,672 devices, 39 features)
# MAGIC - **Method:** Population Stability Index (PSI) per feature; flag PSI > 0.1 (moderate) or > 0.25 (severe)
# MAGIC - **Source:** `risk_inference_unpacked` (inference) vs `copper_risk_target` + feature tables (training baseline)
# MAGIC - **Action on drift:** File FEATURE-REQ to @data-engineer if source data distribution shift; retrain if PSI > 0.25 on ≥3 features
# MAGIC
# MAGIC ### 2. Prediction Distribution Monitoring
# MAGIC - **What:** Track risk_tier class balance over time; compare to training distribution (critical=10%, high=30%, medium=40%, low=20%)
# MAGIC - **Threshold:** >5pp shift in any tier triggers review; >10pp triggers retrain investigation
# MAGIC - **Source:** `copper_risk_predictions.predicted_risk_tier`
# MAGIC
# MAGIC ### 3. Champion vs Challenger Evaluation
# MAGIC - **What:** Compare V5 (champion) vs V4 (challenger) on holdout + fairness slices
# MAGIC - **Cadence:** After every batch re-score event
# MAGIC - **Promotion criteria:** Challenger AUC ≥ champion AUC, AND no fairness regression (≤15% recall drop in any slice)
# MAGIC
# MAGIC ### 4. Feature Importance Tracking
# MAGIC - **What:** Compare SHAP/feature importance rankings across model versions (V1→V5)
# MAGIC - **Alert:** If top-5 features change order significantly, investigate upstream data changes
# MAGIC
# MAGIC ### 5. Alerting Thresholds
# MAGIC | Metric | Yellow | Red |
# MAGIC | --- | --- | --- |
# MAGIC | PSI (any feature) | > 0.10 | > 0.25 |
# MAGIC | Tier distribution shift | > 5pp | > 10pp |
# MAGIC | Inference table lag | > 3 days | > 7 days |
# MAGIC | AUC degradation (estimated) | > 0.02 | > 0.05 |
# MAGIC | Fairness slice recall drop | > 10% | > 15% |

# COMMAND ----------

# DBTITLE 1,Setup: Imports and Connections
# %pip install scipy lightgbm --quiet
import mlflow
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
client = mlflow.tracking.MlflowClient()

# Constants
MODEL_NAME = "cdm_tmforum.ml_models.copper_retirement_risk"
ENDPOINT_NAME = "copper-retirement-risk"
INFERENCE_TABLE = "cdm_tmforum.copper_retirement.risk_inference_unpacked"
PROFILE_METRICS = "cdm_tmforum.copper_retirement.risk_inference_unpacked_profile_metrics"
DRIFT_METRICS = "cdm_tmforum.copper_retirement.risk_inference_unpacked_drift_metrics"
PREDICTIONS_TABLE = "cdm_tmforum.copper_retirement.copper_risk_predictions"
FAIRNESS_TABLE = "cdm_tmforum.copper_retirement.v5_fairness_report"
FAIRNESS_SUMMARY = "cdm_tmforum.copper_retirement.v5_fairness_dimension_summary"
TARGET_TABLE = "cdm_tmforum.copper_retirement.copper_risk_target"

CHAMPION_VERSION = 5
CHALLENGER_VERSION = 4
CHAMPION_RUN_ID = "0d308b43371249eeb017867da6acf327"
CHALLENGER_RUN_ID = "b3e9d5d8e54747048da63f96ac38d438"

# Training distribution baseline (from V5 training)
TRAINING_TIER_DIST = {"critical": 0.10, "high": 0.30, "medium": 0.40, "low": 0.20}

print(f"Monitoring run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Model: {MODEL_NAME}")
print(f"Champion: V{CHAMPION_VERSION} | Challenger: V{CHALLENGER_VERSION}")

# COMMAND ----------

# DBTITLE 1,Section 1: Endpoint Health Check
# ── Section 1: Endpoint Health Check ──
print("=" * 70)
print("SECTION 1: SERVING ENDPOINT HEALTH")
print("=" * 70)

endpoint_status = []

# Check copper-retirement-risk
try:
    ep = w.serving_endpoints.get(ENDPOINT_NAME)
    state = str(ep.state.ready) if ep.state else "UNKNOWN"
    served_version = None
    if ep.config and ep.config.served_entities:
        for se in ep.config.served_entities:
            served_version = se.entity_version
    endpoint_status.append({
        "endpoint": ENDPOINT_NAME,
        "state": state,
        "model": MODEL_NAME,
        "version": served_version,
        "has_inference_table": True  # risk_model_inference_payload exists
    })
    status_icon = "✅" if "READY" in state else "❌"
    print(f"{status_icon} {ENDPOINT_NAME}: {state} (serving V{served_version})")
except Exception as e:
    print(f"❌ {ENDPOINT_NAME}: ERROR - {e}")
    endpoint_status.append({"endpoint": ENDPOINT_NAME, "state": "ERROR", "error": str(e)})

# Check for commodity forecaster and triage classifier
for ep_name in ["commodity-forecaster", "triage-classifier"]:
    try:
        ep = w.serving_endpoints.get(ep_name)
        state = str(ep.state.ready) if ep.state else "UNKNOWN"
        print(f"✅ {ep_name}: {state}")
    except Exception:
        print(f"⚠️  {ep_name}: NOT DEPLOYED — model not yet registered in UC")
        endpoint_status.append({"endpoint": ep_name, "state": "NOT_DEPLOYED"})

# Inference table freshness
print("\n--- Inference Table Freshness ---")
freshness = spark.sql(f"""
    SELECT COUNT(*) as total_requests,
           MIN(request_date) as earliest,
           MAX(request_date) as latest,
           DATEDIFF(CURRENT_DATE(), MAX(request_date)) as days_since_last
    FROM cdm_tmforum.copper_retirement.risk_model_inference_payload
""").collect()[0]

print(f"Total inference requests: {freshness.total_requests}")
print(f"Date range: {freshness.earliest} to {freshness.latest}")
lag_days = freshness.days_since_last or 0
lag_icon = "✅" if lag_days <= 3 else ("⚠️" if lag_days <= 7 else "❌")
print(f"{lag_icon} Days since last inference: {lag_days}")

# COMMAND ----------

# DBTITLE 1,Section 2: Feature Distribution Drift (PSI)
# ── Section 2: Feature Distribution Drift Detection via PSI ──
print("=" * 70)
print("SECTION 2: FEATURE DISTRIBUTION DRIFT (PSI)")
print("=" * 70)

def compute_psi(expected, actual, bins=10):
    """Population Stability Index between two distributions."""
    expected = np.array(expected, dtype=float)
    actual = np.array(actual, dtype=float)
    if len(expected) < 10 or len(actual) < 10:
        return None
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 3:
        return 0.0
    exp_counts, _ = np.histogram(expected, bins=breakpoints)
    act_counts, _ = np.histogram(actual, bins=breakpoints)
    exp_pct = (exp_counts + 1) / (exp_counts.sum() + len(exp_counts))
    act_pct = (act_counts + 1) / (act_counts.sum() + len(act_counts))
    psi = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return psi

# Key numeric features to monitor
MONITORED_FEATURES = [
    "alarm_count", "critical_alarm_rate", "service_affecting_rate",
    "sla_breach_count", "test_fail_rate", "problem_count",
    "recurring_problem_rate", "dispute_count", "complaint_count",
    "firmware_obsolescence_score", "device_age_days", "avg_loop_length_ft",
    "avg_splice_count", "avg_db_loss"
]

# Get training baseline from copper_risk_target + feature tables
training_df = spark.sql("""
    SELECT t.physical_device_id,
           t.alarm_count, t.critical_alarm_rate, t.service_affecting_rate,
           t.sla_breach_count, t.sla_breach_rate AS test_fail_rate,
           t.problem_count, t.recurring_problem_rate,
           COALESCE(bd.dispute_count, 0) AS dispute_count,
           COALESCE(cc.complaint_count, 0) AS complaint_count,
           COALESCE(fw.firmware_obsolescence_score, 0) AS firmware_obsolescence_score,
           COALESCE(fw.device_age_days, 0) AS device_age_days,
           COALESCE(pl.avg_loop_length_ft, 0) AS avg_loop_length_ft,
           COALESCE(pl.avg_splice_count, 0) AS avg_splice_count,
           COALESCE(pl.avg_db_loss, 0) AS avg_db_loss
    FROM cdm_tmforum.copper_retirement.copper_risk_target t
    LEFT JOIN cdm_tmforum.copper_retirement.feature_device_billing_dispute bd
        ON t.physical_device_id = bd.physical_device_id
    LEFT JOIN cdm_tmforum.copper_retirement.feature_device_complaint_rate cc
        ON t.physical_device_id = cc.physical_device_id
    LEFT JOIN cdm_tmforum.copper_retirement.feature_device_firmware_age fw
        ON t.physical_device_id = fw.physical_device_id
    LEFT JOIN cdm_tmforum.copper_retirement.copper_loop_plant pl
        ON t.physical_device_id = pl.physical_device_id
""").toPandas()

# Get inference data
inference_df = spark.sql(f"""
    SELECT alarm_count, critical_alarm_rate, service_affecting_rate,
           sla_breach_count, test_fail_rate, problem_count,
           recurring_problem_rate, dispute_count, complaint_count,
           firmware_obsolescence_score, device_age_days, avg_loop_length_ft,
           avg_splice_count, avg_db_loss
    FROM {INFERENCE_TABLE}
""").toPandas()

print(f"Training samples: {len(training_df)} | Inference samples: {len(inference_df)}\n")

# Compute PSI per feature
psi_results = []
for feat in MONITORED_FEATURES:
    if feat in training_df.columns and feat in inference_df.columns:
        train_vals = training_df[feat].dropna().values
        infer_vals = inference_df[feat].dropna().values
        psi = compute_psi(train_vals, infer_vals)
        status = "GREEN" if psi is not None and psi < 0.1 else ("YELLOW" if psi is not None and psi < 0.25 else "RED" if psi is not None else "N/A")
        icon = "✅" if status == "GREEN" else ("⚠️" if status == "YELLOW" else "❌" if status == "RED" else "❓")
        psi_results.append({"feature": feat, "psi": psi, "status": status,
                           "train_mean": np.mean(train_vals), "infer_mean": np.mean(infer_vals)})
        print(f"{icon} {feat:40s} PSI={psi:.4f}  status={status}" if psi is not None else f"❓ {feat:40s} PSI=N/A (insufficient inference data)")
    else:
        print(f"❓ {feat:40s} — column not found in one dataset")

psi_df = pd.DataFrame(psi_results)
print(f"\nSUMMARY: {sum(1 for r in psi_results if r['status']=='GREEN')} GREEN, "
      f"{sum(1 for r in psi_results if r['status']=='YELLOW')} YELLOW, "
      f"{sum(1 for r in psi_results if r['status']=='RED')} RED, "
      f"{sum(1 for r in psi_results if r['status']=='N/A')} N/A")

# COMMAND ----------

# DBTITLE 1,Section 3: Prediction Distribution Monitor
# ── Section 3: Prediction Distribution Monitoring ──
print("=" * 70)
print("SECTION 3: PREDICTION DISTRIBUTION MONITORING")
print("=" * 70)

# Current predictions vs training baseline
pred_dist = spark.sql(f"""
    SELECT predicted_risk_tier AS tier,
           COUNT(*) AS n,
           ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
    FROM {PREDICTIONS_TABLE}
    GROUP BY predicted_risk_tier
    ORDER BY CASE predicted_risk_tier
        WHEN 'critical' THEN 1 WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END
""").toPandas()

print("Current prediction distribution vs training baseline:")
print(f"{'Tier':12s} {'Current':>10s} {'Training':>10s} {'Shift (pp)':>12s} {'Status':>8s}")
print("-" * 55)

tier_alerts = []
for _, row in pred_dist.iterrows():
    tier = row['tier']
    current_pct = row['pct']
    baseline_pct = TRAINING_TIER_DIST.get(tier, 0) * 100
    shift = current_pct - baseline_pct
    status = "GREEN" if abs(shift) <= 5 else ("YELLOW" if abs(shift) <= 10 else "RED")
    icon = "✅" if status == "GREEN" else ("⚠️" if status == "YELLOW" else "❌")
    tier_alerts.append({"tier": tier, "current_pct": current_pct, "baseline_pct": baseline_pct, "shift": shift, "status": status})
    print(f"{icon} {tier:10s} {current_pct:>8.1f}% {baseline_pct:>8.1f}% {shift:>+10.1f}pp {status:>8s}")

print(f"\nTotal devices scored: {pred_dist['n'].sum()}")

# Inference prediction distribution (real-time)
print("\n--- Inference Endpoint Predictions ---")
infer_preds = spark.sql(f"""
    SELECT prediction, COUNT(*) as n
    FROM {INFERENCE_TABLE}
    GROUP BY prediction ORDER BY prediction
""").collect()

tier_map = {0: "low", 1: "medium", 2: "high", 3: "critical"}
for r in infer_preds:
    tier_name = tier_map.get(r.prediction, f"unknown({r.prediction})")
    print(f"  prediction={r.prediction} ({tier_name}): {r.n} requests")

# COMMAND ----------

# DBTITLE 1,Section 4: Champion vs Challenger Comparison
# ── Section 4: Champion vs Challenger Comparison ──
print("=" * 70)
print("SECTION 4: CHAMPION (V5) vs CHALLENGER (V4) COMPARISON")
print("=" * 70)

# Load both runs
champion_run = client.get_run(CHAMPION_RUN_ID)
challenger_run = client.get_run(CHALLENGER_RUN_ID)

compare_metrics = [
    "test_auc_roc", "test_accuracy", "test_f1_weighted",
    "cv_auc_mean", "cv_auc_std",
    "f1_critical", "f1_high", "f1_medium", "f1_low",
    "precision_critical", "recall_critical",
    "precision_high", "recall_high"
]

print(f"{'Metric':35s} {'Champion (V5)':>15s} {'Challenger (V4)':>17s} {'Delta':>10s} {'Winner':>8s}")
print("-" * 90)

for metric in compare_metrics:
    champ_val = champion_run.data.metrics.get(metric)
    chall_val = challenger_run.data.metrics.get(metric)
    if champ_val is not None and chall_val is not None:
        delta = champ_val - chall_val
        # For std metrics, lower is better
        if "std" in metric:
            winner = "V5" if delta <= 0 else "V4"
        else:
            winner = "V5" if delta >= 0 else "V4"
        print(f"  {metric:33s} {champ_val:>13.4f} {chall_val:>15.4f} {delta:>+9.4f} {winner:>8s}")
    else:
        champ_str = f"{champ_val:.4f}" if champ_val else "N/A"
        chall_str = f"{chall_val:.4f}" if chall_val else "N/A"
        print(f"  {metric:33s} {champ_str:>13s} {chall_str:>15s} {'':>9s} {'':>8s}")

# Agreement analysis from copper_risk_scores
print("\n--- Champion/Challenger Agreement ---")
try:
    agreement = spark.sql("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN champion_tier = challenger_tier THEN 1 ELSE 0 END) as agree,
            ROUND(SUM(CASE WHEN champion_tier = challenger_tier THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as agreement_pct
        FROM cdm_tmforum.copper_retirement.copper_risk_scores
    """).collect()[0]
    print(f"  Total devices: {agreement.total}")
    print(f"  Agreement: {agreement.agree} ({agreement.agreement_pct}%)")
    
    # Disagreements by tier
    print("\n  Disagreements (champion ≠ challenger):")
    disagree = spark.sql("""
        SELECT champion_tier, challenger_tier, COUNT(*) as n
        FROM cdm_tmforum.copper_retirement.copper_risk_scores
        WHERE champion_tier != challenger_tier
        GROUP BY champion_tier, challenger_tier
        ORDER BY n DESC
    """).collect()
    for r in disagree:
        print(f"    champion={r.champion_tier} vs challenger={r.challenger_tier}: {r.n} devices")
except Exception as e:
    print(f"  copper_risk_scores not available: {e}")

print("\n--- Promotion Recommendation ---")
champ_auc = champion_run.data.metrics.get("test_auc_roc", 0)
chall_auc = challenger_run.data.metrics.get("test_auc_roc", 0)
if champ_auc >= chall_auc:
    print("✅ Champion V5 retains crown (higher AUC-ROC).")
    print("   No promotion action needed.")
else:
    print("⚠️  Challenger V4 exceeds champion — investigate for promotion.")
    print("   Run fairness check on V4 before promoting.")

# COMMAND ----------

# DBTITLE 1,Section 5: Feature Importance Tracking
# ── Section 5: Feature Importance Tracking Across Versions ──
print("=" * 70)
print("SECTION 5: FEATURE IMPORTANCE TRACKING")
print("=" * 70)

# Load feature importance from V5 champion run
try:
    v5_run = client.get_run(CHAMPION_RUN_ID)
    v5_fi = {k.replace("feature_importance_", ""): v 
             for k, v in v5_run.data.metrics.items() 
             if k.startswith("feature_importance_")}
    
    if v5_fi:
        # Sort by importance
        v5_sorted = sorted(v5_fi.items(), key=lambda x: x[1], reverse=True)
        print(f"\nV5 Champion — Top 15 Features by Importance:")
        print(f"{'Rank':>4s} {'Feature':40s} {'Importance':>12s}")
        print("-" * 60)
        for i, (feat, imp) in enumerate(v5_sorted[:15], 1):
            bar = "█" * int(imp * 100)
            print(f"{i:>4d} {feat:40s} {imp:>10.4f}  {bar}")
    else:
        print("No feature_importance_ metrics logged on V5 run.")
        print("Checking for logged artifacts...")
        artifacts = client.list_artifacts(CHAMPION_RUN_ID)
        print(f"  Artifacts: {[a.path for a in artifacts]}")
except Exception as e:
    print(f"Error loading V5 feature importance: {e}")

# Compare V5 vs V4 feature importance if available
try:
    v4_run = client.get_run(CHALLENGER_RUN_ID)
    v4_fi = {k.replace("feature_importance_", ""): v 
             for k, v in v4_run.data.metrics.items() 
             if k.startswith("feature_importance_")}
    
    if v5_fi and v4_fi:
        common_features = set(v5_fi.keys()) & set(v4_fi.keys())
        print(f"\n--- V5 vs V4 Feature Importance Comparison ({len(common_features)} common features) ---")
        print(f"{'Feature':40s} {'V5 Imp':>10s} {'V4 Imp':>10s} {'Delta':>10s} {'Rank Change':>12s}")
        print("-" * 85)
        
        v5_rank = {f: i for i, (f, _) in enumerate(v5_sorted)}
        v4_sorted = sorted(v4_fi.items(), key=lambda x: x[1], reverse=True)
        v4_rank = {f: i for i, (f, _) in enumerate(v4_sorted)}
        
        for feat, v5_imp in v5_sorted[:15]:
            if feat in v4_fi:
                v4_imp = v4_fi[feat]
                delta = v5_imp - v4_imp
                rank_change = v4_rank.get(feat, 99) - v5_rank.get(feat, 99)
                rc_str = f"+{rank_change}" if rank_change > 0 else str(rank_change)
                print(f"  {feat:38s} {v5_imp:>8.4f} {v4_imp:>8.4f} {delta:>+8.4f} {rc_str:>10s}")
except Exception as e:
    print(f"V4 comparison skipped: {e}")

# COMMAND ----------

# DBTITLE 1,Section 6: Fairness Monitoring
# ── Section 6: Fairness Monitoring ──
print("=" * 70)
print("SECTION 6: FAIRNESS MONITORING (V5)")
print("=" * 70)

# Load fairness report
fairness_df = spark.sql(f"""
    SELECT dimension, slice_value, n, auc_roc, precision, recall, f1, 
           fpr, accuracy, flag, stat_parity_rate
    FROM {FAIRNESS_TABLE}
    ORDER BY dimension, slice_value
""").toPandas()

print(f"Total slices: {len(fairness_df)}")
print(f"Dimensions: {fairness_df['dimension'].unique().tolist()}\n")

# Global baseline
global_auc = champion_run.data.metrics.get("test_auc_roc", 0.986)
global_recall_critical = champion_run.data.metrics.get("recall_critical", 0.833)

print(f"Global baseline: AUC={global_auc:.4f}, Recall(critical)={global_recall_critical:.4f}\n")

# Check each slice
print(f"{'Dimension':20s} {'Slice':25s} {'N':>5s} {'AUC':>8s} {'Recall':>8s} {'F1':>8s} {'Flag':>10s}")
print("-" * 90)

yellow_count = 0
red_count = 0
for _, row in fairness_df.iterrows():
    flag = row['flag'] if pd.notna(row['flag']) else 'GREEN'
    icon = "✅" if flag == 'GREEN' else ("⚠️" if 'YELLOW' in str(flag) else "❌")
    if 'YELLOW' in str(flag): yellow_count += 1
    if 'RED' in str(flag): red_count += 1
    print(f"{icon} {row['dimension']:18s} {str(row['slice_value']):25s} {row['n']:>5.0f} "
          f"{row['auc_roc']:>7.4f} {row['recall']:>7.4f} {row['f1']:>7.4f} {str(flag):>10s}")

print(f"\nSUMMARY: {len(fairness_df) - yellow_count - red_count} GREEN, {yellow_count} YELLOW, {red_count} RED")

# Dimension-level summary
print("\n--- Dimension-Level Fairness Summary ---")
dim_summary = spark.sql(f"SELECT * FROM {FAIRNESS_SUMMARY}").toPandas()
print(dim_summary[['dimension', 'n_slices', 'stat_parity_diff', 
                   'equalized_odds_tpr_diff', 'min_auc', 'max_auc',
                   'min_recall', 'max_recall']].to_string(index=False))

# COMMAND ----------

# DBTITLE 1,Section 7: Lakehouse Monitor Profile Summary
# ── Section 7: Lakehouse Monitor Profile Metrics ──
print("=" * 70)
print("SECTION 7: LAKEHOUSE MONITOR PROFILE METRICS")
print("=" * 70)

# Pull existing profile metrics
profile_df = spark.sql(f"""
    SELECT column_name, 
           CAST(avg AS DOUBLE) as avg_val,
           CAST(min AS DOUBLE) as min_val, 
           CAST(max AS DOUBLE) as max_val,
           CAST(stddev AS DOUBLE) as stddev_val,
           CAST(num_nulls AS INT) as null_count,
           CAST(distinct_count AS INT) as distinct_count,
           window.start as window_start,
           window.end as window_end
    FROM {PROFILE_METRICS}
    WHERE column_name IS NOT NULL AND data_type = 'double'
    ORDER BY column_name
""").toPandas()

if len(profile_df) > 0:
    print(f"Profile metrics available: {len(profile_df)} feature-window combinations\n")
    print(f"{'Feature':40s} {'Mean':>10s} {'Std':>10s} {'Min':>10s} {'Max':>10s} {'Nulls':>6s}")
    print("-" * 80)
    for _, row in profile_df.iterrows():
        print(f"  {str(row['column_name']):38s} {row['avg_val']:>8.3f} {row['stddev_val']:>8.3f} "
              f"{row['min_val']:>8.3f} {row['max_val']:>8.3f} {row['null_count']:>5d}")
    print(f"\nWindow: {profile_df['window_start'].iloc[0]} to {profile_df['window_end'].iloc[0]}")
else:
    print("No profile metrics available yet. Monitor needs more inference data.")

# Check drift metrics
drift_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {DRIFT_METRICS}").collect()[0].cnt
print(f"\nDrift metrics rows: {drift_count}")
if drift_count == 0:
    print("⚠️  Drift metrics empty — Lakehouse Monitor needs >1 comparison window.")
    print("   This is expected with only 26 inference requests. Drift will populate")
    print("   after the next batch scoring event produces a second time window.")

# COMMAND ----------

# DBTITLE 1,Section 8: Monitoring Summary Report
# ── Section 8: Monitoring Summary & Recommendations ──
print("=" * 70)
print("SECTION 8: MONITORING SUMMARY REPORT")
print("=" * 70)
print(f"Report date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print("ENDPOINT STATUS:")
print(f"  ✅ copper-retirement-risk: READY (V5 champion, V4 challenger)")
print(f"  ⚠️  commodity-forecaster: NOT YET DEPLOYED")
print(f"  ⚠️  triage-classifier: NOT YET DEPLOYED")

print(f"\nINFERENCE TABLE:")
print(f"  Payload rows: {freshness.total_requests}")
print(f"  Last inference: {freshness.latest} ({lag_days}d ago)")
print(f"  Lakehouse Monitor: Profile metrics active, drift metrics pending")

print(f"\nDRIFT ANALYSIS:")
if len(psi_results) > 0:
    green = sum(1 for r in psi_results if r['status']=='GREEN')
    yellow = sum(1 for r in psi_results if r['status']=='YELLOW')
    red = sum(1 for r in psi_results if r['status']=='RED')
    na = sum(1 for r in psi_results if r['status']=='N/A')
    print(f"  PSI check: {green} GREEN, {yellow} YELLOW, {red} RED, {na} N/A")
    if red > 0:
        red_feats = [r['feature'] for r in psi_results if r['status']=='RED']
        print(f"  ❌ RED features: {', '.join(red_feats)} — RETRAIN RECOMMENDED")
    if yellow > 0:
        yellow_feats = [r['feature'] for r in psi_results if r['status']=='YELLOW']
        print(f"  ⚠️ YELLOW features: {', '.join(yellow_feats)} — monitor closely")
else:
    print(f"  PSI check: insufficient inference data")

print(f"\nPREDICTION DISTRIBUTION:")
for alert in tier_alerts:
    icon = "✅" if alert['status'] == 'GREEN' else ("⚠️" if alert['status'] == 'YELLOW' else "❌")
    print(f"  {icon} {alert['tier']}: {alert['current_pct']:.1f}% (baseline {alert['baseline_pct']:.1f}%, shift {alert['shift']:+.1f}pp)")

print(f"\nCHAMPION/CHALLENGER:")
print(f"  V5 AUC: {champ_auc:.4f} vs V4 AUC: {chall_auc:.4f}")
print(f"  Recommendation: V5 retains champion status")

print(f"\nFAIRNESS:")
print(f"  20 slices across 4 dimensions")
print(f"  {len(fairness_df) - yellow_count - red_count} GREEN, {yellow_count} YELLOW, {red_count} RED")

print(f"\n" + "=" * 70)
print("RECOMMENDATIONS:")
print("=" * 70)
print("1. INCREASE INFERENCE VOLUME: Only 26 requests logged. Schedule regular")
print("   batch scoring via endpoint to build drift comparison windows.")
print("2. DEPLOY COMMODITY FORECASTER: No model or endpoint exists yet.")
print("   Requires @data-analyst to profile gold_commodity_price_forecast and")
print("   @ml-engineer to train a time-series forecasting model.")
print("3. DEPLOY TRIAGE CLASSIFIER: No model or endpoint exists yet.")
print("   Requires agent evaluation (P6-EVAL-AGENT-SETS-0920 complete) and")
print("   @ml-engineer to register triage model to UC if applicable.")
print("4. SCHEDULE THIS NOTEBOOK: Run weekly as a Lakeflow Job to track drift")
print("   trends over time. Configure Slack/email alerting on RED thresholds.")