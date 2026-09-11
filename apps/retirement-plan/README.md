# Retirement Plan Tracker (P7-PLAN)

**Demo Beat 2:** "Capital-efficient plan to zero copper?"

## Overview

React/TypeScript Databricks App providing Gantt-style timeline visualization of
LakeLink Fiber's copper retirement wave schedule (2026–2029). Enables planners to
view, filter, and (once Lakebase lands) edit wire-center migration assignments.

## Architecture

* **Framework:** AppKit (React/TypeScript), `--features analytics,lakebase`
* **Data access:** SQL warehouse (analytics) for read-only aggregates; Lakebase
  (Postgres) for plan edit write-back (pending P5-SCHEMA)
* **Mock data:** `USE_MOCK_DATA=true` feature flag toggles between mock and live SQL

## Data Sources

| Query | Source Tables | Status |
|---|---|---|
| `plan_kpis.sql` | `tmf_enterprise.project` + `milestone` + `budget` | AVAILABLE (10K/10K/100K rows) |
| `wave_schedule.sql` | `tmf_enterprise.project` + `milestone` | AVAILABLE (proxy) |
| `milestone_timeline.sql` | `tmf_enterprise.milestone` | AVAILABLE (10K rows) |
| `cost_benefit.sql` | `tmf_enterprise.project` + `budget` + `work` | AVAILABLE |
| `migration_status.sql` | `tmf_enterprise.work` (decommission) + `workforce_employee_pool` | AVAILABLE |
| Wave optimizer output | `copper_retirement.migration_tracking` + P4-SEQ gold table | BLOCKED (P0-DATAGEN-MIGRATION-EXECUTE, P4-SEQ) |
| Revenue at risk | `gold_circuit_revenue_at_risk` (P3-DLP-REVENUE) | BLOCKED |
| Scrap recovery | `recovered_copper_tracking` (P0-DATAGEN-COMMODITY-EXECUTE) | BLOCKED |
| Plan edits (write-back) | Lakebase `retirement_plan` (P5-SCHEMA) | BLOCKED |

## Components (7)

| Component | Description | Complexity |
|---|---|---|
| `PlanKPIs` | 6-card top bar: wire centers, planned%, in-flight%, completed%, budget remaining, customers remaining | LOW |
| `GanttTimeline` | Horizontal Gantt: wire centers on Y-axis, 2026–2029 quarters on X-axis, color by wave, constraint icons | HIGH |
| `WaveSelector` | 4-dropdown filter bar: wave, state, status, constraint | LOW |
| `CostBenefitPanel` | Selected wire center detail: 4-column cost grid, milestone timeline, constraint detail | MEDIUM |
| `ConstraintFlags` | Inline icon badges for constraint types (contract, regulatory, crew, revrec) | LOW |
| `MigrationTable` | Sortable/filterable table: wire center, wave, dates, customers, cost, progress, constraints | MEDIUM |
| `ScenarioCompare` | Side-by-side optimizer scenario cards with cost, duration, waves, risk score, set-active toggle | MEDIUM |

## Blocked Dependencies

* **P0-DATAGEN-MIGRATION-EXECUTE** — migration tracking table (spec complete)
* **P4-SEQ** — optimizer output (gold table TBD)
* **P3-DLP-REVENUE** — revenue-at-risk gold table
* **P5-SCHEMA** — Lakebase write-back schema
* **FIX-COORDINATES** — needed if geographic overlay added to plan view

**None of these block the mock demo.**

## Next Steps

1. Run `databricks apps init` to generate boilerplate (package.json, tsconfig, vite.config), then merge scaffold files
2. @data-engineer executes P0-DATAGEN-MIGRATION → real migration_tracking table
3. @ml-engineer deploys P4-SEQ optimizer → real wave schedule + scenario runs
4. @data-engineer builds P3-DLP-REVENUE → revenue-at-risk per wire center
5. P5-SCHEMA lands → enable Lakebase write-back for drag-to-reschedule
6. Add drag-to-reschedule interaction on GanttTimeline (writes to Lakebase via PUT /api/plan/wave-assignment)

## Governance Tags

* `project: copper-retirement`
* `developer: copper-app`

Applied in `app.yaml` and expected in `bundle/databricks.yml` under `resources.apps.retirement-plan.tags`.

---

*All data displayed is SYNTHETIC. This application is part of the LakeLink Fiber copper retirement demo.*
