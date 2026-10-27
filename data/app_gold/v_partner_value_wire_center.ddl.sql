CREATE OR REPLACE VIEW {fq}.`v_partner_value_wire_center` (
  wire_center_id COMMENT 'Unique wire center identifier. FK to gold_wire_center_scorecard.',
  wire_center_name COMMENT 'Human-readable wire center name for display and reporting.',
  state_code COMMENT 'US state abbreviation. Legacy copper states: CO, MN, WA, OR, ID, AZ.',
  assigned_wave COMMENT 'Optimized retirement wave assignment (YYYY-QN format). Output of LP/MIP solver.',
  wave_year COMMENT 'Year component of assigned_wave (e.g. 2026). For time-series aggregation.',
  wave_quarter COMMENT 'Quarter component of assigned_wave (1-4). For time-series aggregation.',
  fiber_ready COMMENT 'TRUE if fiber overbuild is complete at this wire center. Required before copper retirement.',
  copper_device_count COMMENT 'Count of copper devices (CPE, ONT, OLT, patch_panel) at this wire center.',
  copper_lbs_estimated COMMENT 'Copper lbs in place: pair segment_length_ft x 2 conductors x NIST Handbook 100 lb/kft by AWG (https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf). SYNTHETIC plant',
  copper_lbs_recoverable COMMENT 'copper_lbs_estimated x base salvage_recovery_rate (partner input)',
  copper_price_usd_lb COMMENT 'Derived: copper_price_usd_ton / 2204.62262 (USD per pound). Not a COMEX quote',
  copper_price_month COMMENT 'First day of the observation month (IMF monthly average)',
  copper_price_source_url COMMENT 'Official human-readable citation URL for the series',
  copper_price_is_synthetic COMMENT 'FALSE = real public data. Always false in this table',
  gross_salvage_value_usd COMMENT 'copper_lbs_recoverable x latest REAL IMF copper price USD/lb (https://fred.stlouisfed.org/series/PCOPPUSDM)',
  decommission_cost_usd COMMENT 'Estimated decommission labor + material cost, adjusted for wave-period cost indices.',
  net_salvage_value_usd COMMENT 'gross_salvage_value_usd - SYNTHETIC estimated decommission cost (USD)',
  total_program_cost_usd COMMENT 'SYNTHETIC total retirement cost (fiber build + removal + migration) from retirement_cost_per_wire_center; excludes regulatory filing (NULL PARTNER_DISCOVERY_INPUT, DEC-ROI-FILING-COST)',
  fiber_build_cost_usd COMMENT 'SYNTHETIC fiber overbuild capex (USD) from retirement_cost_per_wire_center',
  customer_migration_cost_usd COMMENT 'SYNTHETIC customer migration cost from retirement_cost_per_wire_center.',
  regulatory_filing_cost_usd COMMENT 'NULL = PARTNER_DISCOVERY_INPUT (DEC-ROI-FILING-COST 2026-10-25). Unsourced flat USD 55K/WC withdrawn; partner supplies regulatory compliance cost in discovery.',
  one_time_cost_ex_fiber_usd COMMENT 'SYNTHETIC decommission + customer migration cost (USD). Regulatory filing is coalesced to 0 and EXCLUDED (NULL PARTNER_DISCOVERY_INPUT, DEC-ROI-FILING-COST 2026-10-25).',
  working_copper_lines COMMENT 'Count of pairs with pair_status=working in copper_plant_wire_center_jurisdiction (SYNTHETIC demo plant). Line basis for opex savings.',
  copper_om_cost_per_line_year_usd COMMENT 'SYNTHETIC illustrative copper O&M cost per working line per year (roi_calculator_assumptions.opex_saved_per_line_year base). Partner input.',
  opex_reduction_pct COMMENT 'Cited fraction of per-line O&M avoided on fiber (base 0.50; low 0.35 AT&T 2024, high 0.63 Analysys Mason 2022).',
  annual_opex_savings_usd COMMENT 'working_copper_lines x SYNTHETIC O&M per line x CITED opex_reduction_pct (USD/yr)',
  customers_impacted COMMENT 'Distinct customers mapped to this wire center in silver_device_service_impact (6 legacy footprint states, DEC-DSI-FOOTPRINT)',
  customers_migrated COMMENT 'customers_impacted if both residential and business migration milestones are completed, else 0 (SYNTHETIC milestones)',
  is_retired COMMENT '1 if the decommission milestone is completed (SYNTHETIC milestones), else 0',
  decommission_date COMMENT 'Decommission milestone date: actual, else forecast, else planned (SYNTHETIC)',
  operational_inputs_synthetic COMMENT 'TRUE: plant, costs, customers and milestones are SYNTHETIC demo inputs; only copper price and cited ratios are real')
COMMENT 'DERIVED FROM SYNTHETIC DATA — Partner value per wire center for the ROI calculator (PARTNER-PLAYBOOK.md section 3). Copper lbs = pair segment_length_ft x 2 conductors x NIST Handbook 100 lb/kft by AWG (https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf) x base salvage_recovery_rate. Dollars = latest REAL IMF copper price (https://fred.stlouisfed.org/series/PCOPPUSDM). Opex (2026-10-25 rev, ACC-DA-OPEX-RESCALE) = working copper lines x SYNTHETIC copper O&M per line (roi_calculator_assumptions.opex_saved_per_line_year, base USD 200/yr) x CITED opex_reduction_pct_fiber_vs_copper (base 0.50; AT&T 0.35 / Analysys Mason 0.63). It replaces the gold_ebitda_forecast allocation (USD 2.63M/yr, implausible). one_time_cost_ex_fiber_usd = decommission + migration (regulatory filing is a NULL PARTNER_DISCOVERY_INPUT, excluded per DEC-ROI-FILING-COST 2026-10-25) (equipment_removal_cost is excluded to avoid double counting removal). Plant, costs, customers and milestones are SYNTHETIC. Sensitivity: v_roi_sensitivity. Owner @data-analyst.'
AS WITH roi AS (SELECT * FROM {fq}.roi_calculator_assumptions),
a AS (SELECT max(CASE WHEN param_code='salvage_recovery_rate' THEN base_value END) recovery,
             max(CASE WHEN param_code='opex_saved_per_line_year' THEN base_value END) om_per_line,
             max(CASE WHEN param_code='opex_reduction_pct_fiber_vs_copper' THEN base_value END) opex_pct FROM roi),
awg AS (SELECT cable_gauge_awg g, base_value lb_kft FROM roi WHERE param_code='cu_lb_per_kft_conductor'),
cu AS (SELECT c.wire_center_id, sum(c.segment_length_ft*2*awg.lb_kft/1000) cu_lbs
       FROM {fq}.copper_plant_wire_center_jurisdiction c JOIN awg ON awg.g=c.cable_gauge_awg GROUP BY c.wire_center_id),
ln AS (SELECT wire_center_id, count_if(pair_status='working') working_lines FROM {fq}.copper_plant_wire_center_jurisdiction GROUP BY wire_center_id),
px AS (
  SELECT price_month, copper_price_usd_lb, source_url, is_synthetic
  FROM {fq}.copper_commodity_price_official
  WHERE price_month = (SELECT max(price_month) FROM {fq}.copper_commodity_price_official)),
cust AS (
  SELECT wire_center_id, count(DISTINCT customer_id) AS customers_impacted
  FROM {fq}.silver_device_service_impact GROUP BY wire_center_id),
ms AS (
  SELECT wire_center_id,
    max(CASE WHEN type='decommission' AND status='completed' THEN 1 ELSE 0 END) AS is_retired,
    CASE WHEN sum(CASE WHEN type IN ('migration_residential','migration_business') AND status='completed' THEN 1 ELSE 0 END)=2 THEN 1 ELSE 0 END AS is_migrated,
    max(CASE WHEN type='decommission' THEN coalesce(actual_date, forecast_date, planned_date) END) AS decommission_date
  FROM {fq}.retirement_milestones GROUP BY wire_center_id)
SELECT g.wire_center_id, g.wire_center_name, g.state_code, g.assigned_wave, g.wave_year, g.wave_quarter, g.fiber_ready,
  g.copper_device_count,
  coalesce(cu.cu_lbs,0)                                       AS copper_lbs_estimated,
  coalesce(cu.cu_lbs,0) * a.recovery                          AS copper_lbs_recoverable,
  px.copper_price_usd_lb, px.price_month AS copper_price_month, px.source_url AS copper_price_source_url, px.is_synthetic AS copper_price_is_synthetic,
  coalesce(cu.cu_lbs,0) * a.recovery * px.copper_price_usd_lb AS gross_salvage_value_usd,
  g.estimated_decommission_cost_usd                           AS decommission_cost_usd,
  coalesce(cu.cu_lbs,0) * a.recovery * px.copper_price_usd_lb - g.estimated_decommission_cost_usd AS net_salvage_value_usd,
  CAST(r.total_retirement_cost AS DOUBLE)                     AS total_program_cost_usd,
  CAST(r.fiber_build_cost AS DOUBLE)                          AS fiber_build_cost_usd,
  CAST(r.customer_migration_cost AS DOUBLE)                   AS customer_migration_cost_usd,
  CAST(r.regulatory_filing_cost AS DOUBLE)                    AS regulatory_filing_cost_usd,
  g.estimated_decommission_cost_usd + coalesce(CAST(r.customer_migration_cost AS DOUBLE),0) + coalesce(CAST(r.regulatory_filing_cost AS DOUBLE),0) AS one_time_cost_ex_fiber_usd,
  coalesce(ln.working_lines,0)                                AS working_copper_lines,
  a.om_per_line                                               AS copper_om_cost_per_line_year_usd,
  a.opex_pct                                                  AS opex_reduction_pct,
  coalesce(ln.working_lines,0) * a.om_per_line * a.opex_pct   AS annual_opex_savings_usd,
  coalesce(c.customers_impacted,0)                            AS customers_impacted,
  coalesce(c.customers_impacted,0) * coalesce(ms.is_migrated,0) AS customers_migrated,
  coalesce(ms.is_retired,0)                                   AS is_retired,
  ms.decommission_date,
  TRUE                                                        AS operational_inputs_synthetic
FROM {fq}.gold_copper_recovery_schedule g
CROSS JOIN a CROSS JOIN px
LEFT JOIN cu ON cu.wire_center_id=g.wire_center_id
LEFT JOIN ln ON ln.wire_center_id=g.wire_center_id
LEFT JOIN {fq}.retirement_cost_per_wire_center r ON r.wire_center_id=g.wire_center_id
LEFT JOIN cust c ON c.wire_center_id=g.wire_center_id
LEFT JOIN ms ON ms.wire_center_id=g.wire_center_id
