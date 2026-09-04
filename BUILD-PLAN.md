# Databricks Build Plan — Lumen Copper Retirement Demo

This is the execution plan for building the demo described in `resources/`. It
translates the architecture docs into a concrete, sequenced, delegate-able set
of work items. It is a living plan: as workstreams land, update the status
column and the open-questions section.

> **How this repo is built:** polly (the orchestrator) does not write code.
> Every code/notebook/pipeline artifact is delegated to a coding sub-agent in
> its own git worktree, opens its own PR, and is cross-reviewed by a different
> vendor before it is considered done. polly authors docs (like this file) and
> coordinates. See "Delivery model" below.

---

## 0. Corrections applied to the resource docs (read this first)

Before planning, three load-bearing external claims were verified against
primary sources. One was materially wrong and has been corrected in
`00-master-architecture.md` and `regulatory-jurisdictions.md`:

- **FCC March 2026 order (FCC 26-19).** The docs originally said the order
  "eliminated Section 214 discontinuance applications." That is **incorrect**.
  The order eliminated the **Section 251(c)(5)** network-change disclosure
  *FCC filing* and its public-notice/objection process for copper retirement,
  and **streamlined** Section 214(a) discontinuance (one consolidated
  tech-transition rule, 31-day automatic grants, blanket grandfathering
  authority, added 911-coordination). **Section 214 authorization is still
  required** when a retirement causes a service discontinuance. The 90-day
  residential direct-notice requirement remains. This matters because the
  regulatory agent is a headline demo screen — grounding it in a wrong federal
  rule would be caught by any regulator in the room.
- **Lakebase.** Confirmed GA on AWS (Jan 22, 2026), Azure in beta, GCP planned
  later 2026. The docs' framing is correct. **Implication: build the demo on
  AWS** unless the customer's workspace is Azure (then flag Lakebase as beta).
- **Mosaic geospatial library.** Confirmed retired/archived (Aug 2026); native
  `h3_*` functions and native Spatial SQL `ST_*` types (DBR 17.1+, Aug 2025)
  are the supported path. The docs' "don't depend on Mosaic" guidance is
  correct — **pin compute to DBR 17.1+** so native `ST_*` is available.

Citations `[cite:N]` in the resource docs are placeholders from the research
phase; a docs task (P0-DOC) will reconcile them to real URLs.

---

## 1. Delivery model (how work flows through polly)

- **Unit of work = one PR** from one implementation sub-agent in one worktree.
- **Implementers:** `claude_code` (multi-file / notebooks / refactors / test
  authoring) and `codex` (narrow, well-scoped changes). `pi` is the read-only
  reviewer / explorer and third-opinion.
- **Cross-review is mandatory and cross-vendor:** a Claude Code PR is reviewed
  by Codex (or Pi), and vice versa. polly never merges — the human does.
- **Roster note for this machine:** only `claude_code`, `codex`, and `pi` are
  installed. `opencode`, `cursor`, `hermes`, and `agy` are unavailable; install
  their CLIs if broader cross-vendor review is wanted.
- **Everything is synthetic/simulated** where it represents Lumen-internal data
  (OSS/GIS exports, circuit inventory, recovered-copper volumes). Label it as
  synthetic in-notebook and in the app UI. Never fabricate real Lumen plant.

---

## 2. Foundational decisions to lock before Phase 0

These are cross-cutting and cheap to get wrong late. Resolve them first (see
open questions):

1. **Cloud = AWS** (Lakebase GA). Confirm the target workspace.
2. **Compute = DBR 17.1+ / serverless where possible** (native `ST_*` + H3).
3. **Unity Catalog layout.** Proposed: catalog `lumen_copper`, schemas
   `bronze`, `silver`, `gold`, `ml`, `ops` (Lakebase-synced), `agents`.
4. **H3 resolution.** Docs suggest res 9–10. Recommend **res 8 for
   wave-planning aggregates, res 9 for the map/join key** — res 10 explodes
   cell counts with little planning benefit. Decide and standardize one join
   resolution.
5. **Repo layout.** Proposed monorepo:
   ```
   /notebooks        # or /src if using Databricks Asset Bundles + .py
   /pipelines        # Lakeflow Declarative Pipeline definitions
   /ml               # training/registration/serving code
   /agents           # agent definitions + eval sets
   /apps             # Databricks Apps (Streamlit)
   /data_gen         # synthetic data generators
   /bundle           # databricks.yml (Asset Bundle) for CI/CD deploy
   /tests            # pytest for pure-Python logic (data gen, scoring, LP)
   ```
6. **IaC = Databricks Asset Bundles (DABs).** Every asset (jobs, pipelines,
   models, apps) declared in `databricks.yml` so the whole demo is
   reproducible `bundle deploy`. This is the single most important choice for a
   demo that must be re-standable on any workspace.
7. **Secrets** (LME/commodity API keys, FCC scrape config) via Databricks
   secret scopes, never in notebooks.

---

## 3. Phased work breakdown (build order)

Each row is a candidate PR / sub-agent task. "Owner" is a suggested implementer;
"Review" is the required cross-vendor reviewer. Status starts `todo`.

### Phase 0 — Foundation & scaffolding
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P0-BUNDLE | Databricks Asset Bundle skeleton (`databricks.yml`), env targets (dev/demo), repo layout above | claude_code → codex | todo |
| P0-UC | UC catalog/schema/external-location setup notebook + bundle resources | codex → claude_code | todo |
| P0-DATAGEN | Synthetic data generators: Lumen OSS/GIS copper footprint (GeoJSON), circuit inventory, recovered-copper volume/grade, contractor registry. Clearly labeled synthetic | claude_code → codex | todo |
| P0-DOC | Reconcile `[cite:N]` placeholders in resources to real source URLs | polly (docs) | todo |

### Phase 1 — Ingestion (bronze)
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P1-FCC | Auto Loader ingestion of FCC BDC + Fabric CSV extracts → bronze | claude_code → codex | todo |
| P1-REG | Scheduled Lakeflow job scraping/pulling FCC orders/PUC docket text → raw document store | codex → pi | todo |
| P1-COMMODITY | Scheduled REST-pull job for LME/commodity price history → bronze (secrets-scoped) | codex → claude_code | todo |
| P1-WEATHER | Batch NOAA/USGS soil/weather pull → bronze | codex → pi | todo |
| P1-SIM | Land synthetic OSS/GIS + circuit + contractor files via Auto Loader → bronze | claude_code → codex | todo |

### Phase 2 — Geospatial enrichment (silver)
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P2-H3 | H3-index all point/polygon layers to standard resolution using native `h3_*`/`ST_*` (no Mosaic dependency) | claude_code → codex | todo |
| P2-JOIN | Point-in-polygon → integer H3 joins: copper proxy × wire-center × jurisdiction × utility corridor | claude_code → pi | todo |

### Phase 3 — Declarative pipelines (silver→gold)
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P3-DLP | Lakeflow Declarative Pipeline: bronze→silver→gold with expectations (data-quality constraints) | claude_code → codex | todo |
| P3-GOLD | Gold tables: `copper_retirement_readiness`, `commodity_price_features`, `contractor_scorecard`, `regulatory_requirements_by_jurisdiction` | claude_code → codex | todo |

### Phase 4 — ML + MLOps
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P4-RISK | Readiness/risk classifier (GBT) on the risk dimensions; MLflow + UC Model Registry | claude_code → codex | todo |
| P4-SEQ | Sequencing optimizer (LP/constraint solver): risk + crew capacity + budget + notice windows → 2026–2029 wave schedule; log scenario runs | claude_code → pi | todo |
| P4-COMMODITY | Copper price forecaster (GBT/Prophet baseline), 3–18mo horizon; Serving endpoint | codex → claude_code | todo |
| P4-SERVE | Model Serving endpoints + Lakehouse Monitoring on inference tables (drift) | codex → claude_code | todo |

### Phase 5 — Lakebase (operational store)
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P5-SCHEMA | Lakebase Postgres schema: `retirement_plan`, `dig_incidents`, `contractor_assignments`, `regulatory_checklist_status` | codex → claude_code | todo |
| P5-SYNC | Sync Gold (readiness, forecasts) → Lakebase for app joins | codex → pi | todo |
| P5-SEARCH | Enable Lakebase Search (hybrid vector+text) for the regulatory corpus | claude_code → codex | todo |

### Phase 6 — Agents
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P6-REG | Regulatory RAG agent over FCC/state corpus (Lakebase Search); returns notice types/lead times/bodies/checklist | claude_code → codex | todo |
| P6-TRIAGE | Dig-triage tool-calling agent: geospatial + plan + rerouting-lookup tool → prioritized action list to `dig_incidents` | claude_code → codex | todo |
| P6-CONTRACTOR | Contractor-sourcing agent: registry × geospatial × incidents → ranked shortlist | codex → pi | todo |
| P6-SUPER | Supervisor agent orchestrating the three + commodity endpoint | claude_code → codex | todo |
| P6-EVAL | Agent Evaluation sets (labeled Q→citation, incident→resolution) + MLflow Tracing; gate before promotion | claude_code → pi | todo |

### Phase 7 — Databricks Apps
| ID | Task | Owner→Review | Status |
|----|------|--------------|--------|
| P7-MAP | Prioritization Map (H3 hex map, deck.gl/pydeck, wave filter) | claude_code → codex | todo |
| P7-PLAN | Retirement Plan Tracker (Gantt, editable, Lakebase-backed) | codex → claude_code | todo |
| P7-TRIAGE | Dig-Triage Console (incident form + live agent actions, human-in-loop approve) | claude_code → codex | todo |
| P7-COMMODITY | Commodity & Workforce dashboard (forecast chart, sell/hold, contractor shortlist w/ assign) | codex → claude_code | todo |

---

## 4. Suggested parallelization waves

polly dispatches in parallel-safe waves (disjoint file scope), each PR
cross-reviewed before its worktree is torn down:

- **Wave A (now):** P0-BUNDLE, P0-UC, P0-DATAGEN, P0-DOC — foundation. Mostly
  independent; P0-BUNDLE lands first as others depend on the layout.
- **Wave B:** all Phase 1 ingestion tasks (independent per-source).
- **Wave C:** Phase 2 geospatial (depends on bronze existing).
- **Wave D:** Phase 3 pipelines (depends on silver).
- **Wave E:** Phase 4 ML + Phase 5 Lakebase can largely run in parallel.
- **Wave F:** Phase 6 agents (depend on Lakebase + gold + serving).
- **Wave G:** Phase 7 apps (depend on agents + gold + Lakebase).

Later phases genuinely depend on earlier ones, so most parallelism is
*within* a phase, not across. Don't fan out Wave F before Wave E is green.

---

## 5. Demo-day narrative → screen mapping (what "done" looks like)

The five-beat story in `00-master-architecture.md` maps to deliverables:
1. "Where is our copper / risk of touching it?" → P2 + P4-RISK + P7-MAP.
2. "Capital-efficient plan to zero copper?" → P4-SEQ + P5 + P7-PLAN.
3. "Dig crew hit something — triage/reroute fast?" → P6-TRIAGE + P7-TRIAGE.
4. "Are we clear on regs everywhere we touch?" → P6-REG (grounded in the
   corrected FCC facts).
5. "Who digs, and when do we sell copper?" → P4-COMMODITY + P6-CONTRACTOR +
   P7-COMMODITY.

A demo is "done" when all five beats run end-to-end on a freshly
`bundle deploy`-ed workspace with synthetic data.

---

## 6. Cross-cutting requirements (apply to every PR)

- Every commit ends with the co-sign trailer:
  `Co-authored-by: omnigent <noreply@omnigent.ai>`.
- Pure-Python logic (data gen, scoring, LP objective, forecast features) gets
  pytest coverage; notebooks/pipelines get pipeline **expectations**.
- No secrets in code; use secret scopes.
- Synthetic data is labeled synthetic everywhere it surfaces.
- Every model version traces to its UC-governed Gold training table.
- Every agent response is MLflow-traced and gated by an eval set before promo.

---

## 7. Open questions for the human (plan gate)

1. **Target cloud/workspace?** Plan assumes AWS (Lakebase GA). Azure ⇒ Lakebase
   is beta — acceptable for the demo?
2. **Scope for v1 demo:** all four apps + four agents, or a thin vertical slice
   first (Map + risk model + regulatory agent) to de-risk?
3. **Real external APIs vs. canned fixtures:** wire live LME/commodity + FCC
   scrape, or ship recorded fixtures so the demo runs offline/repeatably?
4. **H3 resolution** sign-off (recommend res 9 join key, res 8 aggregates).
5. **Asset Bundles** as the deploy mechanism — confirm, since it shapes the
   whole repo layout in P0-BUNDLE.
6. Want me to install the missing coding CLIs (`opencode`/`cursor`/`hermes`/
   `agy`) for wider cross-vendor review, or proceed with claude_code/codex/pi?

Once these are answered, polly kicks off **Wave A** (P0-BUNDLE first, then the
rest of Phase 0 in parallel), cross-reviews each PR, and reports back.
