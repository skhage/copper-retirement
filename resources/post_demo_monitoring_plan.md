# Post-Demo Monitoring Plan — Copper Retirement Risk Model

> **project:** copper-retirement | **developer:** copper-ml  
> **Author:** @ml-engineer  
> **Date:** 2026-09-19  
> **Model:** V5 LightGBM (cdm_tmforum.ml_models.copper_retirement_risk v5, @champion)  
> **Endpoint:** copper-retirement-risk  
> **References:** monitoring_baseline.md, ML_MODEL_CARD.md, ML_PRODUCTION_READINESS.md  

---

## 1. Overview & Objectives

This plan defines the operational monitoring regime for the copper retirement risk model **after the Beat 1 demo**. The model classifies 2,672 copper network devices into four risk tiers (low/medium/high/critical) to drive Lakelink Fiber's retirement sequencing. Post-demo, the model transitions from a demonstration asset to a decision-support tool that must be continuously monitored for:

1. **Prediction drift** — shifts in risk tier distribution vs. baseline
2. **Feature drift** — input feature distributions diverging from training population
3. **Performance decay** — degradation in accuracy, AUC, or per-tier recall
4. **Inference health** — endpoint availability, latency, error rates
5. **Fairness regression** — sub-demographic slice performance degrading

**Monitoring maturity path:**
- **Phase 1 (Immediate post-demo):** Batch scoring comparison + manual drift checks (current state)
- **Phase 2 (Inference capture enabled):** Lakehouse Monitor on inference table, automated alerts
- **Phase 3 (Production):** Automated retraining pipeline triggered by drift/decay signals

---

## 2. Drift Detection — Thresholds & Actions

### 2.1 Prediction Distribution Drift

Baseline tier distribution (from monitoring_baseline.md, 2026-09-13 batch scoring):

| Risk Tier | Baseline % | Alert Threshold | Critical Threshold |
| --- | --- | --- | --- |
| low | 20.0% | ± 5 pp (15–25%) | ± 8 pp (12–28%) |
| medium | 39.7% | ± 5 pp (35–45%) | ± 8 pp (32–48%) |
| high | 30.3% | ± 5 pp (25–35%) | ± 8 pp (22–38%) |
| critical | 10.0% | ± 3 pp (7–13%) | ± 5 pp (5–15%) |

**Actions:**
- **Alert breach:** Log warning, notify @ml-engineer. Investigate root cause — is it a data pipeline change, new device population, or genuine risk shift?
- **Critical breach:** Halt automated consumption of risk scores until reviewed. Trigger retraining evaluation.

**Monitoring SQL (batch comparison):**
```sql
SELECT
  predicted_risk_tier,
  COUNT(*) AS n,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
  CASE
    WHEN predicted_risk_tier = 'critical' AND ABS(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () - 10.0) > 3 THEN 'ALERT'
    WHEN predicted_risk_tier = 'critical' AND ABS(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () - 10.0) > 5 THEN 'CRITICAL'
    WHEN ABS(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () - <baseline_pct>) > 5 THEN 'ALERT'
    WHEN ABS(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () - <baseline_pct>) > 8 THEN 'CRITICAL'
    ELSE 'OK'
  END AS drift_status
FROM cdm_tmforum.copper_retirement.copper_risk_predictions
WHERE scored_at = (SELECT MAX(scored_at) FROM cdm_tmforum.copper_retirement.copper_risk_predictions)
GROUP BY predicted_risk_tier;
```

### 2.2 Confidence Distribution Drift

Baseline: 97.5% of predictions have max_confidence > 0.98. Median = 1.0000.

| Signal | Baseline | Alert | Critical |
| --- | --- | --- | --- |
| Avg max_confidence | 0.9920 | < 0.97 | < 0.95 |
| Count in [0.5, 0.8) bin | 43 / 2,672 (1.6%) | > 100 (3.7%) | > 200 (7.5%) |
| P05 max_confidence | 0.9849 | < 0.90 | < 0.80 |

**Interpretation:** A shift toward mid-range probabilities (0.3–0.7) signals degraded model discrimination — the model is becoming less certain. This often precedes outright accuracy drops.

### 2.3 Feature Drift (Population Stability Index)

| Feature (by importance rank) | PSI Alert | PSI Critical | Notes |
| --- | --- | --- | --- |
| problem_count (#1) | > 0.1 | > 0.2 | Most important; tighter threshold |
| recurring_problem_rate (#2) | > 0.1 | > 0.2 | |
| alarm_count (#3) | > 0.1 | > 0.2 | |
| complaint_avg_resolution_hours (#4) | > 0.15 | > 0.25 | Customer-domain; slightly noisier |
| device_age_days (#5) | > 0.1 | > 0.2 | Should be monotonically increasing |
| months_since_last_dispute (#6) | > 0.15 | > 0.25 | |
| complaint_rate_per_month (#7) | > 0.1 | > 0.2 | |
| service_affecting_rate (#8) | > 0.1 | > 0.2 | |
| escalated_dispute_count (#9) | > 0.15 | > 0.25 | |
| days_past_support_expiry (#10) | > 0.15 | > 0.25 | Firmware domain |

**PSI calculation:** Compare current scoring batch feature histograms against training data distributions (logged as MLflow artifacts on run 0d308b43). Use 10 equal-frequency bins.

**Additional feature monitors:**
- Null rate increase > 5 pp on any feature → investigate data pipeline
- New device_type values not in {cpe, ont, olt, patch_panel} → retrain required
- Firmware coverage below 50% (baseline: 63%) → update imputation strategy

---

## 3. Inference Volume & Health Alerts

### 3.1 Endpoint Health

Baseline latency (from ML-ENDPOINT-WARMUP-0918, 2026-09-18):
- Cold-start: ~94s (scale-to-zero, expected)
- Warm p50: 13 ms
- Warm p95: ~50 ms
- Warm p99: ~58 ms

| Metric | SLA Target | Alert | Critical |
| --- | --- | --- | --- |
| Warm latency p50 | < 200 ms | > 200 ms | > 500 ms |
| Warm latency p99 | < 1,000 ms | > 1,000 ms | > 2,000 ms |
| 5xx error rate | < 1% | > 1% per hour | > 5% per hour |
| Endpoint state | READY | NOT_READY for > 5 min | NOT_READY for > 15 min |
| Cold-start latency | < 120 s | > 120 s | > 180 s |

**Actions on alert:**
1. Check endpoint status via `GET /api/2.0/serving-endpoints/copper-retirement-risk`
2. If cold-start is the cause, evaluate switching to `min_provisioned_throughput > 0` for production
3. For 5xx spikes, check model version compatibility and input schema changes
4. Failover: cached predictions in `copper_risk_predictions` table (2,672 rows, batch-scored), model-failover-plan.md documents the full procedure

### 3.2 Inference Volume

| Scenario | Expected Volume | Alert if |
| --- | --- | --- |
| Batch scoring (weekly) | ~2,672 requests/run | < 2,000 or > 3,000 (device count changed) |
| On-demand (map app) | 0–50 requests/day | > 500/day (unexpected traffic spike) |
| Demo periods | 10–100 requests/session | No alert (expected burst) |
| Zero traffic (> 7 days) | Abnormal | Alert — scoring job may have failed |

### 3.3 Inference Table Monitoring (Phase 2 — post auto-capture enablement)

Once inference table auto-capture is enabled (ACTION-3 from ML_PRODUCTION_READINESS.md):

| Check | Frequency | Query |
| --- | --- | --- |
| New rows arriving | Daily | `SELECT COUNT(*) FROM cdm_tmforum.copper_retirement.risk_model_inference_payload WHERE request_date = CURRENT_DATE` |
| Response schema stability | Weekly | Verify response JSON structure hasn't changed |
| Latency distribution | Daily | `SELECT PERCENTILE(execution_duration_ms, 0.5), PERCENTILE(execution_duration_ms, 0.99) FROM ...` |
| Error rate | Daily | `SELECT COUNT(*) FILTER (WHERE status_code >= 400) * 100.0 / COUNT(*) FROM ...` |

---

## 4. Model Retraining Triggers

### 4.1 Automatic Triggers (require retraining investigation)

| # | Trigger | Threshold | Detection Method | Priority |
| --- | --- | --- | --- | --- |
| T1 | Feature PSI breach | PSI > 0.2 on any top-10 feature | Batch feature comparison | High |
| T2 | AUC-ROC decay | Holdout AUC < 0.95 (baseline: 0.986) | Periodic re-evaluation on labeled data | Critical |
| T3 | Critical-tier recall drop | Recall < 0.75 (baseline: 0.833) | Per-tier metrics on holdout | Critical |
| T4 | Prediction distribution shift | Any tier > 8 pp from baseline | Batch scoring comparison | High |
| T5 | Confidence degradation | Avg confidence < 0.95 | Batch scoring statistics | High |
| T6 | Fairness regression | Any slice drops from GREEN → RED | Slice re-evaluation | High |
| T7 | Champion/challenger divergence | Disagreement > 20% of devices | `copper_risk_scores.models_agree` | Medium |
| T8 | New device types | device_type not in training vocabulary | Schema validation on scoring input | High |
| T9 | Firmware coverage drop | < 50% (baseline: 63%) | Null rate on firmware features | Medium |

### 4.2 Scheduled Triggers

| Cadence | Action | Owner |
| --- | --- | --- |
| Weekly | Run batch scoring job, compare tier distribution vs. baseline | @ml-engineer (automated via Lakeflow Job) |
| Monthly | Compute PSI on top-10 features; re-score holdout for AUC check | @ml-engineer |
| Quarterly | Full retrain with latest data, re-run fairness evaluation across all 20 slices, update model card | @ml-engineer |
| On data delivery | Retrain when @data-engineer delivers new features or real operational data replaces synthetics | @ml-engineer + @data-engineer coordination |

### 4.3 Retraining Workflow

```
Trigger detected
  → Open investigation MLflow run (child of experiment)
  → Log trigger type, magnitude, affected features/slices
  → IF trigger confirmed:
      → Retrain with updated data (Optuna 50-trial, same search space)
      → Register as new version with @challenger alias
      → Run fairness evaluation (20 slices)
      → Compare to @champion on holdout + per-slice metrics
      → IF challenger > champion on AUC AND no fairness regression:
          → Promote @challenger → @champion
          → Update serving endpoint to new version
          → Update model card, monitoring_baseline.md
          → Notify @pm of model version change
      → ELSE:
          → Log findings, keep @champion, escalate to @pm if degradation persists
```

---

## 5. Fairness Monitoring

### 5.1 Slice Definitions (20 slices across 4 dimensions)

| Dimension | Slices | Baseline Status |
| --- | --- | --- |
| device_type | cpe, ont, olt, patch_panel (4) | All GREEN |
| region | midwest, northeast, south, southeast, west (5) | All GREEN |
| service_type | broadband, voice (2) | All GREEN |
| customer_segment | 9 segments (commercial, enterprise, government, healthcare, education, residential, small_business, wholesale, managed_services) | 8 GREEN, 1 YELLOW (residential, n=32) |

### 5.2 Fairness Thresholds

| Metric | GREEN | YELLOW | RED |
| --- | --- | --- | --- |
| AUC-ROC vs. global | Within 10% | 10–15% below global | > 15% below global |
| Recall (high-risk tier) | Within 15% of global | 15–25% below global | > 25% below global |
| Sample size | ≥ 50 | 30–49 | < 30 |

### 5.3 Monitoring Actions

- **GREEN → YELLOW:** Log warning, increase monitoring frequency for that slice to weekly
- **GREEN/YELLOW → RED:** Halt risk scoring for affected sub-population. File FEATURE-REQ to @data-engineer for additional slice-specific features. Escalate to @pm.
- **Residential slice (YELLOW):** Known small-sample issue (n=32, recall 0.933). Monitor as real data grows. If sample remains < 50 after 2 quarters, consider merging into broader segment.

### 5.4 Fairness Re-evaluation Schedule

| Cadence | Scope |
| --- | --- |
| Monthly | Quick check: per-slice prediction distribution (no re-scoring needed) |
| Quarterly | Full re-evaluation: re-score holdout, compute AUC/recall/F1 per slice |
| On retrain | Mandatory full fairness evaluation as part of champion/challenger workflow |

---

## 6. Alert Routing & Escalation

### 6.1 Alert Severity Levels

| Level | Response Time | Notification | Examples |
| --- | --- | --- | --- |
| INFO | Next business day | Logged to MLflow + Lakebase | Weekly batch scoring completed, no drift |
| WARNING | 24 hours | @ml-engineer via Lakebase task | PSI 0.1–0.2, confidence dip, volume anomaly |
| ALERT | 4 hours | @ml-engineer + @pm | PSI > 0.2, AUC < 0.95, fairness YELLOW → RED |
| CRITICAL | 1 hour | @ml-engineer + @pm + CEO | Endpoint down > 15 min, critical recall < 0.75, all-tier drift > 8 pp |

### 6.2 Escalation Path

```
@ml-engineer (first responder)
  → @pm (if blocker requires cross-team coordination)
    → @data-engineer (if data pipeline or feature issue)
    → @devops (if infrastructure/endpoint issue)
    → CEO (if architectural decision or resource allocation needed)
```

### 6.3 Alerting Implementation

**Phase 1 (current):** Manual monitoring via batch scoring notebook + Lakebase status updates
**Phase 2 (target):** Databricks SQL Alerts on monitoring queries:
- Alert 1: Tier distribution drift (daily, on batch scoring table)
- Alert 2: Confidence degradation (daily)
- Alert 3: Endpoint error rate (hourly, on inference table)
- Alert 4: Zero inference volume (daily, check for 7-day gap)

---

## 7. Monitoring Infrastructure Checklist

| Component | Status | Dependency |
| --- | --- | --- |
| Lakehouse Monitor on inference table | ACTIVE (configured) | Awaiting inference auto-capture enablement |
| Batch scoring notebook | READY | `copper-retirement/scripts/batch_score_copper_risk` |
| Drift monitoring notebook | READY | `copper-retirement/scripts/monitor_drift_activation` |
| Manual inference logging | READY | `copper-retirement/scripts/manual_inference_log_demo` |
| Monitoring baseline | DOCUMENTED | `copper-retirement/resources/monitoring_baseline.md` |
| Model card | DOCUMENTED | `copper-retirement/resources/ML_MODEL_CARD.md` |
| Failover plan | DOCUMENTED | Logged as MLflow artifact on V5 run |
| Production readiness checklist | DOCUMENTED | `copper-retirement/resources/ML_PRODUCTION_READINESS.md` |
| Automated batch scoring job | NOT YET CREATED | Needs @devops to create Lakeflow Job |
| SQL Alerts | NOT YET CREATED | Needs inference auto-capture first |

---

## 8. Monitoring Runbook — Weekly Cadence

### Step 1: Run Batch Scoring
```
Open: copper-retirement/scripts/batch_score_copper_risk
Run all cells.
Verify: copper_risk_predictions table updated with new scored_at timestamp.
```

### Step 2: Compare Tier Distribution
```sql
-- Compare latest vs. baseline
WITH latest AS (
  SELECT predicted_risk_tier, COUNT(*) AS n
  FROM cdm_tmforum.copper_retirement.copper_risk_predictions
  WHERE scored_at = (SELECT MAX(scored_at) FROM cdm_tmforum.copper_retirement.copper_risk_predictions)
  GROUP BY predicted_risk_tier
),
baseline AS (
  SELECT 'low' AS tier, 20.0 AS pct UNION ALL
  SELECT 'medium', 39.7 UNION ALL
  SELECT 'high', 30.3 UNION ALL
  SELECT 'critical', 10.0
)
SELECT l.predicted_risk_tier, l.n,
  ROUND(l.n * 100.0 / SUM(l.n) OVER (), 1) AS current_pct,
  b.pct AS baseline_pct,
  ROUND(l.n * 100.0 / SUM(l.n) OVER () - b.pct, 1) AS drift_pp
FROM latest l JOIN baseline b ON l.predicted_risk_tier = b.tier;
```

### Step 3: Check Champion/Challenger Agreement
```sql
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE models_agree) AS agree,
  ROUND(COUNT(*) FILTER (WHERE models_agree) * 100.0 / COUNT(*), 1) AS agreement_pct
FROM cdm_tmforum.copper_retirement.copper_risk_scores;
```

### Step 4: Check Endpoint Health
```
GET /api/2.0/serving-endpoints/copper-retirement-risk
Verify: state = READY, served_entities = copper_retirement_risk-5
```

### Step 5: Log Results to Lakebase
```sql
INSERT INTO status_updates (update_date, agent_role, update_type, summary)
VALUES (CURRENT_DATE, '@ml-engineer', 'weekly_monitoring',
  'Batch scoring complete. Tier distribution: [low X%, medium X%, high X%, critical X%]. Max drift: X pp. Agreement: X%. Endpoint: READY.');
```

---

## 9. Key Metrics Dashboard Requirements

When a monitoring dashboard is built (per CEO SEMANTIC MODELING MANDATE), it should include:

1. **Risk tier distribution over time** — stacked bar chart, one bar per scoring run, with baseline reference lines
2. **Confidence distribution** — histogram of max_confidence per scoring run, with PSI annotation
3. **Feature drift heatmap** — PSI values for top-10 features per scoring run (green/yellow/red)
4. **Slice performance table** — AUC + recall per slice, color-coded by GREEN/YELLOW/RED
5. **Endpoint health** — latency p50/p99 time series, error rate, request volume
6. **Champion vs. challenger** — agreement rate over time, per-tier comparison
7. **Retraining log** — table of all retrain events with trigger type, outcome, version promoted

All dashboard widgets **MUST have an embedded Genie agent** per CEO directive.

---

## 10. Transition Milestones

| Milestone | Trigger | Owner | Status |
| --- | --- | --- | --- |
| M1: Auto-capture enabled | CEO enables on endpoint | CEO + @ml-engineer | PENDING |
| M2: Lakehouse Monitor active | M1 + first 100 inference rows | @ml-engineer | CONFIGURED, awaiting M1 |
| M3: Weekly batch scoring job | @devops creates Lakeflow Job | @devops + @ml-engineer | NOT STARTED |
| M4: SQL Alerts live | M1 + alert queries validated | @ml-engineer | NOT STARTED |
| M5: First quarterly retrain | 3 months post-demo | @ml-engineer | NOT STARTED |
| M6: Real data substitution | @data-engineer delivers operational data | @data-engineer + @ml-engineer | NOT STARTED |

**Note:** When M6 (real data) is achieved, ALL baseline values in this document and monitoring_baseline.md must be recomputed. The synthetic data caveat means current thresholds are calibrated to uniform/random distributions — real operational data will have different natural variance.

---

*End of monitoring plan. Review quarterly or on any retraining event.*
