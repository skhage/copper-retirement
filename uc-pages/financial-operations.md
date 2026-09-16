# Financial Operations

## Overview

The Financial Operations domain models the economic impact of Lakelink Fiber's copper retirement program — answering "what EBITDA improvement does retirement deliver, what does migration cost, and when do we break even per wire center." This domain connects circuit-level revenue-at-risk to retirement milestones, contractor costs, commodity prices, and EBITDA forecasting.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.gold_ebitda_forecast` | Gold | One row per wire_center × forecast_period | 5,655 | Per-wire-center EBITDA impact forecast — projected savings from copper retirement over time. |
| `copper_retirement.gold_circuit_revenue_at_risk` | Gold | One row per circuit | 14,777 | Per-circuit MRR and revenue-at-risk with contract status and churn probability. |
| `copper_retirement.gold_commodity_price_forecast` | Gold | One row per commodity × forecast_month | 72 | Copper commodity price forecast — scrap value projections for retired copper plant. |
| `copper_retirement.gold_contractor_scorecard` | Gold (MV) | One row per contractor | varies | Contractor performance scorecard — cost, schedule adherence, quality ratings. |
| `copper_retirement.gold_retirement_executive_summary` | Gold (MV) | One row per summary dimension | 50 | Executive-level retirement program summary — KPIs, status, financial highlights. |
| `copper_retirement.retirement_milestones` | Reference | One row per wire_center × milestone | 927 | Wire center retirement milestone schedule — planned dates for each phase of retirement. |
| `copper_retirement.copper_commodity_price` | Reference | One row per date × commodity | 10,482 | Historical copper commodity prices — LME and COMEX daily spot/futures. |
| `copper_retirement.contractor_performance` | Reference | One row per contractor × project | 10,000 | Contractor performance records — completion rates, cost overruns, safety incidents. |
| `copper_retirement.copper_ebitda_impact_achieved` | Metric View | Aggregated metric | — | Metric view: realized EBITDA improvement from completed copper retirements. |
| `copper_retirement.copper_ebitda_impact_forecast` | Metric View | Aggregated metric | — | Metric view: projected EBITDA impact from planned copper retirements. |
| `copper_retirement.copper_retirement_project_status` | Metric View | Aggregated metric | — | Metric view: overall project status KPIs including device counts, fiber readiness, risk distribution. |

### ERP & Financial Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_enterprise.budget` | 100,000 | Enterprise budget records — capital and operating budgets by cost center and period. |
| `tmf_enterprise.financial_account` | 10,000 | Financial account master — GL account codes, cost centers, profit centers. |
| `oracle_erp_source.gl_budgets` | 96 | Oracle GL budget entries — annual budget allocations by account. |
| `oracle_erp_source.gl_je_headers` | 10,000 | Oracle GL journal entry headers — posting dates, batch IDs, journal categories. |
| `oracle_erp_source.gl_je_lines` | 20,000 | Oracle GL journal entry lines — debit/credit amounts by account. |
| `oracle_erp_source.ra_billed_circuit_rates` | 56,061 | Billed circuit rates with circuit-level detail — revenue-at-risk calculation source. |
| `refinitiv_fx_source.gl_daily_rates` | 23,360 | Daily FX rates for multi-currency financial consolidation. |
| `salesforce_source.contract_line_item` | 56,088 | Circuit-level MRR with UnitPrice — per-circuit revenue for financial modeling. |

## Entity Relationships

```
gold_ebitda_forecast
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id
  └── wire_center_id → retirement_milestones.wire_center_id

gold_circuit_revenue_at_risk
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id
  └── customer_id → tmf_customer.customer.customer_id

retirement_milestones
  └── wire_center_id → wire_center_boundary.wire_center_id
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id

contractor_performance
  └── contractor_id → tmf_businesspartner.bp_agreement.bp_agreement_id

ra_billed_circuit_rates
  └── circuit_id → gold_circuit_revenue_at_risk (join key)
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Total Revenue at Risk | Sum of monthly recurring revenue across all copper circuits | `gold_circuit_revenue_at_risk` SUM(mrr) |
| EBITDA Impact Achieved | Realized EBITDA improvement from completed retirements | `copper_ebitda_impact_achieved` metric view |
| EBITDA Impact Forecast | Projected EBITDA improvement from planned retirements | `copper_ebitda_impact_forecast` metric view |
| Copper Scrap Value | Projected scrap revenue from retired copper at forecast commodity prices | `gold_commodity_price_forecast` × estimated copper tonnage |
| Contractor Cost per WC | Average contractor cost to retire one wire center | `contractor_performance` AVG(cost) GROUP BY wire_center_id |
| Milestones On-Track | Percentage of retirement milestones meeting planned dates | `retirement_milestones` WHERE actual_date <= planned_date |

## Data Quality Notes

- **EBITDA forecast:** 5,655 rows covering all 103 wire centers across multiple forecast periods.
- **Revenue-at-risk:** 14,777 circuits with MRR data. Cross-validated against 56K Oracle billed circuit rates and 56K Salesforce contract line items.
- **Commodity prices:** 10,482 historical price points. Forecast extends 72 periods ahead.
- **Contractor data:** 10K performance records. Scorecard aggregated as a materialized view in the DLP pipeline.
- **Milestones:** 927 milestone records across 103 wire centers (∼9 milestones per wire center).
- **Currency:** Multi-currency support via 23K daily FX rates from Refinitiv.

## Related Domains

- **Physical Plant** — Wire center scorecard drives retirement sequencing and priority
- **Circuits & Services** — Circuit-level MRR feeds revenue-at-risk aggregation
- **Customer Impact** — Customer churn risk affects realized vs. forecast EBITDA
- **Regulatory** — PUC filing timelines constrain retirement milestone scheduling
