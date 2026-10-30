# Model Card — Copper Device Retirement Risk Classifier (Partner Template)

> **Synthetic-data disclosure.** The shipped model (V6) was trained on SYNTHETIC TMF SID demo data for the fictional operator Lakelink Fiber. Metrics below demonstrate the pipeline, not real-world accuracy. Partners MUST retrain on customer data (Section 6) before any production use.

| Item | Value |
| --- | --- |
| UC model | `cdm_tmforum.ml_models.copper_retirement_risk` (parameterize as `${catalog}.ml_models.copper_retirement_risk`) |
| Aliases | `@champion` = v6 (LightGBM, 39 features, promoted 2026-10-26), `@challenger` = v5 (rollback only; chance-level on current labels) |
| Serving endpoint | `copper-retirement-risk` (CPU Small, scale-to-zero). **As of 2026-10-26 the endpoint still pins v5 by version number (re-verified 2026-10-30: state READY / NOT_UPDATING, served entity `copper_retirement_risk` v5; aliases champion=6, challenger=5)**; switching the served entity to v6 needs a human (agent config updates are blocked by the safety gate). Batch scoring uses `@champion` = v6. |
| Inference table | `copper_retirement.risk_model_inference_payload` / unpacked view `risk_inference_unpacked` (99 rows, last request 2026-09-17). Endpoint `auto_capture_config` is not set, so live traffic is not captured. |
| Training run | MLflow `09db5f470eed4d65be526bc8c4d9c63f` (run name `copper_risk_v6_lgbm_balanced_quartiles`), experiment 3064056660647801. Superseded v5 run: `0d308b43371249eeb017867da6acf327` |
| Label | `risk_tier` = balanced quartiles (668 devices per tier) of `composite_risk_score` in `copper_risk_target`. The table was replaced on 2026-09-15 (Delta v23); earlier labels used fixed thresholds. |
| Retrain template | `copper-retirement/beat1_risk_model_walkthrough`, Section 5 (parameterized widgets) |
| Tags | `telco_project=copper-retirement`, `developer=copper-ml` |

## 1. Intended use
* **Use:** rank copper plant devices into risk tiers (`0=low, 1=medium, 2=high, 3=critical`) to sequence copper retirement / harvesting waves, crew planning, and customer migration outreach.
* **Users:** network planning, retirement program office, SI partner delivery teams.
* **Not for:** automated retirement, discontinuance filings, or customer notices without human review. Regulatory obligations (e.g. network change notice under 47 CFR 51.325-51.335, https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-51/subpart-D, register `FED-FCC-NCD-51D`, verified HTTP 200 on 2026-10-24) apply regardless of model output.

## 2. Output
`predict()` returns an int64 tier index (signature output `Tensor(int64, (-1,))`). Probabilities are available from the underlying LightGBM model when loaded via `mlflow.lightgbm`.

## 3. Feature contract (39 numeric inputs, all `double`)
The serving signature enforces these columns, in this order. A partner feature table must supply all 39 (nulls imputed to 0, matching training).

| Domain | Features | Typical source (TMF SID) |
| --- | --- | --- |
| Network alarms | `alarm_count, critical_alarm_rate, service_affecting_rate` | `tmf_resource.alarm` |
| SLA | `sla_breach_count, sla_breach_rate` | `tmf_service.service_problem` / SLA records |
| Test results | `test_fail_rate` | `tmf_resource.resource_test` |
| Service assurance | `problem_count, recurring_problem_rate` | `tmf_service.service_problem` |
| Billing disputes | `dispute_count, escalated_dispute_count, sla_breach_dispute_count, months_since_last_dispute` | `tmf_customer.billing_dispute` |
| Complaints | `complaint_count, complaint_rate_per_month, escalated_complaint_count, high_severity_complaint_count, complaint_avg_resolution_hours` | `tmf_customer.customer_problem` |
| Usage / revenue | `active_months, avg_monthly_usage, avg_monthly_revenue` | usage + billing |
| Device / firmware lifecycle | `device_age_days, firmware_obsolescence_score, days_since_last_patch, days_past_eol, days_past_support_expiry, is_past_eol, is_support_expired, has_vulnerabilities, has_upgrade_blocked, has_upgrade_ineligible, installed_software_count, has_software_data` | `copper_retirement.feature_device_firmware_age` |
| Physical plant | `plant_pair_count, avg_loop_length_ft, avg_splice_count, avg_cable_vintage_year, avg_db_loss, moisture_rate` | `copper_retirement.copper_loop_plant` (aggregated to device) |
| Device metadata | `device_type_encoded` | category code of `device_type` (cpe/olt/ont/patch_panel) |

Top-5 split importance (v6): `problem_count` 3809, `recurring_problem_rate` 3324, `alarm_count` 3011, `test_fail_rate` 2684, `service_affecting_rate` 2532. All five are inputs to the label formula (see 6.2). Zero importance: `is_support_expired`, `is_past_eol`, `has_software_data` (candidates to drop).

## 4. Performance (v6, holdout 535 devices, 80/20 stratified, seed 42, current labels)
| Metric | v6 (champion) | v5 on the same holdout |
| --- | --- | --- |
| Accuracy | 0.899 | 0.329 (chance) |
| Weighted F1 | 0.900 | 0.245 |
| AUC-ROC (OvR) | 0.985 | 0.693 |
| 5-fold CV accuracy (train split) | 0.873 +/- 0.013 | n/a |
| F1 low / medium / high / critical | 0.947 / 0.856 / 0.854 / 0.943 | n/a |
| Recall critical | 0.918 | n/a |
| Train AUC | 1.000 (memorization; see limitations) | n/a |

Hyperparameters (v6, fixed, not tuned): `n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=20, subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0`. Re-tune with Optuna on partner data.

**Why v5 was retired:** v5 was trained on 2026-09-13 against the earlier threshold-based labels. On 2026-09-15, `copper_risk_target` was CREATE OR REPLACE'd with balanced-quartile labels, and only 33.2% of stored tiers match the new ones. v5's published metrics described the old labels and are no longer valid. Nothing re-validated the champion after the label change (see 6.6).

## 5. Fairness slices
Gate metric: recall on high+critical (`recall_high_crit`) per slice. Flag rules: GREEN >= 0.85, YELLOW 0.75-0.85 or n < 50, RED < 0.75 (blocks promotion).

**v6 holdout (authoritative; MLflow artifact `fairness_report_v6.json` on run 09db5f47..., 72 slices; 0 RED / 0 YELLOW among slices with n >= 30; slices with n < 30 are marked INSUFFICIENT_N):**

| Slice | n | accuracy | recall_high_crit |
| --- | --- | --- | --- |
| device_type=cpe | 138 | 0.891 | 0.984 |
| device_type=olt | 142 | 0.880 | 0.918 |
| device_type=ont | 130 | 0.908 | 0.984 |
| device_type=patch_panel | 125 | 0.920 | 0.925 |
| region (Midwest/Northeast/Southeast/Southwest/West) | 52-135 | 0.885-0.906 | 0.898-1.000 |
| service_type=voice | 45 | 0.911 | 1.000 |
| service_type=broadband / fixed_line | 17 / 19 | 0.941 / 0.895 | 0.909 / 0.900 (INSUFFICIENT_N) |
| service_type=unknown (no service allocation) | 454 | 0.896 | 0.951 |
| state (50 states, n 3-19 each) | 3-19 | 0.70-1.00 | 0.625-1.000 (all INSUFFICIENT_N; lowest MA 0.625, FL/NY 0.667) |
| customer_segment (8 named segments, n 1-17) | 1-17 | 0.80-1.00 | 0.80-1.00 (INSUFFICIENT_N) |

State, customer_segment and most service_type slices are too small to support fairness claims on the 2,672-device demo. Partners with real fleets should gate on state and service_type slices with n >= 30. The legacy `copper_retirement.v5_fairness_report` table is in-sample and v5-only. Do not use it.

## 6. Retraining on customer data (partner procedure)
1. **Build the feature table** `${catalog}.${schema}.copper_risk_features` with `physical_device_id`, the 39 contract columns, label column `risk_tier` (`low/medium/high/critical`), and slice columns `device_type`, `region`, `customer_segment`.
2. **Replace the label (mandatory).** The demo label is a binned composite of percentile ranks of `alarm_count, critical_alarm_rate, service_affecting_rate, sla_breach_count, test_fail_rate, problem_count, recurring_problem_rate`, all of which are also features. A 2026-10-24 smoke test with 19 of 39 features zero-filled still reached holdout AUC 0.989, confirming the model largely re-learns the label formula. Use a real forward-looking outcome instead, e.g. device failure / truck roll / service-affecting outage in the next 90-180 days, binned to tiers by business-agreed thresholds. Features must be computed strictly before the label window (point-in-time).
3. **Run** `beat1_risk_model_walkthrough` Section 5 with widgets `catalog`, `schema`, `feature_table`, `model_name`, `experiment_path`, `register=true`. It validates the contract, trains LightGBM with v5 hyperparameters (re-tune with Optuna on real data), logs metrics + per-slice fairness to MLflow, and registers a new version with alias `@challenger`.
4. **Promotion gate** (challenger -> champion): holdout AUC >= champion AUC - 0.01, critical-tier recall >= 0.80, no RED fairness slice, and a human sign-off recorded in the copper-task-board `decisions` table.
5. **Promote:** `MlflowClient().set_registered_model_alias(model_name, "champion", <version>)`, then update the existing serving endpoint `copper-retirement-risk` served entity to the new version (do not create a new endpoint). Keep the previous champion as `@challenger` for rollback.
6. **Monitor and guard against label changes:** (a) Schedule `scripts/batch_score_copper_risk` weekly. Its job `copper-retirement-weekly-batch-scoring` (218377582606212) exists, but it has no tasks, no schedule and no runs. (b) Before every scoring run, compare `@champion` holdout accuracy on the current `copper_risk_target` against the value logged on its MLflow run. Block and alert if it drops by more than 0.05, and also when `DESCRIBE HISTORY copper_risk_target` shows a CREATE OR REPLACE / WRITE newer than the champion's creation time. (c) Enable the endpoint's inference table and put a Lakehouse Monitor (InferenceLog, label_col=risk_tier) on `risk_inference_unpacked`. No monitor exists on any copper risk table today. Retrain on drift or quarterly.

## 7. Known limitations
* Synthetic training data (uniform/random distributions); not production-representative.
* Label circularity (Section 6.2) inflates all reported metrics.
* 37% of devices lack software lifecycle data; zero-imputation may under-score firmware risk.
* The contract feature table `copper_risk_features` is now materialized by `scripts/batch_score_copper_risk` (ACC-DE-RISK-FEATURE-TABLE). v6 was trained on it.
* State and customer_segment slices are too small in the demo (n < 30) for fairness conclusions.
* The feature and label share inputs, so v6's 0.899 accuracy measures how well it re-learns the composite formula. It is not a predictive-validity result.

## 8. Serving SLA and latency targets
These targets were carried over from the retired `resources/ML_MODEL_CARD.md`. They are design targets, not measured SLOs.

| Scenario | Target | Notes |
| --- | --- | --- |
| Single-device scoring (p50) | < 200 ms | Warm endpoint, real-time lookup |
| Single-device scoring (p99) | < 1,000 ms | Warm endpoint |
| Cold start (scale-to-zero) | 60-90 s | Observed about 82 s on 2026-10-29. Pre-warm before demos, or disable scale-to-zero in production. |
| Batch scoring (2,672 devices) | < 30 s | `scripts/batch_score_copper_risk` loads `@champion` directly. It does not call the endpoint. |
| Error rate | < 1% | 5xx or malformed responses |

## 9. Retraining triggers
| Signal | Threshold | Action |
| --- | --- | --- |
| Label or target table rewritten | Any CREATE OR REPLACE / WRITE on the label table newer than the champion | Block scoring (guard in 6.6b) and retrain. This is the failure that made v5 chance-level. |
| Champion accuracy on current labels | Drop > 0.05 vs. the value logged on the MLflow run | Block scoring and retrain |
| AUC-ROC (OvR) | Below 0.95 (v6: 0.985) | Mandatory retrain |
| Critical-tier recall | Below 0.80 (v6: 0.918) | Mandatory retrain |
| Feature drift (PSI) | PSI > 0.2 on any top-10 feature | Investigate, then retrain if confirmed |
| Null rate | Rises > 5 pp on any feature | Fix the pipeline, then retrain |
| New device type | Any type outside {cpe, ont, olt, patch_panel} | Retrain with the expanded set |
| Fairness regression | Any slice with n >= 30 turns RED | Block promotion and investigate |
| Scheduled | Quarterly | Full retrain, re-run fairness, update this card |

## 10. Ethical considerations
* **False positives (over-classified as critical):** can bring a retirement forward for customers who still rely on copper. This matters most where no fiber alternative exists.
* **False negatives (under-classified):** leave degraded plant in service, which raises outage and safety risk.
* **Geographic bias:** rural plant with sparse alarm telemetry may be under-scored. Region slices exist, but rural/urban is not sliced. Partners should add a density slice.
* **Customer vulnerability:** copper-dependent customers (rural, elderly, low-income, medical alert devices, E911 reliance) need a separate customer-impact review before any retirement decision.
* **Mitigation:** no automated retirement. All critical-tier actions need human review, and regulatory notice obligations apply regardless of the score (Section 1).

## 11. Version history
| Version | Date | Notes |
| --- | --- | --- |
| v1-v2 | 2026-09-11 | Initial LightGBM; Optuna tuning |
| v3 | 2026-09-12 | XGBoost challenger |
| v4 | 2026-09-12 | Added complaint, dispute, usage and revenue features. Leaked the target (`composite_risk_score`). Withdrawn. |
| v5 | 2026-09-13 | Added 11 firmware and 6 plant features; leakage fix. Trained on the pre-2026-09-15 threshold labels. Its published metrics are WITHDRAWN: it scores 0.329 accuracy / 0.693 AUC on current labels. Still the version served by the endpoint; now `@challenger`. |
| **v6** | **2026-10-26** | **`@champion`. LightGBM on `copper_risk_features` with current balanced-quartile labels (Section 4).** |

## Consolidation note
This file is the single model card for the risk model. `resources/model_card.md` (demo talking points) and `resources/ML_MODEL_CARD.md` (V5 production card) were merged here on 2026-10-30 (ACC-ML-MODEL-CARD-DEDUP) and reduced to pointer stubs. Both are on the H4 human-delete list. Their V5 metrics and fairness tables were computed on superseded labels and were intentionally not carried over.

_Maintainer: @ml-engineer. Last updated 2026-10-30 (ACC-ML-MODEL-CARD-DEDUP). Previous update 2026-10-26 (ACC-ML-RISK-RETRAIN-V6 / COO-Q-20261026-0550-1)._
