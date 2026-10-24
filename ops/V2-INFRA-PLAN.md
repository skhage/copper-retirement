# V2 Infrastructure Plan — Copper Retirement (Beats 2/3/5)

**Author:** @devops | **Date:** 2026-09-21 | **Status:** PUBLISHED
**Task:** DEVOPS-V2-INFRA-PLAN-0921

---

## 1. Current V1 Infrastructure Baseline (Beats 1 + 4)

| Category | Asset | Status |
| --- | --- | --- |
| Serving Endpoint | `copper-retirement-risk` (V5 GBT risk model) | READY |
| Vector Search | `regulatory_doc_vs_index` on `demo_telco_vs_endpoint` (528 docs, GTE-large) | ONLINE |
| DLP Pipeline | `copper-retirement-pipeline` (b52532a2) — 8 MVs (3 bronze, 2 silver, 3 gold) | IDLE (triggered) |
| DLP Pipeline | `copper-retirement-dlp` (3d0576c0) — secondary/legacy | IDLE |
| Apps (6) | copper-map, retirement-plan, dig-triage, regulatory-assistant, commodity-dashboard, copper-task-board | Scaffolded |
| Lakebase | `copper_app` schema — 19 tables (device_risk_map, retirement_plan, dig_incidents, etc.) | Operational |
| UC Tables | `cdm_tmforum.copper_retirement` — 78 objects (62 managed, 8 MVs, 5 metric views, 3 views) | Populated |
| DAB Config | `databricks.yml` + 12 resource files (6 apps, 1 pipeline, 1 serving_endpoints, 2 jobs, 1 UC) | In repo |
| Pipeline SQL | 11 files: 3 bronze, 4 silver, 4 gold | In repo |

---

## 2. V2 Infrastructure Requirements by Beat

### Beat 2 — "Capital-efficient plan to zero copper?" (P4-SEQ + P5 + P7-PLAN)

**New Serving Endpoints:**
- `copper-sequencing-optimizer-${target}` — LP/constraint solver model for wave scheduling optimization. Produces 2026-2029 wave plans given risk scores, crew capacity, budget, and regulatory notice windows.
  - **Prereq:** @ml-engineer registers `cdm_tmforum.agents.sequencing_optimizer` in UC Model Registry.
  - **Config:** scale-to-zero, Small workload, inference table logging on.
  - **DAB:** Add to `bundle/resources/serving_endpoints.yml`.

**DLP Pipeline Expansion:**
The following gold tables exist as managed tables but are NOT yet materialized views in the pipeline. Evaluate whether to promote them to MVs for automatic refresh:
- `gold_wave_schedule` — wave scheduling output (currently static managed table)
- `gold_ebitda_forecast` — EBITDA impact forecast
- `silver_budget_allocation` — budget allocation enrichment
- `silver_revenue_recognition_constraints` — revenue constraints for migration timing

**Recommendation:** Keep these as managed tables (not MVs) since they are model outputs and manual planning artifacts, not deterministic SQL transforms. Add a refresh job instead.

**New DLP Pipeline SQL (if promoted):**
- None required immediately. The existing 11 SQL files cover the bronze→silver→gold path.

**App Expansion: retirement-plan V2:**
- Editable Gantt chart backed by Lakebase `retirement_plan` + `retirement_milestones`
- Wire center drag-reorder → writes back to Lakebase `gold_wave_schedule`
- Budget constraint visualization from `silver_budget_allocation`
- Sequencing optimizer "re-plan" button → calls sequencing-optimizer endpoint

**Lakebase Schema Changes:**
- Add `wave_schedule_versions` table for plan versioning (before/after optimizer runs)
- Add `plan_edit_audit_log` table for tracking manual edits to retirement plan

**CI/CD:**
- Add `sequencing_optimizer_refresh.job.yml` — triggered job to re-score wave plans when risk model updates

---

### Beat 3 — "Dig crew hit something — triage/reroute fast" (P6-TRIAGE + P7-TRIAGE)

**Serving Endpoints (already declared in DAB):**
- `copper-triage-agent-${target}` — Dig triage tool-calling agent. ✅ In `serving_endpoints.yml`.
  - **Prereq:** @ml-engineer registers `cdm_tmforum.agents.dig_triage_agent`.
- `copper-contractor-agent-${target}` — Contractor sourcing agent. ✅ In `serving_endpoints.yml`.
  - **Prereq:** @ml-engineer registers `cdm_tmforum.agents.contractor_sourcing_agent`.

**No new endpoint declarations needed** — both are already in the DAB config.

**DLP Pipeline Expansion:**
Evaluate adding these as MVs for automatic refresh:
- `silver_dig_incident_enriched` — enriched dig incidents with geospatial + device joins
- `gold_reroute_options` — pre-computed rerouting alternatives

**Recommendation:** `silver_dig_incident_enriched` is a good MV candidate (deterministic SQL join). `gold_reroute_options` depends on model output — keep as managed.

**New Pipeline SQL files (1):**
- `pipeline/silver_dig_incident_enriched.sql` — promote from managed table to MV.

**App Expansion: dig-triage V2:**
- Incident creation form → writes to Lakebase `dig_incidents`
- Live agent action panel (triage agent recommendations, human approve/reject)
- Contractor assignment from agent shortlist → writes to Lakebase `gold_contractor_assignment_plan`
- Real-time incident status tracking

**Lakebase Schema Changes:**
- Add `incident_actions` table — tracks agent recommendations + human decisions
- Add `triage_agent_sessions` table — MLflow trace IDs linked to incidents for audit

**CI/CD:**
- Add `triage_agent_eval.job.yml` — nightly evaluation job running P6-EVAL against latest triage agent version

---

### Beat 5 — "Who digs, and when do we sell copper?" (P4-COMMODITY + P6-CONTRACTOR + P7-COMMODITY)

**New Serving Endpoints:**
- `copper-commodity-forecaster-${target}` — Copper price forecast model (GBT/Prophet, 3-18mo horizon).
  - **Prereq:** @ml-engineer registers `cdm_tmforum.agents.commodity_forecaster` in UC.
  - **Config:** scale-to-zero, Small workload, inference table logging on.
  - **DAB:** Add to `bundle/resources/serving_endpoints.yml`.
- `copper-supervisor-agent-${target}` — Supervisor orchestrating all sub-agents. ✅ Already in `serving_endpoints.yml`.
  - **Prereq:** @ml-engineer registers `cdm_tmforum.agents.supervisor_agent`.

**DLP Pipeline Expansion:**
Evaluate these for MV promotion:
- `gold_commodity_price_forecast` — model output, keep managed
- `gold_contractor_assignment_plan` — planning output, keep managed
- `gold_copper_recovery_schedule` — schedule output, keep managed
- `gold_circuit_revenue_at_risk` — ✅ Good MV candidate (deterministic SQL aggregation)

**New Pipeline SQL files (1):**
- `pipeline/gold_circuit_revenue_at_risk.sql` — already exists in `/pipeline/` folder. Verify it's included in pipeline glob.

**App Expansion: commodity-dashboard V2:**
- Copper price forecast chart (3-18mo) from commodity-forecaster endpoint
- Sell/hold signal visualization from `copper_commodity_sell_hold_signal` metric view
- Contractor shortlist with assign capability → writes to Lakebase
- Recovery schedule timeline from `gold_copper_recovery_schedule`

**Lakebase Schema Changes:**
- Add `commodity_forecast_versions` table for tracking forecast model runs
- Add `sell_hold_decisions` table for tracking human sell/hold decisions with audit trail

**CI/CD:**
- Add `commodity_forecast_refresh.job.yml` — scheduled daily job to re-run commodity forecast
- Add `supervisor_agent_eval.job.yml` — nightly eval for supervisor agent

---

## 3. Consolidated V2 Infra Backlog

### New Serving Endpoints (add to `serving_endpoints.yml`)

| Endpoint Name | Model Entity | Beat | Priority | Prereq |
| --- | --- | --- | --- | --- |
| `copper-sequencing-optimizer-${target}` | `cdm_tmforum.agents.sequencing_optimizer` | 2 | high | @ml-engineer UC registration |
| `copper-commodity-forecaster-${target}` | `cdm_tmforum.agents.commodity_forecaster` | 5 | high | @ml-engineer UC registration |
| `copper-triage-agent-${target}` | Already in DAB | 3 | — | @ml-engineer UC registration |
| `copper-contractor-agent-${target}` | Already in DAB | 3 | — | @ml-engineer UC registration |
| `copper-supervisor-agent-${target}` | Already in DAB | all | — | @ml-engineer UC registration |

**Net new endpoint declarations to add:** 2 (sequencing-optimizer, commodity-forecaster)
**Already declared, awaiting model registration:** 3 (triage, contractor, supervisor)

### New DLP Pipeline SQL Files

| File | Type | Beat | Priority | Notes |
| --- | --- | --- | --- | --- |
| `silver_dig_incident_enriched.sql` | MV promotion | 3 | medium | Promote from managed table to pipeline MV |
| `gold_circuit_revenue_at_risk.sql` | Already exists | 5 | low | Verify included in pipeline glob |

### New Lakebase Tables (`copper_app` schema)

| Table | Beat | Purpose |
| --- | --- | --- |
| `wave_schedule_versions` | 2 | Plan versioning for optimizer runs |
| `plan_edit_audit_log` | 2 | Manual edit audit trail |
| `incident_actions` | 3 | Agent recommendations + human decisions |
| `triage_agent_sessions` | 3 | MLflow trace linkage for incident audit |
| `commodity_forecast_versions` | 5 | Forecast model run tracking |
| `sell_hold_decisions` | 5 | Human sell/hold decision audit |

### New DAB Job Configs (`bundle/resources/`)

| Job Config File | Beat | Trigger | Purpose |
| --- | --- | --- | --- |
| `sequencing_refresh.job.yml` | 2 | On risk model update | Re-score wave plans |
| `triage_agent_eval.job.yml` | 3 | Nightly | Agent eval against latest version |
| `commodity_forecast_refresh.job.yml` | 5 | Daily | Re-run commodity price forecast |
| `supervisor_agent_eval.job.yml` | all | Nightly | Supervisor agent eval |

### App V2 Feature Summary

| App | Beat | V2 Features |
| --- | --- | --- |
| retirement-plan | 2 | Editable Gantt, optimizer re-plan button, budget viz, plan versioning |
| dig-triage | 3 | Incident form, live agent panel, contractor assign, status tracking |
| commodity-dashboard | 5 | Price forecast chart, sell/hold signal, contractor shortlist, recovery timeline |

### CI/CD Pipeline Updates

1. **Add `agents` schema validation** to DAB deploy: verify UC models exist before endpoint creation.
2. **Add integration test job** (`e2e_demo_validation.job.yml`): runs golden queries for all 5 beats, validates app health checks, checks endpoint readiness.
3. **Add monitoring job** (`inference_monitoring.job.yml`): Lakehouse Monitoring on inference tables for all serving endpoints — drift detection.
4. **Update `pipeline_refresh.job.yml`**: include new MVs in refresh trigger.

---

## 4. Deployment Sequence

**Wave 1 (immediate — @devops can do now):**
1. Add 2 new endpoint declarations to `serving_endpoints.yml`
2. Verify `gold_circuit_revenue_at_risk.sql` is in pipeline glob
3. Create Lakebase tables (6 new tables)

**Wave 2 (after @ml-engineer registers models):**
1. `bundle deploy --target dev` to create/update all 5 endpoints
2. Validate endpoint health

**Wave 3 (after @app-developer builds V2 features):**
1. Add new job configs for eval + refresh
2. Add integration test job
3. Full `bundle deploy --target prod`

---

## 5. Risk Register

| Risk | Mitigation |
| --- | --- |
| UC model registration delay blocks endpoint creation | Endpoints use scale-to-zero — declare them early, they cost nothing until models land |
| Lakebase schema migration on existing copper_app tables | New tables only — no ALTER on existing V1 tables |
| Pipeline glob doesn't pick up new SQL files | Verify `../../pipeline/**` glob in pipeline.yml covers all new files |
| Agent eval jobs consume compute nightly | Scale-to-zero + serverless — minimal cost when idle |
| Multiple serving endpoints increase monitoring surface | Consolidate into single `inference_monitoring.job.yml` |
