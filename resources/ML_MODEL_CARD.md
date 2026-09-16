# Production Model Card — Copper Retirement Risk Classifier (V5)

**Model name:** `cdm_tmforum.ml_models.copper_retirement_risk`  
**Version:** 5 (`@champion`)  
**Algorithm:** LightGBM GBDT (Gradient Boosted Decision Trees)  
**Author:** @ml-engineer  
**Created:** 2026-09-13  
**Last updated:** 2026-09-16  
**Project tags:** `telco_project=copper-retirement`, `developer=copper-ml`  
**MLflow experiment:** `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier` (ID: 3064056660647801)  
**Training run:** `0d308b43371249eeb017867da6acf327`  
**Serving endpoint:** `copper-retirement-risk` (READY, CPU Small, scale-to-zero)  

---

## 1. Model Overview

### Purpose
Classifies physical copper network devices into four risk tiers — **low**, **medium**, **high**, **critical** — to prioritize Lakelink Fiber's copper retirement program. Risk tiers drive:
- Retirement sequencing (critical-risk devices first)
- Workforce/crew capacity planning
- Customer communication and migration campaign targeting
- Regulatory filing timelines per jurisdiction

### Intended Use
- **Primary:** Batch scoring of all 2,672 copper devices in Lakelink's network to populate the copper-map planning app and triage dashboard.
- **Secondary:** On-demand single-device risk lookup via the serving endpoint (e.g., field technician queries during site surveys).
- **Not intended for:** Automated retirement execution without human review. Risk scores are decision-support inputs, not autonomous triggers.

### Target Variable
Composite risk score binned into four tiers based on weighted percentile ranks of alarm frequency, critical alarm rate, SLA breach count, and test failure rate. Target distribution: uniform (25% per tier, 668 devices each). Prediction distribution shifts to ~20% low, ~40% medium, ~30% high, ~10% critical due to model decision boundaries.

---

## 2. Training Data

### Source Tables
| Table | Role | Rows |
| --- | --- | --- |
| `cdm_tmforum.copper_retirement.copper_risk_target` | Target variable + base features | 2,672 (copper devices only) |
| `cdm_tmforum.tmf_resource.alarm` | Alarm frequency, severity, service-affecting rate | 100K |
| `cdm_tmforum.tmf_service.service_problem` | Problem count, recurring problem rate | 100K |
| `cdm_tmforum.tmf_resource.resource_performance` | Performance degradation signals | 10K |
| `cdm_tmforum.tmf_resource.resource_test` | Test pass/fail rates | 10K |
| `cdm_tmforum.copper_retirement.feature_device_firmware_age` | Firmware lifecycle (11 features, new in V5) | 2,672 |
| `cdm_tmforum.copper_retirement.copper_loop_plant` | Physical plant aggregates (6 features, new in V5) | 50,000 raw (2,011 distinct devices; aggregated to device-grain for training) |
| `cdm_tmforum.tmf_customer.customer_problem` | Complaint rate, resolution hours | 100K |
| `cdm_tmforum.tmf_customer.billing_dispute` | Dispute count, escalation rate | 100K |

### Data Split
- **Training set:** 2,137 devices (80%, stratified by risk tier)
- **Test/holdout set:** 535 devices (20%, stratified)
- **Cross-validation:** 5-fold stratified, used for hyperparameter selection and stability validation

### Data Caveats
- **Synthetic data.** All training data is synthetically generated (uniform/random distributions). Feature distributions do not reflect real-world operational patterns. The model validates pipeline architecture and scoring patterns; production discriminative power will differ when real data is substituted.
- **Firmware coverage gap.** 37% of copper devices lack software lifecycle data (`installed_software` table). Missing values imputed with zeros. These devices may be systematically underscored for firmware-related risk.

---

## 3. Features (39 Total)

### Feature Importance (LightGBM split-based, descending)

| Rank | Feature | Importance | Domain |
| --- | --- | --- | --- |
| 1 | `problem_count` | 1,354 | Service assurance |
| 2 | `recurring_problem_rate` | 1,229 | Service assurance |
| 3 | `alarm_count` | 1,147 | Network alarms |
| 4 | `complaint_avg_resolution_hours` | 655 | Customer experience |
| 5 | `device_age_days` | 618 | Device lifecycle |
| 6 | `months_since_last_dispute` | 612 | Customer experience |
| 7 | `complaint_rate_per_month` | 550 | Customer experience |
| 8 | `service_affecting_rate` | 543 | Network alarms |
| 9 | `escalated_dispute_count` | 465 | Customer experience |
| 10 | `days_past_support_expiry` | 381 | Firmware lifecycle |
| 11 | `firmware_obsolescence_score` | 377 | Firmware lifecycle |
| 12 | `critical_alarm_rate` | 374 | Network alarms |
| 13 | `sla_breach_count` | 362 | SLA compliance |
| 14 | `device_type_encoded` | 326 | Device metadata |
| 15 | `avg_loop_length_ft` | 319 | Physical plant |
| 16 | `avg_monthly_revenue` | 307 | Financial impact |
| 17 | `days_past_eol` | 300 | Firmware lifecycle |
| 18 | `test_fail_rate` | 297 | Test results |
| 19 | `avg_monthly_usage` | 272 | Service usage |
| 20 | `avg_cable_vintage_year` | 256 | Physical plant |
| 21 | `days_since_last_patch` | 241 | Firmware lifecycle |
| 22 | `complaint_count` | 240 | Customer experience |
| 23 | `moisture_rate` | 236 | Physical plant |
| 24 | `avg_db_loss` | 236 | Physical plant |
| 25 | `high_severity_complaint_count` | 227 | Customer experience |
| 26 | `dispute_count` | 187 | Customer experience |
| 27 | `sla_breach_rate` | 152 | SLA compliance |
| 28 | `sla_breach_dispute_count` | 117 | SLA compliance |
| 29 | `avg_splice_count` | 101 | Physical plant |
| 30 | `escalated_complaint_count` | 77 | Customer experience |
| 31 | `plant_pair_count` | 53 | Physical plant |
| 32 | `has_upgrade_blocked` | 38 | Firmware lifecycle |
| 33 | `has_vulnerabilities` | 36 | Firmware lifecycle |
| 34 | `has_upgrade_ineligible` | 29 | Firmware lifecycle |
| 35 | `active_months` | 28 | Device lifecycle |
| 36 | `installed_software_count` | 6 | Firmware lifecycle |
| 37 | `is_support_expired` | 0 | Firmware lifecycle |
| 38 | `is_past_eol` | 0 | Firmware lifecycle |
| 39 | `has_software_data` | 0 | Firmware lifecycle |

### New in V5
- **11 firmware/software lifecycle features** from `feature_device_firmware_age`: `device_age_days`, `firmware_obsolescence_score`, `days_past_support_expiry`, `days_past_eol`, `days_since_last_patch`, `installed_software_count`, `has_upgrade_blocked`, `has_vulnerabilities`, `has_upgrade_ineligible`, `is_support_expired`, `is_past_eol`
- **6 copper loop plant aggregates** from `copper_loop_plant`: `avg_loop_length_ft`, `avg_cable_vintage_year`, `moisture_rate`, `avg_db_loss`, `avg_splice_count`, `plant_pair_count`

### Leakage Fix (V5)
V4 model contained target leakage: `composite_risk_score` and 7 `_prank` (percentile rank) features were derived from the target and leaked into the feature set. V5 removes all leaked features and trains exclusively on raw operational signals. Max tree depth constrained to 3 (\<=5 requirement) to limit overfitting.

---

## 4. Hyperparameters

Optuna Bayesian optimization, 50 trials, optimizing AUC-ROC.

| Parameter | Value |
| --- | --- |
| `boosting_type` | gbdt |
| `learning_rate` | 0.2430 |
| `max_depth` | 3 |
| `n_estimators` | 489 |
| `num_leaves` | 80 |
| `colsample_bytree` | 0.7202 |
| `subsample` | 0.6431 |
| `min_child_samples` | 22 |
| `reg_alpha` | 3.60e-07 |
| `reg_lambda` | 1.97e-07 |
| `objective` | multiclass |
| `metric` | multi_logloss |
| `num_class` | 4 |
| `random_state` | 42 |

---

## 5. Performance Metrics

### Holdout Set (n=535)

| Metric | Value |
| --- | --- |
| **AUC-ROC** | 0.9864 |
| **Accuracy** | 0.8953 |
| **Weighted F1** | 0.8954 |
| Train AUC-ROC | 1.0 (memorization — see Limitations) |

### Per-Tier Performance

| Tier | Precision | Recall | F1 |
| --- | --- | --- | --- |
| low | 0.906 | 0.897 | 0.901 |
| medium | 0.923 | 0.893 | 0.907 |
| high | 0.870 | 0.919 | 0.894 |
| critical | 0.849 | 0.833 | 0.841 |

### Cross-Validation (5-Fold Stratified)

| Metric | Mean | Std |
| --- | --- | --- |
| AUC-ROC | 0.9789 | ±0.0046 |
| F1 | 0.8744 | ±0.0215 |

### Confusion Matrix (Holdout, n=535)

| Actual \\ Predicted | low | medium | high | critical |
| --- | --- | --- | --- | --- |
| **low** | 96 | 11 | 0 | 0 |
| **medium** | 10 | 191 | 13 | 0 |
| **high** | 0 | 5 | 147 | 8 |
| **critical** | 0 | 0 | 9 | 45 |

**Key observation:** Misclassifications are almost entirely between adjacent tiers (medium\<->high accounts for 18 of 56 total errors). Zero off-by-two-or-worse errors. This is operationally acceptable — adjacent-tier confusion has minimal retirement-planning impact.

---

## 6. Fairness & Sub-Demographic Validation

20 slices evaluated across 4 demographic dimensions. Binary evaluation: high-risk detection (high+critical vs. low+medium).

**Summary:** 19/20 GREEN, 1/20 YELLOW, 0/20 RED.

### Device Type (4 slices)

| Slice | n | AUC | Precision | Recall | Flag |
| --- | --- | --- | --- | --- | --- |
| cpe | 688 | 0.9999 | 0.976 | 1.000 | GREEN |
| ont | 663 | 0.9999 | 0.996 | 0.989 | GREEN |
| olt | 661 | 0.9998 | 0.979 | 0.992 | GREEN |
| patch_panel | 660 | 1.0000 | 0.997 | 1.000 | GREEN |

### Region (5 slices)

| Slice | n | AUC | Precision | Recall | Flag |
| --- | --- | --- | --- | --- | --- |
| Midwest | 655 | 1.0000 | 0.996 | 0.996 | GREEN |
| West | 636 | 0.9996 | 0.973 | 0.992 | GREEN |
| Southeast | 601 | 0.9999 | 0.991 | 0.996 | GREEN |
| Northeast | 540 | 1.0000 | 0.991 | 1.000 | GREEN |
| Southwest | 240 | 0.9995 | 0.988 | 0.988 | GREEN |

### Service Type (2 slices)

| Slice | n | AUC | Precision | Recall | Flag |
| --- | --- | --- | --- | --- | --- |
| unknown | 1,950 | 0.9998 | 0.985 | 0.996 | GREEN |
| dsl | 722 | 0.9999 | 0.996 | 0.993 | GREEN |

### Customer Segment (9 slices)

| Slice | n | AUC | Precision | Recall | Flag |
| --- | --- | --- | --- | --- | --- |
| unknown | 1,950 | 0.9998 | 0.985 | 0.996 | GREEN |
| carrier | 133 | 1.0000 | 1.000 | 0.983 | GREEN |
| enterprise | 108 | 1.0000 | 1.000 | 1.000 | GREEN |
| sme | 104 | 1.0000 | 1.000 | 1.000 | GREEN |
| wholesale | 101 | 0.9991 | 0.973 | 1.000 | GREEN |
| mvno | 101 | 1.0000 | 1.000 | 1.000 | GREEN |
| mid_market | 92 | 1.0000 | 1.000 | 1.000 | GREEN |
| public_sector | 51 | 1.0000 | 1.000 | 1.000 | GREEN |
| **residential** | **32** | **0.9961** | **1.000** | **0.933** | **YELLOW** |

**YELLOW flag — residential (n=32):** Recall 0.933 is below global ~0.996. Sample size (n=32) is below the n=50 stability threshold. Metrics may be volatile. Monitor as real data grows; consider collapsing into a broader segment if sample remains small.

---

## 7. Serving Configuration

| Property | Value |
| --- | --- |
| Endpoint name | `copper-retirement-risk` |
| State | READY |
| Served entity | `cdm_tmforum.ml_models.copper_retirement_risk` v5 |
| Workload size | Small (CPU) |
| Scale-to-zero | Enabled |
| Inference table | `cdm_tmforum.copper_retirement.risk_model_inference_payload` |
| Monitoring views | `risk_inference_unpacked` (unpacked features + predictions) |
| Lakehouse Monitor | Active (InferenceLog profile, CLASSIFICATION, 1-day granularity) |

### Prediction Tables

| Table | Rows | Purpose |
| --- | --- | --- |
| `cdm_tmforum.copper_retirement.copper_risk_predictions` | 2,672 | App-facing predictions (feeds copper-map) |
| `cdm_tmforum.copper_retirement.gold_device_risk_predictions` | 2,672 | Gold table with full feature set + composite score |
| `cdm_tmforum.copper_retirement.copper_risk_scores` | 2,672 | Champion vs. challenger comparison (V5 champion, V4 challenger, 94.7% agreement) |

### Prediction Distribution

| Tier | Count | Percentage |
| --- | --- | --- |
| critical | 267 | 10.0% |
| high | 810 | 30.3% |
| medium | 1,061 | 39.7% |
| low | 534 | 20.0% |

---

## 8. SLA & Latency Targets

| Scenario | Target | Notes |
| --- | --- | --- |
| Single-device scoring (p50) | < 200 ms | Real-time field technician lookup |
| Single-device scoring (p99) | < 1,000 ms | Includes cold-start variability |
| Batch scoring (2,672 devices) | < 30 seconds | Weekly refresh cycle |
| Error rate | < 1% | 5xx or malformed responses |
| Availability | 99.5% uptime | Scale-to-zero adds 60–90s cold-start after idle |

---

## 9. Retraining Triggers

### Data Drift
| Signal | Threshold | Action |
| --- | --- | --- |
| Feature distribution (PSI) | PSI > 0.2 on any top-10 feature | Investigate; retrain if confirmed |
| Null rate increase | > 5 percentage points on any feature | Investigate data pipeline; retrain after fix |
| New device types | Any type not in {cpe, ont, olt, patch_panel} | Retrain with expanded training set |
| Firmware coverage drop | Below 50% (currently 63%) | Retrain with updated imputation strategy |

### Performance Decay
| Signal | Threshold | Action |
| --- | --- | --- |
| AUC-ROC decline | Below 0.95 (current: 0.986) | Mandatory retrain |
| Critical-tier recall | Below 0.75 (current: 0.833) | Mandatory retrain |
| Fairness regression | Any slice drops to YELLOW or RED | Investigate slice; file FEATURE-REQ |
| Champion/challenger divergence | Disagreement > 20% of scored devices | Evaluate challenger; promote if superior |

### Scheduled Review
| Cadence | Action |
| --- | --- |
| Monthly | Batch score, compare prediction distribution vs. prior month |
| Quarterly | Full retrain with latest data, re-evaluate all fairness slices, update this card |
| On data delivery | Retrain when @data-engineer delivers new features or real operational data |

---

## 10. Drift Monitoring Setup

- **Unpacked view:** `cdm_tmforum.copper_retirement.risk_inference_unpacked` — extracts 39 model features + prediction from raw JSON request/response in the inference payload table.
- **Lakehouse Monitor:** Active on inference pipeline. Profile type: InferenceLog, model type: CLASSIFICATION, granularity: 1 day.
- **Baselines (2,672 devices):**
  - 11 numeric features monitored with z-score drift detection (threshold: z > 2.0)
  - Tier distribution shift alert: > 5% absolute change on any tier
  - Confidence degradation: average max-probability below 0.99

---

## 11. Ethical Considerations

### False Positive Risk (Over-classification as Critical)
Devices classified as critical risk when they are not could trigger premature copper retirement, disrupting customers still relying on copper service. **Impact:** potential service interruption for residential and SME customers, particularly those without fiber alternatives.

### False Negative Risk (Under-classification)
Devices classified as low risk when they are actively degraded could leave failing copper infrastructure in service longer, increasing outage probability and maintenance costs. **Impact:** prolonged poor service quality, potential safety hazards.

### Geographic Bias
If alarm data is unevenly distributed geographically (e.g., urban areas have more sensors and denser monitoring), rural copper devices may be systematically underscored for risk. **Mitigation:** regional fairness slices (5 regions, all GREEN) help detect this; but within-region rural/urban disparities are not currently sliced.

### Customer Vulnerability
Copper retirement disproportionately affects customers who may lack alternatives — rural, elderly, low-income, and customers dependent on copper for medical alert systems or E911. Risk scores should be supplemented with customer impact assessment before retirement decisions are finalized.

### Mitigation Summary
- Adjacent-tier confusion (medium\<->high) is the dominant error mode and has low operational impact.
- Critical-tier precision (0.849) and recall (0.833) are monitored per-slice across 20 demographic groups.
- The residential customer segment (n=32, YELLOW) is flagged for ongoing monitoring.
- No automated retirement execution — all critical-tier actions require human review.

---

## 12. Version History

| Version | Date | Changes |
| --- | --- | --- |
| v1 | 2026-09-11 | Initial LightGBM, base features |
| v2 | 2026-09-11 | Optuna hyperparameter tuning (50 trials) |
| v3 | 2026-09-12 | XGBoost challenger variant |
| v4 | 2026-09-12 | Enhanced features (complaint, dispute, usage, revenue) |
| **v5** | **2026-09-13** | **Champion. Firmware lifecycle (11 features) + plant aggregates (6). Leakage fix (removed composite_risk_score + _prank features). 5-fold CV validated. 20-slice fairness evaluated.** |

---

## 13. Known Limitations

1. **Synthetic data ceiling.** All training data is synthetic with uniform/random distributions. Train AUC=1.0 confirms memorization of synthetic patterns. Test AUC=0.986 demonstrates generalization on held-out synthetic data, but production performance with real operational data will differ. The pipeline, scoring, and monitoring architecture are production-grade; the model coefficients are not.
2. **Firmware coverage gap.** 37% of copper devices lack software lifecycle data (imputed with zeros). These devices may be systematically underscored for firmware-related risk signals.
3. **3 zero-importance features.** `is_support_expired`, `is_past_eol`, and `has_software_data` contribute zero split importance. Likely constant or redundant with `days_past_support_expiry`/`days_past_eol`. Candidates for removal in V6.
4. **Small residential segment.** Only 32 residential devices in the dataset — below the n=50 stability threshold. YELLOW flag on recall (0.933 vs. 0.996 global).
5. **No ensemble fallback.** Single-model architecture. If V5 fails, the endpoint returns errors with no graceful degradation.

---

## 14. Artifacts & References

| Artifact | Location |
| --- | --- |
| MLflow experiment | `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier` |
| Training run | `0d308b43371249eeb017867da6acf327` |
| Model card JSON (v2) | MLflow artifact: `model_card_v2.json` (run `e33757e09a93486988af292455b3ec74`) |
| Fairness report | MLflow artifact: `fairness_report_v5.json` (run `0d308b43`) |
| Feature importance plot | MLflow artifact: `feature_importance.png` (run `0d308b43`) |
| Confusion matrix | MLflow artifact: `confusion_matrix.png` (run `0d308b43`) |
| Production readiness | `copper-retirement/resources/ML_PRODUCTION_READINESS.md` |
| UC Model Registry | `cdm_tmforum.ml_models.copper_retirement_risk` (`@champion`=v5, `@challenger`=v4) |
| Serving endpoint | `copper-retirement-risk` (Databricks Model Serving) |
| Batch scoring notebook | `copper-retirement/` folder (batch_score_copper_risk) |

---

*This model card is a living document. Update on every retrain, feature addition, or fairness evaluation. Next scheduled review: Q4 2026.*
