# Financial & EBITDA Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

Commodity pricing, cost forecasting, EBITDA impact tracking, and executive summary rollups.

## Tables (5)

> **Scope note:** Financial tables cover all 50 US states (synthetic data), not limited to LEGACY_STATES (CO, MN, WA, OR, ID, AZ).

| Table | Type | Description |
|-------|------|-------------|
| `copper_commodity_price` | MANAGED | Synthetic copper/fiber commodity price history (2020-2026) with regional labor costs |
| `gold_commodity_price_forecast` | MANAGED | Forecasted copper/fiber commodity prices, labor costs, and material cost indices |
| `gold_ebitda_forecast` | MANAGED | EBITDA forecast for copper retirement program |
| `copper_ebitda_impact_achieved` | METRIC_VIEW | EBITDA and revenue impact metrics for the Lakelink Fiber copper retirement program |
| `gold_retirement_executive_summary` | MATERIALIZED_VIEW | Gold layer: per-state executive summary of copper retirement program |

## Key Relationships

* copper_ebitda_impact_achieved is a METRIC VIEW over financial rollups
* gold_retirement_executive_summary joins device/service/financial data by state
* gold_commodity_price_forecast extends copper_commodity_price with ai_forecast predictions

## Financial Metrics

The EBITDA impact model tracks:
* **Avoided maintenance costs**: Savings from decommissioning aging copper plant
* **Network operating expense reduction**: Power, cooling, space savings at COs
* **Revenue retention**: Customers migrated to fiber with equivalent or higher ARPU
* **Capital efficiency**: CapEx avoided on copper plant life extension

## Table Details

### `copper_commodity_price` (Managed)

> Synthetic copper/fiber commodity price history (2020-2026) with regional labor costs.

Key columns: price_date, region, copper_lme_price_usd_ton, copper_comex_price_usd_lb, fiber_cable_price_usd_km, labor_cost_index, material_cost_index. (7 cols — denormalized: one row per trading date × region with separate price columns for each commodity.)

### `gold_commodity_price_forecast` (Managed)

> Forecasted copper/fiber commodity prices, labor costs, and material cost indices.

Key columns: forecast_month (YYYY-MM), region (CO/MN/WA/OR/ID/AZ), copper_lme_forecast_usd_ton, copper_comex_forecast_usd_lb, fiber_cable_forecast_usd_km, labor_cost_index_forecast, material_cost_index_forecast, model_version, forecast_generated_date. (9 cols — same denormalized structure as copper_commodity_price but forward-looking.)

### `gold_ebitda_forecast` (Managed)

> EBITDA forecast for copper retirement program.

Key columns: state_code, device_type, risk_tier, fiber_ready, scenario, quarter, forecast_revenue_at_risk, forecast_annual_revenue_exposure, forecast_cost_savings, forecast_capex, forecast_net_benefit, forecast_ebitda_impact, circuit_count, avg_risk_score. Unique key is 6-part: state_code + device_type + risk_tier + fiber_ready + scenario + quarter. (15 cols, 5,655 rows)

### `copper_ebitda_impact_achieved` (Metric View)

> EBITDA and revenue impact metrics for the Lakelink Fiber copper retirement program -- quantifies annual savings, avoided costs, and revenue impact.

This is a governed metric view providing standardized EBITDA KPIs. Key dimensions: State, Device Type, Risk Tier, ML Risk Tier, Revenue Tier, Action Priority, Fiber Ready, Technology Domain, Circuit Lifecycle, PUC Filing Required. Key measures: Total Annual Revenue at Risk, Total Monthly Revenue at Risk, Total Billed Amount, Total Circuits, Avg Revenue per Circuit, High Value Circuits, High Value Revenue, Immediate Action Revenue, Critical Risk Revenue, Avg ML Composite Risk Score, Fiber Ready Revenue, PUC Filing Revenue. (22 cols = 10 dims + 12 measures, 14,777 rows)

### `gold_retirement_executive_summary` (Materialized View)

> Gold layer: per-state executive summary of copper retirement program.

Key columns: state_code (one row per state), total_copper_devices, active_devices, critical_risk_count, high_risk_count, wire_center_count, fiber_ready_devices, fiber_ready_pct, total_affected_services, total_affected_customers, voice_services_at_risk, broadband_services_at_risk, total_dig_incidents, regulatory_violations, total_repair_cost, avg_resolution_hours, available_contractors, avg_contractor_rating, total_crew_capacity, preferred_contractors, program_health_status (red/amber/green), _pipeline_aggregated_at. (23 cols — comprehensive per-state rollup joining device, service, dig-safe, and contractor data.)
