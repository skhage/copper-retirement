# Copper Retirement Solution Accelerator

A Databricks Solution Accelerator that helps telecommunications operators plan, execute, and monetize the retirement of legacy copper networks. It combines risk scoring, regulatory compliance, commodity forecasting, geospatial analysis, and an AI-powered regulatory assistant into a single deployable package designed for SI/consulting partners to sell and deliver copper retirement / copper harvesting SOWs.

## Table of Contents

* [What This Does](#what-this-does)
* [Architecture](#architecture)
* [Prerequisites](#prerequisites)
* [Quick Start (One-Command Deploy)](#quick-start-one-command-deploy)
* [Repository Structure](#repository-structure)
* [Key Databricks Resources](#key-databricks-resources)
* [The Demo Scenario](#the-demo-scenario-lakelink-fiber)
* [Data Disclosure](#data-disclosure)
* [Industry Context](#industry-context)
* [Known Gaps and Handoff Items](#known-gaps-and-handoff-items)
* [Documentation Index](#documentation-index)

---

## What This Does

Copper networks are being retired worldwide as operators migrate to FTTP. This accelerator gives a partner everything needed to:

1. **Assess retirement risk** - A GBT risk model scores 103 wire centers across 6 risk dimensions (customer impact, revenue at risk, regulatory readiness, network complexity, decommissioning cost, commodity recovery value). Predictions are served via a Model Serving endpoint and refreshed weekly.
2. **Navigate regulations** - A regulatory RAG assistant answers questions about FCC Section 214 discontinuance, 47 CFR network change disclosure, state PUC rules, 811/one-call damage prevention, OSHA excavation safety, PHMSA, FHWA, and EPA lead-sheathed cable guidance. Every answer cites an official source URL. 2,635 real chunks from 104 official sources in `regulatory_doc_chunks`.
3. **Forecast commodity revenue** - A copper price forecaster (LightGBM / IMF drift model) projects salvage value over 3-18 month horizons, feeding an ROI calculator that estimates per-wire-center copper recovery pounds, LME value, and net decommissioning cost.
4. **Plan the retirement wave** - A Lakeflow Spark Declarative Pipeline (bronze -> silver -> gold) enriches copper plant data with geospatial H3 indices, revenue at risk, and contractor scorecards, producing wave-planning tables.
5. **Run the demo** - A unified tabbed Databricks App (`retirement-plan`) presents Map/Risk, Plan, Dig Triage, Regulatory, and Commodity tabs. A second app (`copper-task-board`) provides an internal ops dashboard backed by Lakebase Postgres.

## Architecture

```
                         +-----------------------+
                         |  Synthetic Sources    |
                         | (OSS, GIS, circuits,  |
                         |  contractors, 811)    |
                         +-----------+-----------+
                                     |
                          Auto Loader / Seed Job
                                     v
                         +-----------------------+
                         |  Bronze Tables        |
                         | (raw ingest)          |
                         +-----------+-----------+
                                     |
                         Lakeflow SDP Pipeline
                         (8 materialized views)
                                     v
                         +-----------------------+         +-----------------------+
                         |  Silver Tables        |         |  Regulatory Source    |
                         | (enriched, H3-indexed)|         |  Docs (UC Volume)     |
                         +-----------+-----------+         | 104 official URLs    |
                                     |                   +-----------+-----------+
                                     |                               |
                                     v                               v
                    +-----------------------+       +-----------------------+
                    |  Gold Tables          |       | regulatory_doc_chunks  |
                    | (scorecard, revenue   |       | (2,635 real chunks)    |
                    |  at risk, contractor,  |       | search_regulatory_     |
                    |  exec summary)         |       | chunks() TVF           |
                    +-----------+-----------+       +-----------+-----------+
                                |                               |
                 +--------------+--------------+        |
                 |                             |        |
                 v                             v        v
    +-----------------------+     +-----------------------+
    | Risk Model (GBT v6)   |     | Unified App           |
    | MLflow + UC Registry  |     | (retirement-plan)     |
    | Serving Endpoint      |     |  Map/Risk | Plan      |
    | copper-retirement-risk|     |  Dig Triage | Reg     |
    +-----------------------+     |  Commodity            |
                                  +-----------------------+
                                          |
                                          v
                                  +-----------------------+
                                  | Lakebase Postgres      |
                                  | (copper-task-board)    |
                                  | Task board + ops data  |
                                  +-----------------------+
```

## Prerequisites

The partner target deploys to a **fresh Databricks workspace**. Before deploying, ensure:

| Requirement | How to Verify |
|---|---|
| Databricks workspace with serverless compute | Workspace URL accessible; `databricks clusters list` returns results |
| Unity Catalog enabled; a catalog exists (e.g. `cdm_tmforum`) | `SHOW CATALOGS` returns it |
| SQL warehouse (any size) | `databricks warehouses list` returns an ID |
| Lakebase Postgres project | `databricks postgres list-projects` returns one |
| Databricks CLI v0.240+ with bundle support | `databricks bundle --version` |
| Python 3.10+ with `databricks-sdk>=0.118.0` | `pip show databricks-sdk` |
| Git access to this repo | `git clone` succeeds |

The bundle does NOT create the catalog, SQL warehouse, Lakebase project, or serving endpoint. Those are prerequisites created by the workspace admin. The `partner` target creates the `copper_retirement` schema inside the existing catalog.

## Quick Start (One-Command Deploy)

```bash
# Clone the repo
git clone https://github.com/skhage/copper-retirement.git
cd copper-retirement

# Deploy to a fresh partner workspace (all job schedules deploy PAUSED)
databricks bundle deploy -t partner \
  --var warehouse_id=<WAREHOUSE_ID> \
  --var lakebase_project=<YOUR_LAKEBASE_PROJECT> \
  --var lakebase_host=<YOUR_LAKEBASE_HOST>

# Seed the synthetic source tables (creates upstream bronze sources)
databricks bundle run -t partner seed_synthetic_sources_job

# Unpause the pipeline refresh job to build bronze -> silver -> gold
databricks jobs run-now --job-name pipeline_refresh
```

**Optional overrides** (see `databricks.yml` header for full list):
```bash
--var catalog_name=...      # default: cdm_tmforum
--var schema_name=...       # default: copper_retirement
--var serving_endpoint=... # default: copper-retirement-risk
--var llm_endpoint=...     # default: databricks-claude-sonnet-4-5
```

**Post-deploy grants** (catalog owner, once per workspace):
```bash
SP=$(databricks apps get retirement-plan-partner --output json | jq -r .service_principal_client_id)
```
Then in a SQL editor:
```sql
GRANT USE CATALOG ON CATALOG <catalog_name> TO `<SP>`;
GRANT USE SCHEMA, SELECT ON SCHEMA <catalog_name>.provable_resilience_intelligence TO `<SP>`;
```

**To retrain the risk model** (partner-retrainable template):
Open and run the notebook `beat1_risk_model_walkthrough` in the workspace. It trains a GBT, logs to MLflow, registers to UC as `copper_retirement_risk@champion`, and deploys to the serving endpoint.

## Repository Structure

```
copper-retirement/
|
+-- databricks.yml                 # DAB bundle: all resources, targets, variables
+-- PARTNER-PLAYBOOK.md             # Partner-facing playbook (start here for SOW work)
+-- BUILD-PLAN.md                   # Original build plan (phased work breakdown)
+-- README.md                       # This file
|
+-- pipeline/                       # Lakeflow SDP SQL definitions (bronze/silver/gold)
|   +-- bronze_copper_devices.sql
|   +-- bronze_copper_services.sql
|   +-- bronze_dig_safe_incidents.sql
|   +-- silver_copper_plant_enriched.sql
|   +-- silver_device_service_impact.sql
|   +-- silver_contract_constraints.sql
|   +-- silver_revenue_recognition_constraints.sql
|   +-- gold_wire_center_scorecard.sql
|   +-- gold_circuit_revenue_at_risk.sql
|   +-- gold_contractor_scorecard.sql
|   +-- gold_retirement_executive_summary.sql
|
+-- risk/                           # Risk scoring module
|   +-- scoring.py                  # GBT feature engineering + scoring logic
|   +-- MODEL_CARD.md               # Model card (v6 champion)
|
+-- apps/                           # Databricks Apps
|   +-- retirement-plan/            # Unified accelerator app (5 tabs: Map/Risk, Plan, Dig Triage, Regulatory, Commodity)
|   +-- copper-task-board/          # Internal ops dashboard (Lakebase-backed)
|   +-- BRAND_GUIDE.md              # Design tokens, brand colors, WCAG AA standards
|   +-- APP_INVENTORY.md            # App inventory and consolidation log
|
+-- bundle/                         # Declarative Automation Bundle resources
|   +-- resources/                  # Job, pipeline, app YAML definitions
|   +-- targets/                    # Reference workspace targets (dev/staging/prod)
|   +-- PARTNER_EXPORT_MANIFEST.md  # What ships vs. what is excluded
|
+-- data/                           # Synthetic fixtures + regulatory reference data
|   +-- fixtures/synthetic/          # Deterministic demo data (OSS, GIS, circuits, contractors)
|   +-- reference/regulatory/       # Offline regulatory exports (register, matrix, chunks .jsonl)
|
+-- data_gen/                       # Synthetic data generation scripts
+-- src/metric_views/                # UC metric view definitions (partner value KPIs)
+-- experiments/                    # MLflow experiments (regulatory RAG eval)
+-- monitoring/                     # Model monitoring runbooks
+-- ops/                            # Operational runbooks, health checks
+-- resources/                      # Architecture docs, model cards, brand guides
+-- scripts/                        # Utility scripts (synthetic gen, inference demo)
+-- tests/                          # Regression test suite
+-- uc-pages/                       # UC Glossary pages (semantic modeling)
```

## Key Databricks Resources

### Tables (cdm_tmforum.copper_retirement)

| Table | Description | Rows (demo) |
|---|---|---|
| `regulatory_doc_chunks` | Real regulatory text chunks from official sources | 3,163 (2,635 real + 528 synthetic) |
| `regulatory_source_register` | Register of all regulatory sources with official URLs | 117 |
| `state_puc_jurisdiction_requirements` | State-by-state PUC requirements matrix | - |
| `gold_wire_center_scorecard` | Risk-scored wire centers (6 dimensions) | 103 |
| `gold_circuit_revenue_at_risk` | Revenue at risk per circuit | - |
| `gold_contractor_scorecard` | Contractor capacity and performance scores | - |
| `gold_retirement_executive_summary` | Executive KPIs (revenue at risk, customers impacted) | - |
| `copper_commodity_price_official` | Monthly real copper price (LME-based) | - |

### Pipeline
* **Lakeflow SDP** (`copper_retirement_pipeline`): 3 bronze -> 4 silver -> 4 gold materialized views with data quality expectations.

### Serving
* `copper-retirement-risk` - GBT risk model (v6 champion), 2,672 predictions logged.
* `databricks-claude-sonnet-4-5` - LLM for the Regulatory tab's grounded answers via `ai_query`.

### Apps
* `retirement-plan` - Unified 5-tab accelerator app (ACTIVE, deploy `01f1dd02626c`).
* `copper-task-board` - Internal ops dashboard (ACTIVE, Lakebase-backed).

### Lakebase
* Project `copper-task-board` - Postgres task board (`agent_tasks`, `status_updates`, `ceo_directives`, `decisions`, `asset_ledger`).

## The Demo Scenario (Lakelink Fiber)

The demo uses a fictional operator, **Lakelink Fiber**, with a synthetic copper footprint of 103 wire centers, 299,455 lb of recoverable copper, and USD 603.8M in revenue at risk across 288 customers and 2,672 devices. The scenario walks through:

1. **Map/Risk tab** - Geospatial view of copper wire centers colored by risk score, with revenue-at-risk and customer-impact overlays.
2. **Plan tab** - Wave-planning timeline showing decommissioning schedule, regulatory notice windows, and contractor assignments.
3. **Dig Triage tab** - 811 dig-ticket incident triage with risk-weighted prioritization and rerouting recommendations.
4. **Regulatory tab** - Ask the AI assistant about FCC, state PUC, OSHA, EPA, and 811 requirements. Every answer cites official URLs.
5. **Commodity tab** - Copper price forecast, salvage value estimate, and per-wire-center ROI.

All network, customer, device, contractor, and dig-incident data is **synthetic**. Regulatory content is **real** (downloaded from official sources). See [PARTNER-PLAYBOOK.md](PARTNER-PLAYBOOK.md) for the full demo script.

## Data Disclosure

* **Synthetic**: All OSS, GIS, circuit inventory, copper recovery, contractor, dig-incident, and customer data is generated by deterministic scripts in `data_gen/`. Every table and UI surface labels it as synthetic.
* **Real**: Regulatory documents (FCC orders, eCFR sections, state PUC rules, OSHA standards, EPA guidance) are downloaded from official government websites and stored in the UC volume `cdm_tmforum.copper_retirement.regulatory_source_docs`. Chunk text lives in `regulatory_doc_chunks` with `is_synthetic = false`. The Regulatory tab answers only from real chunks.
* **Provenance**: `data/fixtures/synthetic/manifest.json` records row counts and SHA-256 hashes for all synthetic fixtures.

Regenerate fixtures offline:
```bash
python -m scripts.generate_synthetic_sources
```

## Industry Context

This accelerator is informed by the WBBA/Omdia white paper *"Copper Decommissioning: Mastering the Process"* by Stephen Wilson (Senior Principal Analyst, Broadband Technology, Omdia), available at `/Volumes/cdm_tmforum/copper_retirement/reference_docs/copper_decommission_white_paper.pdf`. Key industry benchmarks from that paper inform the ROI calculator and SOW phase template:

| Operator | Metric | Value |
|---|---|---|
| Chorus (NZ) | Net profit per premises | USD 6.8 - 12.1 |
| Bezeq (Israel) | Net profit per premises | USD 6.1 (30% margin) |
| MEO (Portugal) | Total consideration per line | USD 11.3 |
| Telus (Canada) | Copper extracted | 4,000 tonnes; CAD 500M profit target |
| BT (UK) | Copper recycled since 2023 | 22,347 tonnes; 200,000 tonne target |
| Telefónica (Spain) | Copper revenue (2020) | EUR 131M; 350,000 tonnes extracted |

The white paper identifies five copper sale business models partners should offer: (1) direct sale to recycler, (2) recycler-held inventory with flexible sell timing, (3) commodity price forward guarantee, (4) forward agreement with upfront payment, (5) bank asset purchase. Operators achieve approximately 30% margin on copper sales. Copper prices have risen ~50% over five years (approx. USD 14,500/tonne as of Sept 2026), making hedging strategies essential.

## Known Gaps and Handoff Items

The following items require human action (agent guardrails block these). Each ships to partners as a disclosed gap if not completed:

1. **Origin/main is behind local main** - A `git push origin main` from the workspace terminal is needed so a fresh clone gets the latest code (including the npm lockfile fix). The feature branch `devops/accel-consolidation-20261029` has all commits.
2. **Legacy app deletion** - `copper-map` and `commodity-dashboard` are STOPPED but not yet deleted. Eligible for deletion after 2026-11-13. Run `databricks apps delete copper-map` and `databricks apps delete commodity-dashboard`.
3. **Fresh-deploy sandbox proof** - No sandbox workspace has been named for the one-command deploy smoke test. Create a sandbox catalog, run `databricks bundle deploy -t partner`, and verify all tabs render.
4. **Browser-only regulatory downloads** - AZ R14-2-1107 / R17-3-502 and CO 6 CCR 1007-3 Part 261 return HTTP 403 to automated fetch. A human browser session is needed to download these PDFs.
5. **Weekly risk-scoring job tasks** - The `risk_scoring` job is deployed PAUSED but has no scheduled tasks. Add a weekly task after `copper_retirement_risk@champion` is registered.
6. **White paper integration** - The following white paper findings are documented but not yet implemented as data model enhancements: (a) network architecture cost differentiation (ducted vs. direct-buried vs. overhead extraction costs), (b) copper sale business model selection (forward guarantee, swap, upfront payment, bank sale), (c) environmental/waste tracking metrics (recycling rate, WEEE, creosote pole disposal), (d) EU Digital Networks Act compliance tracking (proposed Dec 2035 switch-off deadline), (e) sustainability KPIs (energy savings, waste diversion rate, CO2 reduction).

## Documentation Index

| Document | Purpose | Audience |
|---|---|---|
| [PARTNER-PLAYBOOK.md](PARTNER-PLAYBOOK.md) | Discovery questionnaire, SOW phase template, ROI calculator inputs, demo script, deploy/recovery, run cost | SI partners |
| [BUILD-PLAN.md](BUILD-PLAN.md) | Original phased build plan (6 phases, task breakdown) | Developers |
| [resources/00-master-architecture.md](resources/00-master-architecture.md) | System architecture and data model design | Architects |
| [resources/regulatory-jurisdictions.md](resources/regulatory-jurisdictions.md) | Regulatory jurisdiction matrix | Compliance |
| [resources/ML_MODEL_CARD.md](resources/ML_MODEL_CARD.md) | Risk model card (v6 champion) | ML engineers |
| [resources/DLP_PIPELINE_RUNBOOK.md](resources/DLP_PIPELINE_RUNBOOK.md) | Pipeline operations runbook | Data engineers |
| [apps/BRAND_GUIDE.md](apps/BRAND_GUIDE.md) | Design tokens, brand colors, WCAG AA standards | UI developers |
| [bundle/PARTNER_EXPORT_MANIFEST.md](bundle/PARTNER_EXPORT_MANIFEST.md) | What ships in the bundle vs. what is excluded | DevOps |
| [SEMANTIC-MODELING-STANDARDS.md](SEMANTIC-MODELING-STANDARDS.md) | UC semantic modeling standards and audit | Data architects |

---

*Built on Databricks. Synthetic data. Real regulatory citations. Partner-ready.*
