# ML Production Readiness Checklist — Copper Retirement Risk Model (V5)

**Author:** @ml-engineer  
**Date:** 2026-09-15  
**Model:** `cdm_tmforum.ml_models.copper_retirement_risk` v5  
**Endpoint:** `copper-retirement-risk`  
**Project tags:** `telco_project=copper-retirement`, `developer=copper-ml`

---

## 1. Serving Endpoint Configuration

| Check | Status | Detail |
| --- | --- | --- |
| Endpoint state | PASS | READY, NOT_UPDATING |
| Served entity | PASS | `copper_retirement_risk-5` → model v5 |
| Scale-to-zero | PASS | Enabled — cost-efficient for demo/batch workloads |
| Workload size | PASS | Small (CPU) — appropriate for 2,672-device batch scoring |
| Endpoint tags | PASS | `project=copper-retirement`, `developer=copper-ml` |
| Auto-scaling config | REVIEW | Scale-to-zero only. No min/max replica config. For production burst traffic, consider setting `min_provisioned_throughput` to avoid cold-start latency |

### Action Items — Endpoint
- **[ACTION-1]** If real-time scoring is needed (e.g., map app on-demand risk lookup), configure `min_provisioned_throughput` > 0 to eliminate cold-start delay (~60-90s on first request after idle)
- **[ACTION-2]** Add health-check alerting: monitor `copper-retirement-risk` endpoint for 5xx rates > 1% and latency p99 > 2s

---

## 2. Inference Table Logging

| Check | Status | Detail |
| --- | --- | --- |
| auto_capture_config | FAIL | `None` — endpoint does NOT have built-in inference logging enabled |
| Payload table exists | PASS | `cdm_tmforum.copper_retirement.risk_model_inference_payload` (Delta, clustered by `request_date`, CDF enabled) |
| Payload row count | WARN | 3 rows only (all from 2026-09-14) — appears to be manual test data, not continuous capture |
| Payload schema | PASS | Includes `databricks_request_id`, `request`, `response`, `status_code`, `execution_duration_ms`, `requester` |

### Action Items — Inference Logging
- **[ACTION-3] CRITICAL:** Enable `auto_capture_config` on the endpoint so every inference request is automatically logged. Without this, there is no production audit trail and no data for drift detection. CEO should update endpoint config:
  ```
  auto_capture_config:
    catalog_name: cdm_tmforum
    schema_name: copper_retirement
    table_name_prefix: risk_model
    enabled: true
  ```
- **[ACTION-4]** After enabling, validate that subsequent requests appear in the payload table within 5 minutes

---

## 3. Model Registry & Versioning

| Check | Status | Detail |
| --- | --- | --- |
| UC Model registered | PASS | `cdm_tmforum.ml_models.copper_retirement_risk` — 5 versions |
| Champion alias | PASS | `@champion` → v5 (LightGBM, 39 features, AUC 0.986) |
| Challenger alias | PASS | `@challenger` → v4 (LightGBM, 35 features — superseded by v5 leakage fix) |
| Model description | PASS | Comprehensive: algorithm, feature count, metrics, fairness status, deployment note |
| Model tags | PASS | `telco_project=copper-retirement`, `developer=copper-ml`, `test_auc_roc=0.9864` |
| Version history | PASS | v1 (initial) → v2 (Optuna-tuned) → v3 (XGBoost challenger) → v4 (enhanced features) → v5 (firmware + leakage fix) — clean progression |
| Input signature | REVIEW | Registered via `mlflow.register_model` — verify signature matches current feature schema |

### Action Items — Registry
- **[ACTION-5]** Verify model input signature matches the 39-feature schema used in production scoring. Run `mlflow.models.get_model_info()` to confirm
- **[ACTION-6]** Consider archiving v1-v3 (superseded) to reduce registry clutter while preserving audit trail

---

## 4. Model Card Completeness

| Check | Status | Detail |
| --- | --- | --- |
| Logged as MLflow artifact | PASS | `model_card.json` attached to run `0d308b43` |
| Algorithm documented | PASS | LightGBM GBDT, Optuna 50-trial |
| Training data lineage | PASS | `copper_risk_target` + 4 feature tables + firmware_age + plant aggregates |
| Feature count | PASS | 39 features (11 new in v5: firmware lifecycle) |
| Performance metrics | PASS | AUC 0.986, accuracy 0.895, per-tier F1 (low=0.901, medium=0.907, high=0.894, critical=0.841) |
| Known limitations | PASS | Synthetic data caveat, 63% firmware coverage, train AUC=1.0 memorization |
| Top features | PASS | problem_count, recurring_problem_rate, alarm_count, complaint_avg_resolution_hours, device_age_days |
| Retraining triggers | FAIL | Only says "Retrain on new feature delivery" — no quantitative drift or decay thresholds |
| SLA / latency targets | FAIL | Not documented |
| Ethical considerations | FAIL | No section on potential harms of risk misclassification (e.g., premature copper retirement affecting vulnerable customers) |

### Action Items — Model Card
- **[ACTION-7]** Add retraining trigger criteria (see Section 7 below)
- **[ACTION-8]** Add SLA section: target p50 latency < 200ms, p99 < 1s for single-device scoring; batch (2,672 devices) < 30s
- **[ACTION-9]** Add ethical considerations section documenting: (a) false-positive critical risk could trigger premature retirement affecting customers still on copper, (b) false-negative could leave degraded infrastructure in service longer, (c) geographic bias risk if alarm data is unevenly distributed

---

## 5. Fairness & Sub-Demographic Validation

| Check | Status | Detail |
| --- | --- | --- |
| Fairness report logged | PASS | `fairness_report_v5.json` as MLflow artifact |
| Total slices evaluated | PASS | 21 slices across device_type, service_type, geography, customer_segment, alarm_recency |
| Red flags | PASS | 0 red flags |
| Yellow flags | PASS | 0 yellow flags |
| All GREEN | PASS | 21/21 slices GREEN |
| Small-sample warnings | REVIEW | Several service_type slices (broadband=29, data_roaming=28, cloud=37) flagged as "GREEN (small sample)" — metrics may be unstable |
| Slice performance range | PASS | AUC range: 0.949 (data_roaming) to 0.999 (iot) — no slice below 0.94 |

### Confusion Matrix Summary (Holdout, n=535)

| Actual \\ Predicted | low | medium | high | critical |
| --- | --- | --- | --- | --- |
| low | 96 | 11 | 0 | 0 |
| medium | 10 | 191 | 13 | 0 |
| high | 0 | 5 | 147 | 8 |
| critical | 0 | 0 | 9 | 45 |

Key observation: misclassifications are almost entirely between adjacent tiers (medium↔high accounts for 18 of 56 total errors). No off-by-two or worse errors. This is operationally acceptable — adjacent-tier confusion has minimal retirement-planning impact.

### Action Items — Fairness
- **[ACTION-10]** Monitor small-sample slices (n<50) as real data replaces synthetics. If slice sample sizes remain small, consider collapsing into broader groups

---

## 6. Scoring Pipeline & Gold Tables

| Check | Status | Detail |
| --- | --- | --- |
| `copper_risk_predictions` | PASS | 2,672 rows — all copper devices scored. Columns: physical_device_id, risk_tier, predicted_risk_tier, probabilities, model_version, scored_at |
| `copper_risk_scores` | PASS | 2,672 rows — champion + challenger comparison. Columns: champion_prediction, challenger_prediction, models_agree flag |
| `gold_device_risk_predictions` | PASS | 2,672 rows — full gold table with composite_risk_score, feature_set, scored_date |
| Batch scoring freshness | WARN | `scored_at` / `scored_date` from initial batch run only. No automated refresh pipeline |
| Champion/challenger agreement | REVIEW | `models_agree` column present but agreement rate not monitored |

### Action Items — Scoring Pipeline
- **[ACTION-11]** Create a Lakeflow Job to run batch scoring weekly (or on DLP pipeline refresh): load champion model, score all copper devices, append to `copper_risk_predictions` with timestamp. Tag @devops for job creation.
- **[ACTION-12]** Add a champion/challenger disagreement alert: if `models_agree = FALSE` rate exceeds 20%, trigger review for potential model refresh

---

## 7. Retraining Trigger Criteria

The model card currently lacks quantitative retraining thresholds. Recommended criteria:

### 7.1 Data Drift Triggers
| Signal | Threshold | Action |
| --- | --- | --- |
| Feature distribution shift (PSI) | PSI > 0.2 on any top-10 feature | Investigate; retrain if confirmed |
| Null rate increase | > 5pp increase on any feature vs. training baseline | Investigate data pipeline; retrain after fix |
| New device types appearing | Any `device_type` not in {cpe, ont, olt, patch_panel} | Retrain with expanded training set |
| Feature coverage drop | Firmware coverage drops below 50% (currently 63%) | Retrain with updated imputation strategy |

### 7.2 Performance Decay Triggers
| Signal | Threshold | Action |
| --- | --- | --- |
| Holdout AUC-ROC decline | AUC drops below 0.95 (currently 0.986) | Mandatory retrain |
| Per-tier recall (critical) | Recall drops below 0.75 (currently 0.833) | Mandatory retrain — critical devices must not be missed |
| Fairness regression | Any slice drops to YELLOW or RED | Investigate slice; file FEATURE-REQ if data gap |
| Champion/challenger divergence | Disagreement > 20% of scored devices | Evaluate challenger; promote if superior |

### 7.3 Scheduled Review
| Cadence | Action |
| --- | --- |
| Monthly | Run batch scoring, compare predictions vs. prior month for stability |
| Quarterly | Full retrain with latest data, re-evaluate fairness slices, update model card |
| On data delivery | Retrain when @data-engineer delivers new features (e.g., real operational data replacing synthetics) |

---

## 8. MLflow Experiment & Tracking

| Check | Status | Detail |
| --- | --- | --- |
| Experiment exists | PASS | `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier` (ID: 3064056660647801) |
| Experiment tags | PASS | `project=copper-retirement`, `developer=copper-ml`, `telco_project=copper-retirement` |
| Run artifacts | PASS | confusion_matrix.json/.png, fairness_report_v5.json, feature_importance.json/.png, model_card.json |
| CV metrics logged | PASS | 5-fold CV AUC: 0.979 ± 0.005 |
| Slice runs | PASS | 21 slice child runs logged (device_type, service_type, geography, customer_segment, alarm_recency) |
| Optuna params | PASS | Best trial: lr=0.243, max_depth=3, n_estimators=489, num_leaves=80 |

---

## 9. Known Risks & Limitations

1. **Synthetic data ceiling:** All training data is synthetic (uniform/random distributions). Real-world discriminative power is unknown. Train AUC=1.0 confirms memorization of synthetic patterns. Test AUC=0.986 shows pattern generalization on held-out synthetic data, but production performance will differ.
2. **Firmware coverage gap:** 37% of copper devices lack software lifecycle data (imputed with zeros). These devices may be systematically misscored.
3. **No real-time drift monitoring:** Without inference table auto-capture, there is no mechanism to detect input drift or prediction distribution shift.
4. **Single-model architecture:** No ensemble or fallback model. If V5 fails, the endpoint serves errors (no graceful degradation).
5. **Batch-only scoring:** No automated refresh pipeline. Predictions are static until manual re-scoring.

---

## 10. Overall Readiness Summary

| Category | Grade | Key Gap |
| --- | --- | --- |
| Endpoint config | B | Scale-to-zero good, but no cold-start mitigation or alerting |
| Inference logging | D | auto_capture NOT enabled — only 3 manual test rows exist |
| Model registry | A | Clean versioning, aliases set, tags correct |
| Model card | C+ | Solid ML content, missing production ops sections (drift, SLA, ethics) |
| Fairness | A | 21/21 slices GREEN, no red/yellow flags |
| Scoring pipeline | C | Tables exist but no automated refresh or disagreement alerting |
| Retraining plan | D | No quantitative triggers defined (now proposed above) |
| Experiment tracking | A | Comprehensive artifacts, slice runs, CV metrics |

**Overall: NOT YET PRODUCTION-READY.** The model itself is strong (AUC 0.986, fairness validated), but production operations infrastructure has gaps. Critical items: enable inference table auto-capture [ACTION-3], implement batch scoring refresh [ACTION-11], and codify retraining triggers [ACTION-7].

---

## 11. Action Item Summary (Priority Order)

| ID | Priority | Owner | Description |
| --- | --- | --- | --- |
| ACTION-3 | CRITICAL | CEO/@devops | Enable `auto_capture_config` on `copper-retirement-risk` endpoint |
| ACTION-11 | HIGH | @devops | Create weekly batch scoring Lakeflow Job |
| ACTION-7 | HIGH | @ml-engineer | Update model card with retraining triggers from Section 7 |
| ACTION-12 | HIGH | @devops | Add champion/challenger disagreement alert |
| ACTION-2 | MEDIUM | @devops | Add endpoint health-check alerting (5xx rate, latency p99) |
| ACTION-8 | MEDIUM | @ml-engineer | Add SLA section to model card |
| ACTION-9 | MEDIUM | @ml-engineer | Add ethical considerations section to model card |
| ACTION-1 | LOW | CEO/@devops | Configure min_provisioned_throughput if real-time scoring needed |
| ACTION-4 | LOW | @ml-engineer | Validate inference logging after ACTION-3 |
| ACTION-5 | LOW | @ml-engineer | Verify model input signature matches 39-feature schema |
| ACTION-6 | LOW | @ml-engineer | Archive superseded model versions v1-v3 |
| ACTION-10 | LOW | @ml-engineer | Monitor small-sample fairness slices as data grows |

---

*Generated by @ml-engineer automated production readiness audit, 2026-09-15. Next review: after ACTION-3 and ACTION-11 are completed.*