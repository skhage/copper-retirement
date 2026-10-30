# Copper Retirement Accelerator — unified app (`retirement-plan`)

One partner-facing Databricks App with five tabs: **Map & Risk**, **Plan**, **Dig Triage**,
**Regulatory**, **Commodity & Value** (DEC-ACCEL-UNIFIED-APP). The app name stays `retirement-plan`
so existing deploy wiring keeps working. The internal ops app `copper-task-board` is separate and stays.

## Release notes — Plan C, release `accel-r1-planc-20261031` (DEC-PLANC-20261031, DEC-PLANC-MANIFEST-20261030)

**Status: DEPLOYED BUT NOT DEMO-VERIFIED.**

* The reference workspace runs deployment `01f1d422d72a18da86bfbf70bf80e893` (2026-10-30 05:29 UTC, state ACTIVE).
* No one has watched a rendered end-to-end demo of the live app. Agent tokens get 401/SSO at the app URL.
* Every route has been exercised from source with the server harness, as the developer identity. They
  return HTTP 200 with that identity, and HTTP 403 "Data access pending" when grants are missing.
* The live app service principal (`d96a80a5-cf49-4947-b518-164cd950f872`) has **no UC grants**. Checked
  2026-10-30 via effective-permissions: only `account users` READ_METADATA is inherited. Until those
  grants exist, the deployed tabs show their error state, not data.

### 1. Every tab depends on the app SP grants (PARTNER-PLAYBOOK §5b-2, runbook step R1)

After deploying, the partner must grant the app's service principal:

* `USE CATALOG` on `<catalog>`
* `USE SCHEMA`, `SELECT` and `EXECUTE` on `<catalog>.<schema>`
* `SELECT` on the 811 table configured in `DIG_811_TABLE`
* Nothing on the serving endpoint: Map reads precomputed `copper_risk_predictions` and only displays
  the `SERVING_ENDPOINT` name
* `CAN_USE` on the SQL warehouse

| Tab | Route prefix | Reads | Without grants |
|---|---|---|---|
| Map & Risk (default) | `/api/map/*` | `copper_risk_predictions`, `gold_wire_center_scorecard`, `gold_retirement_executive_summary` | Error state ("Data access pending"), no map points |
| Plan | `/api/plan/*` | `gold_wave_schedule`, `silver_budget_allocation`, `retirement_milestones`, `jurisdiction_requirements_cited` | KPI cards and checklist show an error state. Mock fallback was removed (`USE_MOCK_DATA = false`) |
| Dig Triage | `/api/triage/*` | `DIG_811_TABLE`, `silver_dig_incident_enriched`, functions `incident_lookup` / `proximity_search` / `reroute_suggest` | KPIs show the `denied` state ("Data access pending"), and the incident table is empty |
| Regulatory | `/api/regulatory/*` | `regulatory_doc_chunks`, `regulatory_source_register`, `jurisdiction_requirements_cited`, `LLM_ENDPOINT` (ai_query) | `/ask` and the matrix return 403 |
| Commodity & Value | `/api/commodity/*` | `copper_commodity_price_official`, `gold_commodity_price_forecast`, `roi_calculator_assumptions`, `v_partner_value_wire_center`, `gold_contractor_scorecard` | Charts show an error state |

No tab silently shows mock data in place of live data. Missing grants always surface as an explicit error.

### 2. Regulatory tab: grounding, citations and the jurisdiction pre-filter

* **Citations.** Every `/ask` answer and every jurisdiction-matrix row shows a source title and an official
  URL. When retrieval finds no relevant source, the answer is `INSUFFICIENT SOURCES` (grounded=false)
  and the app does not guess.
* **Public-domain sources only.** Retrieval and the sources KPI exclude every register entry with
  `is_public_domain = false`. Today that is IND-CGA-BP21 (194 chunks), which is kept for reference only
  and never shown. Synthetic chunks (528) are excluded too (`is_synthetic = false`).
* **Reference counts on 2026-10-30:** 2,898 chunks in total. 2,176 are real and public-domain, 194 are CGA
  reference-only, and 528 are synthetic (pending CEO DELETE). The matrix (`jurisdiction_requirements_cited`)
  has 86 rows, and none is missing a URL.
* **State pre-filter** (`resolveJurisdiction` / `detectState` in `server/routes/regulatory.js`):
  * When the selector names a state, retrieval is filtered to that state plus federal (`US`).
  * When the selector is "All" and the question names **exactly one** state, that state is detected and
    used as the filter. The UI shows it as "detected in question".
  * **Questions that name two or more states, or none, get NO pre-filter** (`jurisdiction_source = none`).
    Answers can then cite any state, so users should pick a state in the selector for multi-state
    comparisons. This is the @designer advisory in ACC-DES-REG-JURIS-NOTE-REVIEW.
  * Bare 2-letter codes that collide with English words (OR, IN, ME, OK, HI, OH, PA, …) are not detected.
    Use the full state name instead.
* **Coverage.** Real sources cover federal (US) plus the 6 demo states. A regulatory fact outside those
  sources is a gap, never an invented citation.

### 3. Map & Risk and Commodity & Value are code-complete but NOT YET PORTED

* The tabs live in `client/src/tabs/map/MapTab.tsx` + `server/routes/map.js` and in
  `client/src/tabs/commodity/CommodityTab.tsx` + `server/routes/commodity.js`.
* ACC-APP-PORT-MAP and ACC-APP-PORT-COMMODITY stay **blocked**. Their verification step (rows returned by
  the live unified tab) needs the SP grants above.
* The legacy apps `copper-map` and `commodity-dashboard` therefore remain deployed, with a LEGACY banner,
  in the reference workspace. Per DEC-LIVE-2APPS-CUTOVER-20261029 they are stopped, then deleted ≥72 h
  later, only after the grants land, both ports are verified and the @qa 5-tab smoke test passes.
* The partner package ships only 2 apps: this app and `copper-task-board`. The reference workspace still
  has 4.
* `dig-triage` and `regulatory-assistant` are already ported and deleted.

### 4. Synthetic data labels

* Network, device, customer, plant and contractor data is **SYNTHETIC**. It is labeled in UC table
  comments, and in the UI with `SyntheticBadge`: Map header "SYNTHETIC NETWORK DATA", Commodity
  workforce/value panels, and Plan components.
* The commodity forecast label is driven by the table comment, and stays synthetic until
  DEC-COMMODITY-REAL-RETRAIN lands. The price history is real (IMF PCOPPUSDM via FRED, with `source_url`
  per row).
* Synthetic decommission cost and opex-high values are `PARTNER_DISCOVERY_INPUT`s, not benchmarks
  (DEC-DECOM-PARTNER-INPUT-20261028).

### 5. Other known limits

* The risk endpoint `copper-retirement-risk` serves model V5. Its predictions are dated 2026-09-13.
* The live reference app has no `sql-warehouse` resource attached, so `app.yaml` carries a literal
  `DATABRICKS_WAREHOUSE_ID` (ACC-DEVOPS-APP-WH-RESOURCE). Partner DAB deploys use `value_from: sql-warehouse`.
* There is no npm lockfile, and no `tsc`/`vite` build has been run by agents (the registry is blocked).
  The Apps runtime builds via `npm install && npm run build`.
* Plan write-back (drag-to-reschedule) is not implemented. Plan is read-only.

## Architecture

* React/TypeScript client (`client/`) plus a Node ESM server (`server/server.js`, `server/routes/*.js`).
* Data comes from UC via the SQL Statement API on `DATABRICKS_WAREHOUSE_ID` (named parameters only).
  Data location is set by `CATALOG` / `SCHEMA`.
* Theme: one shared token file `client/src/styles/tokens.css` (white-label: `--brand-name`,
  `--brand-footprint-label`), WCAG 2.1 AA.
* Config: `app.yaml` (manual deploy) and `bundle/resources/retirement_plan.app.yml` (DAB, supersedes `app.yaml`).
* Port history: `PORT-MAP.md`. Requirements: `REQUIREMENTS-V2.md`.

## Governance tags

* `telco_project: copper-retirement`
* `developer: copper-app`

---

*Network, customer and plant data shown is SYNTHETIC. Regulatory answers cite real official sources.
Part of the Copper Retirement Solution Accelerator.*
