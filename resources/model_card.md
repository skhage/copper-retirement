> **SUPERSEDED 2026-10-30 (ACC-ML-MODEL-CARD-DEDUP). Do not use. The single model card is [risk/MODEL_CARD.md](../risk/MODEL_CARD.md).** Everything below describes V5 on labels that were replaced on 2026-09-15, and those metrics are WITHDRAWN. The original is preserved in git commit 20598e7. This file is on the H4 human-delete list.

# (SUPERSEDED) Copper Retirement Risk Model — Demo Talking Points

> **Beat 1 Risk Walkthrough** | Presenter reference for the copper-retirement-risk V5 model
> Updated: 2026-09-21 by @ml-engineer

---

## Model at a Glance

| Property | Value |
| --- | --- |
| **Model** | `cdm_tmforum.ml_models.copper_retirement_risk` v5 (`@champion`) |
| **Algorithm** | LightGBM GBDT — Optuna-tuned (50 trials) |
| **Scope** | 2,672 copper devices across LakeLink Fiber's network |
| **Target** | 4-tier risk classification: low / medium / high / critical |
| **Serving** | `copper-retirement-risk` endpoint (READY, CPU Small, scale-to-zero) |
| **MLflow Experiment** | `copper_risk_classifier` (run: `0d308b43…`) |
| **Fairness** | 20 demographic slices evaluated — **19 GREEN, 1 YELLOW, 0 RED** |

**Elevator pitch:** _"We score every copper device in the network across 39 operational features — alarms, service problems, firmware age, physical plant condition, and customer impact signals — to classify retirement urgency into four tiers. The model drives wave sequencing: critical-risk devices get retired first, protecting SLA compliance and customer experience."_

---

## Feature Importance — Top 10 with Business Context

These are the top signals the model uses to distinguish risk tiers. Split-count importance from LightGBM.

| Rank | Feature | Importance | Business Explanation |
| --- | --- | --- | --- |
| 1 | `problem_count` | 1,354 | Total service problems linked to the device — the single strongest predictor of retirement urgency. High problem counts signal chronic degradation. |
| 2 | `recurring_problem_rate` | 1,229 | Fraction of problems that recur within 30 days. Repeat failures indicate the device can't be stabilized with maintenance alone — retirement is the fix. |
| 3 | `alarm_count` | 1,147 | Volume of network alarms generated. More alarms = more NOC attention, higher ops cost, and greater outage risk. |
| 4 | `complaint_avg_resolution_hours` | 655 | Average time to resolve customer complaints tied to this device. Long resolution times signal difficult-to-fix underlying copper plant issues. |
| 5 | `device_age_days` | 618 | How long the device has been deployed. Older equipment correlates with outdated firmware, expired support, and physical wear. |
| 6 | `months_since_last_dispute` | 612 | Time since the last billing dispute. Recent disputes tied to service quality suggest active customer dissatisfaction with copper performance. |
| 7 | `complaint_rate_per_month` | 550 | Normalized complaint frequency. Captures the velocity of customer-reported issues — a proxy for deteriorating service quality. |
| 8 | `service_affecting_rate` | 543 | Fraction of alarms that directly impact customer service. Distinguishes nuisance alarms from truly harmful events. |
| 9 | `escalated_dispute_count` | 465 | Number of billing disputes that were escalated — indicates systemic service failures that standard processes couldn't resolve. |
| 10 | `days_past_support_expiry` | 381 | How long since the device firmware lost vendor support. Unsupported devices can't receive security patches or bug fixes — a firmware lifecycle risk signal new in V5. |

**Key narrative:** The model blends four signal domains — **network alarms** (alarm_count, service_affecting_rate), **service assurance** (problem_count, recurring_problem_rate), **customer experience** (complaints, disputes), and **firmware lifecycle** (support expiry, obsolescence score) — giving a 360° view of device health.

---

## Model Performance

### Overall (Holdout Set, n=535)

| Metric | Value |
| --- | --- |
| **AUC-ROC** | **[V5 value withdrawn; see risk/MODEL_CARD.md]** |
| Accuracy | 0.895 |
| Weighted F1 | 0.895 |
| 5-Fold CV AUC | 0.979 ± 0.005 |

### Per-Tier Breakdown

| Risk Tier | Precision | Recall | F1 | Talking Point |
| --- | --- | --- | --- | --- |
| **Critical** | 0.849 | 0.833 | 0.841 | 5 in 6 truly critical devices are caught. The misses land in "high" — still prioritized. |
| **High** | 0.870 | 0.919 | 0.894 | High recall means few dangerous devices slip through to medium/low. |
| **Medium** | 0.923 | 0.893 | 0.907 | Most balanced tier — reliable for mid-priority wave planning. |
| **Low** | 0.906 | 0.897 | 0.901 | Low-risk devices correctly identified; safe to defer retirement. |

### Prediction Distribution (All 2,672 Devices)

| Tier | Devices | % |
| --- | --- | --- |
| Critical | 267 | 10.0% |
| High | 810 | 30.3% |
| Medium | 1,061 | 39.7% |
| Low | 534 | 20.0% |

**Demo talking point:** _"The model identifies \~1,077 devices (40%) as high or critical risk — these are Wave 1 retirement candidates. The remaining 60% can be sequenced over later waves, freeing crew capacity for the most impactful work first."_

---

## Sub-Demographic Fairness Results

The model was evaluated across 20 demographic slices to ensure it doesn't systematically under- or over-predict risk for any subgroup.

### By Device Type (4 slices — all GREEN)

| Device Type | n | AUC | Precision | Recall | Status |
| --- | --- | --- | --- | --- | --- |
| CPE | 688 | 0.9999 | 0.976 | 1.000 | ✅ GREEN |
| ONT | 663 | 0.9999 | 0.996 | 0.989 | ✅ GREEN |
| OLT | 661 | 0.9998 | 0.979 | 0.992 | ✅ GREEN |
| Patch Panel | 660 | 1.0000 | 0.997 | 1.000 | ✅ GREEN |

**Takeaway:** No device-type bias. All four equipment categories perform within tolerance.

### By Region (5 slices — all GREEN)

| Region | n | AUC | Precision | Recall | Status |
| --- | --- | --- | --- | --- | --- |
| Midwest | 655 | 1.0000 | 0.996 | 0.996 | ✅ GREEN |
| West | 636 | 0.9996 | 0.973 | 0.992 | ✅ GREEN |
| Southeast | 601 | 0.9999 | 0.991 | 0.996 | ✅ GREEN |
| Northeast | 540 | 1.0000 | 0.991 | 1.000 | ✅ GREEN |
| Southwest | 240 | 0.9995 | 0.988 | 0.988 | ✅ GREEN |

**Takeaway:** Risk scoring is geographically consistent — no region is systematically over- or under-scored. Important for regulatory filings that require jurisdiction-level fairness.

### By Service Type (2 slices — all GREEN)

| Service Type | n | AUC | Precision | Recall | Status |
| --- | --- | --- | --- | --- | --- |
| DSL | 722 | 0.9999 | 0.996 | 0.993 | ✅ GREEN |
| Unknown | 1,950 | 0.9998 | 0.985 | 0.996 | ✅ GREEN |

### By Customer Segment (9 slices — 8 GREEN, 1 YELLOW)

| Customer Segment | n | AUC | Recall | Status |
| --- | --- | --- | --- | --- |
| Enterprise | 108 | 1.0000 | 1.000 | ✅ GREEN |
| SME | 104 | 1.0000 | 1.000 | ✅ GREEN |
| Carrier | 133 | 1.0000 | 0.983 | ✅ GREEN |
| MVNO | 101 | 1.0000 | 1.000 | ✅ GREEN |
| Mid Market | 92 | 1.0000 | 1.000 | ✅ GREEN |
| Public Sector | 51 | 1.0000 | 1.000 | ✅ GREEN |
| Wholesale | 101 | 0.9991 | 1.000 | ✅ GREEN |
| Unknown | 1,950 | 0.9998 | 0.996 | ✅ GREEN |
| **Residential** | **32** | **0.9961** | **0.933** | ⚠️ **YELLOW** |

**YELLOW flag — Residential (n=32):** Recall dips to 0.933 (vs. 0.996 global). Root cause is small sample size (32 devices, below the n=50 stability threshold). Not a systemic bias — the model simply has limited residential data to learn from. Monitored for improvement as data grows.

**Demo talking point:** _"We tested the model across 20 demographic slices — by equipment type, geography, service type, and customer segment. 19 out of 20 are fully green. The one yellow flag is residential customers, where we only have 32 devices — a sample-size issue, not a model bias issue. No red flags anywhere."_

---

## V5 Improvements Over V4

| Change | Impact |
| --- | --- |
| **Leakage fix** | V4 accidentally included the target variable (composite_risk_score) as a feature, inflating accuracy to 99.8%. V5 removes all leaked features — AUC [withdrawn; see risk/MODEL_CARD.md]. |
| **+11 firmware features** | Device age, firmware obsolescence score, vendor support expiry, patch recency — adds a lifecycle dimension V4 lacked. |
| **+6 plant features** | Loop length, cable vintage, moisture rate, dB loss, splice count — physical infrastructure signals. |
| **Depth cap (max_depth=3)** | Limits overfitting on synthetic data; V4 used depth=8. |
| **5-fold cross-validation** | V5 reports CV AUC (0.979 ± 0.005), confirming stability across folds. |

---

## Production Infrastructure

| Component | Status | Detail |
| --- | --- | --- |
| Serving endpoint | ✅ READY | `copper-retirement-risk`, V5, CPU Small, scale-to-zero |
| Batch predictions | ✅ Active | `copper_risk_predictions` (2,672 rows, feeds copper-map app) |
| Inference logging | ✅ Active | Payload capture to `risk_model_inference_payload` |
| Lakehouse Monitor | ✅ Active | Drift detection on 11 numeric features, 1-day granularity |
| Champion/Challenger | ✅ Active | V5 champion vs. V4 challenger (94.7% agreement) |

---

## Known Caveats (Be Transparent in Demo)

1. **Synthetic data.** All training data is synthetic — the model architecture and pipeline are production-grade, but accuracy numbers reflect synthetic patterns, not real operational telemetry.
2. **Train AUC = 1.0.** The model memorizes training data (expected with synthetics). Test AUC [withdrawn; see risk/MODEL_CARD.md] showed it generalizes within the synthetic distribution.
3. **37% firmware data gap.** Roughly 1 in 3 copper devices lack software lifecycle data — imputed with zeros. These devices may be under-scored on firmware risk.
4. **3 zero-importance features.** `is_support_expired`, `is_past_eol`, `has_software_data` contribute nothing — candidates for removal in V6.
5. **Residential sample.** Only 32 residential devices — too few for reliable slice metrics.

---

## Quick Reference Links

| Asset | Path |
| --- | --- |
| Full model card | `resources/ML_MODEL_CARD.md` |
| MLflow experiment | `/copper-retirement/experiments/copper_risk_classifier` |
| V5 training run | `0d308b43371249eeb017867da6acf327` |
| V5 fairness run | `582ad9444a924e54b504aa2b45657014` |
| Demo walkthrough notebook | `beat1_risk_model_walkthrough` (ID: 3633949023586530) |
| Serving endpoint | `copper-retirement-risk` |
| Gold predictions | `cdm_tmforum.copper_retirement.copper_risk_predictions` |
