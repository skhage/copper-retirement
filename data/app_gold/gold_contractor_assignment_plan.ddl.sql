CREATE TABLE IF NOT EXISTS {fq}.`gold_contractor_assignment_plan` (
  `wave` STRING COMMENT 'Retirement wave (YYYY-QN). FK to gold_wave_schedule.assigned_wave.',
  `state_code` STRING COMMENT 'US state abbreviation where the contractor is assigned to work. Legacy states: CO, MN, WA, OR, ID, AZ.',
  `contractor_id` BIGINT COMMENT 'FK to gold_contractor_scorecard.contractor_performance_id.',
  `contractor_name` STRING COMMENT 'Legal name of the contractor firm.',
  `contractor_type` STRING COMMENT 'Contractor classification: telco_specialist, general_contractor, or fiber_installer.',
  `primary_state` STRING COMMENT 'Contractors home state. Preference given to local contractors to minimize mobilization cost.',
  `dispatch_status` STRING COMMENT 'Current dispatch readiness: available, on_assignment, or standby.',
  `crew_size` BIGINT COMMENT 'Number of crew members this contractor can deploy per assignment.',
  `safety_score` DOUBLE COMMENT 'Contractor safety performance score (0-1). Weighted 40pct in composite. From partner SLA data.',
  `overall_rating` DOUBLE COMMENT 'Contractor overall performance rating (0-1). Weighted 30pct in composite. From project completions.',
  `sla_compliance_pct` DOUBLE COMMENT 'Percentage of SLA targets met by this contractor (0-1). Weighted 30pct in composite.',
  `composite_score` DOUBLE COMMENT 'Contractor quality score: safety(40%) + rating(30%) + SLA(30%). Range 0-1.',
  `allocated_crew_days` BIGINT COMMENT 'Crew-days allocated to this contractor for this wave×state.',
  `estimated_cost_usd` DOUBLE COMMENT 'Estimated cost = allocated_crew_days × avg_daily_rate for the state.',
  `wire_centers_in_wave` BIGINT COMMENT 'Number of wire centers in this wave×state that the contractor is assigned to cover.',
  `devices_in_wave` BIGINT COMMENT 'Total copper devices in the assigned wave×state scope.',
  `optimizer_version` STRING COMMENT 'Version of the assignment optimizer that produced this plan.',
  `assignment_date` STRING COMMENT 'Date this contractor was assigned to the wave. Set by the optimizer run.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Gold-layer contractor assignment plan for copper retirement waves. Each row = one contractor assigned to a specific wave×state combination. Allocates crew-days and costs based on contractor composite scores (safety, rating, SLA compliance). Produced by the assignment optimizer to pair qualified contractors with retirement work.'