# Partner Export Manifest — Copper Retirement Solution Accelerator

Owner: @devops. Tasks: ACC-DEVOPS-PLANB-EXPORT-MANIFEST (COO-Q-20261028-0550-3), refreshed under ACC-DEVOPS-PLANC-TAG-MANIFEST (COO-Q-20261031-0550-2). Re-verified 2026-10-31 on HEAD 7b1a51f plus the commit that carries this refresh, branch `devops/accel-consolidation-20261029`. The §7 SHIP list equals the `-t partner` sync set: 189 files.

## 1. Counts

| Set | Files |
| --- | --- |
| Workspace folder walk (excl. `.git`, MLflow experiment objects listed as files) | 297 |
| Git-tracked files (2026-10-31) | 284 |
| **SHIP = `-t partner` bundle sync set (2026-10-31)** | **189** (includes this manifest; full list in §7) |
| Git-tracked but excluded by `sync.exclude` | 95 |
| EXCLUDE (workspace walk, 2026-10-28) | 109 |

SHIP = git-tracked files minus the 20 `sync.exclude` patterns in `databricks.yml` (2026-10-28 basis: clean `git clone` minus `ops/`). Both apps in `databricks.yml` (retirement_plan, copper_task_board) and all 5 jobs/pipeline source paths resolve inside SHIP.

## 2. EXCLUDE list (with reason)

| Path | Files | Reason |
| --- | --- | --- |
| `apps/regulatory-assistant/` | 28 | Retired app (deleted; merged into retirement-plan Regulatory tab, ledger 108) |
| `apps/copper-map/` | 25 | LEGACY Plan B demo surface only; merged as Map/Risk tab; not in `databricks.yml` |
| `apps/commodity-dashboard/` | 25 | LEGACY Plan B demo surface only; merged as Commodity tab; not in `databricks.yml` |
| `experiments/*` | 11 | MLflow experiment objects, not exportable files |
| `bundle/resources/{apps,commodity_dashboard,copper_map,dig_triage,regulatory_assistant}.app.yml`, `serving_endpoints.yml`, `unity_catalog.yml` | 7 | Inert (not in the `include:` list); pending CEO delete batch H4 |
| `DEMO-RUNBOOK.md`, `DEMO-ROLLBACK-RECOVERY.md`, `DEMO-ENV-FREEZE-CHECKLIST.md`, `demo_kpi_cheat_sheet.md` | 4 | Merged into PARTNER-PLAYBOOK.md (ledger 57-60) |
| `P6_regulatory_rag_chain`, `data_gen/fix_coordinates`, `scripts/manual_inference_log_demo`, `scripts/monitor_drift_activation` | 4 | Retired notebooks, content merged (ledger 95, 86, 84, 85) |
| `ops/` (`operational_runbook`, `pre_demo_healthcheck.py`, `V2-INFRA-PLAN.md`) | 3 | Demo-workspace ops; hardcodes the internal Lakebase host |
| `.assistant_instructions.md`, `.databricks/` | 2 | Internal swarm charter (untracked) and local CLI state |

## 3. Notebooks (11 in workspace)

* SHIP (6): `beat1_risk_model_walkthrough`, `P6_supervisor_agent`, `data_gen/populate_h3_indexes`, `monitoring/v2_model_monitoring_runbook`, `scripts/batch_score_copper_risk` (job task), `06_demo_reset`.
* Demo-workspace only (1): `ops/operational_runbook`.
* Retired, excluded (4): see §2.

## 4. Hardcoded values in SHIP

* Secrets (`dapi…`, `ghp_…`, AWS keys, literal passwords): **0**.
* `/Users/stephen.hage` or the user email: **29 hits in 9 files, all Markdown docs, 0 in code** (P6 experiment path fixed in commit 012d593). Largest: `resources/DLP_PIPELINE_RUNBOOK.md` (19). This manifest adds 2 more, both in the §6 export command (source path in this workspace).
* Internal Lakebase host `ep-rough-bar-d229503i…`: **0 lines in `databricks.yml`** since 2026-10-30 (ACC-QA-DEF-PARTNER-DEPLOY-DEFAULTS). `lakebase_project` and `lakebase_host` have no default; `-t partner` fails fast unless both are passed. Reference values live only in `bundle/targets/reference_workspace.yml` (dev/staging/prod; excluded from bundle sync). Still present in `apps/copper-task-board/app.yaml` (superseded on bundle deploy by `config.env` = `${var.lakebase_host}`; kept because the live reference app reads it).
* Bundle sync (2026-10-30): `databricks.yml` `sync.exclude` mirrors the §2 EXCLUDE list. `bundle sync --dry-run --full -t partner` uploads 189 files (was 283): 0 files under the 3 retired app folders, 0 ledger-retired notebooks, 0 `ops/`, 0 non-Markdown files containing `stephen.hage`.
* Partner target sets `presets.trigger_pause_status: PAUSED`: the refresh, Lakebase sync and weekly scoring job schedules deploy PAUSED (seed job is manual). Unpause after the seed job has run and `copper_retirement_risk@champion` is registered.
* Doc-only host mentions remain in `resources/DEMO_DEPLOYMENT_RUNBOOK.md` and `resources/MANUAL_RUNBOOK.md`.

## 5. Validation

* `databricks bundle validate -t partner --var warehouse_id=<id> --var lakebase_project=<project> --var lakebase_host=<host>` on HEAD 7b1a51f (2026-10-31): **Validation OK!** All 7 included resource files are in the sync set (§7), and all 7 `source_code_path`/`notebook_path`/`python_file` targets resolve.
* Fail-fast check (2026-10-31): the same command without the Lakebase vars returns `Error: no value assigned to required variable lakebase_project`.
* `apps/retirement-plan` clean build: **NOT VERIFIED.** No `package-lock.json` is committed (lockfile present: no), so `npm ci` cannot run. Agent compute has `node` v22 but no `npm`, and fetching npm from the registry is blocked by the agent guardrail. CEO step H2a (commit a lockfile) still applies.

## 6. Human export command (CEO batch H2)

Preferred path (git): run H2a (commit `package-lock.json`), then `git push origin main` from the workspace Git folder. Partners `git clone` and drop the excluded paths below.

Fallback path (folder export), run from a local shell with the CLI authenticated to this workspace:

```
databricks workspace export-dir /Users/stephen.hage@databricks.com/copper-retirement ./copper-retirement-accelerator
cd ./copper-retirement-accelerator
rm -rf .git .databricks .assistant_instructions.md experiments ops \
  apps/regulatory-assistant apps/copper-map apps/commodity-dashboard \
  bundle/resources/apps.app.yml bundle/resources/commodity_dashboard.app.yml bundle/resources/copper_map.app.yml \
  bundle/resources/dig_triage.app.yml bundle/resources/regulatory_assistant.app.yml \
  bundle/resources/serving_endpoints.yml bundle/resources/unity_catalog.yml \
  DEMO-RUNBOOK.md DEMO-ROLLBACK-RECOVERY.md DEMO-ENV-FREEZE-CHECKLIST.md demo_kpi_cheat_sheet.md \
  P6_regulatory_rag_chain.py data_gen/fix_coordinates.py scripts/manual_inference_log_demo.py scripts/monitor_drift_activation.py
databricks bundle validate -t partner --var warehouse_id=<WAREHOUSE_ID> --var lakebase_project=<PARTNER_LAKEBASE_PROJECT> --var lakebase_host=<PARTNER_LAKEBASE_HOST>
```

## 7. SHIP file list (`-t partner` sync set, 189 files, 2026-10-31)

How it was computed: `git ls-files -z` (284) minus the `databricks.yml` `sync.exclude` patterns gives 189. This matches the 189 that `bundle sync --dry-run --full -t partner` measured at 7bb2ea1. Since 7bb2ea1 no files were added or removed (`git diff --name-status 7bb2ea1 HEAD` shows only M entries). `data/reference/regulatory/matrix.jsonl` has 86 rows.

* `./` (11): `.gitignore`, `06_demo_reset.py`, `BUILD-PLAN.md`, `P6_supervisor_agent.py`, `PARTNER-PLAYBOOK.md`, `README.md`, `SEMANTIC-MODELING-STANDARDS.md`, `beat1_risk_model_walkthrough.py`, `databricks.yml`, `pyproject.toml`, `requirements.txt`
* `apps/` (2): `APP_INVENTORY.md`, `BRAND_GUIDE.md`
* `apps/copper-task-board/` (4): `README.md`, `app.py`, `app.yaml`, `requirements.txt`
* `apps/copper-task-board/static/` (1): `index.html`
* `apps/retirement-plan/` (6): `PORT-MAP.md`, `README.md`, `REQUIREMENTS-V2.md`, `app.yaml`, `package.json`, `tsconfig.json`
* `apps/retirement-plan/client/` (2): `index.html`, `vite.config.ts`
* `apps/retirement-plan/client/src/` (2): `App.tsx`, `main.tsx`
* `apps/retirement-plan/client/src/components/` (10): `BudgetChart.tsx`, `ConstraintFlags.tsx`, `CostBenefitPanel.tsx`, `GanttTimeline.tsx`, `LakeLinkHeader.tsx`, `MigrationTable.tsx`, `PlanKPIs.tsx`, `RegulatoryChecklist.tsx`, `ScenarioCompare.tsx`, `WaveSelector.tsx`
* `apps/retirement-plan/client/src/components/shared/` (2): `TabBar.tsx`, `index.tsx`
* `apps/retirement-plan/client/src/lib/` (2): `formatters.ts`, `planApi.ts`
* `apps/retirement-plan/client/src/mock/` (1): `mockData.ts`
* `apps/retirement-plan/client/src/styles/` (1): `tokens.css`
* `apps/retirement-plan/client/src/tabs/` (2): `PendingPortTab.tsx`, `PlanTab.tsx`
* `apps/retirement-plan/client/src/tabs/commodity/` (1): `CommodityTab.tsx`
* `apps/retirement-plan/client/src/tabs/map/` (1): `MapTab.tsx`
* `apps/retirement-plan/client/src/tabs/regulatory/` (1): `RegulatoryTab.tsx`
* `apps/retirement-plan/client/src/tabs/triage/` (1): `App.tsx`
* `apps/retirement-plan/client/src/tabs/triage/components/` (7): `ActionLog.tsx`, `IncidentDetailPanel.tsx`, `IncidentForm.tsx`, `IncidentMap.tsx`, `IncidentTable.tsx`, `TriageAgentChat.tsx`, `TriageKPIs.tsx`
* `apps/retirement-plan/client/src/tabs/triage/lib/` (2): `formatters.ts`, `triageApi.ts`
* `apps/retirement-plan/client/src/tabs/triage/mock/` (1): `mockData.ts`
* `apps/retirement-plan/config/queries/` (5): `cost_benefit.sql`, `migration_status.sql`, `milestone_timeline.sql`, `plan_kpis.sql`, `wave_schedule.sql`
* `apps/retirement-plan/server/` (3): `databricksSQL.js`, `server.js`, `server.ts`
* `apps/retirement-plan/server/routes/` (4): `commodity.js`, `map.js`, `regulatory.js`, `triage.js`
* `apps/retirement-plan/tests/` (1): `smoke.spec.ts`
* `bundle/` (1): `PARTNER_EXPORT_MANIFEST.md`
* `bundle/resources/` (7): `copper_retirement_pipeline.pipeline.yml`, `copper_task_board.app.yml`, `lakebase_sync.job.yml`, `pipeline_refresh.job.yml`, `retirement_plan.app.yml`, `risk_scoring.job.yml`, `seed_synthetic_sources.job.yml`
* `dashboards/` (2): `ebitda_dashboard_config.json`, `status_dashboard_config.json`
* `data/app_gold/` (22): `copper_commodity_price_official.ddl.sql`, `copper_commodity_price_official.jsonl`, `copper_risk_predictions.ddl.sql`, `copper_risk_predictions.jsonl`, `gold_commodity_price_forecast.ddl.sql`, `gold_commodity_price_forecast.jsonl`, `gold_contractor_assignment_plan.ddl.sql`, `gold_contractor_assignment_plan.jsonl`, `gold_copper_recovery_schedule.ddl.sql`, `gold_copper_recovery_schedule.jsonl`, `gold_wave_schedule.ddl.sql`, `gold_wave_schedule.jsonl`, `manifest.json`, `retirement_cost_per_wire_center.ddl.sql`, `retirement_cost_per_wire_center.jsonl`, `retirement_milestones.ddl.sql`, `retirement_milestones.jsonl`, `roi_calculator_assumptions.ddl.sql`, `roi_calculator_assumptions.jsonl`, `silver_budget_allocation.ddl.sql`, `silver_budget_allocation.jsonl`, `v_partner_value_wire_center.ddl.sql`
* `data/fixtures/synthetic/` (6): `circuit_inventory.csv`, `contractor_registry.csv`, `copper_recovery.csv`, `gis_assets.csv`, `gis_assets.geojson`, `manifest.json`
* `data/reference/regulatory/` (2): `matrix.jsonl`, `register.jsonl`
* `data_gen/` (13): `SPEC_commodity_price.md`, `SPEC_contractor_performance.md`, `SPEC_copper_loop_plant.md`, `SPEC_dig_safe_incident.md`, `SPEC_migration_tracking.md`, `SPEC_regulatory_requirements.md`, `SPEC_wire_center_boundary.md`, `__init__.py`, `populate_h3_indexes.py`, `seed_source_tables.py`, `source_table_contract.json`, `synthetic_assets.py`, `synthetic_sources.py`
* `monitoring/` (1): `v2_model_monitoring_runbook.py`
* `monitoring/cdm_tmforum.copper_retirement.risk_inference_unpacked/` (1): `risk_inference_unpacked Monitoring.lvdash.json`
* `pipeline/` (11): `bronze_copper_devices.sql`, `bronze_copper_services.sql`, `bronze_dig_safe_incidents.sql`, `gold_circuit_revenue_at_risk.sql`, `gold_contractor_scorecard.sql`, `gold_retirement_executive_summary.sql`, `gold_wire_center_scorecard.sql`, `silver_contract_constraints.sql`, `silver_copper_plant_enriched.sql`, `silver_device_service_impact.sql`, `silver_revenue_recognition_constraints.sql`
* `resources/` (17): `00-master-architecture.md`, `BRANCH_STRATEGY.md`, `BRAND_GUIDE_LAKELINK_FIBER.md`, `DEMO_DEPLOYMENT_RUNBOOK.md`, `DLP_PIPELINE_RUNBOOK.md`, `MANUAL_RUNBOOK.md`, `ML_MODEL_CARD.md`, `ML_PRODUCTION_READINESS.md`, `commodity-workforce.md`, `demo-script.md`, `dig-safe-triage.md`, `model_card.md`, `monitoring_baseline.md`, `post_demo_monitoring_plan.md`, `regulatory-jurisdictions.md`, `technical-reference.md`, `zero-copper-plan.md`
* `resources/uc-pages/` (9): `00_schema_overview.md`, `01_physical_plant.md`, `02_circuits_and_services.md`, `03_customer_impact.md`, `04_risk_and_ml.md`, `05_regulatory.md`, `06_financial_and_ebitda.md`, `07_operations.md`, `FULL_COLUMN_REFERENCE.md`
* `risk/` (3): `MODEL_CARD.md`, `__init__.py`, `scoring.py`
* `scripts/` (6): `batch_score_copper_risk.py`, `generate_synthetic_sources.py`, `load_regulatory_reference.py`, `provision_app_objects.py`, `run_thin_slice.py`, `sync_gold_to_lakebase.py`
* `src/metric_views/` (4): `copper_customers_impacted.sql`, `copper_ebitda_impact_achieved.sql`, `copper_ebitda_impact_forecast.sql`, `copper_retirement_project_status.sql`
* `tests/` (5): `__init__.py`, `regression_suite.py`, `test_risk_scoring.py`, `test_synthetic_assets.py`, `test_synthetic_sources.py`
* `uc-pages/` (6): `circuits-services.md`, `customer-impact.md`, `financial-operations.md`, `physical-plant.md`, `regulatory-compliance.md`, `risk-ml.md`

Residual, not changed in this refresh (that would need `databricks.yml` edits and a G3 re-verify): `resources/model_card.md` and `resources/ML_MODEL_CARD.md` are superseded by `risk/MODEL_CARD.md` (ledger 196/197). `resources/DEMO_DEPLOYMENT_RUNBOOK.md` and `resources/MANUAL_RUNBOOK.md` mention the reference Lakebase host. All four still ship. Candidates for `sync.exclude` after Plan C.
