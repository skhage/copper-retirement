# Partner Export Manifest — Copper Retirement Solution Accelerator

Owner: @devops. Task: ACC-DEVOPS-PLANB-EXPORT-MANIFEST (answers COO-Q-20261028-0550-3). Verified 2026-10-28 on HEAD 012d593 (49 commits ahead of origin/main 4227295).

## 1. Counts

| Set | Files |
| --- | --- |
| Workspace folder walk (excl. `.git`, MLflow experiment objects listed as files) | 297 |
| Git-tracked files | 282 |
| **SHIP (partner package)** | **188** (+1 = this manifest) |
| EXCLUDE | 109 |

SHIP = clean `git clone` of HEAD (191 files) minus `ops/` (3 files, demo-workspace only). Both apps in `databricks.yml` (retirement_plan, copper_task_board) and all 5 jobs/pipeline source paths resolve inside SHIP.

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
* Internal Lakebase host `ep-rough-bar-d229503i…`: in `databricks.yml` as the `lakebase_host` variable default (partners must override) and in `apps/copper-task-board/app.yaml` (superseded by bundle `config.env` = `${var.lakebase_host}`). Doc-only mentions remain in `resources/DEMO_DEPLOYMENT_RUNBOOK.md` and `resources/MANUAL_RUNBOOK.md`.

## 5. Validation

* `databricks bundle validate -t partner --var warehouse_id=<id>` on HEAD 012d593: **Validation OK!** All 7 included resource files are present in the pruned clone, and all 7 `source_code_path`/`notebook_path`/`python_file` targets resolve.
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
databricks bundle validate -t partner --var warehouse_id=<WAREHOUSE_ID> --var lakebase_host=<PARTNER_LAKEBASE_HOST>
```
