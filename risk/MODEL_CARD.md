# Model Card — Copper Device Retirement Risk Classifier (Partner Template)

> **Synthetic-data disclosure.** The shipped model (V5) was trained on SYNTHETIC TMF SID demo data for the fictional operator Lakelink Fiber. Metrics below demonstrate the pipeline, not real-world accuracy. Partners MUST retrain on customer data (Section 6) before any production use.

| Item | Value |
| --- | --- |
| UC model | `cdm_tmforum.ml_models.copper_retirement_risk` (parameterize as `${catalog}.ml_models.copper_retirement_risk`) |
| Aliases | `@champion` = v5 (LightGBM, 39 features), `@challenger` = v4 |
| Serving endpoint | `copper-retirement-risk` (CPU Small, scale-to-zero, 100% traffic to v5; health-checked 2026-10-24: READY, 2-row query returned tiers [2, 3]) |
| Inference table | `copper_retirement.risk_model_inference_payload` / unpacked view `risk_inference_unpacked` (99 rows, last request 2026-09-17) |
| Training run | MLflow `0d308b43371249eeb017867da6acf327`, experiment `copper-retirement/experiments/copper_risk_classifier` (3064056660647801) |
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

Top-5 split importance (v5): `problem_count` 1354, `recurring_problem_rate` 1229, `alarm_count` 1147, `complaint_avg_resolution_hours` 655, `device_age_days` 618. Zero importance: `is_support_expired`, `is_past_eol`, `has_software_data` (candidates to drop).

## 4. Performance (v5, holdout 535 devices, 80/20 stratified, seed 42)
| Metric | Value |
| --- | --- |
| AUC-ROC (OvR) | 0.9864 |
| Accuracy | 0.8953 |
| Weighted F1 | 0.8954 |
| 5-fold CV AUC | 0.9789 +/- 0.0046 |
| F1 low / medium / high / critical | 0.901 / 0.907 / 0.894 / 0.841 |
| Recall critical | 0.833 |
| Train AUC | 1.000 (memorization; see limitations) |

Hyperparameters (Optuna, 50 trials): `learning_rate=0.243, max_depth=3, num_leaves=80, n_estimators=489, min_child_samples=22, subsample=0.643, colsample_bytree=0.720`.

**Correction:** `beat1_risk_model_walkthrough` previously quoted 97.9% accuracy; that figure is in-sample over all 2,672 devices (incl. training rows). The holdout accuracy is 0.895.

## 5. Fairness slices
Gate metric: recall on high+critical (`recall_high_crit`) per slice. Flag rules: GREEN >= 0.85, YELLOW 0.75-0.85 or n < 50, RED < 0.75 (blocks promotion).

**Holdout (authoritative, MLflow artifact `fairness_report_v5.json`, 21 slices, 0 red / 0 yellow):**

| Slice | n | AUC | recall_high_crit |
| --- | --- | --- | --- |
| device_type=cpe | 132 | 0.994 | 1.000 |
| device_type=olt | 133 | 0.973 | 0.958 |
| device_type=ont | 123 | 0.986 | 0.932 |
| device_type=patch_panel | 147 | 0.992 | 1.000 |
| service_type (14 slices, n 28-48 each) | 28-48 | 0.950-0.999 | 0.857-1.000 (lowest: messaging 0.857) |
| revenue=high_value | 343 | 0.986 | 0.976 |
| revenue=unknown | 192 | 0.985 | 0.978 |
| state=other | 153 | 0.994 | 0.986 |

All 14 service_type slices are small-sample (n < 50) and should be treated as YELLOW for decisions.

**In-sample (UC table `copper_retirement.v5_fairness_report`, 20 slices, 19 GREEN / 1 YELLOW):** `customer_segment=residential` n=32 recall 0.933, flagged YELLOW_RECALL + YELLOW_SMALL_N. This table scores all 2,672 devices including training rows, so AUCs near 1.0 are inflated; use it for coverage of region/customer_segment only, not for promotion decisions.

## 6. Retraining on customer data (partner procedure)
1. **Build the feature table** `${catalog}.${schema}.copper_risk_features` with `physical_device_id`, the 39 contract columns, label column `risk_tier` (`low/medium/high/critical`), and slice columns `device_type`, `region`, `customer_segment`.
2. **Replace the label (mandatory).** The demo label is a binned composite of percentile ranks of `alarm_count, critical_alarm_rate, service_affecting_rate, sla_breach_count, test_fail_rate, problem_count, recurring_problem_rate`, all of which are also features. A 2026-10-24 smoke test with 19 of 39 features zero-filled still reached holdout AUC 0.989, confirming the model largely re-learns the label formula. Use a real forward-looking outcome instead, e.g. device failure / truck roll / service-affecting outage in the next 90-180 days, binned to tiers by business-agreed thresholds. Features must be computed strictly before the label window (point-in-time).
3. **Run** `beat1_risk_model_walkthrough` Section 5 with widgets `catalog`, `schema`, `feature_table`, `model_name`, `experiment_path`, `register=true`. It validates the contract, trains LightGBM with v5 hyperparameters (re-tune with Optuna on real data), logs metrics + per-slice fairness to MLflow, and registers a new version with alias `@challenger`.
4. **Promotion gate** (challenger -> champion): holdout AUC >= champion AUC - 0.01, critical-tier recall >= 0.80, no RED fairness slice, and a human sign-off recorded in the copper-task-board `decisions` table.
5. **Promote:** `MlflowClient().set_registered_model_alias(model_name, "champion", <version>)`, then update the existing serving endpoint `copper-retirement-risk` served entity to the new version (do not create a new endpoint). Keep the previous champion as `@challenger` for rollback.
6. **Monitor:** inference table logging is on; compare weekly tier distribution vs training distribution and retrain on drift or quarterly.

## 7. Known limitations
* Synthetic training data (uniform/random distributions); not production-representative.
* Label circularity (Section 6.2) inflates all reported metrics.
* 37% of devices lack software lifecycle data; zero-imputation may under-score firmware risk.
* No reproducible feature-build job in the repo: v5 features were assembled in an interactive session (source tag points to a conversation notebook). Follow-up ACC-DE-RISK-FEATURE-TABLE materializes the contract table.
* Region and customer_segment fairness are only available in-sample.

_Maintainer: @ml-engineer. Last updated 2026-10-24 (ACC-ML-MODEL-CARD)._
