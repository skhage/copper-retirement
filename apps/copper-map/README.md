# P7-MAP — Copper Retirement Impact Map

**Demo Beat 1:** "Where should we dig up copper, and what happens when we do?"

**REDESIGNED 2026-09-11** per CEO directive: App is NOT about at-risk devices.
It's about the **impact of retiring copper** — customer risk, revenue at risk,
network disruption, and what-if scenario analysis.

**Framework:** AppKit (React/TypeScript) — Databricks Apps platform
**Data pattern:** Analytics (SQL warehouse, read-only) + Genie Agent (what-if)
**Status:** SCAFFOLDED v2 — redesigned mock data layer, real queries blocked on FIX-COORDINATES + P2-H3 + P4-RISK

---

## Overview

Interactive H3 hex-grid map showing **wire center retirement impact** across
Lakelink's network footprint. Each wire center shows:
- **Customer impact** — affected customers (residential + business), contract-locked count, churn risk
- **Revenue at risk** — MRR from copper services (voice, broadband, fixed line)
- **Network disruption** — cascading service impact score, fiber readiness
- **Cost/benefit** — retirement cost, scrap copper recovery, net cost
- **What-if analysis** — Genie Agent chat for scenario planning

Three tabs: **Impact Map** | **Wire Center Table** | **What-If Analysis**

All data displayed is **SYNTHETIC** — generated for demo purposes only.

## Architecture

```
client/src/
├── App.tsx                  # Root: 3-tab layout, KPI bar, filters, map+table+whatif
├── components/
│   ├── ImpactDetailPanel.tsx # Slide-out detail for selected wire center
│   ├── WhatIfChat.tsx       # Genie Agent chat for what-if scenarios
│   ├── MapView.tsx          # [LEGACY] deck.gl map placeholder
│   ├── FilterPanel.tsx      # [LEGACY] Sidebar filters
│   ├── SummaryKPIs.tsx      # [LEGACY] Top KPI bar (device-centric)
│   ├── DevicePopover.tsx    # [LEGACY] Device detail popover
│   ├── DeviceTable.tsx      # [LEGACY] Device drill-down table
│   └── RiskLegend.tsx       # [LEGACY] Risk color legend
├── lib/
│   └── formatters.ts        # Number/currency/percent formatting helpers
└── mock/
    ├── retirementData.ts    # NEW: Wire center impact data model
    └── mockData.ts          # [LEGACY] Old device-centric mock data

config/queries/
├── map_kpis.sql             # Retirement KPIs (revenue, customers, cost)
├── hex_risk_summary.sql     # Wire center impact aggregation
├── device_detail.sql        # Per-device detail (legacy)
├── filter_options.sql       # Distinct values for filter dropdowns
└── wire_center_boundaries.sql # GeoJSON polygons for wire-center overlay

server/
└── server.ts                # AppKit backend (analytics plugin)

tests/
└── smoke.spec.ts            # Playwright smoke test
```

## Data Model (v2 — Retirement Impact)

| Field | Description |
|---|---|
| `wire_center_id` | Unique wire center identifier |
| `customers_affected` | Total customers on copper in this area |
| `revenue_at_risk_mrr` | Monthly recurring revenue from copper services |
| `network_disruption_score` | 0-100: cascading impact of digging here |
| `retirement_priority` | 0-100: composite score (higher = retire sooner) |
| `priority_tier` | retire-now / plan-next / evaluate / defer |
| `retirement_cost_usd` | Estimated cost to decommission |
| `scrap_recovery_usd` | Copper scrap value recovery |
| `customers_contract_locked` | Customers who can't be migrated yet |
| `fiber_ready_pct` | % of area already fiber-capable |

## Mock Data Strategy

11 wire centers across 6 LEGACY_STATES (CO, MN, WA, OR, AZ, ID) with:
- Realistic customer counts (45-231 per wire center)
- Revenue MRR broken down by voice/broadband/fixed line
- Network disruption scores (12-62/100)
- Fiber readiness ranging 58%-94%
- Retirement costs $108K-$924K with scrap recovery
- Regulatory notice periods (150-365 days)
- Contract-locked customer constraints
- Mock Genie Agent responses for what-if scenarios

## What-If Analysis (Genie Agent)

The What-If tab provides a chat interface for scenario analysis.
Currently uses mock responses; will connect to P6-SUPER Genie Agent when deployed.

Example questions:
- "What if we retire all copper in Colorado first?"
- "Show me the revenue impact of retiring Denver Downtown"
- "Which wire centers can we retire with zero contract-locked customers?"

## Blockers

1. **FIX-COORDINATES** — `geographic_address` lat/lon need valid US coords. Partially fixed (Cells 3+4 done, Cell 7 pending).
2. **P2-H3** — H3 indexing of address points. Blocks hex grid aggregation.
3. **P4-RISK-MODEL-TRAIN** — Risk model scores. Blocks priority scoring.
4. **P0-DATAGEN-WIRECENTER-EXECUTE** — Wire-center boundary polygons.
5. **P6-SUPER** — Genie Agent endpoint for real what-if analysis.

## Governance Tags

| Tag | Value |
|---|---|
| `project` | `copper-retirement` |
| `developer` | `copper-app` |

## Dependencies on Other Agents

- **@data-engineer:** FIX-COORDINATES, P0-DATAGEN-WIRECENTER-EXECUTE
- **@ml-engineer:** P4-RISK-MODEL-TRAIN (retirement priority scoring)
- **@data-analyst:** Profiled data for realistic filter values
- **@pm:** P6-SUPER Genie Agent endpoint for what-if
