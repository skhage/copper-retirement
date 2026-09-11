# Commodity & Workforce Dashboard (P7-COMMODITY)

**Demo Beat 5:** "Who digs, and when do we sell copper?"

## Overview

React/TypeScript Databricks App providing copper commodity price forecasting,
recovered copper tracking, and contractor workforce management for LakeLink
Fiber's copper retirement program.

**All data is SYNTHETIC.**

## Architecture

- **Framework:** AppKit (React/TypeScript), `--features analytics`
- **Data access:** SQL warehouse via analytics plugin
- **Mock data:** Feature flag `USE_MOCK_DATA=true` toggles between mock and live SQL

## Screens (3 tabs)

1. **Price Forecast** — Historical LME copper spot + 3M/15M forwards chart,
   AI sell/hold recommendation with confidence bands, FX rate context
2. **Recovery Tracker** — Recovered copper volume/grade/value by decommission
   project, scrap grade breakdown with LME discount percentages
3. **Contractors** — Contractor scorecard with safety scores, OSHA rates,
   SLA compliance, geographic coverage, and project assignment

## Components (7)

| Component | Description |
|---|---|
| `CommodityKPIs` | 7-card KPI bar: spot price, recovered copper, scrap value, etc. |
| `PriceChart` | SVG area chart with historical + forecast + confidence bands |
| `SellHoldRecommendation` | AI recommendation card with price targets and reasoning |
| `FxContextPanel` | FX cross-rates from `refinitiv_fx_source.gl_daily_rates` |
| `RecoveryTracker` | Recovery table + scrap grade breakdown cards |
| `ContractorScorecard` | Contractor cards with metrics grid + assign button |

## SQL Queries (5)

| Query | Source Tables | Status |
|---|---|---|
| `commodity_kpis.sql` | bp_agreement, work | Partial (proxy KPIs) |
| `price_history.sql` | copper_commodity_price | BLOCKED (table pending) |
| `recovery_summary.sql` | recovered_copper_tracking | BLOCKED (table pending) |
| `contractor_shortlist.sql` | bp_agreement + work | Works NOW (proxy) |
| `fx_rates.sql` | gl_daily_rates | Works NOW (23K rows) |

## Data Dependencies

| Table | Schema | Status | Blocking Task |
|---|---|---|---|
| `copper_commodity_price` | copper_retirement | NOT EXISTS | P0-DATAGEN-COMMODITY-EXECUTE |
| `recovered_copper_tracking` | copper_retirement | NOT EXISTS | P0-DATAGEN-COMMODITY-EXECUTE |
| `contractor_performance` | copper_retirement | NOT EXISTS | P0-DATAGEN-CONTRACTOR-EXECUTE |
| `bp_agreement` | tmf_businesspartner | Available (10K) | — |
| `gl_daily_rates` | refinitiv_fx_source | Available (23K) | — |
| `work` | tmf_enterprise | Available (100K) | — |

## Governance Tags

- `project: copper-retirement`
- `developer: copper-app`

Applied in `app.yaml` and should be mirrored in `bundle/databricks.yml`:
```yaml
resources:
  apps:
    commodity-dashboard:
      tags:
        project: copper-retirement
        developer: copper-app
```

## Next Steps

1. Run `databricks apps init` to generate boilerplate (package.json, tsconfig.json, vite.config)
2. @data-engineer executes P0-DATAGEN-COMMODITY-EXECUTE → real price + recovery tables
3. @data-engineer executes P0-DATAGEN-CONTRACTOR-EXECUTE → contractor_performance table
4. @ml-engineer deploys P4-COMMODITY model → implement live forecast via server.ts endpoint
5. Install recharts/visx for production chart rendering (replace SVG placeholder)
6. P5-SCHEMA lands → enable Lakebase write-back for contractor assignment
