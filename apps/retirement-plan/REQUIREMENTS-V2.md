# Retirement Plan Tracker — V2 Requirements

**App:** `retirement-plan` | **Beat 2:** "Capital-efficient plan to zero copper?"
**Author:** @app-developer | **Date:** 2026-09-21
**Status:** Draft — pending @designer UX review

---

## 1. Executive Summary

V1 of the retirement-plan app is a scaffolded React/TypeScript AppKit application with
9 components, mock data for 25 wire centers, and 5 proxy SQL queries against
`tmf_enterprise` tables. V2 upgrades the app to use **real gold-layer tables** that
are now materialized in `cdm_tmforum.copper_retirement`, replacing all mock data and
proxy queries. V2 also adds cross-app integration with the copper-map (Beat 1) risk
model outputs and introduces new data-driven features enabled by the optimizer,
cost-estimation, and salvage-forecast gold tables.

### What Changed Since V1 Scaffold

Per CEO directive (2026-09-14), **all blockers are resolved:**
- P4-SEQ optimizer output → `gold_wave_schedule` (materialized)
- P0-DATAGEN migration tracking → `retirement_milestones`, `retirement_cost_per_wire_center`
- P3-DLP revenue-at-risk → `gold_circuit_revenue_at_risk` (materialized)
- Scrap recovery → `gold_copper_recovery_schedule` (materialized)
- P4-RISK model → `gold_device_risk_predictions`, `copper_risk_scores` (V5 model READY)
- EBITDA forecast → `gold_ebitda_forecast` (3 scenarios)
- Budget allocation → `silver_budget_allocation`
- Constraint tables → `silver_contract_constraints`, `silver_revenue_recognition_constraints`
- Crew capacity → `crew_availability_per_region_per_month`

The only remaining blocker is **P5-SCHEMA (Lakebase write-back)** for plan edits.
V2 focuses on **read-only live data** with mock write-back preserved.

---

## 2. Data Dependencies (Gold/Silver Tables)

### 2.1 Primary Data Sources

| Table | Schema | Join Key | Role in App |
|---|---|---|---|
| `gold_wave_schedule` | 21 columns | `wire_center_id` | **Master schedule** — wave assignments (YYYY-QN), dates, device counts, risk scores, priority rank, customer counts, revenue at risk |
| `retirement_cost_per_wire_center` | 17 columns | `wire_center_id` | **Cost breakdown** — fiber build, equipment removal, customer migration, regulatory filing, total cost, cost-per-device |
| `retirement_milestones` | 14 columns | `wire_center_id` | **Milestone timeline** — planned/actual/forecast dates, critical path flags, regulatory gates, completion % |
| `gold_copper_recovery_schedule` | 28 columns | `wire_center_id` | **Salvage forecast** — copper weight, LME/COMEX prices, gross/net salvage value, timing signal (SELL/HOLD) |
| `gold_ebitda_forecast` | multi-dim | `state`, `quarter` | **EBITDA scenarios** — base/optimistic/conservative projections by state × quarter |
| `gold_circuit_revenue_at_risk` | per-circuit | `wire_center_id` (agg) | **Revenue at risk** — per-circuit MRR aggregated to wire-center level |

### 2.2 Supporting/Enrichment Tables

| Table | Role |
|---|---|
| `silver_budget_allocation` | Budget-vs-cost gap analysis per wire center |
| `silver_contract_constraints` | Contract lock flags blocking retirement |
| `silver_revenue_recognition_constraints` | ASC 606 RevRec constraints |
| `crew_availability_per_region_per_month` | Crew capacity by region/skill type |
| `state_puc_jurisdiction_requirements` | Regulatory notice periods (90-270 days) |
| `gold_contractor_assignment_plan` | Contractor assignments per wave × state |
| `gold_device_risk_predictions` | V5 ML risk tier per device (cross-app from Beat 1) |
| `gold_wire_center_scorecard` | Wire-center readiness scorecard (cross-app from Beat 1) |
| `wire_center_boundary` | GeoJSON polygons for geographic overlay |

### 2.3 Key Column Details

**`gold_wave_schedule` columns (all 21):**
- `wire_center_id` (string, PK/FK)
- `wire_center_name` (string)
- `state_code` (string — CO, MN, WA, OR, ID, AZ)
- `assigned_wave` (string — YYYY-QN format, e.g., "2026-Q3")
- `wave_year` (bigint), `wave_quarter` (bigint)
- `wave_start_date` (string — first day of quarter)
- `fiber_ready` (boolean)
- `puc_filing_required` (boolean)
- `copper_device_count` (bigint)
- `critical_risk_devices` (bigint), `high_risk_devices` (bigint)
- `retirement_readiness_score` (double — 0-100)
- `retirement_priority_rank` (bigint — 1 = retire first)
- `risk_urgency_weight` (double)
- `estimated_crew_days` (bigint)
- `earliest_eligible_wave` (string — earliest possible wave given constraints)
- `affected_customer_count` (bigint)
- `annual_revenue_at_risk` (double)
- `optimizer_version` (string), `solved_date` (string)

**`retirement_cost_per_wire_center` cost components:**
- `fiber_build_cost` (double) — 80% discount if `fiber_ready`
- `equipment_removal_cost` (decimal) — mobilization + $1,500/device
- `customer_migration_cost` (bigint) — PM + $800/customer + $200/service
- `regulatory_filing_cost` (bigint) — base + Section 214 + PUC + notification
- `total_retirement_cost` (double) — sum of above
- `cost_per_device` (double)
- `retirement_readiness_score` (decimal), `retirement_priority_rank` (int)

**`retirement_milestones` types:**
- `regulatory`, `construction`, `notification`, `migration`, `decommission`
- Status: `not_started`, `in_progress`, `completed`, `delayed`, `blocked`
- Flags: `critical_path_flag`, `regulatory_requirement_flag`

---

## 3. SQL Query Replacements

All 5 V1 proxy queries in `config/queries/` must be replaced with gold-table queries.

### 3.1 `plan_kpis.sql` → V2

**V1:** Queries `tmf_enterprise.project` + `milestone` + `budget` + `work`
**V2:** Queries `gold_wave_schedule` + `retirement_cost_per_wire_center` + `retirement_milestones`

```sql
-- plan_kpis.sql (V2)
SELECT
  count(DISTINCT ws.wire_center_id)                                    AS total_wire_centers,
  count(DISTINCT CASE WHEN rm.status = 'completed' THEN ws.wire_center_id END)
    * 100.0 / count(DISTINCT ws.wire_center_id)                        AS pct_completed,
  count(DISTINCT CASE WHEN rm.status = 'in_progress' THEN ws.wire_center_id END)
    * 100.0 / count(DISTINCT ws.wire_center_id)                        AS pct_in_flight,
  count(DISTINCT CASE WHEN rm.status IN ('not_started','delayed') THEN ws.wire_center_id END)
    * 100.0 / count(DISTINCT ws.wire_center_id)                        AS pct_planned,
  sum(rc.total_retirement_cost)                                        AS total_budget_allocated,
  sum(ba.total_allocated_budget)                                       AS total_budget_allocated_calc,
  sum(ba.budget_gap)                                                   AS total_budget_gap,
  sum(ws.affected_customer_count)                                      AS total_customers_affected,
  sum(ws.annual_revenue_at_risk)                                       AS total_annual_revenue_at_risk,
  sum(cr.net_salvage_value_usd)                                        AS total_net_salvage_value,
  count(DISTINCT CASE WHEN rm.critical_path_flag AND rm.status IN ('delayed','blocked')
    THEN rm.milestone_id END)                                          AS critical_milestones_at_risk
FROM cdm_tmforum.copper_retirement.gold_wave_schedule ws
LEFT JOIN cdm_tmforum.copper_retirement.retirement_cost_per_wire_center rc
  ON rc.wire_center_id = ws.wire_center_id
LEFT JOIN cdm_tmforum.copper_retirement.retirement_milestones rm
  ON rm.wire_center_id = ws.wire_center_id
LEFT JOIN cdm_tmforum.copper_retirement.gold_copper_recovery_schedule cr
  ON cr.wire_center_id = ws.wire_center_id
LEFT JOIN cdm_tmforum.copper_retirement.silver_budget_allocation ba
  ON ba.wire_center_id = ws.wire_center_id
```

### 3.2 `wave_schedule.sql` → V2

**V1:** Queries `tmf_enterprise.project` as proxy
**V2:** Direct from `gold_wave_schedule` joined with costs and recovery

```sql
-- wave_schedule.sql (V2)
SELECT
  ws.wire_center_id,
  ws.wire_center_name,
  ws.state_code,
  ws.assigned_wave,
  ws.wave_year,
  ws.wave_quarter,
  ws.wave_start_date,
  ws.fiber_ready,
  ws.puc_filing_required,
  ws.copper_device_count,
  ws.critical_risk_devices,
  ws.high_risk_devices,
  ws.retirement_readiness_score,
  ws.retirement_priority_rank,
  ws.estimated_crew_days,
  ws.affected_customer_count,
  ws.annual_revenue_at_risk,
  rc.total_retirement_cost     AS migration_cost_usd,
  rc.fiber_build_cost,
  rc.equipment_removal_cost,
  rc.customer_migration_cost,
  rc.regulatory_filing_cost,
  cr.net_salvage_value_usd     AS scrap_recovery_usd,
  cr.salvage_timing_signal,
  -- Constraint flags (inline subqueries)
  CASE
    WHEN cc.wire_center_id IS NOT NULL THEN 'contract_locked'
    WHEN rr.wire_center_id IS NOT NULL THEN 'revrec_locked'
    WHEN ws.puc_filing_required THEN 'regulatory_notice_pending'
    ELSE 'none'
  END AS constraint_type
FROM cdm_tmforum.copper_retirement.gold_wave_schedule ws
LEFT JOIN cdm_tmforum.copper_retirement.retirement_cost_per_wire_center rc
  ON rc.wire_center_id = ws.wire_center_id
LEFT JOIN cdm_tmforum.copper_retirement.gold_copper_recovery_schedule cr
  ON cr.wire_center_id = ws.wire_center_id
LEFT JOIN (
  SELECT DISTINCT cwj.wire_center_id
  FROM cdm_tmforum.copper_retirement.silver_contract_constraints cc
  JOIN cdm_tmforum.copper_retirement.copper_plant_wire_center_jurisdiction cwj
    ON cwj.physical_device_id = cc.physical_device_id
  WHERE cc.constraint_status = 'blocked'
) cc ON cc.wire_center_id = ws.wire_center_id
LEFT JOIN (
  SELECT DISTINCT cwj.wire_center_id
  FROM cdm_tmforum.copper_retirement.silver_revenue_recognition_constraints rr
  JOIN cdm_tmforum.copper_retirement.copper_plant_wire_center_jurisdiction cwj
    ON cwj.physical_device_id = rr.physical_device_id
  WHERE rr.revrec_eligible_for_retirement = false
) rr ON rr.wire_center_id = ws.wire_center_id
ORDER BY ws.retirement_priority_rank
```

### 3.3 `cost_benefit.sql` → V2

**V1:** Queries `tmf_enterprise.project` + `budget` + `work`
**V2:** Direct cost breakdown + salvage + revenue-at-risk from gold tables

```sql
-- cost_benefit.sql (V2) — parameterized by :wire_center_id
SELECT
  rc.wire_center_id,
  rc.wire_center_name,
  rc.fiber_build_cost,
  rc.equipment_removal_cost,
  rc.customer_migration_cost,
  rc.regulatory_filing_cost,
  rc.total_retirement_cost,
  rc.cost_per_device,
  rc.fiber_ready,
  ws.annual_revenue_at_risk,
  ws.affected_customer_count,
  cr.gross_salvage_revenue_usd,
  cr.estimated_decommission_cost_usd,
  cr.net_salvage_value_usd,
  cr.salvage_timing_signal,
  ba.total_allocated_budget     AS budget_allocated,
  ba.budget_gap                 AS budget_gap,
  ba.budget_coverage_ratio      AS budget_coverage_ratio,
  -- Net cost = total retirement - salvage recovery
  rc.total_retirement_cost - coalesce(cr.net_salvage_value_usd, 0) AS net_retirement_cost
FROM cdm_tmforum.copper_retirement.retirement_cost_per_wire_center rc
LEFT JOIN cdm_tmforum.copper_retirement.gold_wave_schedule ws
  ON ws.wire_center_id = rc.wire_center_id
LEFT JOIN cdm_tmforum.copper_retirement.gold_copper_recovery_schedule cr
  ON cr.wire_center_id = rc.wire_center_id
LEFT JOIN cdm_tmforum.copper_retirement.silver_budget_allocation ba
  ON ba.wire_center_id = rc.wire_center_id
WHERE rc.wire_center_id = :wire_center_id
```

### 3.4 `milestone_timeline.sql` → V2

**V1:** Queries `tmf_enterprise.milestone`
**V2:** Direct from `retirement_milestones` (purpose-built table)

```sql
-- milestone_timeline.sql (V2) — parameterized by :wire_center_id
SELECT
  m.milestone_id,
  m.wire_center_id,
  m.name,
  m.type,
  m.status,
  m.priority,
  m.planned_date,
  m.actual_date,
  m.forecast_date,
  m.completion_percentage,
  m.critical_path_flag,
  m.regulatory_requirement_flag,
  m.risk_level,
  m.risk_description,
  datediff(m.forecast_date, m.planned_date) AS variance_days
FROM cdm_tmforum.copper_retirement.retirement_milestones m
WHERE m.wire_center_id = :wire_center_id
ORDER BY m.planned_date
```

### 3.5 `migration_status.sql` → V2

**V1:** Queries `tmf_enterprise.work` + `workforce_employee_pool`
**V2:** Aggregates from gold_wave_schedule + crew_availability

```sql
-- migration_status.sql (V2)
SELECT
  ws.assigned_wave,
  ws.state_code,
  count(*) AS wire_center_count,
  sum(ws.copper_device_count) AS total_devices,
  sum(ws.affected_customer_count) AS total_customers,
  sum(ws.estimated_crew_days) AS total_crew_days,
  ca.available_crew_days,
  CASE WHEN sum(ws.estimated_crew_days) > coalesce(ca.available_crew_days, 0)
    THEN 'capacity_constrained' ELSE 'capacity_ok' END AS crew_status
FROM cdm_tmforum.copper_retirement.gold_wave_schedule ws
LEFT JOIN (
  SELECT region, sum(available_crew_days) AS available_crew_days
  FROM cdm_tmforum.copper_retirement.crew_availability_per_region_per_month
  GROUP BY region
) ca ON ca.region = ws.state_code
GROUP BY ws.assigned_wave, ws.state_code, ca.available_crew_days
ORDER BY ws.assigned_wave, ws.state_code
```

### 3.6 NEW: `ebitda_scenarios.sql`

```sql
-- ebitda_scenarios.sql (NEW V2) — powers ScenarioCompare tab
SELECT
  quarter,
  scenario,
  state,
  sum(annual_revenue_at_risk) AS revenue_at_risk,
  sum(cost_savings_realized) AS cost_savings,
  sum(net_ebitda_impact) AS net_ebitda_impact
FROM cdm_tmforum.copper_retirement.gold_ebitda_forecast
GROUP BY quarter, scenario, state
ORDER BY quarter, scenario
```

### 3.7 NEW: `crew_capacity.sql`

```sql
-- crew_capacity.sql (NEW V2) — powers capacity heatmap
SELECT
  region,
  month,
  skill_type,
  available_crew_days,
  allocated_crew_days,
  available_crew_days - allocated_crew_days AS slack_days
FROM cdm_tmforum.copper_retirement.crew_availability_per_region_per_month
ORDER BY month, region
```

---

## 4. TypeScript Type Updates

Replace `mockData.ts` types with types matching gold-table schemas:

```typescript
// types.ts (V2)
export interface WireCenterPlan {
  wire_center_id: string;
  wire_center_name: string;
  state_code: string;              // was: state
  assigned_wave: string;           // NEW: YYYY-QN format
  wave_year: number;
  wave_quarter: number;
  wave_start_date: string;
  fiber_ready: boolean;            // NEW: from gold_wave_schedule
  puc_filing_required: boolean;    // NEW
  copper_device_count: number;     // was: copper_devices
  critical_risk_devices: number;   // NEW: V5 ML model
  high_risk_devices: number;       // NEW
  retirement_readiness_score: number; // NEW: 0-100
  retirement_priority_rank: number;   // NEW: optimizer rank
  estimated_crew_days: number;     // NEW
  affected_customer_count: number; // was: customers_affected
  annual_revenue_at_risk: number;  // was: revenue_at_risk_mrr
  // Cost breakdown (from retirement_cost_per_wire_center)
  total_retirement_cost: number;   // was: migration_cost_usd
  fiber_build_cost: number;        // NEW
  equipment_removal_cost: number;  // NEW
  customer_migration_cost: number; // NEW
  regulatory_filing_cost: number;  // NEW
  cost_per_device: number;         // NEW
  // Salvage (from gold_copper_recovery_schedule)
  net_salvage_value_usd: number;   // was: scrap_recovery_usd
  salvage_timing_signal: string;   // NEW: 'SELL' | 'HOLD'
  // Constraints
  constraint_type: ConstraintType;
}

export type ConstraintType =
  | 'contract_locked'
  | 'regulatory_notice_pending'
  | 'revrec_locked'
  | 'crew_capacity_constrained'
  | 'none';

export interface MilestoneItem {
  milestone_id: number;            // was: string
  wire_center_id: string;
  name: string;
  type: 'regulatory' | 'construction' | 'notification' | 'migration' | 'decommission';
  status: 'not_started' | 'in_progress' | 'completed' | 'delayed' | 'blocked';
  priority: 'critical' | 'high' | 'medium' | 'low';
  planned_date: string;
  actual_date: string | null;
  forecast_date: string;           // NEW
  completion_percentage: number;
  critical_path_flag: boolean;
  regulatory_requirement_flag: boolean;
  risk_level: string;
  risk_description: string;
  variance_days: number;           // NEW: forecast - planned
}

export interface EbitdaScenario {
  quarter: string;
  scenario: 'base' | 'optimistic' | 'conservative';
  state: string;
  revenue_at_risk: number;
  cost_savings: number;
  net_ebitda_impact: number;
}

export interface CrewCapacity {
  region: string;
  month: string;
  skill_type: 'copper_decom' | 'fiber_install' | 'customer_migration';
  available_crew_days: number;
  allocated_crew_days: number;
  slack_days: number;
}
```

---

## 5. Component Specifications (V2 Upgrades)

### 5.1 PlanKPIs — 8-Card Top Bar

Upgrade from 6 mock KPI cards to 8 live KPI cards:

| # | KPI | Source | Format |
|---|---|---|---|
| 1 | Wire Centers | `gold_wave_schedule` count | "42 total" |
| 2 | Planned % | milestone status aggregation | "38%" with progress ring |
| 3 | In-Flight % | milestone status = in_progress | "24%" |
| 4 | Completed % | milestone status = completed | "12%" |
| 5 | Total Cost | `retirement_cost_per_wire_center` sum | "$24.8M" |
| 6 | Budget Remaining | `silver_budget_allocation` gap | "$8.2M" |
| 7 | Net Salvage Value | `gold_copper_recovery_schedule` sum | "$3.4M" |
| 8 | Critical Milestones at Risk | milestone count (critical + delayed/blocked) | "7" in `--ll-critical` |

**Brand compliance:**
- Grid: `grid-cols-4` (2 rows of 4) or `grid-cols-8` on wide screens
- Card style: `--ll-surface-elevated`, 1px `#E5E2DD` border, no shadows
- Label: 12px uppercase `--ll-text-secondary`, tracking-wide
- Value: 28px bold `--ll-text-primary` or semantic color
- Focus ring: `outline: 2px solid #FF3621, offset 2px`

### 5.2 GanttTimeline — Live Wave Schedule

**V1:** Renders mock wire centers on a horizontal Gantt
**V2 upgrades:**
- Y-axis: wire centers from `gold_wave_schedule`, sorted by `retirement_priority_rank`
- X-axis: 2026-Q2 through 2029-Q4 (from `wave_year`/`wave_quarter`)
- Bar color by `assigned_wave` using brand data viz palette:
  - 2026: `#FF3621` (red), `#1B3139` (navy)
  - 2027: `#00A972` (green), `#6E8898` (slate)
  - 2028: `#FF8C69` (coral), `#FFD700` (gold)
  - 2029: repeat with lighter tints
- Bar width: proportional to `estimated_crew_days`
- Constraint icon overlay: Lucide icons per `ConstraintFlags` component
- Risk badge: colored dot on bar based on `retirement_readiness_score`
  - 80-100: `--ll-low` (green)
  - 60-79: `--ll-medium` (gold)
  - 40-59: `--ll-high` (coral)
  - 0-39: `--ll-critical` (red)
- Tooltip on hover: wire center name, wave, devices, customers, cost, salvage, constraints
- Click: selects wire center → opens `CostBenefitPanel`
- NEW: `earliest_eligible_wave` shown as a thin dotted line ("earliest possible")

### 5.3 WaveSelector — Enhanced Filter Bar

**V1:** 4 dropdowns (wave, state, status, constraint)
**V2:** 6 filter controls:

| Filter | Values | Source |
|---|---|---|
| Wave | All, 2026-Q2, 2026-Q3, ... 2029-Q4 | `assigned_wave` distinct |
| State | All, CO, MN, WA, OR, ID, AZ | `state_code` distinct |
| Fiber Ready | All, Yes, No | `fiber_ready` |
| Constraint | All, contract_locked, regulatory, revrec, crew_capacity, none | derived |
| Risk Tier | All, Critical, High, Medium, Low | from `retirement_readiness_score` ranges |
| Search | Free-text wire center name search | `wire_center_name` ILIKE |

**Brand compliance:**
- Labels: 12px uppercase `--ll-text-secondary`
- Dropdowns: `--ll-surface-elevated` background
- Clear button on each filter
- Active filter count badge

### 5.4 CostBenefitPanel — Detailed Cost Breakdown

**V1:** 4-column cost grid from proxy data
**V2:** Full cost waterfall + salvage offset:

```
┌────────────────────────────────────────────────────────────────┐
│ [Wire Center Name]                          [Close ✕]        │
├────────────────────────────────────────────────────────────────┤
│ COST BREAKDOWN          │ SALVAGE & OFFSET                   │
│ Fiber Build    $380K    │ Copper Weight    2.4 tons           │
│ Equip Removal  $142K    │ LME Price        $8,420/ton         │
│ Cust Migration $96K     │ Gross Salvage    $20.2K             │
│ Reg Filing     $28K     │ Decom Cost       -$12.1K            │
│ ─────────────────────── │ ───────────────────────────         │
│ TOTAL COST     $646K    │ NET SALVAGE      $8.1K              │
│                         │ Signal: 🟢 SELL                     │
├────────────────────────────────────────────────────────────────┤
│ MILESTONES (from retirement_milestones)                       │
│ ● PUC Filing Submitted         ✅ Completed  2026-04-15      │
│ ● 90-Day Notice Mailed         🔵 In Progress                │
│ ● Fiber Install Complete       ⚪ Not Started 2026-08-01     │
│ ● Customer Migration Start     ⚪ Not Started 2026-09-01     │
│ ● Copper Decommission          ⚪ Not Started 2026-11-01     │
├────────────────────────────────────────────────────────────────┤
│ CONSTRAINTS                                                   │
│ 🔒 Contract: MSA expires 2027-03-15 (Ironclad CLM)           │
│ ⚖️ RevRec: ASC 606 deferred through 2027-06                  │
└────────────────────────────────────────────────────────────────┘
```

New data from gold tables:
- Cost waterfall with 4 components (was: single total)
- Salvage revenue offset with LME pricing and SELL/HOLD signal
- Real milestones with `planned_date`, `actual_date`, `forecast_date`, `variance_days`
- Contract + RevRec constraints from silver tables

### 5.5 MigrationTable — Sortable Data Grid

**V1:** Sortable table with mock data
**V2 columns (from joined gold tables):**

| Column | Source | Sortable | Format |
|---|---|---|---|
| Priority | `retirement_priority_rank` | ✅ | #1, #2, ... |
| Wire Center | `wire_center_name` | ✅ | text |
| State | `state_code` | ✅ | badge |
| Wave | `assigned_wave` | ✅ | "2026-Q3" |
| Devices | `copper_device_count` | ✅ | number |
| Customers | `affected_customer_count` | ✅ | number |
| Readiness | `retirement_readiness_score` | ✅ | progress bar 0-100 |
| Total Cost | `total_retirement_cost` | ✅ | currency |
| Net Salvage | `net_salvage_value_usd` | ✅ | currency |
| Revenue at Risk | `annual_revenue_at_risk` | ✅ | currency/yr |
| Crew Days | `estimated_crew_days` | ✅ | number |
| Constraint | derived | ✅ | icon + label |
| Fiber Ready | `fiber_ready` | ✅ | ✅/❌ |

**Brand compliance:**
- Header: `--ll-surface`, `--ll-text-secondary`, 600 weight, 13px
- Rows: alternating `--ll-surface-elevated` / `--ll-surface`
- Conditional formatting: readiness score color-coded by tier
- Sort indicator: Lucide `ArrowUpDown` icon

### 5.6 ScenarioCompare — EBITDA Scenario Cards

**V1:** Mock scenario cards
**V2:** Real EBITDA scenario comparison from `gold_ebitda_forecast`

3 scenario cards side-by-side:

| Scenario | Description |
|---|---|
| Base | Standard retirement timeline by ML risk tier |
| Optimistic | Accelerated retirement, higher salvage prices |
| Conservative | Delayed retirement, lower salvage prices |

Each card shows:
- Net EBITDA impact (sum across quarters)
- Revenue at risk (cumulative)
- Cost savings realized
- Quarterly sparkline chart (mini area chart)
- "Set Active" toggle (mock — Lakebase P5-SCHEMA)

### 5.7 BudgetChart — Budget vs. Actual

**V2 upgrade:** Replace mock data with `silver_budget_allocation` joined to `retirement_cost_per_wire_center`.
- Stacked bar chart by state: allocated vs. spent vs. remaining
- Color: `#FF3621` (spent), `#00A972` (remaining), `#6E8898` (unallocated)
- Y-axis: USD with units label

### 5.8 RegulatoryChecklist — Per-State Compliance

**V2 upgrade:** Use `state_puc_jurisdiction_requirements` + `retirement_milestones` (type=regulatory).
- Grouped by state
- Notice period countdown (days remaining to clear)
- Status: `--ll-low` (clear), `--ll-medium` (pending), `--ll-critical` (blocked)

### 5.9 ConstraintFlags — Icon Badges (Unchanged)

Existing Lucide icons, updated to use CSS custom properties for color:
- `Lock` → contract_locked (`--ll-medium`)
- `Scale` → regulatory_notice_pending (`--ll-info`)
- `DollarSign` → revrec_locked (`--ll-high`)
- `Users` → crew_capacity_constrained (`--ll-critical`)

### 5.10 NEW: CrewCapacityHeatmap

New component powered by `crew_availability_per_region_per_month`:
- Heatmap: rows = regions (CO, MN, WA, OR, ID, AZ), columns = months
- Cell color: slack_days gradient (green → yellow → red)
- Tooltip: available, allocated, slack crew-days
- Skill type toggle: copper_decom / fiber_install / customer_migration

---

## 6. Integration Points with Existing Apps

### 6.1 copper-map (Beat 1) → retirement-plan (Beat 2)

| Integration | Direction | Mechanism |
|---|---|---|
| Risk tier per device | copper-map → retirement-plan | Shared table: `gold_device_risk_predictions` |
| Wire center scorecard | copper-map → retirement-plan | Shared table: `gold_wire_center_scorecard` |
| Wire center boundary (GeoJSON) | copper-map → retirement-plan | Shared table: `wire_center_boundary` |
| Selected wire center context | copper-map → retirement-plan | URL param: `?wire_center_id=WC-CO-001` |

**Deep-link pattern:** A user clicks a wire center on the copper-map hex map → the app
links to `retirement-plan/?wire_center_id=WC-CO-001` which:
1. Pre-selects the wire center in the WaveSelector filter
2. Opens the CostBenefitPanel for that wire center
3. Scrolls the GanttTimeline to highlight that wire center's bar

**Implementation:**
- `App.tsx`: Parse `?wire_center_id` from URL on mount
- If present, fetch that wire center's data and pre-select it
- copper-map adds outbound links in its wire-center detail popover

### 6.2 Risk Model Integration

| Data Point | Source | Usage in retirement-plan |
|---|---|---|
| Device risk tier | `gold_device_risk_predictions.risk_tier` | Color-coded risk badges in GanttTimeline and MigrationTable |
| Composite risk score | `gold_device_risk_predictions.composite_risk_score` | Aggregated to wire-center level for readiness scoring |
| Critical device count | `gold_wave_schedule.critical_risk_devices` | KPI card: "X critical-risk devices" |
| Champion vs. challenger | `copper_risk_scores.models_agree` | Future: flag wire centers where models disagree |

### 6.3 regulatory-assistant (Beat 4) → retirement-plan (Beat 2)

| Integration | Direction | Mechanism |
|---|---|---|
| State PUC requirements | reg-assistant → retirement-plan | Shared table: `state_puc_jurisdiction_requirements` |
| Regulatory milestones | Both | Shared table: `retirement_milestones` (type=regulatory) |
| Deep link | retirement-plan → reg-assistant | Link from RegulatoryChecklist → reg-assistant `?state=CO` |

---

## 7. Server Endpoint Updates

### 7.1 Existing Endpoints (V2 updates)

| Endpoint | V1 Status | V2 Change |
|---|---|---|
| `PUT /api/plan/wave-assignment` | Mock (console log) | Keep mock until P5-SCHEMA |
| `PUT /api/plan/status` | Mock (console log) | Keep mock until P5-SCHEMA |
| `POST /api/plan/scenario` | Mock (queued) | Keep mock until P4-SEQ job API |

### 7.2 New Endpoints

| Endpoint | Purpose | Source |
|---|---|---|
| `GET /api/plan/ebitda-scenarios` | EBITDA scenario data for ScenarioCompare | `ebitda_scenarios.sql` |
| `GET /api/plan/crew-capacity` | Crew capacity heatmap data | `crew_capacity.sql` |
| `GET /api/plan/wire-center/:id/detail` | Full wire-center detail (cost + milestones + constraints) | `cost_benefit.sql` + `milestone_timeline.sql` |

---

## 8. UX Wireframe Concepts

### 8.1 Page Layout (Desktop, 1440px+)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Lakelink Fiber  │  Retirement Plan Tracker        [LIVE] [SYNTHETIC]  │
├─────────────────────────────────────────────────────────────────────────┤
│ [KPI 1] [KPI 2] [KPI 3] [KPI 4] [KPI 5] [KPI 6] [KPI 7] [KPI 8]    │
├─────────────────────────────────────────────────────────────────────────┤
│ Wave [▾] State [▾] Fiber [▾] Constraint [▾] Risk [▾] [🔍 Search]     │
├─────────────────────────────────────────────────────────────────────────┤
│ [Gantt Timeline] [Migration Table] [Budget] [Regulatory] [Scenarios]  │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                        │
│   ACTIVE TAB CONTENT                                                   │
│   (GanttTimeline / MigrationTable / BudgetChart /                      │
│    RegulatoryChecklist / ScenarioCompare)                               │
│                                                                        │
│   + CrewCapacityHeatmap (below main content on Gantt tab)              │
│                                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ [CostBenefitPanel] — slides up when a wire center is selected          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Nav Header

Per brand guide §6:
- Left: "Lakelink Fiber" wordmark (`--ll-secondary`, 600 weight, 16px)
- Left: "Retirement Plan Tracker" subtitle (muted, 13px)
- Right: Data source badge (LIVE + SYNTHETIC)
- Background: `--ll-surface` with bottom border `#E5E2DD`
- **Note:** V1 uses dark navy nav (`bg-[#1B3139]`). V2 must switch to brand-guide
  light nav (`--ll-surface`) for cross-app consistency with copper-map.

### 8.3 Color System (CSS Custom Properties)

```css
:root {
  --ll-primary: #FF3621;
  --ll-secondary: #1B3139;
  --ll-accent: #00A972;
  --ll-surface: #F9F7F4;
  --ll-surface-elevated: #FFFFFF;
  --ll-surface-dark: #1B3139;
  --ll-text-primary: #1B3139;
  --ll-text-secondary: #6E8898;
  --ll-text-inverse: #FFFFFF;
  --ll-critical: #FF3621;
  --ll-high: #FF8C69;
  --ll-medium: #FFD700;
  --ll-low: #00A972;
  --ll-info: #60A5FA;
  --ll-border: #E5E2DD;
}
```

### 8.4 Responsive Breakpoints

| Breakpoint | KPI Grid | Gantt | Table |
|---|---|---|---|
| ≥1440px | 8 columns | Full timeline | All columns |
| 1024–1439px | 4 columns (2 rows) | Scrollable | Hide crew_days, salvage |
| 768–1023px | 2 columns (4 rows) | Horizontal scroll | Priority columns only |
| <768px | 1 column (stack) | Not shown (table only) | Card view |

---

## 9. Mock Data Transition Strategy

### 9.1 Feature Flag

Retain `USE_MOCK_DATA` feature flag for fallback:

```typescript
// config.ts
export const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';
```

### 9.2 Data Fetching Layer

```typescript
// lib/planApi.ts (V2)
import { USE_MOCK_DATA } from '../config';
import { mockWireCenters, mockKPIs, mockMilestones, mockScenarios } from '../mock/mockData';

export async function fetchWaveSchedule(filters: PlanFilters) {
  if (USE_MOCK_DATA) return mockWireCenters;
  const res = await fetch(`/api/sql/wave_schedule?${filterParams(filters)}`);
  return res.json();
}

export async function fetchPlanKPIs() {
  if (USE_MOCK_DATA) return mockKPIs;
  const res = await fetch('/api/sql/plan_kpis');
  return res.json();
}

// ... similar for all queries
```

### 9.3 Acceptance Criteria for "Live Data" Mode

- [ ] All 5 existing SQL queries replaced with V2 gold-table queries
- [ ] 2 new SQL queries added (ebitda_scenarios, crew_capacity)
- [ ] `USE_MOCK_DATA=false` renders correctly with live data
- [ ] Filter dropdowns populated from live data (not hardcoded)
- [ ] GanttTimeline renders wire centers from `gold_wave_schedule`
- [ ] CostBenefitPanel shows 4-component cost waterfall + salvage
- [ ] MilestoneTimeline renders from `retirement_milestones`
- [ ] ScenarioCompare shows 3 EBITDA scenarios from `gold_ebitda_forecast`
- [ ] Deep-link `?wire_center_id=X` pre-selects and scrolls

---

## 10. Deployment & Testing

### 10.1 App Configuration

- **App name:** `retirement-plan`
- **Source path:** `/Workspace/Users/stephen.hage@databricks.com/copper-retirement/apps/retirement-plan`
- **Command:** `npm install && npm run build && npm start`
- **SQL warehouse:** Required (analytics plugin)
- **Port:** 8000 (injected by `DATABRICKS_APP_PORT`)

### 10.2 Test Plan

| Test | Expected Result |
|---|---|
| Load with `USE_MOCK_DATA=true` | Renders V1 mock data correctly |
| Load with `USE_MOCK_DATA=false` | Renders live gold-table data |
| Filter by state=CO | Shows only Colorado wire centers |
| Filter by wave=2026-Q3 | Shows only Q3 2026 wire centers |
| Click wire center on Gantt | CostBenefitPanel opens with correct data |
| Navigate from copper-map deep link | Pre-selects wire center |
| All KPI cards populated | 8 cards with non-zero values |
| ScenarioCompare tab | 3 scenario cards with EBITDA data |
| Budget tab | Stacked bar chart by state |
| Regulatory tab | Per-state checklist with countdown |

---

## 11. Coordination Notes

### For @designer
- Please review: nav header change (dark → light per brand guide §6)
- Please review: 8-KPI layout (was 6) — grid-cols-8 vs grid-cols-4×2
- Please review: CrewCapacityHeatmap color ramp (green→yellow→red)
- Please review: CostBenefitPanel wireframe layout
- Please review: responsive breakpoints

### For @data-engineer
- **silver_budget_allocation:** Uses `total_allocated_budget` and `budget_gap` (no `spent_amount`
  column). SQL queries should compute budget remaining as `total_allocated_budget + budget_gap`
  (budget_gap is negative when cost > budget).
- **silver_contract_constraints:** No `wire_center_id` column — joins to wire centers via
  `physical_device_id` → `copper_plant_wire_center_jurisdiction.wire_center_id`. Constraint
  status uses `constraint_status` (blocked/expiring_soon/clear) and `eligible_for_retirement`.
- **silver_revenue_recognition_constraints:** Same join path via `physical_device_id`.
  Uses `revrec_eligible_for_retirement` and `constraint_severity` (high/medium/low).
- Verify `crew_availability_per_region_per_month` column names match

### For @pm
- Lakebase write-back (P5-SCHEMA) remains the sole blocker for edit functionality
- All other Beat 2 data dependencies are now resolved
- Recommend prioritizing P5-SCHEMA to enable drag-to-reschedule on Gantt

---

*All data displayed is SYNTHETIC. This application is part of the Lakelink Fiber copper retirement demo.*
