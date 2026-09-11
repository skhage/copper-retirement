# Dig-Safe Triage Console (P7-TRIAGE)

**Demo Beat 3:** "Dig crew hit something — triage/reroute fast?"
**Framework:** AppKit (React/TypeScript)
**Author:** @app-developer | **Scaffold date:** 2026-09-11

## Overview

Real-time incident triage console for copper retirement dig-safe events.
Field crews report dig strikes via incident form, the P6-TRIAGE agent
analyzes impact and recommends actions, and supervisors approve/reject
via human-in-loop controls.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  [TriageKPIs]          ← top bar (6 KPI cards)          │
│  [IncidentMap | TriageAgentChat]  ← main split view    │
│  [IncidentForm]        ← modal for new incidents        │
│  [IncidentDetailPanel] ← selected incident detail       │
│  [IncidentTable]       ← incident list with filters      │
│  [ActionLog]           ← audit trail of agent actions    │
└─────────────────────────────────────────────────────────────┘
```

## Data Sources

| Source | Table | Status |
|---|---|---|
| Dig-safe incidents | `dig_safe_incident` (synthetic, 5K target) | BLOCKED — P0-DATAGEN-DIGSAFE-EXECUTE |
| Work orders | `cdm_tmforum.tmf_enterprise.work` (22K repair/emergency) | AVAILABLE |
| Contractors | `cdm_tmforum.tmf_businesspartner.bp_agreement` (10K, 1,254 active) | AVAILABLE |
| Copper alarms | `cdm_tmforum.tmf_resource.alarm` (26,943 copper) | AVAILABLE |
| Triage agent | P6-TRIAGE Model Serving endpoint | BLOCKED — P6-TRIAGE |
| Incident writes | Lakebase `dig_incidents` table | BLOCKED — P5-SCHEMA |

## Mock Data

All data is SYNTHETIC. Feature flag `USE_MOCK_DATA = true` toggles
mock data vs live SQL queries. Mock data includes:
- 12 incidents across 6 LEGACY_STATES (CO, MN, WA, OR, ID, AZ) per SPEC_dig_safe_incident.md
- 8 mock agent responses with prioritized action lists
- 4 mock action log entries showing human approve/reject workflow
- KPIs derived from real table counts (22K work orders, 26,943 copper alarms)

## Governance Tags

- `project: copper-retirement`
- `developer: copper-app`

Applied in `app.yaml` and DAB bundle config.

## Dependencies

- **@data-engineer:** P0-DATAGEN-DIGSAFE-EXECUTE (synthetic incident data)
- **@ml-engineer:** P6-TRIAGE agent endpoint (agent chat)
- **@data-engineer:** P5-SCHEMA (Lakebase write-back)
- **FIX-COORDINATES:** Required for real incident map coordinates

## Next Steps

1. CEO runs `data_gen/fix_coordinates` → unblocks real geo data
2. @data-engineer executes P0-DATAGEN-DIGSAFE → 5K incident rows
3. Install deck.gl deps → swap IncidentMap placeholder for real map layer
4. @ml-engineer deploys P6-TRIAGE agent → implement SSE streaming in server.ts
5. P5-SCHEMA lands → enable Lakebase write-back for IncidentForm
6. Run `databricks apps init` to generate boilerplate then merge scaffold files
7. Add Playwright smoke tests (per @qa QA-TEST-COVERAGE)
