# DEMO-DAY-CHECKLIST.md
## Copper Retirement — Demo Day Startup & Verification
### Release: v1.0-demo-rc4 | Frozen: 2026-09-17

---

## 1. PRE-FLIGHT (15 min before demo)

### 1.1 SQL Warehouse
```sql
-- Verify warehouse is RUNNING (auto-starts on query)
SELECT 1 AS warehouse_check;
-- Warehouse ID: 7b65956f30d66feb (Serverless Starter Warehouse)
```
**Expected:** Query returns in <5s. If STOPPED, it auto-starts in ~30s.

### 1.2 Serving Endpoint — copper-retirement-risk
```python
import requests
endpoint_url = "https://fevm-cmegdemos.cloud.databricks.com/serving-endpoints/copper-retirement-risk/invocations"
# Health check: send one warm-up request with 39-feature V5 schema
payload = {
  "dataframe_records": [{
    "source_system": "LFACS", "device_type": "terminal", "installation_year": 1985,
    "device_age_years": 41, "manufacturer": "Western Electric", "model_variant": "500-type",
    "cable_gauge_awg": 24, "loop_length_ft": 8500.0, "bridge_tap_count": 2,
    "loading_coil_present": 1, "splice_count": 5, "cable_material": "pulp",
    "pressurization_type": "none", "pedestal_type": "buried", "ground_type": "rod",
    "pair_count_in_cable": 200, "aerial_span_pct": 0.15, "underground_pct": 0.60,
    "buried_pct": 0.25, "alarm_count_90d": 3, "trouble_ticket_count_12m": 5,
    "repeat_trouble_pct": 0.40, "mttr_hours": 6.2, "snr_db": 18.5,
    "line_resistance_ohms": 950.0, "insulation_resistance_mohms": 12.0,
    "loop_current_ma": 22.0, "bit_error_rate": 0.002, "customers_on_circuit": 45,
    "revenue_at_risk_monthly": 8500.0, "has_fiber_nearby": 1,
    "fiber_distance_ft": 1200.0, "permits_required": 1,
    "environmental_restrictions": 0, "historic_district": 0,
    "dig_safe_incidents_1mi": 2, "contractor_capacity_score": 0.72,
    "h3_res9_index": "892a100d2c3ffff", "state_code": "MA"
  }]
}
# Expected: 200 OK, prediction in <2s (scale-to-zero may add ~60s on first call)
```
**Model:** cdm_tmforum.ml_models.copper_retirement_risk v5 (LightGBM, AUC 0.986)
**Scale-to-zero:** Enabled — first call after idle may take 60-90s

### 1.3 Vector Search — Regulatory RAG
```python
# Verify VS index is ONLINE with 528 documents
# Endpoint: cmeg-demos-vs
# Index: cdm_tmforum.copper_retirement.regulatory_doc_chunks_vs_index
# Embedding: BGE-large-en-v1.5 (1024-dim)
```

### 1.4 DLP Pipelines
| Pipeline | ID | Expected State |
| --- | --- | --- |
| copper-retirement-pipeline (active) | b52532a2-6398-44ed-b239-9e95cafb745c | IDLE |
| copper-retirement-dlp (superseded) | 3d0576c0-5881-4c79-bd54-cdf2e57ad207 | IDLE |

### 1.5 Databricks Apps
| App | URL | Expected |
| --- | --- | --- |
| copper-map (Beat 1) | https://copper-map-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| regulatory-assistant (Beat 4) | https://regulatory-assistant-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |
| copper-task-board | https://copper-task-board-7474656585748611.aws.databricksapps.com | ACTIVE / SUCCEEDED |

### 1.6 Data Freshness
```sql
-- Check key tables have data
SELECT 'gold_retirement_executive_summary' AS tbl, COUNT(*) AS cnt FROM cdm_tmforum.copper_retirement.gold_retirement_executive_summary
UNION ALL
SELECT 'copper_risk_target', COUNT(*) FROM cdm_tmforum.copper_retirement.copper_risk_target
UNION ALL
SELECT 'regulatory_doc_chunks', COUNT(*) FROM cdm_tmforum.copper_retirement.regulatory_doc_chunks;
-- Expected: exec_summary ~6, risk_target ~2672, reg_chunks ~528
```

---

## 2. DEMO STARTUP SEQUENCE

### Step 1: Warm up SQL Warehouse
Open any SQL editor and run: `SELECT current_timestamp()`

### Step 2: Warm up Serving Endpoint
Send one inference request (see §1.2 payload). If scale-to-zero is active, allow 60-90s.

### Step 3: Open Apps
1. Open copper-map: https://copper-map-7474656585748611.aws.databricksapps.com
2. Open regulatory-assistant: https://regulatory-assistant-7474656585748611.aws.databricksapps.com
3. Verify both load without errors

### Step 4: Verify Data
Run data freshness queries (§1.6). All counts should match expected values.

---

## 3. RECOVERY PLAYBOOK

### Serving Endpoint Not Responding
1. Check: Workspace → Serving → copper-retirement-risk → Status
2. If FAILED: Click "Update" to redeploy same model version
3. Fallback: Use batch predictions table `cdm_tmforum.copper_retirement.copper_risk_predictions`

### App Not Loading
1. Check: Workspace → Apps → [app-name] → Logs
2. Restart: `databricks apps stop [name]` then `databricks apps start [name]`
3. Typical boot time: 30-60s

### Vector Search Unavailable
1. Check: VS endpoint cmeg-demos-vs status
2. Fallback: Direct table query on `cdm_tmforum.copper_retirement.regulatory_doc_chunks`

### Pipeline Needs Refresh
```
databricks pipelines start-update b52532a2-6398-44ed-b239-9e95cafb745c
```
Full refresh takes ~5-10 min.

---

## 4. ENVIRONMENT INVENTORY (Frozen State)

| Component | Version/ID | Status at Freeze |
| --- | --- | --- |
| Git tag | v1.0-demo-rc4 | Tagged 2026-09-17 |
| Git commit | 467f329 | main branch, CLEAN |
| Risk model | v5 (cdm_tmforum.ml_models.copper_retirement_risk) | READY |
| Serving endpoint | copper-retirement-risk (Small, scale-to-zero) | READY |
| VS index | regulatory_doc_chunks_vs_index (528 docs, BGE-large 1024d) | ONLINE |
| DLP pipeline | b52532a2 (copper-retirement-pipeline) | IDLE |
| App: copper-map | Beat 1 network risk map | ACTIVE |
| App: regulatory-assistant | Beat 4 RAG compliance assistant | ACTIVE |
| SQL warehouse | 7b65956f30d66feb (Serverless Starter) | RUNNING |
| Catalog | cdm_tmforum.copper_retirement | 50 tables |

---

## 5. DO NOT CHANGE AFTER FREEZE
- Model serving endpoint configuration
- Pipeline SQL definitions
- App source code deployments
- VS index embedding model or source table
- Unity Catalog table schemas

Any changes require @devops approval and a new RC tag.
