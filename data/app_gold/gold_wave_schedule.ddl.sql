CREATE TABLE IF NOT EXISTS {fq}.`gold_wave_schedule` (
  `wire_center_id` STRING COMMENT 'Unique wire center identifier. FK to gold_wire_center_scorecard.',
  `wire_center_name` STRING COMMENT 'Human-readable wire center name for display (e.g. Denver-Central, Minneapolis-West).',
  `state_code` STRING COMMENT 'US state abbreviation. Legacy copper states: CO, MN, WA, OR, ID, AZ.',
  `assigned_wave` STRING COMMENT 'Optimized retirement wave assignment (YYYY-QN format). Output of LP/MIP solver.',
  `wave_year` BIGINT COMMENT 'Year component of assigned_wave (e.g. 2026). Extracted for time-series analysis.',
  `wave_quarter` BIGINT COMMENT 'Quarter component of assigned_wave (1-4). Extracted for time-series analysis.',
  `wave_start_date` STRING COMMENT 'Calendar start date of the assigned wave (first day of the quarter).',
  `fiber_ready` BOOLEAN COMMENT 'TRUE if fiber overbuild is complete and lit at this wire center. Prerequisite for copper retirement.',
  `puc_filing_required` BOOLEAN COMMENT 'TRUE if the state PUC requires a formal filing before copper retirement can proceed. Adds lead time.',
  `copper_device_count` BIGINT COMMENT 'Count of copper network devices (CPE, ONT, OLT, patch_panel) at this wire center.',
  `critical_risk_devices` BIGINT COMMENT 'Count of devices scoring critical risk in the V5 risk model. Drives retirement urgency.',
  `high_risk_devices` BIGINT COMMENT 'Count of devices scoring high risk in the V5 risk model.',
  `retirement_readiness_score` DOUBLE COMMENT 'Composite 0-100 score reflecting fiber readiness, regulatory clearance, and risk profile. Higher = more ready.',
  `retirement_priority_rank` BIGINT COMMENT 'Priority rank across all wire centers (1 = retire first). Based on readiness score and risk urgency.',
  `risk_urgency_weight` DOUBLE COMMENT 'Risk-weighted urgency score driving wave priority. Higher = more urgent to retire.',
  `estimated_crew_days` BIGINT COMMENT 'Estimated crew-days needed to decommission this wire center (5 days/device).',
  `earliest_eligible_wave` STRING COMMENT 'Earliest wave eligible after regulatory notice periods and fiber readiness.',
  `affected_customer_count` BIGINT COMMENT 'Count of distinct customers served by copper at this wire center. Drives migration planning.',
  `annual_revenue_at_risk` DOUBLE COMMENT 'Annual recurring revenue (USD) from copper-dependent services at this wire center.',
  `optimizer_version` STRING COMMENT 'Version of the LP/MIP optimizer that produced this schedule.',
  `solved_date` STRING COMMENT 'Date the optimizer last solved/updated this wire centers wave assignment.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Gold-layer optimized copper retirement wave schedule. Each row = one wire center with its assigned retirement wave (quarter), priority ranking, and resource estimates. Produced by LP/MIP solver using fiber readiness, regulatory constraints, risk scores, and crew capacity. Drives the master retirement timeline for Lakelink Fiber copper plant decommissioning.'