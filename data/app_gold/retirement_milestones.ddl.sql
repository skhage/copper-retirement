CREATE TABLE IF NOT EXISTS {fq}.`retirement_milestones` (
  `milestone_id` BIGINT COMMENT 'PK. Unique identifier for this milestone.',
  `wire_center_id` STRING COMMENT 'FK to wire_center_boundary. The wire center this milestone applies to.',
  `name` STRING COMMENT 'Descriptive name of the milestone (e.g. PUC Filing Submitted, Fiber Install Complete).',
  `type` STRING COMMENT 'Milestone type classification (regulatory, construction, notification, migration, decommission).',
  `status` STRING COMMENT 'Current status (not_started, in_progress, completed, delayed, blocked).',
  `priority` STRING COMMENT 'Priority level (critical, high, medium, low).',
  `planned_date` DATE COMMENT 'Original planned completion date.',
  `actual_date` DATE COMMENT 'Actual completion date. NULL if not yet completed.',
  `forecast_date` DATE COMMENT 'Current forecasted completion date. May differ from planned_date due to delays.',
  `completion_percentage` DOUBLE COMMENT 'Progress percentage (0-100). 100 = fully complete.',
  `critical_path_flag` BOOLEAN COMMENT 'TRUE if this milestone is on the critical path for wire center retirement.',
  `regulatory_requirement_flag` BOOLEAN COMMENT 'TRUE if this is a regulatory gating milestone that cannot be skipped.',
  `risk_level` STRING COMMENT 'Risk level for this milestone (high, medium, low).',
  `risk_description` STRING COMMENT 'Description of risks that may delay or block this milestone.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Reference table: copper retirement project milestones per wire center — planned vs actual dates, completion status, and regulatory deadlines. One row per milestone_id per wire_center_id. Source: synthesized from tmf_enterprise.milestone and wire_center_boundary by @data-engineer.'