# Inference Monitoring Baseline — Copper Retirement Risk Model

> **project:** copper-retirement | **developer:** copper-ml  
> **Generated:** 2026-09-16 | **Agent:** @ml-engineer  
> **Model:** V5 LightGBM (4-class risk classifier)  
> **UC Model:** `cdm_tmforum.ml_models.copper_retirement_risk` version 5  
> **MLflow Run:** `0d308b43371249eeb017867da6acf327`  
> **Scoring Date:** 2026-09-13 (batch scoring of all 2,672 copper devices)  
> **Endpoint:** `copper-retirement-risk`  

---

## Purpose

This document establishes the **reference distributions** for drift detection on the copper retirement risk model. Once inference table auto-capture is enabled (see `ML-ENABLE-INF-CAPTURE`), Lakehouse Monitoring will compare incoming prediction distributions against these baselines to detect:

- **Prediction drift** — shift in risk tier distribution (e.g., sudden spike in critical predictions)
- **Confidence drift** — model uncertainty increasing (lower max_confidence scores)
- **Feature drift** — input feature distributions diverging from training/scoring population
- **Sub-population drift** — device_type or geographic slices shifting disproportionately

**Drift thresholds** (from ML_PRODUCTION_READINESS.md):
- PSI > 0.2 on top features → trigger retraining investigation
- AUC < 0.95 on holdout → performance decay alert
- Critical-tier recall < 0.75 → high-risk misclassification alert

---

## 1. Overall Prediction Distribution

| Risk Tier | Count | % of Total | Avg Confidence | Std Confidence | P05 Conf | P50 Conf | P95 Conf |
|-----------|-------|-----------|----------------|----------------|----------|----------|----------|
| low       | 534   | 20.0%     | 0.9930         | 0.0396         | —        | 1.0000   | —        |
| medium    | 1,061 | 39.7%     | 0.9918         | 0.0477         | —        | 0.9999   | —        |
| high      | 810   | 30.3%     | 0.9919         | 0.0482         | —        | 1.0000   | —        |
| critical  | 267   | 10.0%     | 0.9908         | 0.0486         | —        | 1.0000   | —        |
| **TOTAL** | **2,672** | **100%** | **0.9920** | **0.0464** | **0.9849** | **1.0000** | **1.0000** |

**Expected tier proportions (drift reference):**
- low: 20.0% ± 3%
- medium: 39.7% ± 4%
- high: 30.3% ± 3%
- critical: 10.0% ± 2%

A shift of >5 percentage points in any tier from this baseline warrants investigation.

---

## 2. Per-Class Probability Distributions (Global)

| Metric         | prob_low | prob_medium | prob_high | prob_critical | max_confidence |
|----------------|----------|-------------|-----------|---------------|----------------|
| Mean           | 0.2004   | 0.3974      | 0.3029    | 0.0993        | 0.9920         |
| Std            | 0.3974   | 0.4845      | 0.4559    | 0.2976        | 0.0464         |
| P05            | 0.0      | 0.0         | 0.0       | 0.0           | 0.9849         |
| P10            | 0.0      | 0.0         | 0.0       | 0.0           | 0.9993         |
| P25            | 0.0      | 0.0         | 0.0       | 0.0           | 0.9998         |
| P50 (median)   | 0.0      | 0.00027     | 0.00002   | 0.0           | 1.0000         |
| P75            | 0.00026  | 0.99983     | 0.99968   | 0.0           | 1.0000         |
| P90            | 0.99996  | 0.99999     | 0.99999   | 0.21079       | 1.0000         |
| P95            | 1.0      | 1.0         | 1.0       | 0.99999       | 1.0000         |

**Key observation:** The model is highly confident (>97.5% of predictions have max_confidence > 0.98). The probability distributions are heavily bimodal (near 0 or near 1), reflecting strong LightGBM separation. Drift toward mid-range probabilities (0.3–0.7) would signal degraded discrimination.

---

## 3. PSI Reference Bins — max_confidence

Histogram bins for Population Stability Index calculation:

| Bin [start, start+0.1) | Count | Proportion |
|------------------------|-------|------------|
| [0.5, 0.6)             | 12    | 0.0045     |
| [0.6, 0.7)             | 15    | 0.0056     |
| [0.7, 0.8)             | 16    | 0.0060     |
| [0.8, 0.9)             | 24    | 0.0090     |
| [0.9, 1.0]             | 2,605 | 0.9749     |

**PSI interpretation:** The baseline is extremely concentrated in the [0.9, 1.0] bin. Any meaningful redistribution toward lower bins would produce a large PSI even with small absolute counts. Recommend monitoring the count in [0.5, 0.8) bins — if this exceeds 100 in a batch (vs. baseline 43), investigate.

---

## 4. Distribution by Device Type

### 4a. Tier Distribution

| device_type  | Total | n_low | n_medium | n_high | n_critical | % high+critical |
|-------------|-------|-------|----------|--------|------------|------------------|
| cpe          | 688   | 167   | 270      | 193    | 58         | 36.5%            |
| olt          | 661   | 164   | 254      | 187    | 56         | 36.8%            |
| ont          | 663   | 139   | 265      | 193    | 66         | 39.1%            |
| patch_panel  | 660   | 64    | 272      | 237    | 87         | 49.1%            |

**Drift alert:** patch_panel has notably higher risk concentration (49.1% high+critical vs. 36–39% for others). If this gap narrows or reverses, it signals a population shift.

### 4b. Per-Class Probabilities by Device Type

| device_type  | avg_p_low | std_p_low | avg_p_med | std_p_med | avg_p_high | std_p_high | avg_p_crit | std_p_crit |
|-------------|-----------|-----------|-----------|-----------|------------|------------|------------|------------|
| cpe          | 0.2427    | 0.4272    | 0.3936    | 0.4845    | 0.2808     | 0.4451     | 0.0828     | 0.2732     |
| olt          | 0.2502    | 0.4284    | 0.3834    | 0.4795    | 0.2826     | 0.4470     | 0.0837     | 0.2758     |
| ont          | 0.2096    | 0.4052    | 0.3992    | 0.4858    | 0.2916     | 0.4511     | 0.0996     | 0.2982     |
| patch_panel  | 0.0971    | 0.2930    | 0.4135    | 0.4885    | 0.3578     | 0.4767     | 0.1317     | 0.3375     |

### 4c. Confidence by Device Type

| device_type  | avg_confidence | std_confidence | P05          | P50          | P95          |
|-------------|----------------|----------------|--------------|--------------|---------------|
| cpe          | 0.9920         | 0.0468         | 0.9864       | 1.0000       | 1.0000        |
| olt          | 0.9890         | 0.0574         | 0.9766       | 0.9999       | 1.0000        |
| ont          | 0.9931         | 0.0415         | 0.9834       | 1.0000       | 1.0000        |
| patch_panel  | 0.9938         | 0.0376         | 0.9907       | 1.0000       | 1.0000        |

---

## 5. Distribution by Geography (State)

50 states, all 2,672 devices geocoded (100% join coverage).

### 5a. State-Level Summary (sorted by device count)

| State | Devices | % High+Critical | Avg Conf | Std Conf | Flag |
|-------|---------|-----------------|----------|----------|------|
| SD    | 75      | 40.0%           | 0.9935   | 0.0483   |      |
| DE    | 75      | 48.0%           | 0.9982   | 0.0144   |      |
| AK    | 75      | 42.7%           | 0.9977   | 0.0149   |      |
| OK    | 69      | 37.7%           | 0.9974   | 0.0132   |      |
| WA    | 69      | 37.7%           | 0.9894   | 0.0588   |      |
| UT    | 69      | 37.7%           | 0.9993   | 0.0036   |      |
| NY    | 66      | 45.5%           | 0.9803   | 0.0829   | ⚠    |
| NH    | 64      | 51.6%           | 0.9818   | 0.0771   | ⚠    |
| HI    | 63      | 39.7%           | 0.9908   | 0.0322   |      |
| WI    | 62      | 30.6%           | 0.9896   | 0.0577   |      |
| ND    | 61      | 39.3%           | 0.9985   | 0.0074   |      |
| AZ    | 61      | 44.3%           | 0.9919   | 0.0553   |      |
| TN    | 60      | 45.0%           | 0.9874   | 0.0646   |      |
| IL    | 59      | 44.1%           | 0.9937   | 0.0264   |      |
| NM    | 59      | 30.5%           | 0.9953   | 0.0225   |      |
| MN    | 58      | 32.8%           | 0.9996   | 0.0018   |      |
| NV    | 58      | 29.3%           | 0.9945   | 0.0397   |      |
| CO    | 57      | 47.4%           | 0.9914   | 0.0437   |      |
| WV    | 56      | 35.7%           | 0.9845   | 0.0718   |      |
| SC    | 56      | 35.7%           | 0.9915   | 0.0401   |      |
| MO    | 56      | 44.6%           | 0.9955   | 0.0197   |      |
| OR    | 55      | 29.1%           | 0.9805   | 0.0703   |      |
| GA    | 55      | 34.5%           | 0.9892   | 0.0567   |      |
| IN    | 53      | 60.4%           | 0.9757   | 0.0993   | ⚠⚠   |
| LA    | 53      | 43.4%           | 0.9824   | 0.0672   |      |
| NC    | 53      | 30.2%           | 0.9937   | 0.0408   |      |
| RI    | 53      | 37.7%           | 0.9854   | 0.0563   |      |
| OH    | 51      | 47.1%           | 0.9954   | 0.0204   |      |
| FL    | 51      | 39.2%           | 0.9998   | 0.0004   |      |
| TX    | 51      | 27.5%           | 0.9964   | 0.0199   |      |
| CA    | 50      | 48.0%           | 0.9954   | 0.0320   |      |
| WY    | 50      | 46.0%           | 0.9976   | 0.0132   |      |
| KS    | 50      | 42.0%           | 0.9899   | 0.0594   |      |
| AL    | 49      | 32.7%           | 0.9987   | 0.0056   |      |
| MI    | 48      | 31.3%           | 0.9910   | 0.0528   |      |
| AR    | 48      | 43.8%           | 0.9963   | 0.0155   |      |
| MT    | 47      | 46.8%           | 0.9906   | 0.0377   |      |
| NJ    | 46      | 41.3%           | 0.9967   | 0.0184   |      |
| VA    | 44      | 34.1%           | 0.9990   | 0.0045   |      |
| ID    | 43      | 55.8%           | 0.9838   | 0.0778   | ⚠    |
| MA    | 43      | 39.5%           | 0.9906   | 0.0610   |      |
| NE    | 42      | 42.9%           | 0.9919   | 0.0340   |      |
| ME    | 42      | 50.0%           | 0.9920   | 0.0359   |      |
| MS    | 40      | 45.0%           | 0.9987   | 0.0075   |      |
| IA    | 40      | 40.0%           | 0.9942   | 0.0287   |      |
| VT    | 40      | 27.5%           | 0.9982   | 0.0065   |      |
| MD    | 38      | 44.7%           | 0.9910   | 0.0547   |      |
| CT    | 37      | 35.1%           | 0.9807   | 0.0828   |      |
| KY    | 36      | 44.4%           | 0.9841   | 0.0679   |      |
| PA    | 36      | 36.1%           | 0.9953   | 0.0276   |      |

**⚠ Flagged states (higher variance or extreme risk proportions):**
- **IN (Indiana):** 60.4% high+critical — highest in fleet. Std_conf=0.0993 (highest variance). Monitor for increased volatility.
- **NH (New Hampshire):** 51.6% high+critical, std_conf=0.0771.
- **ID (Idaho):** 55.8% high+critical, std_conf=0.0778.
- **NY (New York):** 45.5% high+critical, std_conf=0.0829 — lower confidence consistency.

---

## 6. Champion vs Challenger Agreement

| Models Agree | Count | %    | Avg Champion Conf | Avg Challenger Conf |
|-------------|-------|------|-------------------|---------------------|
| true        | 2,531 | 94.7%| 0.9955            | 0.8995              |
| false       | 141   | 5.3% | 0.9295            | 0.7366              |

**Disagreement patterns (141 cases):**

| Champion → | Challenger → | Count | Avg Champ Conf | Avg Chall Conf |
|------------|-------------|-------|----------------|----------------|
| medium     | low          | 37    | 0.9434         | 0.7187         |
| high       | medium       | 32    | 0.9020         | 0.7172         |
| low        | medium       | 24    | 0.9044         | 0.7462         |
| critical   | high         | 18    | 0.9318         | 0.8350         |
| medium     | high         | 17    | 0.9602         | 0.6975         |
| high       | critical     | 13    | 0.9608         | 0.7327         |

**Drift alert:** Disagreement rate of 5.3% is the baseline. If this exceeds 10%, one of the models has drifted and the ensemble is unreliable. Disagreements concentrate at adjacent tiers (medium↔low, high↔medium), not extreme jumps — this is expected and healthy.

---

## 7. Monitoring Thresholds Summary

These thresholds, combined with the baselines above, define the monitoring rules:

| Metric | Baseline Value | Yellow Alert | Red Alert |
|--------|---------------|-------------|----------|
| Overall AUC-ROC | 0.9860 | < 0.9500 | < 0.9000 |
| Critical-tier recall | 0.9300 | < 0.7500 | < 0.6000 |
| Max confidence mean | 0.9920 | < 0.9500 | < 0.9000 |
| Low-confidence (< 0.8) count per batch | 43/2672 (1.6%) | > 5% | > 10% |
| Champion-challenger disagreement | 5.3% | > 10% | > 15% |
| Tier distribution shift (any tier) | See §1 | > 5pp | > 10pp |
| PSI (max_confidence) | 0.0 (self-reference) | > 0.1 | > 0.2 |
| New device_type unseen in training | 0 | ≥ 1 | — |
| State with < 30 devices (small-n risk) | 0 states | ≥ 1 | ≥ 5 |

---

## 8. Fairness Baseline (from V5 Fairness Report)

Source: `cdm_tmforum.copper_retirement.v5_fairness_report`

| Dimension | Slices | All GREEN | YELLOW | RED |
|-----------|--------|-----------|--------|-----|
| device_type | 4 (cpe, olt, ont, patch_panel) | 4 | 0 | 0 |
| region (state clusters) | 5 | 5 | 0 | 0 |
| service_type | 2 (unknown, dsl) | 2 | 0 | 0 |
| customer_segment | 9 | 8 | 1 (residential) | 0 |
| **Total** | **20** | **19** | **1** | **0** |

**Known YELLOW:** residential customer segment (n=32) — YELLOW_RECALL + YELLOW_SMALL_N. Too few samples for reliable fairness metrics. Monitor for sample size growth.

---

## 9. Implementation Notes

### Pending Dependency
This baseline is ready for use. However, **inference table auto-capture** is not yet enabled on the `copper-retirement-risk` endpoint (see `ML-ENABLE-INF-CAPTURE`, currently blocked/escalated to @pm). Once enabled:

1. Lakehouse Monitoring (already configured per `ML-DRIFT-MONITOR-SETUP`) will compare incoming predictions against these baselines.
2. The unpacked view `cdm_tmforum.copper_retirement.risk_inference_unpacked` will extract features + predictions from the raw inference payload table.
3. Drift metrics will surface in the Lakehouse Monitoring dashboard.

### How to Use This Baseline
- **PSI calculation:** Use the histogram bins in §3 as the reference distribution. Compute PSI against each new batch's max_confidence histogram.
- **Tier shift detection:** Compare new batch tier proportions to §1 baselines.
- **Sub-population monitoring:** Compare new device_type and state distributions to §4 and §5. Flag if any device_type's proportion changes by >3pp or a state gains/loses >20% of its device count.
- **Champion-challenger:** If disagreement rate exceeds 10% (§6), evaluate whether champion or challenger has drifted.

### Source Tables
- `cdm_tmforum.copper_retirement.copper_risk_predictions` — batch predictions with probabilities
- `cdm_tmforum.copper_retirement.copper_risk_scores` — champion vs challenger comparison
- `cdm_tmforum.copper_retirement.v5_fairness_report` — per-slice fairness metrics
- `cdm_tmforum.tmf_enterprise.physical_device` — device metadata (join for device_type, geography)
- `cdm_tmforum.tmf_shared.geographic_address` — state/lat/lon (join via geographic_address_id)

---

*End of monitoring baseline. Next step: enable inference table auto-capture (ML-ENABLE-INF-CAPTURE) to activate live drift detection against these reference distributions.*
