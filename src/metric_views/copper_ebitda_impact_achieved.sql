-- Metric view: copper_ebitda_impact_achieved
-- Exported 2026-11-01 by @data-analyst (ACC-DA-MV-DDL-EXPORT) from SHOW CREATE TABLE cdm_tmforum.copper_retirement.copper_ebitda_impact_achieved.
-- Template parameters (text substitution before execution): ${catalog} (reference: cdm_tmforum), ${schema} (reference: copper_retirement).
-- Space-containing column names are backtick-quoted. Provisioning/execution is owned by ACC-DE-MV-DDL-PROVISION.
-- Synthetic-data note: see the view COMMENT below.
-- 2026-11-04 @data-analyst ACC-DA-MV-FRESH-SRC-GAP: the source is now a SQL query. It selects explicit pipeline columns from
-- gold_circuit_revenue_at_risk and LEFT JOINs gold_device_risk_predictions (1 row per device) for ML Risk Tier / Avg ML Composite
-- Risk Score, so it no longer needs the out-of-pipeline ml_* columns. Prerequisite on a fresh deploy: gold_device_risk_predictions
-- must be loaded (snapshot, ACC-DE-MV-FRESH-SNAPSHOTS-1104) before this file runs. Live output is byte-identical (md5 43cfc2d5..., 5,464 groups).

CREATE OR REPLACE VIEW ${catalog}.${schema}.copper_ebitda_impact_achieved (
  `State` COMMENT 'US state code where the copper circuit is deployed',
  `Device Type` COMMENT 'Type of copper equipment serving this circuit',
  `Risk Tier` COMMENT 'Computed risk tier from plant health metrics — drives retirement prioritization and EBITDA timing',
  `ML Risk Tier` COMMENT 'ML model predicted risk tier (V5 model) — more granular than computed tier, includes medium and high levels',
  `Revenue Tier` COMMENT 'Revenue classification of the circuit: High Value (top revenue circuits), Medium Value, Standard',
  `Action Priority` COMMENT 'Recommended action priority for retirement: Immediate Action (critical risk + high value), High Priority, Monitor (low risk)',
  `Fiber Ready` COMMENT 'Whether the wire center has fiber infrastructure ready — fiber-ready circuits can migrate faster with lower capex',
  `Technology Domain` COMMENT 'Network technology domain of the circuit (e.g., copper_dsl, copper_pots, 5g_nr, gpon)',
  `Circuit Lifecycle` COMMENT 'Current lifecycle stage of the circuit — Active circuits generate revenue; Retired circuits represent achieved savings',
  `PUC Filing Required` COMMENT 'Whether state Public Utility Commission filing is required before retirement — affects timeline and cost',
  `Total Annual Revenue at Risk` COMMENT 'Total annualized revenue from copper circuits at risk of retirement — the headline financial exposure metric',
  `Total Monthly Revenue at Risk` COMMENT 'Monthly recurring revenue from copper circuits — the run-rate financial exposure',
  `Total Billed Amount` COMMENT 'Total billed operating cost for copper circuits — represents cost savings potential when circuits are retired',
  `Total Circuits` COMMENT 'Total number of copper circuits in the revenue-at-risk analysis',
  `Avg Revenue per Circuit` COMMENT 'Average annual revenue per copper circuit — used to estimate per-unit EBITDA impact of retirement',
  `High Value Circuits` COMMENT 'Circuits classified as high-value — these require careful migration to retain revenue',
  `High Value Revenue` COMMENT 'Annual revenue from high-value circuits — the most important revenue to retain during migration',
  `Immediate Action Revenue` COMMENT 'Revenue from circuits requiring immediate retirement action — the most urgent financial exposure',
  `Critical Risk Revenue` COMMENT 'Revenue from critical-risk circuits — highest probability of service degradation',
  `Avg ML Composite Risk Score` COMMENT 'Average ML composite risk score across circuits — higher values indicate greater retirement urgency',
  `Fiber Ready Revenue` COMMENT 'Revenue from circuits in fiber-ready wire centers — can be migrated with minimal capex',
  `PUC Filing Revenue` COMMENT 'Revenue from circuits requiring PUC regulatory filing — these have longer retirement timelines')
COMMENT 'DERIVED FROM SYNTHETIC DATA — Metric view: EBITDA and revenue impact achieved from copper retirement — annual revenue at risk, cost savings realized, and net EBITDA impact. Dimensions: quarter, state, retirement_phase. Source: gold_circuit_revenue_at_risk, gold_ebitda_forecast.'
WITH METRICS
LANGUAGE YAML
AS
$$
version: 1.1

source: |-
  SELECT g.state_code, g.device_type, g.computed_risk_tier, g.revenue_tier, g.action_priority,
    g.fiber_ready, g.technology_domain, g.circuit_lifecycle_status, g.puc_filing_required,
    g.estimated_annual_revenue, g.monthly_unit_price, g.total_billed_amount,
    d.risk_tier_predicted AS ml_risk_tier, d.composite_risk_score AS ml_composite_risk_score
  FROM ${catalog}.${schema}.gold_circuit_revenue_at_risk g
  LEFT JOIN ${catalog}.${schema}.gold_device_risk_predictions d
    ON g.physical_device_id = d.physical_device_id

comment: "DERIVED FROM SYNTHETIC DATA — Metric view: EBITDA and revenue impact achieved\
  \ from copper retirement — annual revenue at risk, cost savings realized, and net\
  \ EBITDA impact. Dimensions: quarter, state, retirement_phase. Source: gold_circuit_revenue_at_risk,\
  \ gold_ebitda_forecast."

dimensions:
  - name: State
    expr: state_code
    comment: US state code where the copper circuit is deployed
    display_name: State
    synonyms:
      - state code
      - geography
      - location

  - name: Device Type
    expr: |-
      CASE device_type
        WHEN 'cpe' THEN 'CPE'
        WHEN 'olt' THEN 'OLT'
        WHEN 'ont' THEN 'ONT'
        WHEN 'patch_panel' THEN 'Patch Panel'
        ELSE device_type
      END
    comment: Type of copper equipment serving this circuit
    display_name: Device Type
    synonyms:
      - equipment type

  - name: Risk Tier
    expr: |-
      CASE computed_risk_tier
        WHEN 'critical' THEN 'Critical'
        WHEN 'high' THEN 'High'
        WHEN 'medium' THEN 'Medium'
        WHEN 'low' THEN 'Low'
        ELSE COALESCE(computed_risk_tier, 'Unknown')
      END
    comment: Computed risk tier from plant health metrics — drives retirement prioritization
      and EBITDA timing
    display_name: Risk Tier
    synonyms:
      - risk level
      - priority tier

  - name: ML Risk Tier
    expr: |-
      CASE ml_risk_tier
        WHEN 'critical' THEN 'Critical'
        WHEN 'high' THEN 'High'
        WHEN 'medium' THEN 'Medium'
        WHEN 'low' THEN 'Low'
        ELSE COALESCE(ml_risk_tier, 'Unknown')
      END
    comment: "ML model predicted risk tier (V5 model) — more granular than computed\
      \ tier, includes medium and high levels"
    display_name: ML Risk Tier
    synonyms:
      - predicted risk
      - model risk tier

  - name: Revenue Tier
    expr: |-
      CASE revenue_tier
        WHEN 'high_value' THEN 'High Value'
        WHEN 'medium_value' THEN 'Medium Value'
        WHEN 'standard' THEN 'Standard'
        ELSE COALESCE(revenue_tier, 'Unknown')
      END
    comment: "Revenue classification of the circuit: High Value (top revenue circuits),\
      \ Medium Value, Standard"
    display_name: Revenue Tier
    synonyms:
      - revenue category
      - circuit value

  - name: Action Priority
    expr: |-
      CASE action_priority
        WHEN 'immediate_action' THEN 'Immediate Action'
        WHEN 'high_priority' THEN 'High Priority'
        WHEN 'monitor' THEN 'Monitor'
        ELSE COALESCE(action_priority, 'Unknown')
      END
    comment: "Recommended action priority for retirement: Immediate Action (critical\
      \ risk + high value), High Priority, Monitor (low risk)"
    display_name: Action Priority
    synonyms:
      - retirement priority
      - action category

  - name: Fiber Ready
    expr: |-
      CASE
        WHEN fiber_ready = true THEN 'Fiber Ready'
        WHEN fiber_ready = false THEN 'Not Fiber Ready'
        ELSE 'Not Assessed'
      END
    comment: Whether the wire center has fiber infrastructure ready — fiber-ready
      circuits can migrate faster with lower capex
    display_name: Fiber Readiness
    synonyms:
      - migration readiness
      - fiber availability

  - name: Technology Domain
    expr: "COALESCE(technology_domain, 'Unknown')"
    comment: "Network technology domain of the circuit (e.g., copper_dsl, copper_pots,\
      \ 5g_nr, gpon)"
    display_name: Technology Domain
    synonyms:
      - technology
      - network type

  - name: Circuit Lifecycle
    expr: |-
      CASE circuit_lifecycle_status
        WHEN 'designed' THEN 'Designed'
        WHEN 'in_test' THEN 'In Test'
        WHEN 'active' THEN 'Active'
        WHEN 'retired' THEN 'Retired'
        ELSE COALESCE(circuit_lifecycle_status, 'Unknown')
      END
    comment: Current lifecycle stage of the circuit — Active circuits generate revenue;
      Retired circuits represent achieved savings
    display_name: Circuit Lifecycle
    synonyms:
      - circuit status
      - lifecycle status

  - name: PUC Filing Required
    expr: |-
      CASE
        WHEN puc_filing_required = true THEN 'PUC Filing Required'
        WHEN puc_filing_required = false THEN 'No PUC Filing'
        ELSE 'Unknown'
      END
    comment: Whether state Public Utility Commission filing is required before retirement
      — affects timeline and cost
    display_name: PUC Filing Required
    synonyms:
      - regulatory filing
      - PUC requirement

measures:
  - name: Total Annual Revenue at Risk
    expr: SUM(estimated_annual_revenue)
    comment: Total annualized revenue from copper circuits at risk of retirement —
      the headline financial exposure metric
    display_name: Annual Revenue at Risk
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - revenue exposure
      - annual revenue
      - revenue at risk

  - name: Total Monthly Revenue at Risk
    expr: SUM(monthly_unit_price)
    comment: Monthly recurring revenue from copper circuits — the run-rate financial
      exposure
    display_name: Monthly Revenue at Risk
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - MRR at risk
      - monthly revenue

  - name: Total Billed Amount
    expr: SUM(total_billed_amount)
    comment: Total billed operating cost for copper circuits — represents cost savings
      potential when circuits are retired
    display_name: Total Billed
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - operating cost
      - billed amount
      - cost base

  - name: Total Circuits
    expr: COUNT(1)
    comment: Total number of copper circuits in the revenue-at-risk analysis
    display_name: Total Circuits
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - circuit count

  - name: Avg Revenue per Circuit
    expr: AVG(estimated_annual_revenue)
    comment: Average annual revenue per copper circuit — used to estimate per-unit
      EBITDA impact of retirement
    display_name: Avg Revenue/Circuit
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - ARPC
      - average circuit revenue

  - name: High Value Circuits
    expr: COUNT(1) FILTER (WHERE revenue_tier = 'high_value')
    comment: Circuits classified as high-value — these require careful migration to
      retain revenue
    display_name: High Value Circuits
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - premium circuits

  - name: High Value Revenue
    expr: SUM(estimated_annual_revenue) FILTER (WHERE revenue_tier = 'high_value')
    comment: Annual revenue from high-value circuits — the most important revenue
      to retain during migration
    display_name: High Value Revenue
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - premium revenue

  - name: Immediate Action Revenue
    expr: SUM(estimated_annual_revenue) FILTER (WHERE action_priority = 'immediate_action')
    comment: Revenue from circuits requiring immediate retirement action — the most
      urgent financial exposure
    display_name: Immediate Action Revenue
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - urgent revenue
      - critical revenue at risk

  - name: Critical Risk Revenue
    expr: SUM(estimated_annual_revenue) FILTER (WHERE computed_risk_tier = 'critical')
    comment: Revenue from critical-risk circuits — highest probability of service
      degradation
    display_name: Critical Risk Revenue
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0

  - name: Avg ML Composite Risk Score
    expr: AVG(ml_composite_risk_score)
    comment: Average ML composite risk score across circuits — higher values indicate
      greater retirement urgency
    display_name: Avg Risk Score
    format:
      type: number
      decimal_places:
        type: max
        places: 3
    synonyms:
      - average risk score
      - mean risk

  - name: Fiber Ready Revenue
    expr: SUM(estimated_annual_revenue) FILTER (WHERE fiber_ready = true)
    comment: Revenue from circuits in fiber-ready wire centers — can be migrated with
      minimal capex
    display_name: Fiber Ready Revenue
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - migration ready revenue

  - name: PUC Filing Revenue
    expr: SUM(estimated_annual_revenue) FILTER (WHERE puc_filing_required = true)
    comment: Revenue from circuits requiring PUC regulatory filing — these have longer
      retirement timelines
    display_name: PUC Filing Revenue
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 0
    synonyms:
      - regulated revenue
$$;
