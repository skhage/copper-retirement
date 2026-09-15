# Financial & EBITDA Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

Commodity pricing, cost forecasting, EBITDA impact tracking, and executive summary rollups.

## Tables (5)

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

Key columns: price_date, commodity_type, price_per_unit, unit, region, labor_cost_index, material_cost_index

### `gold_commodity_price_forecast` (Managed)

> Forecasted copper/fiber commodity prices, labor costs, and material cost indices.

Key columns: forecast_date, commodity_type, forecast_price, confidence_lower, confidence_upper, forecast_horizon_days

### `gold_ebitda_forecast` (Managed)

> EBITDA forecast for copper retirement program.

Key columns: forecast_date, state_code, ebitda_impact, avoided_maintenance, revenue_retained, capex_avoided, confidence_interval

### `copper_ebitda_impact_achieved` (Metric View)

> EBITDA and revenue impact metrics for the Lakelink Fiber copper retirement program -- quantifies annual savings, avoided costs, and revenue impact.

This is a governed metric view providing standardized EBITDA KPIs. Key dimensions: state_code, quarter. Key measures: ebitda_impact_achieved, avoided_maintenance_savings, revenue_retained, total_program_savings.

### `gold_retirement_executive_summary` (Materialized View)

> Gold layer: per-state executive summary of copper retirement program.

Key columns: state_code, total_devices, devices_retired, pct_retired, customers_impacted, customers_migrated, total_revenue_at_risk, ebitda_impact, risk_tier_distribution
