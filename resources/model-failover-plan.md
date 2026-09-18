# Risk Model Demo Failover Plan

> **project: copper-retirement | developer: copper-ml**
>
> Last updated: 2026-09-18 by @ml-engineer
>
> Purpose: If the `copper-retirement-risk` serving endpoint degrades during a live demo, follow this runbook to restore risk score availability with minimal disruption.

---

## 1. Cached Prediction Fallback

**When to use:** Endpoint returns 5xx errors, latency exceeds 5s, or the endpoint is in NOT_READY state.

### Gold Predictions Table (Primary Fallback)

All 2,672 copper devices have pre-scored predictions stored in Delta:

```sql
SELECT physical_device_id, device_type, predicted_risk_tier,
       prob_low, prob_medium, prob_high, prob_critical,
       max_confidence, model_version, scored_at
FROM cdm_tmforum.copper_retirement.copper_risk_predictions
WHERE model_version = 5
```

| Property | Value |
| --- | --- |
| Table | `cdm_tmforum.copper_retirement.copper_risk_predictions` |
| Row count | 2,672 (all copper devices) |
| Model version | 5 (V5 champion, LightGBM) |
| Last scored | 2026-09-13 |
| Risk tiers | low, medium, high, critical |
| Avg confidence | 0.992 |

**How the map app should consume this:** Query the table directly via Spark SQL or DBSQL warehouse instead of calling the endpoint. The `predicted_risk_tier` and `prob_*` columns are identical to the endpoint response shape.

### Secondary Fallback Tables

| Table | Rows | Description |
| --- | --- | --- |
| `cdm_tmforum.copper_retirement.gold_device_risk_predictions` | 2,672 | Device-grain predictions with geo columns for map rendering |
| `cdm_tmforum.copper_retirement.copper_risk_scores` | 2,672 | Champion (V5) vs Challenger (V4) comparison — use the `champion_*` columns |

### App-Level Failover Pattern

For the copper-map and planning-dashboard apps, implement this pattern:

```python
import requests, time

def get_risk_score(device_id, endpoint_url, token, max_retries=2, timeout_s=3):
    """Try endpoint first, fall back to cached predictions."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                endpoint_url,
                headers={"Authorization": f"Bearer {token}"},
                json={"dataframe_records": [{"physical_device_id": device_id}]},
                timeout=timeout_s,
            )
            if resp.status_code == 200:
                return {"source": "endpoint", "data": resp.json()}
        except (requests.Timeout, requests.ConnectionError):
            time.sleep(0.5)
    
    # Fallback: read from cached predictions
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    result = w.statement_execution.execute_statement(
        warehouse_id="<WAREHOUSE_ID>",
        statement=f"""
            SELECT * FROM cdm_tmforum.copper_retirement.copper_risk_predictions
            WHERE physical_device_id = '{device_id}'
        """
    )
    return {"source": "cached_prediction", "data": result}
```

**Staleness tolerance:** Cached predictions are from 2026-09-13 (V5 model). For demo purposes, these are fully representative — the underlying data is synthetic and does not change between scoring runs. In production, enforce a staleness SLA of ≤7 days.

---

## 2. Batch Re-Score Notebook

**When to use:** Predictions table is stale (>7 days old), endpoint is down for extended period, or you need to refresh after a model version change.

### Notebook Details

| Property | Value |
| --- | --- |
| Path | `/Users/stephen.hage@databricks.com/copper-retirement/scripts/batch_score_copper_risk` |
| Notebook ID | 2509136426379665 |
| Runtime | ~2 minutes on serverless compute |
| Output table | `cdm_tmforum.copper_retirement.copper_risk_predictions` |

### What It Does

1. Loads the **champion** model from UC: `cdm_tmforum.ml_models.copper_retirement_risk@champion`
2. Assembles 39 features from 6 source tables:
   - `copper_risk_target` (base: alarm, SLA, test, problem features)
   - `feature_device_billing_dispute`
   - `feature_device_complaint_rate`
   - `feature_device_service_usage`
   - `feature_device_firmware_age`
   - `copper_loop_plant` (aggregated per device)
3. Scores all 2,672 copper devices
4. Writes results with `MERGE` into `copper_risk_predictions`

### How to Run (3 options)

**Option A — Interactive (fastest for demo recovery):**
1. Open the notebook in Databricks
2. Attach to any serverless cluster
3. Run All cells
4. Verify: `SELECT COUNT(*), MAX(scored_at) FROM cdm_tmforum.copper_retirement.copper_risk_predictions`

**Option B — CLI:**
```bash
databricks jobs run-now --job-id <BATCH_SCORE_JOB_ID>
```

**Option C — Python SDK:**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
run = w.jobs.run_now(job_id=<BATCH_SCORE_JOB_ID>)
print(f"Run started: {run.run_id}")
```

---

## 3. Endpoint Restart Procedure

**When to use:** Endpoint is in FAILED, NOT_READY, or UPDATE_FAILED state, or latency has degraded beyond SLA (p99 > 1s warm).

### Current Endpoint Configuration

| Property | Value |
| --- | --- |
| Endpoint name | `copper-retirement-risk` |
| Endpoint ID | `612701e183a8471f90849f5da2c8875f` |
| Model | `cdm_tmforum.ml_models.copper_retirement_risk` v5 |
| Workload | CPU / Small |
| Scale-to-zero | Enabled |
| Cold-start latency | ~85 seconds |
| Warm latency (p50) | ~83ms |
| Creator | stephen.hage@databricks.com |
| Inference table logging | Enabled |

### Step-by-Step Restart

**Step 1 — Check current state:**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
ep = w.serving_endpoints.get("copper-retirement-risk")
print(f"State: {ep.state.ready}")
print(f"Config ready: {ep.state.config_update}")
```

Or via CLI:
```bash
databricks serving-endpoints get copper-retirement-risk --output JSON | grep -E '"ready|config_update"'
```

**Step 2 — If state is NOT_READY or FAILED, trigger config update (soft restart):**
```python
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

w.serving_endpoints.update_config(
    name="copper-retirement-risk",
    served_entities=[
        ServedEntityInput(
            entity_name="cdm_tmforum.ml_models.copper_retirement_risk",
            entity_version="5",
            scale_to_zero_enabled=True,
            workload_size="Small",
        )
    ],
)
print("Config update triggered — endpoint will re-provision.")
```

Or via CLI:
```bash
databricks serving-endpoints update-config copper-retirement-risk \
  --json '{
    "served_entities": [{
      "entity_name": "cdm_tmforum.ml_models.copper_retirement_risk",
      "entity_version": "5",
      "scale_to_zero_enabled": true,
      "workload_size": "Small"
    }]
  }'
```

**Step 3 — Wait for READY state (up to 10 minutes):**
```python
import time
for i in range(60):
    ep = w.serving_endpoints.get("copper-retirement-risk")
    if str(ep.state.ready) == "EndpointStateReady.READY":
        print(f"Endpoint READY after {i*10}s")
        break
    print(f"  [{i*10}s] State: {ep.state.ready}")
    time.sleep(10)
else:
    print("TIMEOUT — endpoint did not reach READY in 10 minutes.")
    print("Action: Delete and recreate endpoint (Step 4).")
```

**Step 4 — Nuclear option (delete + recreate):**

Only use if Step 2-3 fails after 10 minutes.

```python
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput, ServedEntityInput, AutoCaptureConfigInput
)

# Delete
w.serving_endpoints.delete("copper-retirement-risk")
print("Endpoint deleted. Waiting 30s...")
import time; time.sleep(30)

# Recreate
w.serving_endpoints.create(
    name="copper-retirement-risk",
    config=EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name="cdm_tmforum.ml_models.copper_retirement_risk",
                entity_version="5",
                scale_to_zero_enabled=True,
                workload_size="Small",
            )
        ],
        auto_capture_config=AutoCaptureConfigInput(
            catalog_name="cdm_tmforum",
            schema_name="ml_models",
            enabled=True,
        ),
    ),
    tags=[{"key": "telco_project", "value": "copper-retirement"}],
)
print("Endpoint recreated. Allow 5-10 minutes to provision.")
```

**Step 5 — Validate after restart:**
```python
import requests

token = w.tokens.create(comment="failover-test", lifetime_seconds=600).token_value
resp = requests.post(
    f"{w.config.host}/serving-endpoints/copper-retirement-risk/invocations",
    headers={"Authorization": f"Bearer {token}"},
    json={"dataframe_records": [{
        "alarm_count": 15.0, "critical_alarm_rate": 0.3,
        "test_fail_rate": 0.5, "sla_breach_count": 3.0,
        "problem_count": 8.0, "device_type_encoded": 0.0
    }]},
    timeout=120  # Allow cold-start
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")
assert resp.status_code == 200, f"Endpoint validation failed: {resp.text}"
print("Endpoint validated successfully.")
```

---

## 4. Decision Tree: Quick Reference

```
Endpoint issue detected
│
├─ Latency > 5s but endpoint responds?
│  └─ Likely cold-start (scale-to-zero). Send a warm-up request, wait 90s, retry.
│
├─ 5xx errors / timeout?
│  ├─ Check endpoint state (Step 1)
│  ├─ If NOT_READY → trigger config update (Step 2), wait (Step 3)
│  ├─ If FAILED → delete + recreate (Step 4)
│  └─ Meanwhile → switch app to cached predictions (Section 1)
│
├─ Predictions table empty or stale?
│  └─ Run batch-score notebook (Section 2)
│
└─ Everything down (endpoint + Spark SQL)?
    └─ Use gold_device_risk_predictions from secondary fallback table.
        If SQL warehouse also down, this is an infrastructure outage — escalate to platform team.
```

---

## 5. Key Contacts & Assets

| Asset | Location |
| --- | --- |
| Serving endpoint | `copper-retirement-risk` (Databricks Model Serving) |
| Champion model | `cdm_tmforum.ml_models.copper_retirement_risk` v5 (@champion) |
| Predictions table | `cdm_tmforum.copper_retirement.copper_risk_predictions` |
| Geo predictions | `cdm_tmforum.copper_retirement.gold_device_risk_predictions` |
| Batch-score notebook | `/Users/stephen.hage@databricks.com/copper-retirement/scripts/batch_score_copper_risk` |
| Model card | MLflow artifact on run `0d308b43371249eeb017867da6acf327` |
| MLflow experiment | `/Users/stephen.hage@databricks.com/copper-retirement/experiments/copper_risk_classifier` (ID: 3064056660647801) |
| Drift monitoring | `monitor_drift_activation` notebook in `/copper-retirement/scripts/` |
| Demo walkthrough | `beat1_risk_model_walkthrough` notebook |

---

## 6. Pre-Demo Checklist

- [ ] Verify endpoint state: `databricks serving-endpoints get copper-retirement-risk`
- [ ] Send warm-up request (cold-start takes ~85s if scaled to zero)
- [ ] Verify predictions freshness: `SELECT MAX(scored_at) FROM cdm_tmforum.copper_retirement.copper_risk_predictions`
- [ ] Confirm SQL warehouse is running (for cached fallback)
- [ ] Bookmark this doc and the batch-score notebook for quick access
