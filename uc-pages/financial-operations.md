# Financial & Operations

## Overview

The Financial & Operations domain quantifies the business case for Lakelink Fiber's copper retirement program. It models EBITDA impact across three scenarios (base, optimistic, pessimistic), tracks copper and fiber commodity prices for capital planning, scores contractor performance for dig-crew deployment, manages retirement milestones per wire center, and enforces ASC 606 revenue recognition constraints that gate retirement timing. Two metric views provide executive-ready KPIs for achieved and forecasted EBITDA impact.

## Key Tables

### EBITDA & Revenue Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.gold_ebitda_forecast` | Gold | One row per state/device_type/risk_tier/scenario/quarter | 5,655 | Projected quarterly EBITDA impact from copper retirement — three scenarios (base/optimistic/pessimistic) with revenue at risk, cost savings, capex, and net benefit per segment. |
| `copper_retirement.silver_revenue_recognition_constraints` | Silver | One row per transaction | 708 | ASC 606 revenue recognition constraints — flags circuits with deferred revenue that block retirement until recognition milestones are met. 29 columns with transaction detail, billing, and service linkage. |

### Commodity & Material Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.copper_commodity_price` | Reference | One row per date/region | 10,482 | Synthetic copper/fiber commodity price history (2020–2026) with LME and COMEX copper prices, fiber cable pricing, and regional labor/material cost indices. |
| `copper_retirement.gold_commodity_price_forecast` | Gold | One row per forecast_month/region | 72 | Forecasted copper/fiber commodity prices, labor costs, and material cost indices by region for capital planning. |

### Contractor & Workforce Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.gold_contractor_scorecard` | Gold (MV) | One row per contractor performance record | 10,000 | Contractor scorecard with actual incident and work order metrics — 36 columns covering safety scores, OSHA rates, crew size, certification status, and overall ratings. DLP materialized view. |
| `copper_retirement.contractor_performance` | Reference | One row per contractor performance record | 10,000 | Contractor performance baseline data — safety scores, project history, and operational metrics for fiber deployment contractor selection. 27 columns. |

### Project Milestone Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.retirement_milestones` | Reference | One row per wire_center/milestone | 927 | Copper retirement project milestones per wire center — planned vs actual dates, completion status, regulatory dependencies, and forecast dates. 14 columns. |

### Dig-Safe Incident Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.bronze_dig_safe_incidents` | Bronze (MV) | One row per dig-safe incident | 5,000 | Dig-safe incident registry with contractor enrichment — 30 columns including damage details, contractor accountability, geographic coordinates. DLP materialized view. |
| `copper_retirement.dig_safe_incident` | Source | One row per dig-safe incident | 5,000 | Source table for dig-safe excavation incidents with damage details, contractor accountability, and geographic/network route linkage. 24 columns. |

### Metric Views

| Table | Type | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.copper_ebitda_impact_achieved` | Metric View | One row per circuit (10 dimensions, 12 measures) | 14,777 | Achieved EBITDA and revenue impact metrics — quantifies annual revenue at risk, monthly exposure, billed amounts, and circuit counts across state, device type, risk tier, revenue tier, action priority, and fiber readiness dimensions. |
| `copper_retirement.copper_ebitda_impact_forecast` | Metric View | One row per state/device_type/risk_tier/scenario/quarter | 5,655 | Projected quarterly EBITDA impact across three scenarios — cost savings, capex, net benefit, and EBITDA impact by state, device type, risk tier, and fiber readiness. |

## Entity Relationships

```
gold_ebitda_forecast
  └── state_code → state_puc_jurisdiction_requirements.state_code (regulatory timeline)
  └── device_type, risk_tier → gold_device_risk_predictions (ML risk model output)
  └── Derived from: gold_circuit_revenue_at_risk (Circuits domain) aggregated by segment

silver_revenue_recognition_constraints
  └── customer_trx_id (PK) → oracle_erp_source.gl_je_lines (ERP transaction)
  └── bill_id → tmf_customer.bill.bill_id
  └── customer_id → tmf_customer.customer.customer_id
  └── customer_facing_service_id → tmf_service.customer_facing_service.customer_facing_service_id
  └── Blocks retirement when deferred_revenue_flag = TRUE

copper_commodity_price
  └── price_date + region (composite key)
  └── Sources: refinitiv_fx_source.gl_daily_rates (FX), synthetic LME/COMEX feeds
  └── → gold_commodity_price_forecast (time-series forecast from historical prices)

gold_commodity_price_forecast
  └── forecast_month + region (composite key)
  └── Derived from: copper_commodity_price (historical actuals → forecast model)

gold_contractor_scorecard (DLP materialized view)
  └── contractor_performance_id (PK) → contractor_performance.contractor_performance_id
  └── bp_agreement_id → tmf_businesspartner.bp_agreement.bp_agreement_id
  └── party_id → tmf_businesspartner.party_id
  └── Enriched with: dig_safe incident counts, work order metrics

contractor_performance
  └── contractor_performance_id (PK)
  └── bp_agreement_id → tmf_businesspartner.bp_agreement.bp_agreement_id
  └── Baseline data for gold_contractor_scorecard enrichment

retirement_milestones
  └── milestone_id (PK)
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id (Physical Plant)
  └── Links: planned/actual dates, regulatory dependencies

bronze_dig_safe_incidents (DLP materialized view)
  └── incident_id (PK) → dig_safe_incident.incident_id
  └── work_id → tmf_enterprise.work.work_id
  └── bp_agreement_id → tmf_businesspartner.bp_agreement.bp_agreement_id
  └── geographic_address_id → tmf_shared.geographic_address.geographic_address_id
  └── network_route_id → tmf_shared.network_route.network_route_id

copper_ebitda_impact_achieved (metric view)
  └── Sourced from: gold_circuit_revenue_at_risk + gold_device_risk_predictions + state_puc_jurisdiction_requirements
  └── 10 dimensions × 12 measures for executive dashboard slicing

copper_ebitda_impact_forecast (metric view)
  └── Sourced from: gold_ebitda_forecast
  └── 6 dimensions × 10 measures for scenario-based forecasting
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Total Annual Revenue at Risk | Annualized revenue from copper circuits at risk of retirement (USD) | `copper_ebitda_impact_achieved.Total Annual Revenue at Risk` |
| Quarterly EBITDA Impact | Net EBITDA impact per quarter: savings + avoided maintenance − amortized capex | `gold_ebitda_forecast.forecast_ebitda_impact` |
| Forecast Net Benefit | Quarterly net benefit: cost savings minus amortized capex (5yr/20Q) | `gold_ebitda_forecast.forecast_net_benefit` |
| Copper LME Price (USD/ton) | London Metal Exchange copper price for scrap value estimation | `copper_commodity_price.copper_lme_price_usd_ton` |
| Contractor Safety Score | Composite safety rating for fiber deployment contractors | `gold_contractor_scorecard.safety_score` |
| OSHA Recordable Rate | OSHA injury/illness rate per contractor | `gold_contractor_scorecard.osha_recordable_rate` |
| Milestone Completion % | Percentage of retirement milestones completed per wire center | `retirement_milestones.completion_percentage` |
| Deferred Revenue Blocks | Circuits blocked from retirement by ASC 606 deferred revenue | `silver_revenue_recognition_constraints WHERE deferred_revenue_flag = TRUE` |
| Dig-Safe Incident Count | Number of dig-safe incidents per state/contractor | `bronze_dig_safe_incidents` aggregate by state |
| Avg Revenue per Circuit | Average annual revenue per copper circuit for per-unit EBITDA modeling | `copper_ebitda_impact_achieved.Avg Revenue per Circuit` |

## Data Quality Notes

- **Commodity prices are synthetic:** `copper_commodity_price` contains synthetic LME/COMEX and fiber pricing data (2020–2026). Realistic ranges but not sourced from actual commodity exchanges. Forecasts extend 6 months ahead.
- **Three EBITDA scenarios:** `gold_ebitda_forecast` models base (planned timeline), optimistic (1 quarter earlier), and pessimistic (1 quarter later) retirement paths. 5,655 rows = all state/device/risk/quarter combinations across 3 scenarios.
- **Contractor data breadth:** Both `gold_contractor_scorecard` and `contractor_performance` have 10,000 rows — broader than the copper retirement scope to capture the full fiber deployment contractor pool.
- **Revenue recognition constraints:** 708 transactions flagged with ASC 606 deferred revenue constraints. These gate retirement timing — circuits cannot be retired until revenue recognition milestones are met.
- **Retirement milestones:** 927 milestones across wire centers with planned, actual, and forecast dates. Tracks regulatory dependencies that affect scheduling.
- **Metric views are rich:** `copper_ebitda_impact_achieved` has 14,777 rows with 10 dimensions and 12 measures — the primary executive dashboard table. `copper_ebitda_impact_forecast` mirrors the EBITDA forecast with 16 columns.
- **DLP materialized views:** `gold_contractor_scorecard` and `bronze_dig_safe_incidents` are DLP pipeline-managed. Refreshed on schedule.

## Related Domains

- **Circuits & Services** — `gold_circuit_revenue_at_risk` is the primary revenue input feeding EBITDA forecast models
- **Risk & ML** — Risk tier predictions from V5 model drive retirement sequencing and scenario timing in the EBITDA forecast
- **Regulatory** — PUC filing requirements and notice periods from `state_puc_jurisdiction_requirements` constrain retirement timelines and milestone scheduling
- **Physical Plant** — Wire center boundaries and device locations link milestones to physical deployment sites; contractor scorecard links to `tmf_businesspartner` for dig-crew selection
- **Customers** — Revenue recognition constraints reference customer billing and service subscriptions that must complete before retirement
