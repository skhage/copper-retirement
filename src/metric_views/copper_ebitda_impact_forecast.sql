-- Metric view: copper_ebitda_impact_forecast
-- Exported 2026-11-01 by @data-analyst (ACC-DA-MV-DDL-EXPORT) from SHOW CREATE TABLE cdm_tmforum.copper_retirement.copper_ebitda_impact_forecast.
-- Template parameters (text substitution before execution): ${catalog} (reference: cdm_tmforum), ${schema} (reference: copper_retirement).
-- Space-containing column names are backtick-quoted. Provisioning/execution is owned by ACC-DE-MV-DDL-PROVISION.
-- Synthetic-data note: see the view COMMENT below.

CREATE OR REPLACE VIEW ${catalog}.${schema}.copper_ebitda_impact_forecast (
  `State` COMMENT 'US state code where the copper circuits are deployed',
  `Device Type` COMMENT 'Type of copper equipment: CPE, OLT, ONT, or Patch Panel',
  `Risk Tier` COMMENT 'ML model predicted risk tier (V5) — drives retirement prioritization and forecast timing',
  `Scenario` COMMENT 'Forecast scenario: Base (planned timeline), Optimistic (accelerated by 1 quarter), Pessimistic (delayed by 1 quarter)',
  `Quarter` COMMENT 'Projected retirement quarter (YYYY-QN format) — when circuits are expected to be decommissioned',
  `Fiber Readiness` COMMENT 'Whether the wire center has fiber infrastructure ready — fiber-ready circuits have lower capex and faster migration',
  `Forecast Revenue at Risk` COMMENT 'Quarterly revenue at risk from copper circuit retirements — revenue that must be migrated to fiber to be retained',
  `Forecast Annual Revenue Exposure` COMMENT 'Full annualized revenue exposure from circuits retiring in this period — the total annual revenue tied to retiring circuits',
  `Forecast Cost Savings` COMMENT 'Quarterly operating cost savings from decommissioning copper plant — the primary EBITDA driver',
  `Forecast Capex` COMMENT 'Capital expenditure for fiber replacement in this quarter — fiber-ready circuits average $1.5K, new builds average $5.5K',
  `Forecast Net Benefit` COMMENT 'Net quarterly benefit: cost savings minus amortized capex (5-year straight-line) — the bottom-line quarterly gain',
  `Forecast EBITDA Impact` COMMENT 'Total quarterly EBITDA impact: cost savings + avoided maintenance (15%) minus amortized capex — the headline financial metric',
  `Circuit Count` COMMENT 'Number of copper circuits projected to retire in this period',
  `Avg Capex per Circuit` COMMENT 'Average capital expenditure per circuit — varies by fiber readiness ($1.5K fiber-ready vs $5.5K new build)',
  `Avg Risk Score` COMMENT 'Average ML composite risk score for circuits in this group — higher values indicate greater retirement urgency',
  `Savings to Capex Ratio` COMMENT 'Ratio of quarterly savings to capex investment — values above 0.5 indicate strong ROI within 2 years')
COMMENT 'DERIVED FROM SYNTHETIC DATA — Metric view: projected quarterly EBITDA impact from copper retirement across three scenarios (base, optimistic, conservative). Dimensions: quarter, scenario, state. Source: gold_ebitda_forecast.'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: ${catalog}.${schema}.gold_ebitda_forecast

comment: "DERIVED FROM SYNTHETIC DATA — Metric view: projected quarterly EBITDA impact\
  \ from copper retirement across three scenarios (base, optimistic, conservative).\
  \ Dimensions: quarter, scenario, state. Source: gold_ebitda_forecast."

dimensions:
  - name: State
    expr: state_code
    comment: US state code where the copper circuits are deployed
    display_name: State
    synonyms:
      - state code
      - geography
      - location
      - region

  - name: Device Type
    expr: device_type
    comment: "Type of copper equipment: CPE, OLT, ONT, or Patch Panel"
    display_name: Device Type
    synonyms:
      - equipment type
      - device category

  - name: Risk Tier
    expr: |-
      CASE risk_tier
        WHEN 'critical' THEN 'Critical'
        WHEN 'high' THEN 'High'
        WHEN 'medium' THEN 'Medium'
        WHEN 'low' THEN 'Low'
        ELSE COALESCE(risk_tier, 'Unknown')
      END
    comment: ML model predicted risk tier (V5) — drives retirement prioritization
      and forecast timing
    display_name: Risk Tier
    synonyms:
      - risk level
      - priority tier
      - ML risk tier

  - name: Scenario
    expr: |-
      CASE scenario
        WHEN 'base' THEN 'Base'
        WHEN 'optimistic' THEN 'Optimistic'
        WHEN 'pessimistic' THEN 'Pessimistic'
        ELSE scenario
      END
    comment: "Forecast scenario: Base (planned timeline), Optimistic (accelerated\
      \ by 1 quarter), Pessimistic (delayed by 1 quarter)"
    display_name: Scenario
    synonyms:
      - forecast scenario
      - projection type
      - case

  - name: Quarter
    expr: quarter
    comment: Projected retirement quarter (YYYY-QN format) — when circuits are expected
      to be decommissioned
    display_name: Quarter
    synonyms:
      - retirement quarter
      - period
      - time period

  - name: Fiber Readiness
    expr: |-
      CASE
        WHEN fiber_ready = true THEN 'Fiber Ready'
        WHEN fiber_ready = false THEN 'Not Fiber Ready'
        ELSE 'Not Assessed'
      END
    comment: Whether the wire center has fiber infrastructure ready — fiber-ready
      circuits have lower capex and faster migration
    display_name: Fiber Readiness
    synonyms:
      - migration readiness
      - fiber availability

measures:
  - name: Forecast Revenue at Risk
    expr: SUM(forecast_revenue_at_risk)
    comment: Quarterly revenue at risk from copper circuit retirements — revenue that
      must be migrated to fiber to be retained
    display_name: Revenue at Risk
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - revenue exposure
      - quarterly revenue at risk
      - revenue impact

  - name: Forecast Annual Revenue Exposure
    expr: SUM(forecast_annual_revenue_exposure)
    comment: Full annualized revenue exposure from circuits retiring in this period
      — the total annual revenue tied to retiring circuits
    display_name: Annual Revenue Exposure
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - annual exposure
      - total revenue at risk

  - name: Forecast Cost Savings
    expr: SUM(forecast_cost_savings)
    comment: Quarterly operating cost savings from decommissioning copper plant —
      the primary EBITDA driver
    display_name: Cost Savings
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - OpEx savings
      - operating savings
      - maintenance savings

  - name: Forecast Capex
    expr: SUM(forecast_capex)
    comment: "Capital expenditure for fiber replacement in this quarter — fiber-ready\
      \ circuits average $1.5K, new builds average $5.5K"
    display_name: Capex Investment
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - capital expenditure
      - fiber investment
      - capex

  - name: Forecast Net Benefit
    expr: SUM(forecast_net_benefit)
    comment: "Net quarterly benefit: cost savings minus amortized capex (5-year straight-line)\
      \ — the bottom-line quarterly gain"
    display_name: Net Benefit
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - net savings
      - net quarterly benefit

  - name: Forecast EBITDA Impact
    expr: SUM(forecast_ebitda_impact)
    comment: "Total quarterly EBITDA impact: cost savings + avoided maintenance (15%)\
      \ minus amortized capex — the headline financial metric"
    display_name: EBITDA Impact
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - EBITDA improvement
      - EBITDA benefit
      - financial impact

  - name: Circuit Count
    expr: SUM(circuit_count)
    comment: Number of copper circuits projected to retire in this period
    display_name: Circuits Retiring
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - circuits
      - retirement count
      - device count

  - name: Avg Capex per Circuit
    expr: "SUM(forecast_capex) / NULLIF(SUM(circuit_count), 0)"
    comment: Average capital expenditure per circuit — varies by fiber readiness ($1.5K
      fiber-ready vs $5.5K new build)
    display_name: Avg Capex/Circuit
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - unit capex
      - per-circuit cost

  - name: Avg Risk Score
    expr: AVG(avg_risk_score)
    comment: Average ML composite risk score for circuits in this group — higher values
      indicate greater retirement urgency
    display_name: Avg Risk Score
    format:
      type: number
      decimal_places:
        type: max
        places: 3
    synonyms:
      - average risk
      - risk score

  - name: Savings to Capex Ratio
    expr: "SUM(forecast_cost_savings) / NULLIF(SUM(forecast_capex), 0)"
    comment: Ratio of quarterly savings to capex investment — values above 0.5 indicate
      strong ROI within 2 years
    display_name: Savings/Capex Ratio
    format:
      type: number
      decimal_places:
        type: max
        places: 2
    synonyms:
      - ROI ratio
      - payback ratio
$$;
