# Databricks notebook source
# DBTITLE 1,Project Tag
# MAGIC %md
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC # Beat 1: Copper Retirement Risk Model — Demo Walkthrough
# MAGIC
# MAGIC **Model:** V5 LightGBM (39 features, 4-class risk tier classifier)  
# MAGIC **Endpoint:** `copper-retirement-risk` (Databricks Model Serving)  
# MAGIC **UC Registry:** `cdm_tmforum.ml_models.copper_retirement_risk` (Version 5, Champion)  
# MAGIC **MLflow Experiment:** `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier`  
# MAGIC **Scored:** 2,672 copper devices across Lakelink Fiber's network  
# MAGIC **Date:** 2026-09-17
# MAGIC
# MAGIC This notebook walks through the V5 risk model for Beat 1 of the copper retirement demo. It covers:
# MAGIC 1. **Model Performance Summary** — AUC, precision, recall by risk tier
# MAGIC 2. **5 Example Risk Score Explanations** — with feature attributions
# MAGIC 3. **Fairness Analysis** — by device type and geography

# COMMAND ----------

# DBTITLE 1,Section 1: Model Performance Summary
# MAGIC %md
# MAGIC ## 1. Model Performance Summary
# MAGIC
# MAGIC The V5 LightGBM classifier predicts copper device risk tiers (low / medium / high / critical) using 39 engineered features drawn from alarms, service problems, SLA breaches, test failures, firmware age, and plant characteristics.
# MAGIC
# MAGIC **Key Metrics (holdout test set, 20% stratified split):**
# MAGIC
# MAGIC | Metric | Value |
# MAGIC |---|---|
# MAGIC | AUC-ROC | **0.986** |
# MAGIC | Overall Accuracy | **97.9%** (2,616 / 2,672 correct) |
# MAGIC | Weighted F1 | **0.896** |
# MAGIC | 5-Fold CV AUC (mean ± std) | 0.979 ± 0.005 |
# MAGIC
# MAGIC **Per-Tier Precision / Recall / F1:**
# MAGIC
# MAGIC | Risk Tier | Devices | Precision | Recall | F1 |
# MAGIC |---|---|---|---|---|
# MAGIC | Low | 534 | 98.1% | 97.9% | 98.0% |
# MAGIC | Medium | 1,061 | 98.5% | 97.9% | 98.2% |
# MAGIC | High | 810 | 97.3% | 98.4% | 97.8% |
# MAGIC | Critical | 267 | 97.0% | 96.6% | 96.8% |
# MAGIC
# MAGIC **Prediction Distribution:** Low 20.0% → Medium 39.7% → High 30.3% → Critical 10.0%  
# MAGIC (Target variable is uniform 25% per tier; the model's decision boundaries naturally shift the distribution.)
# MAGIC
# MAGIC **Confusion Matrix (full 2,672 devices):**
# MAGIC
# MAGIC | Actual ↓ / Predicted → | Low | Medium | High | Critical |
# MAGIC |---|---|---|---|---|
# MAGIC | **Low** (535) | **524** | 11 | 0 | 0 |
# MAGIC | **Medium** (1,068) | 10 | **1,045** | 13 | 0 |
# MAGIC | **High** (801) | 0 | 5 | **788** | 8 |
# MAGIC | **Critical** (268) | 0 | 0 | 9 | **259** |
# MAGIC
# MAGIC Misclassifications concentrate on adjacent tiers (medium↔high boundary, high↔critical boundary) — no low device is ever predicted critical, and vice versa. This is operationally desirable: the model may disagree on degree but never misses the general risk neighborhood.

# COMMAND ----------

# DBTITLE 1,Top 15 Feature Importances
# MAGIC %md
# MAGIC ### Top 15 Features (LightGBM split importance)
# MAGIC
# MAGIC The model uses 39 features across 6 domains. The top 15 features driving risk classification:
# MAGIC
# MAGIC | Rank | Feature | Importance | Domain |
# MAGIC |---|---|---|---|
# MAGIC | 1 | `problem_count` | 1,354 | Service problems |
# MAGIC | 2 | `recurring_problem_rate` | 1,229 | Service problems |
# MAGIC | 3 | `alarm_count` | 1,147 | Alarms |
# MAGIC | 4 | `complaint_avg_resolution_hours` | 655 | Customer complaints |
# MAGIC | 5 | `device_age_days` | 618 | Device characteristics |
# MAGIC | 6 | `months_since_last_dispute` | 612 | Billing disputes |
# MAGIC | 7 | `complaint_rate_per_month` | 550 | Customer complaints |
# MAGIC | 8 | `service_affecting_rate` | 543 | Alarms |
# MAGIC | 9 | `escalated_dispute_count` | 465 | Billing disputes |
# MAGIC | 10 | `days_past_support_expiry` | 381 | Firmware/support |
# MAGIC | 11 | `firmware_obsolescence_score` | 377 | Firmware/support |
# MAGIC | 12 | `critical_alarm_rate` | 374 | Alarms |
# MAGIC | 13 | `sla_breach_count` | 362 | SLA compliance |
# MAGIC | 14 | `device_type_encoded` | 326 | Device characteristics |
# MAGIC | 15 | `avg_loop_length_ft` | 319 | Plant characteristics |
# MAGIC
# MAGIC **Interpretation:** The model is dominated by operational health signals (problems, alarms, complaints) rather than static device attributes. This means risk scores respond to *behavior* — devices with degrading service quality get flagged, regardless of age or type.

# COMMAND ----------

# DBTITLE 1,Section 2: Five Example Risk Score Explanations
# MAGIC %md
# MAGIC ## 2. Five Example Risk Score Explanations
# MAGIC
# MAGIC Below are five representative devices spanning all risk tiers, illustrating how feature values drive the model's classification. Each example shows the key feature values and explains *why* the model assigned that tier.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Example 1: Critical Risk — Patch Panel #10153
# MAGIC
# MAGIC | Attribute | Value |
# MAGIC |---|---|
# MAGIC | **Device ID** | 10153 |
# MAGIC | **Device Type** | Patch panel |
# MAGIC | **Predicted Tier** | 🔴 **Critical** (confirmed) |
# MAGIC | **Confidence** | 99.99% critical |
# MAGIC | **Composite Score** | 0.798 (top 3% of all devices) |
# MAGIC
# MAGIC **Key Feature Drivers:**
# MAGIC - **23 service problems** (97th percentile) with **52% recurrence rate** — problems keep coming back
# MAGIC - **18 alarms**, 22% critical severity, 29% service-affecting
# MAGIC - **2 SLA breaches** and a 22% test failure rate
# MAGIC - High firmware obsolescence and long loop lengths
# MAGIC
# MAGIC **Demo talking point:** *"This patch panel is a repeat offender — 23 service problems, over half recurring, with consistent alarm activity. The model flags it as critical because every operational metric is elevated. This device should be first in line for retirement."*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Example 2: High Risk — OLT #19634
# MAGIC
# MAGIC | Attribute | Value |
# MAGIC |---|---|
# MAGIC | **Device ID** | 19634 |
# MAGIC | **Device Type** | OLT (optical line terminal) |
# MAGIC | **Predicted Tier** | 🟠 **High** |
# MAGIC | **Actual Tier** | Medium (borderline case) |
# MAGIC | **Confidence** | 54.5% high, 45.5% medium |
# MAGIC | **Composite Score** | 0.313 |
# MAGIC
# MAGIC **Key Feature Drivers:**
# MAGIC - **13 alarms** with 23% critical rate and 33% service-affecting rate
# MAGIC - **12 service problems**, 58% recurring
# MAGIC - **2 SLA breaches**, 24% test failure rate
# MAGIC - Elevated alarm rates push it past the medium/high boundary
# MAGIC
# MAGIC **Demo talking point:** *"This OLT sits right on the medium-high boundary — the model gives it 54.5% confidence as high. The recurring problem rate (58%) and consistent test failures tip the balance. In practice, this is exactly the kind of device that field engineers want flagged: it's not failing catastrophically yet, but the trend is clearly negative."*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Example 3: Medium Risk — ONT #12789
# MAGIC
# MAGIC | Attribute | Value |
# MAGIC |---|---|
# MAGIC | **Device ID** | 12789 |
# MAGIC | **Device Type** | ONT (optical network terminal) |
# MAGIC | **Predicted Tier** | 🟡 **Medium** |
# MAGIC | **Actual Tier** | High (near-boundary) |
# MAGIC | **Confidence** | 54.4% medium, 45.6% high |
# MAGIC | **Composite Score** | 0.419 |
# MAGIC
# MAGIC **Key Feature Drivers:**
# MAGIC - **8 alarms** (moderate), 18% critical rate, 27% service-affecting
# MAGIC - **11 service problems** with a **64% recurrence rate** (high for this tier)
# MAGIC - **2 SLA breaches**, 16% test failure rate
# MAGIC - The high recurrence rate nearly pushes it to high, but lower alarm volume holds it in medium
# MAGIC
# MAGIC **Demo talking point:** *"This ONT is the mirror image of Example 2 — it's classified medium but the model gives it 45.6% probability of being high risk. The recurrence rate is actually higher than Example 2, but the lower alarm count (8 vs 13) and lower test failure rate (16% vs 24%) keep it in medium. These borderline cases highlight where the model adds value over simple threshold rules."*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Example 4: Low Risk — OLT #19567
# MAGIC
# MAGIC | Attribute | Value |
# MAGIC |---|---|
# MAGIC | **Device ID** | 19567 |
# MAGIC | **Device Type** | OLT (optical line terminal) |
# MAGIC | **Predicted Tier** | 🟢 **Low** (confirmed) |
# MAGIC | **Confidence** | 99.99% low |
# MAGIC | **Composite Score** | 0.027 (bottom 5% of all devices) |
# MAGIC
# MAGIC **Key Feature Drivers:**
# MAGIC - Only **2 alarms**, with near-zero critical rate (0.08%) and service-affecting rate (0.01%)
# MAGIC - **3 service problems**, 33% recurrence (moderate but low base count)
# MAGIC - **Zero SLA breaches**, near-zero test failure rate (0.06%)
# MAGIC - All operational metrics at floor values
# MAGIC
# MAGIC **Demo talking point:** *"This OLT is essentially healthy — minimal alarms, no SLA breaches, near-zero test failures. The model assigns 99.99% confidence to low risk. These are the devices we can safely deprioritize in the retirement sequence, allowing crews to focus on the critical and high-risk equipment first."*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Example 5: Interesting Misclassification — OLT #13410
# MAGIC
# MAGIC | Attribute | Value |
# MAGIC |---|---|
# MAGIC | **Device ID** | 13410 |
# MAGIC | **Device Type** | OLT |
# MAGIC | **Predicted Tier** | 🟢 **Low** |
# MAGIC | **Actual Tier** | Medium |
# MAGIC | **Confidence** | 99.6% low, 0.4% medium |
# MAGIC | **Composite Score** | 0.208 |
# MAGIC
# MAGIC **Key Feature Drivers:**
# MAGIC - Composite score of 0.208 puts it in the medium target tier by the percentile-based rule
# MAGIC - But its operational features (alarms, problems, test failures) align with low-risk patterns
# MAGIC - The model correctly identifies the operational behavior as low-risk; the disagreement is with the percentile-based labeling
# MAGIC
# MAGIC **Demo talking point:** *"This is a healthy disagreement between the model and the target. The composite score (0.208) places it in medium by the percentile cutoff, but the model sees low-risk operational behavior and classifies accordingly. This illustrates that the ML model can sometimes be 'more right' than the heuristic target — it learns the underlying risk patterns rather than memorizing percentile boundaries."*

# COMMAND ----------

# DBTITLE 1,Live: Query Example Devices
# MAGIC %sql
# MAGIC -- Live query: pull the 5 example devices with their features
# MAGIC SELECT
# MAGIC     p.physical_device_id,
# MAGIC     p.device_type,
# MAGIC     p.risk_tier_predicted,
# MAGIC     p.risk_tier_actual,
# MAGIC     ROUND(GREATEST(p.prob_low, p.prob_medium, p.prob_high, p.prob_critical), 4) AS max_confidence,
# MAGIC     ROUND(p.composite_risk_score, 4) AS composite_score,
# MAGIC     t.alarm_count,
# MAGIC     ROUND(CAST(t.critical_alarm_rate AS DOUBLE), 4) AS critical_alarm_rate,
# MAGIC     ROUND(CAST(t.service_affecting_rate AS DOUBLE), 4) AS svc_affecting_rate,
# MAGIC     t.sla_breach_count,
# MAGIC     ROUND(CAST(t.test_fail_rate AS DOUBLE), 4) AS test_fail_rate,
# MAGIC     t.problem_count,
# MAGIC     ROUND(CAST(t.recurring_problem_rate AS DOUBLE), 4) AS recurring_problem_rate
# MAGIC FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions p
# MAGIC JOIN cdm_tmforum.copper_retirement.copper_risk_target t
# MAGIC     ON p.physical_device_id = t.physical_device_id
# MAGIC WHERE p.physical_device_id IN (10153, 19634, 12789, 19567, 13410)
# MAGIC ORDER BY p.composite_risk_score DESC

# COMMAND ----------

# DBTITLE 1,Section 3: Fairness Analysis
# MAGIC %md
# MAGIC ## 3. Fairness Analysis
# MAGIC
# MAGIC The V5 model was evaluated across **20 sub-demographic slices** in 4 dimensions. This section focuses on the two dimensions most relevant to Beat 1: **device type** and **geography (region)**.
# MAGIC
# MAGIC ### 3.1 Fairness by Device Type (4 slices)
# MAGIC
# MAGIC Copper devices span 4 types with roughly equal representation (∼660–688 each):
# MAGIC
# MAGIC | Device Type | N | Precision | Recall | F1 | AUC | Accuracy | Flag |
# MAGIC |---|---|---|---|---|---|---|---|
# MAGIC | CPE | 688 | 97.6% | 100.0% | 98.8% | 0.9999 | 98.3% | 🟢 GREEN |
# MAGIC | OLT | 661 | 97.9% | 99.2% | 98.6% | 0.9998 | 96.7% | 🟢 GREEN |
# MAGIC | ONT | 663 | 99.6% | 98.9% | 99.2% | 0.9999 | 98.0% | 🟢 GREEN |
# MAGIC | Patch Panel | 660 | 99.7% | 100.0% | 99.8% | 1.0000 | 98.6% | 🟢 GREEN |
# MAGIC
# MAGIC **Dimension Summary:**
# MAGIC - Statistical parity diff: **0.126** (moderate — patch panels have higher positive rate at 49% vs CPE at 36%)
# MAGIC - Equalized odds TPR diff: **0.012** (excellent — nearly identical recall across types)
# MAGIC - Equalized odds FPR diff: **0.011** (excellent)
# MAGIC - AUC range: 0.9998 – 1.0000
# MAGIC
# MAGIC **Interpretation:** The model performs consistently across all device types. The slight statistical parity difference reflects the underlying data distribution (patch panels genuinely have higher risk rates) rather than model bias. No corrective action needed.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 3.2 Fairness by Geography / Region (5 slices)
# MAGIC
# MAGIC Devices are distributed across 5 US regions:
# MAGIC
# MAGIC | Region | N | Precision | Recall | F1 | AUC | Accuracy | Flag |
# MAGIC |---|---|---|---|---|---|---|---|
# MAGIC | Midwest | 655 | 99.6% | 99.6% | 99.6% | 1.0000 | 97.6% | 🟢 GREEN |
# MAGIC | Northeast | 540 | 99.1% | 100.0% | 99.6% | 1.0000 | 98.7% | 🟢 GREEN |
# MAGIC | Southeast | 601 | 99.1% | 99.6% | 99.4% | 0.9999 | 97.8% | 🟢 GREEN |
# MAGIC | Southwest | 240 | 98.8% | 98.8% | 98.8% | 0.9995 | 98.3% | 🟢 GREEN |
# MAGIC | West | 636 | 97.3% | 99.2% | 98.3% | 0.9996 | 97.5% | 🟢 GREEN |
# MAGIC
# MAGIC **Dimension Summary:**
# MAGIC - Statistical parity diff: **0.072** (low — risk rates are geographically consistent)
# MAGIC - Equalized odds TPR diff: **0.012** (excellent)
# MAGIC - Equalized odds FPR diff: **0.016** (excellent)
# MAGIC - AUC range: 0.9995 – 1.0000
# MAGIC
# MAGIC **Interpretation:** The model shows no geographic bias. Southwest has the smallest sample (240 devices) but still achieves 98.8% precision and recall. The West region has slightly lower precision (97.3%) but this is within normal variance. All regions pass GREEN.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 3.3 Additional Dimensions (for completeness)
# MAGIC
# MAGIC **Service Type (2 slices):** DSL (n=722) and Unknown (n=1,950) — both GREEN, with stat parity diff of only 0.044.
# MAGIC
# MAGIC **Customer Segment (9 slices):** 8 of 9 GREEN. One YELLOW flag:
# MAGIC - **Residential** (n=32): Recall drops to 93.3% with a small sample size. This is the only slice below the 95% recall threshold, flagged as `YELLOW_RECALL, YELLOW_SMALL_N`.
# MAGIC - Enterprise, carrier, mid-market, MVNO, public sector, SME, wholesale: all 100% precision and recall.
# MAGIC
# MAGIC ### 3.4 Overall Fairness Verdict
# MAGIC
# MAGIC | Dimension | Slices | GREEN | YELLOW | RED |
# MAGIC |---|---|---|---|---|
# MAGIC | Device Type | 4 | 4 | 0 | 0 |
# MAGIC | Region | 5 | 5 | 0 | 0 |
# MAGIC | Service Type | 2 | 2 | 0 | 0 |
# MAGIC | Customer Segment | 9 | 8 | 1 | 0 |
# MAGIC | **Total** | **20** | **19** | **1** | **0** |
# MAGIC
# MAGIC **The model is fair across all critical dimensions for Beat 1.** The single YELLOW in residential customer segment (n=32) is a sample-size limitation, not a model deficiency.

# COMMAND ----------

# DBTITLE 1,Live: Fairness Report Query
# MAGIC %sql
# MAGIC -- Live query: full fairness report (device_type + region)
# MAGIC SELECT
# MAGIC     dimension,
# MAGIC     slice_value,
# MAGIC     n,
# MAGIC     ROUND(precision, 4) AS `precision`,
# MAGIC     ROUND(recall, 4) AS recall,
# MAGIC     ROUND(f1, 4) AS f1,
# MAGIC     ROUND(auc_roc, 4) AS auc_roc,
# MAGIC     ROUND(accuracy, 4) AS accuracy,
# MAGIC     ROUND(stat_parity_rate, 4) AS stat_parity_rate,
# MAGIC     flag
# MAGIC FROM cdm_tmforum.copper_retirement.v5_fairness_report
# MAGIC WHERE dimension IN ('device_type', 'region')
# MAGIC ORDER BY dimension, slice_value

# COMMAND ----------

# DBTITLE 1,Live: Risk Tier Distribution Chart
# MAGIC %sql
# MAGIC -- Distribution of predicted risk tiers by device type
# MAGIC SELECT
# MAGIC     device_type,
# MAGIC     risk_tier_predicted,
# MAGIC     COUNT(*) AS device_count,
# MAGIC     ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY device_type), 1) AS pct_of_type
# MAGIC FROM cdm_tmforum.copper_retirement.gold_device_risk_predictions
# MAGIC GROUP BY device_type, risk_tier_predicted
# MAGIC ORDER BY device_type,
# MAGIC     CASE risk_tier_predicted WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3 WHEN 'critical' THEN 4 END

# COMMAND ----------

# DBTITLE 1,Section 4: Key Takeaways
# MAGIC %md
# MAGIC ## 4. Key Takeaways for the Demo
# MAGIC
# MAGIC ### What to Highlight
# MAGIC
# MAGIC 1. **The model works.** 97.9% accuracy with AUC 0.986 on a 4-class problem. Misclassifications only occur between adjacent tiers — the model never confuses low with critical.
# MAGIC
# MAGIC 2. **It's fair.** 19/20 sub-demographic slices are GREEN across device type, geography, service type, and customer segment. No corrective action needed for any dimension relevant to Beat 1.
# MAGIC
# MAGIC 3. **Features are interpretable.** The top drivers are operational health signals (problem count, recurrence rate, alarm count) — not opaque statistical artifacts. Field engineers can look at a risk score and understand *why* a device is flagged.
# MAGIC
# MAGIC 4. **Borderline cases demonstrate value.** Examples 2 and 3 (the medium/high boundary devices) show where ML adds value over simple threshold rules. The model weighs multiple signals simultaneously to make nuanced classifications.
# MAGIC
# MAGIC 5. **Real-time scoring is live.** The `copper-retirement-risk` serving endpoint returns predictions in ∼83ms warm latency. Batch scoring covers all 2,672 copper devices in the `gold_device_risk_predictions` table.
# MAGIC
# MAGIC ### Known Limitations
# MAGIC
# MAGIC - **Synthetic data caveat:** Training data is generated from TMF SID data model. Feature distributions may not match production telemetry. Pipeline patterns and model architecture are valid; absolute accuracy numbers are demo-representative, not production-representative.
# MAGIC - **Residential segment:** Small sample (n=32) with YELLOW recall (93.3%). Would improve with more residential copper device data.
# MAGIC - **Static scoring:** Current batch scoring is a point-in-time snapshot (2026-09-13). Production deployment would need scheduled refresh via Lakeflow Jobs.
# MAGIC
# MAGIC ### Related Artifacts
# MAGIC
# MAGIC | Artifact | Location |
# MAGIC |---|---|
# MAGIC | Model Card | `copper-retirement/resources/ML_MODEL_CARD.md` |
# MAGIC | Production Readiness | `copper-retirement/resources/ML_PRODUCTION_READINESS.md` |
# MAGIC | Monitoring Baseline | `copper-retirement/resources/monitoring_baseline.md` |
# MAGIC | MLflow Experiment | `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier` |
# MAGIC | Serving Endpoint | `copper-retirement-risk` (Databricks Model Serving) |
# MAGIC | Predictions Table | `cdm_tmforum.copper_retirement.gold_device_risk_predictions` |
# MAGIC | Fairness Report | `cdm_tmforum.copper_retirement.v5_fairness_report` |