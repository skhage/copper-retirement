# Unified Accelerator App — Port Map (ACC-APP-PORT-INVENTORY)

**Author:** @app-developer | **Date:** 2026-10-24 | **Decision:** DEC-ACCEL-UNIFIED-APP | **Directive:** APP SIMPLIFICATION (id 12)

Target: evolve `apps/retirement-plan` (AppKit: React + Vite + Express) into the ONE partner-facing app with tabs **Map/Risk, Plan, Dig Triage, Regulatory, Commodity**. `copper-task-board` stays as the internal ops app. End state = 2 apps (from 6).

Snapshot of deployed apps (2026-10-24, `w.apps.get`): all 6 ComputeState.ACTIVE. Last deployments: copper-map 2026-09-19, regulatory-assistant 2026-09-18, commodity-dashboard 2026-09-20, retirement-plan 2026-09-20, dig-triage 2026-09-21, copper-task-board 2026-09-12.

---

## 1. Target structure (inside apps/retirement-plan)

```
client/src/
  App.tsx                    -> shell: one LakeLinkHeader + top-level tab bar (5 tabs), URL hash routing (#map, #plan, #triage, #regulatory, #commodity)
  styles/tokens.css          -> shared design tokens from @designer (ACC-APP-IA) -- single file, partner rebrand = swap this file
  components/shared/         -> LakeLinkHeader, KpiCard, SyntheticBadge, CitationLink, ErrorBoundary (dedupe 5 copies of LakeLinkHeader)
  tabs/map/                  -> from copper-map
  tabs/plan/                 -> existing retirement-plan components (move, do not rewrite)
  tabs/triage/               -> from dig-triage
  tabs/regulatory/           -> from regulatory-assistant
  tabs/commodity/            -> from commodity-dashboard
  lib/formatters.ts          -> merge 4 copies
server/
  server.js                  -> single Express app; mounts routers below
  routes/plan.js | map.js | triage.js | regulatory.js | commodity.js
  databricksSQL.js           -> single SQL-warehouse helper (merge dig-triage + retirement-plan copies)
config/queries/              -> all .sql files, prefixed by tab (map_*.sql, triage_*.sql ...)
```

Runtime config (app.yaml env, no hardcoded values in code): `DATABRICKS_WAREHOUSE_ID` (today 7b65956f30d66feb), `CATALOG`=cdm_tmforum, `SCHEMA`=copper_retirement, `VS_INDEX`=cdm_tmforum.copper_retirement.regulatory_doc_chunks_vs_index, `LLM_ENDPOINT`=databricks-meta-llama-3-3-70b-instruct, `RISK_ENDPOINT`=copper-retirement-risk, `LAKEBASE_ENDPOINT`=projects/copper-task-board/branches/production/endpoints/primary. These become DAB variables for ACC-DAB-ONE-COMMAND.

Union of npm deps: express, react, react-dom, lucide-react, react-simple-maps (Regulatory jurisdiction map). Map tab needs a map lib (see 2.1).

---

## 2. Per-source-app port plan

### 2.1 copper-map -> Map/Risk tab  (ACC-APP-PORT-MAP)
* **Runtime:** Python **Dash** (`app.py` 1,029 lines + `data.py` 518 lines) is the deployed implementation (DEC-MAP-DASH-V-APPKIT). A React `client/` scaffold also exists (9 components, never deployed, 18+ brand violations).
* **Port approach:** React port. Reuse `client/src/components/{MapView,FilterPanel,RiskLegend,SummaryKPIs,DeviceTable,DevicePopover,ImpactDetailPanel,WhatIfChat}.tsx` as the starting point; re-implement the Dash data functions from `data.py` as Express routes. Highest-effort port (Python -> Node).
* **New routes:** `GET /api/map/kpis`, `/api/map/hex-risk?res=`, `/api/map/wire-centers`, `/api/map/devices?hex=`, `/api/map/device/:id`, `/api/map/filters`.
* **Data sources (UC, via SQL warehouse):** `copper_retirement.gold_wire_center_scorecard` (103), `copper_retirement.gold_retirement_executive_summary`, `tmf_enterprise.physical_device`, `tmf_resource.alarm`, `tmf_service.customer_facing_service`, `tmf_shared.geographic_address`; SQL files `device_detail, filter_options, hex_risk_summary, map_kpis, wire_center_boundaries`.
* **Lakebase (reuse):** `copper_app.device_risk_map` (2,672), `copper_app.wire_center_boundaries` (1,699), `copper_app.wire_center_scorecard` (103), `copper_app.executive_summary` (50).
* **Env:** `H3_RESOLUTION` (default 4), `LIVE_DATA`.
* **Risk:** serving endpoint `copper-retirement-risk` for what-if (WhatIfChat).
* **Delete after verify:** Databricks App `copper-map` + folder `apps/copper-map` (25 files incl. app.py, data.py, requirements.txt).

### 2.2 dig-triage -> Dig Triage tab  (ACC-APP-PORT-TRIAGE)
* **Runtime:** AppKit React + Express (`server/server.js` 288 lines, `server/databricksSQL.js` 216 lines). Straight move.
* **Components:** IncidentForm, IncidentMap, IncidentTable, IncidentDetailPanel, TriageAgentChat, TriageKPIs, ActionLog; `lib/triageApi.ts`.
* **Routes to mount under `/api/triage`:** `/health, /kpis, /incidents, /incident, /incident/:id, /nearby, /reroute/:id, /action, /chat`.
* **Data sources:** UC functions `copper_retirement.incident_lookup`, `proximity_search`, `reroute_suggest`; table `copper_retirement.silver_dig_incident_enriched` (5,000); `tmf_resource.dig_safe_incident`, `tmf_businesspartner.bp_agreement`, `tmf_enterprise.work`, `tmf_shared.network_route`; real 811 source to wire in: `cdm_tmforum.provable_resilience_intelligence.stg_811_dig_ticket` (directive 13).
* **Lakebase (reuse):** `copper_app.dig_incidents` (5,000), `copper_app.gold_reroute_options` (2,258), `copper_app.incident_actions` (0 - human-in-loop write target), `copper_app.triage_agent_sessions` (0).
* **Delete after verify:** App `dig-triage` + folder `apps/dig-triage` (28 files).

### 2.3 regulatory-assistant -> Regulatory tab  (ACC-APP-PORT-REG; also depends on ACC-REG-JURISDICTION-MATRIX)
* **Runtime:** AppKit React + Express (`server/server.js` 528 lines).
* **Components:** RegAgentChat, CitationSidebar, DocumentBrowser, JurisdictionMap (react-simple-maps), ComplianceChecklist, RegKPIs, SuggestedQuestions, ErrorBoundary; `api/ragChat.ts`, `api/corpus.ts`. `REG_UX_BACKLOG.md` -> do NOT port (superseded per-app backlog).
* **Routes under `/api/regulatory`:** `/agent/chat`, `/corpus/documents`, `/corpus/kpis`, `/corpus/search`, NEW `/jurisdictions`, NEW `/sources`.
* **RAG (reuse, no new endpoints):** VS index `cdm_tmforum.copper_retirement.regulatory_doc_chunks_vs_index` on `demo_telco_vs_endpoint`; LLM `databricks-meta-llama-3-3-70b-instruct` (pay-per-token).
* **Citation contract (charter hard rule):** every chat answer and every jurisdiction row renders `source title` + clickable `official_url`, joined from `copper_retirement.regulatory_source_register` (36 rows; cols source_id, title, citation, official_url, verification_status, is_synthetic, last_verified). Server filters chunks where `is_synthetic = true` (DEC-REG-SOURCE-VOLUME); if no real-source chunk is retrieved, answer is replaced with "No verified source found - flagged gap" rather than an uncited answer. Rows with verification_status != verified show an UNVERIFIED badge.
* **Blocking data gaps (owned by others):** `regulatory_doc_chunks` lacks is_synthetic/source_url/jurisdiction columns (ACC-REG-PARSE-INDEX, @data-engineer); `state_puc_jurisdiction_requirements` (56 legacy synthetic rows) lacks source_id/official_url (ACC-REG-JURISDICTION-MATRIX, @data-analyst). `fcc_regulatory_document` (305) and `copper_app.regulatory_documents` (297) are synthetic -> replace with register. New: show `copper_retirement.fcc_retirement_workflow` (12 steps) as an FCC workflow stepper.
* **Delete after verify:** App `regulatory-assistant` + folder `apps/regulatory-assistant` (28 files).

### 2.4 commodity-dashboard -> Commodity tab  (ACC-APP-PORT-COMMODITY)
* **Runtime:** AppKit React + Express (`server/server.js` 66 lines) - backend is **100% mock** (random-noise forecast, mock assign).
* **Components:** CommodityKPIs, PriceChart, SellHoldRecommendation, RecoveryTracker, ContractorScorecard, FxContextPanel.
* **Routes under `/api/commodity`:** replace mocks with `/prices` (REAL: `copper_retirement.copper_commodity_price_official`, 417 monthly IMF PCOPPUSDM rows via FRED, 1992-01..2026-09), `/forecast` (`copper_app.commodity_forecast` 72, labeled synthetic/model), `/sell-hold` (`copper_app.sell_hold_decisions` 20), `/contractors` (`copper_retirement.contractor_performance` 10,000 / `copper_app.contractor_scorecard`), `/recovery` (`copper_app.gold_copper_recovery_schedule` 103), `/fx` (`refinitiv_fx_source.gl_daily_rates`).
* **Broken refs to fix during port:** SQL files reference `copper_retirement.recovered_copper_tracking` which does NOT exist (TABLE_OR_VIEW_NOT_FOUND) -> use `copper_app.gold_copper_recovery_schedule`. `copper_retirement.copper_commodity_price` (10,482) is synthetic -> prefer `_official`.
* **Value tie-in:** surface `copper_retirement.copper_partner_value` metric view (ACC-DA-VALUE-METRICS) KPIs.
* **Delete after verify:** App `commodity-dashboard` + folder `apps/commodity-dashboard` (25 files).

### 2.5 retirement-plan (host) -> Plan tab  (ACC-APP-UNIFY-SHELL)
* Existing inner tabs (gantt/table/budget/regulatory/scenarios) become Plan sub-tabs. Plan's own `RegulatoryChecklist` stays (wave checklist from `copper_app.regulatory_checklist_status`, 2,200) but must link to the Regulatory tab citations.
* Routes `/api/plan/*` (11) unchanged. Lakebase: `copper_app.retirement_plan` (200), `retirement_milestones` (927), `regulatory_checklist_status`, `plan_edit_audit_log` (50), `wave_schedule_versions` (5); UC `gold_wave_schedule` (103), `gold_contractor_assignment_plan` (35).
* app.yaml: `resources.sql-warehouse` id is a TODO; tag key `project` is deprecated -> `telco_project: copper-retirement` (directive 6). Header `dataSource="MOCK"` -> per-tab SyntheticBadge.

---

## 3. Other findings
* **copper-task-board** is deployed from `/Users/stephen.hage@databricks.com/copper-task-board-src`, NOT `apps/copper-task-board`. The two `static/index.html` copies differ (38,764 vs 38,833 chars). ACC-LEGACY-TASKBOARD-WCAG must edit the deployed source; `apps/copper-task-board` is a stale duplicate -> candidate for removal by @devops (ledger 'removed').
* `apps/designer_sweep_2026_10_04.ipynb` and `apps/designer_sweep_2026_10_08.ipynb` are scratch notebooks named in directive 11 -> removal candidates (owner @devops/@designer).
* 5 duplicated `LakeLinkHeader.tsx` (110-112 lines each) and 4 `formatters.ts` collapse to one each.
* Every source app has `tests/smoke.spec.ts` -> merge into one `tests/smoke.spec.ts` with one describe per tab (handoff to @qa).

## 4. Execution order & ledger
1. ACC-APP-IA (@designer) delivers tokens file -> 2. ACC-APP-UNIFY-SHELL (shell + Plan tab; edits existing app, no new app => no ledger offset needed) -> 3. ACC-APP-PORT-TRIAGE (lowest risk, same stack) -> 4. ACC-APP-PORT-COMMODITY -> 5. ACC-APP-PORT-MAP (Dash->React) -> 6. ACC-APP-PORT-REG (after jurisdiction matrix + parse/index).
For each port: copy files -> deploy retirement-plan -> verify tab against source app -> `w.apps.stop` + `w.apps.delete` old app -> delete source folder -> `asset_ledger` row (action='consolidated', asset_type='app', merged_into='retirement-plan').
