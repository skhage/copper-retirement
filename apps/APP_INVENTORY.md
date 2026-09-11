# Copper Retirement — App Feature Inventory & Backlog

**Author:** @app-developer | **Date:** 2026-09-10
**Framework:** AppKit (React/TypeScript) — Databricks Apps platform
**Project:** `/Users/stephen.hage@databricks.com/copper-retirement/apps/`

---

## Executive Summary

BUILD-PLAN.md defines 5 demo beats mapped to 4 Phase 7 app tasks (P7-MAP, P7-PLAN, P7-TRIAGE, P7-COMMODITY). Demo Beat 4 (regulatory) is primarily an agent surface (P6-REG) without a dedicated P7 task, but needs a thin UI wrapper. This inventory maps each beat to concrete React components, data sources, agent/model endpoints, and inter-agent dependencies.

**Recommended build order:** MAP (critical path terminus) → TRIAGE (real-time wow factor) → PLAN (Gantt complexity) → COMMODITY (least blocking).

---

## App Architecture Decisions

| Decision | Recommendation | Rationale |
|---|---|---|
| Data access pattern | **Analytics** (SQL warehouse) for all read-heavy dashboards; **Lakebase** for write-back on PLAN and TRIAGE apps | MAP/COMMODITY are read-only aggregation; PLAN needs editable wave assignments; TRIAGE needs incident form submission |
| Auth | OAuth (default AppKit) | All apps run on Databricks Apps platform with workspace SSO |
| Deployment | DAB (`bundle/`) — one app resource per P7 task | Reproducible via `bundle deploy` per BUILD-PLAN.md §6 |
| Geospatial rendering | deck.gl (H3HexagonLayer) via `@deck.gl/layers` | BUILD-PLAN.md P7-MAP specifies deck.gl/pydeck; React → deck.gl is natural fit |
| Agent chat | AppKit Genie plugin or custom SSE endpoint to agent serving endpoints | P6-TRIAGE and P6-REG agents will be Model Serving endpoints |

---

## Demo Beat 1: "Where is our copper / risk of touching it?"
### App: P7-MAP — Copper Prioritization Map

**Priority:** P0 (CRITICAL PATH TERMINUS — P2→P4-RISK→P7-MAP)
**Complexity:** HIGH (geospatial rendering + model scores + multi-layer interaction)
**Features:** `analytics` (SQL warehouse for aggregated geo data)

#### Components

| Component | Description | Complexity |
|---|---|---|
| `MapView` | Full-screen deck.gl map with H3HexagonLayer. Color = risk score (red/yellow/green). Zoom controls, layer toggles. | HIGH |
| `RiskLegend` | Color ramp legend mapping risk tiers to hex colors. | LOW |
| `WireCenterOverlay` | GeoJSON polygon layer for wire-center boundaries. Toggle on/off. | MEDIUM |
| `DevicePopover` | Click-on-hex popover: device count, avg risk score, top alarm types, customer count, wire-center name. | MEDIUM |
| `FilterPanel` | Sidebar filters: state, risk tier (critical/high/medium/low), device type (CPE/ONT/OLT/patch_panel), service type. | MEDIUM |
| `SummaryKPIs` | Top bar: total copper devices, % critical risk, customers affected, wire centers remaining. | LOW |
| `DeviceTable` | Drill-down table: devices in selected hex/wire-center with risk scores, alarm counts, customer counts. | MEDIUM |

#### Data Sources

| Query | Source Tables | Status | Dependency |
|---|---|---|---|
| H3 hex risk aggregates | `tmf_shared.geographic_address` (H3 indexed) + `tmf_enterprise.physical_device` + risk model scores | BLOCKED | Needs P2-H3 (H3 indexing), P4-RISK-MODEL-TRAIN (risk scores), FIX-COORDINATES (valid lat/lon) |
| Wire-center boundaries | Synthetic wire_center_boundary table | BLOCKED | Needs P0-DATAGEN-WIRECENTER-EXECUTE |
| Device detail | `tmf_enterprise.physical_device` WHERE device_type IN ('cpe','ont','olt','patch_panel') | AVAILABLE | 2,672 copper devices ready |
| Customer impact | `tmf_resource.device_service_allocation` → `tmf_service.customer_facing_service` → `tmf_customer.customer` | AVAILABLE (sparse) | Only 255/2,672 devices have allocations |
| Alarm summary | `tmf_resource.alarm` → `physical_device` (copper filter) | AVAILABLE | 26,943 copper alarms ready |
| Risk scores | `copper_retirement_risk_scores` (gold table from P4-RISK-CHAMPION-CHALLENGER) | BLOCKED | Needs full ML pipeline |

#### SQL Queries (config/queries/)

1. `hex-risk-summary.sql` — H3 cell aggregates: cell_id, device_count, avg_risk_score, customer_count, alarm_count, dominant_severity
2. `wire-center-boundaries.sql` — GeoJSON polygons for wire-center overlay
3. `device-detail.sql` — Parameterized by H3 cell: device_id, device_type, risk_score, alarm_count, installation_date
4. `map-kpis.sql` — Summary KPIs: total_devices, pct_critical, total_customers, wire_centers_remaining
5. `filter-options.sql` — Distinct states, risk tiers, device types for filter panel

#### Mock Data Strategy
Until P2-H3 and P4-RISK land, scaffold with:
- Hardcoded US state centroids as H3 cell stand-ins
- Random risk scores (0-100) per device
- Real device/alarm data from existing tables (2,672 copper devices, 26,943 alarms)

---

## Demo Beat 2: "Capital-efficient plan to zero copper?"
### App: P7-PLAN — Retirement Plan Tracker

**Priority:** P1 (depends on P4-SEQ optimizer output)
**Complexity:** HIGH (Gantt rendering + editable write-back + Lakebase)
**Features:** `analytics,lakebase` (read gold tables + write plan edits to Lakebase)

#### Components

| Component | Description | Complexity |
|---|---|---|
| `GanttTimeline` | Horizontal Gantt chart: wire-centers on Y-axis, 2026-2029 quarters on X-axis. Color by wave/priority. Drag-to-reschedule (writes to Lakebase). | HIGH |
| `WaveSelector` | Wave filter: Wave 1/2/3/.../N. Show/hide waves on Gantt. | LOW |
| `CostBenefitPanel` | Per-wire-center cost/benefit breakdown: migration cost, revenue at risk, scrap recovery value, net savings. | MEDIUM |
| `ConstraintFlags` | Icons on Gantt bars: contract-locked (from P3-DLP-CLM), regulatory notice pending, crew capacity constrained. | MEDIUM |
| `PlanSummaryKPIs` | Top bar: total wire-centers, % planned, % in-flight, % complete, total budget allocated vs remaining. | LOW |
| `MigrationTable` | Tabular view of migration plan: wire_center, wave, scheduled_start, scheduled_end, status, customers_affected, estimated_cost. Sortable/filterable. | MEDIUM |
| `ScenarioCompare` | Side-by-side comparison of optimizer scenarios (if P4-SEQ produces multiple). | MEDIUM |

#### Data Sources

| Query | Source Tables | Status | Dependency |
|---|---|---|---|
| Wave schedule | P4-SEQ optimizer output (gold table TBD) | BLOCKED | Needs P4-SEQ |
| Cost estimates | `tmf_enterprise.budget` + `oracle_erp_source.gl_budgets` | AVAILABLE | 100K budget rows |
| Revenue at risk | `gold_circuit_revenue_at_risk` (from P3-DLP-REVENUE) | BLOCKED | Needs P3-DLP-REVENUE |
| Contract constraints | P3-DLP-CLM output (gold table TBD) | BLOCKED | Needs P3-DLP-CLM |
| Migration tracking | Synthetic migration table (P0-DATAGEN-MIGRATION) | BLOCKED | Needs P0-DATAGEN-MIGRATION |
| Crew capacity | `tmf_enterprise.workforce_employee_pool` + `work` | AVAILABLE | 100K workforce rows |
| Plan edits (write-back) | Lakebase `retirement_plan` table (P5-SCHEMA) | BLOCKED | Needs P5-SCHEMA |

#### Lakebase Tables (P5-SCHEMA)

- `retirement_plan` — wire_center_id, wave, scheduled_start, scheduled_end, status, assigned_crew_id, notes, last_modified_by
- Synced from gold optimizer output; user edits write back to Lakebase

#### Mock Data Strategy
- Generate 200 synthetic wire-center plan rows with random wave assignments (1-8), dates in 2026-2029
- Use real budget data for cost KPIs
- Gantt component can render with mock data immediately

---

## Demo Beat 3: "Dig crew hit something — triage?"
### App: P7-TRIAGE — Dig-Safe Triage Console

**Priority:** P1 (high demo impact, depends on P6-TRIAGE agent)
**Complexity:** HIGH (real-time agent chat + map overlay + form submission)
**Features:** `analytics,lakebase` (read incidents + write triage actions to Lakebase)

#### Components

| Component | Description | Complexity |
|---|---|---|
| `IncidentMap` | Map overlay showing dig-safe incidents. Color by severity (red=critical, orange=major, yellow=minor). Click to select. | HIGH |
| `IncidentForm` | New incident submission form: lat/lon (click-on-map), severity, cable_type, description, contractor. Writes to Lakebase. | MEDIUM |
| `TriageAgentChat` | Chat panel connected to P6-TRIAGE agent endpoint. Shows agent actions: reroute recommendation, affected customers, priority score. Human-in-loop approve/reject buttons. | HIGH |
| `IncidentDetailPanel` | Selected incident detail: severity, cable type, contractor, resolution time, affected services, reroute status. | MEDIUM |
| `IncidentTable` | Sortable table of recent incidents: timestamp, location, severity, status, assigned_contractor, resolution_time. | MEDIUM |
| `TriageKPIs` | Top bar: open incidents, avg resolution time, incidents this week, reroutes pending approval. | LOW |
| `ActionLog` | Audit trail of agent recommendations + human approvals/rejections. | LOW |

#### Data Sources

| Query | Source Tables | Status | Dependency |
|---|---|---|---|
| Dig-safe incidents | Synthetic dig_safe_incident table | BLOCKED | Needs P0-DATAGEN-DIGSAFE-EXECUTE |
| Work orders | `tmf_enterprise.work` (repair + emergency types) | AVAILABLE | 22K relevant work orders |
| Contractor info | `tmf_businesspartner.bp_agreement` | AVAILABLE | 10K agreements |
| Contractor performance | Synthetic contractor_performance table | BLOCKED | Needs P0-DATAGEN-CONTRACTOR-EXECUTE |
| Triage agent endpoint | P6-TRIAGE Model Serving endpoint | BLOCKED | Needs P6-TRIAGE |
| Incident writes | Lakebase `dig_incidents` table (P5-SCHEMA) | BLOCKED | Needs P5-SCHEMA |

#### Agent Integration

- P6-TRIAGE agent will be a Model Serving endpoint
- Chat interface sends incident context → agent returns prioritized action list
- Human-in-loop: approve/reject agent recommendations before execution
- SSE streaming for real-time agent responses

#### Mock Data Strategy
- Generate 50 mock incidents with realistic US coordinates (once FIX-COORDINATES runs)
- Mock agent responses as static JSON until P6-TRIAGE endpoint exists
- Form submission writes to local state (no Lakebase) until P5-SCHEMA

---

## Demo Beat 4: "Clear on regs?"
### App: P7-REG — Regulatory Assistant UI

**Priority:** P2 (thin-slice demo beat, but no dedicated P7 task in BUILD-PLAN.md)
**Complexity:** MEDIUM (chat + document viewer)
**Features:** `analytics` (read regulatory data) — may add Genie plugin for agent

**Note:** BUILD-PLAN.md has no P7-REG task. This is a gap — the regulatory agent (P6-REG) needs a UI surface. Proposing as a new feature request to @pm.

#### Components

| Component | Description | Complexity |
|---|---|---|
| `RegAgentChat` | Chat interface to P6-REG regulatory RAG agent. Ask questions like "What's the notice period for copper retirement in Texas?" | HIGH |
| `DocumentViewer` | Side panel showing source FCC/PUC documents cited by the agent. PDF or text rendering with citation highlighting. | MEDIUM |
| `JurisdictionTable` | Reference table: state, notice_period_days, filing_type, section_214_required, residential_notice_days. | LOW |
| `ComplianceChecklist` | Per-wire-center regulatory compliance status: notices sent, waiting periods, approvals received. | MEDIUM |
| `RegKPIs` | Top bar: jurisdictions covered, pending filings, days until next deadline. | LOW |

#### Data Sources

| Query | Source Tables | Status | Dependency |
|---|---|---|---|
| Regulatory rules | `tmf_marketsales.policy` (10K) + `policy_rule` (100K) | AVAILABLE | 110K rows — evaluate before synthesizing |
| Regulator info | `tmf_enterprise.regulator` (1K) | AVAILABLE | |
| Documents | `tmf_shared.document` (10K) | AVAILABLE | |
| Jurisdiction lookup | Synthetic state_puc_requirements (P0-DATAGEN-REG) | BLOCKED | Needs P0-DATAGEN-REG |
| Agent endpoint | P6-REG Model Serving endpoint | BLOCKED | Needs P6-REG |
| FCC corpus | P1-REG document store | BLOCKED | Needs P1-REG |

---

## Demo Beat 5: "Who digs, when to sell copper?"
### App: P7-COMMODITY — Contractor & Commodity Dashboard

**Priority:** P2 (independent chain, least blocking)
**Complexity:** MEDIUM (charts + scorecard + forecast display)
**Features:** `analytics` (SQL warehouse for read-only data)

#### Components

| Component | Description | Complexity |
|---|---|---|
| `CopperPriceChart` | Time-series line chart: LME spot + 3M forward + 15M forward. 2018-present with forecast overlay (P4-COMMODITY model). | MEDIUM |
| `SellHoldIndicator` | Traffic-light indicator: SELL (green) / HOLD (red) / NEUTRAL (yellow) based on price forecast vs current. | LOW |
| `ScrapRecoveryTracker` | Cumulative recovered copper: volume (MT), value ($), by grade. Bar chart by quarter. | MEDIUM |
| `ContractorScorecard` | Table/cards: contractor name, safety_score, incident_count, avg_resolution_time, geographic_coverage, certification_status. Sortable. | MEDIUM |
| `ContractorMap` | Map showing contractor geographic coverage (H3 cells). Color by overall_rating. | MEDIUM |
| `CommodityKPIs` | Top bar: current copper spot price, 3M forecast, total recovered value, active contractors, avg safety score. | LOW |
| `ForecastConfidence` | Confidence interval band on price chart from P4-COMMODITY model. | LOW |

#### Data Sources

| Query | Source Tables | Status | Dependency |
|---|---|---|---|
| Copper prices | Synthetic copper_commodity_price (P0-DATAGEN-COMMODITY) | BLOCKED | Needs P0-DATAGEN-COMMODITY-EXECUTE |
| Recovered copper | Synthetic recovered_copper_tracking (P0-DATAGEN-COMMODITY) | BLOCKED | Needs P0-DATAGEN-COMMODITY-EXECUTE |
| Price forecast | P4-COMMODITY Model Serving endpoint | BLOCKED | Needs P4-COMMODITY |
| Contractor scorecard | Synthetic contractor_performance (P0-DATAGEN-CONTRACTOR) | BLOCKED | Needs P0-DATAGEN-CONTRACTOR-EXECUTE |
| Contractor agreements | `tmf_businesspartner.bp_agreement` (10K) | AVAILABLE | |
| FX reference | `refinitiv_fx_source.gl_daily_rates` (23K) | AVAILABLE | |
| Billed circuit rates | `oracle_erp_source.ra_billed_circuit_rates` (56K) | AVAILABLE | Revenue context |

---

## Prioritized Build Order

| Priority | App | Critical Path? | Blocked On | Est. Effort |
|---|---|---|---|---|
| **P0** | P7-MAP (Copper Map) | YES — terminus of longest chain | FIX-COORDINATES, P2-H3, P4-RISK-MODEL-TRAIN | 3-4 days (scaffold now with mock data) |
| **P1** | P7-TRIAGE (Dig Triage) | No (parallel chain) | P0-DATAGEN-DIGSAFE-EXECUTE, P6-TRIAGE | 3-4 days |
| **P1** | P7-PLAN (Retirement Plan) | No (parallel chain) | P4-SEQ, P0-DATAGEN-MIGRATION, P5-SCHEMA | 4-5 days (Gantt is complex) |
| **P2** | P7-REG (Regulatory) | No (NEW — not in BUILD-PLAN.md P7) | P6-REG, P0-DATAGEN-REG | 2-3 days |
| **P2** | P7-COMMODITY (Commodity) | No (independent) | P0-DATAGEN-COMMODITY-EXECUTE, P4-COMMODITY | 2-3 days |

**Total estimated effort:** 14-19 days for all 5 apps (parallelizable to ~8-10 with mock data scaffolding).

---

## Cross-Cutting Dependencies

### From @data-engineer (data generation / pipelines)
- FIX-COORDINATES must be RUN (blocks all geo visualization)
- P0-DATAGEN-*-EXECUTE tasks produce the synthetic tables apps consume
- P2-H3 (H3 indexing) is required for MAP hex grid
- P3-DLP gold tables feed all dashboard KPIs
- P5-SCHEMA (Lakebase) needed for PLAN and TRIAGE write-back

### From @ml-engineer (models)
- P4-RISK-MODEL-TRAIN → `copper_retirement_risk_scores` gold table (MAP)
- P4-COMMODITY → price forecast endpoint (COMMODITY)
- P4-SEQ → optimizer output (PLAN)

### From @ml-engineer / @data-engineer (agents)
- P6-TRIAGE → triage agent serving endpoint (TRIAGE chat)
- P6-REG → regulatory RAG agent endpoint (REG chat)
- P6-CONTRACTOR → contractor sourcing agent (COMMODITY)

---

## Immediate Actions (can start NOW)

1. **Scaffold P7-MAP app skeleton** with AppKit (`--features analytics`), mock data, and component stubs. Use real device/alarm data from `tmf_enterprise.physical_device` and `tmf_resource.alarm` (both available now).
2. **Scaffold P7-TRIAGE app skeleton** — incident table using real `tmf_enterprise.work` data (22K repair/emergency orders), mock agent chat.
3. **Scaffold P7-COMMODITY app skeleton** — contractor scorecard using real `tmf_businesspartner.bp_agreement` data, mock price chart.
4. **File feature request to @pm:** P7-REG app is missing from BUILD-PLAN.md Phase 7 — regulatory agent needs a UI surface.

---

## Feature Request to @pm

**APP-NEEDS-P7-REG:** BUILD-PLAN.md Phase 7 has 4 app tasks (MAP, PLAN, TRIAGE, COMMODITY) but Demo Beat 4 ("Clear on regs?") has no corresponding P7 task. The P6-REG regulatory RAG agent needs a UI wrapper with chat interface, document viewer, and jurisdiction checklist. Proposing P7-REG as a new Phase 7 task.

**APP-BLOCKED: All geo visualization** needs FIX-COORDINATES notebook to be RUN by CEO. Without valid US coordinates, no map app can render meaningful hex grids.
