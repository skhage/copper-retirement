CREATE TABLE IF NOT EXISTS {fq}.`retirement_cost_per_wire_center` (
  `wire_center_id` STRING COMMENT 'Unique wire center identifier. FK to gold_wire_center_scorecard.wire_center_id.',
  `wire_center_name` STRING COMMENT 'Human-readable wire center facility name.',
  `clli_code` STRING COMMENT 'CLLI code (Common Language Location Identifier) for inter-carrier coordination.',
  `state_code` STRING COMMENT 'US state abbreviation (legacy states: CO, MN, WA, OR, ID, AZ).',
  `fiber_ready` BOOLEAN COMMENT 'TRUE if fiber infrastructure is already deployed. Reduces fiber_build_cost by 80%.',
  `copper_device_count` BIGINT COMMENT 'Count of copper devices (CPE, ONT, OLT, patch_panel) at this wire center.',
  `affected_customer_count` BIGINT COMMENT 'Count of customers impacted by copper retirement at this wire center.',
  `affected_service_count` BIGINT COMMENT 'Count of customer-facing services impacted by retirement.',
  `fiber_build_cost` DOUBLE COMMENT 'Estimated fiber overbuild cost (USD). Based on:  base + /km avg loop + /device, adjusted by state labor and terrain multipliers. 80% discount if fiber_ready.',
  `equipment_removal_cost` DECIMAL(25,2) COMMENT 'Estimated copper equipment decommission cost (USD). Based on:  mobilization + ,500/device, adjusted by state labor multiplier.',
  `customer_migration_cost` BIGINT COMMENT 'Estimated customer migration cost (USD). Based on:  project mgmt + /customer (CPE swap + truck roll) + /service (reconfiguration).',
  `regulatory_filing_cost` BIGINT COMMENT 'PARTNER_DISCOVERY_INPUT — intentionally NULL for all wire centers (DEC-ROI-FILING-COST, 2026-10-25). The former flat synthetic USD 55K/WC value had no source and was withdrawn. The partner supplies per-state regulatory compliance cost during SOW discovery. FCC fee-schedule bounds may be shown only as a labeled reference (roi_calculator_assumptions.regulatory_filing_cost_per_wc); they are not the compliance cost.',
  `total_retirement_cost` DOUBLE COMMENT 'Sum of fiber_build + equipment_removal + customer_migration costs (USD, synthetic). EXCLUDES regulatory filing cost, which is a NULL PARTNER_DISCOVERY_INPUT (DEC-ROI-FILING-COST, rev 2026-10-25).',
  `cost_per_device` DOUBLE COMMENT 'total_retirement_cost (ex regulatory filing) divided by copper device count (USD). Unit economics metric for sequencing optimization. Rev 2026-10-25.',
  `retirement_readiness_score` DECIMAL(27,1) COMMENT 'Composite 0-100 readiness score from gold_wire_center_scorecard. Higher = more ready to retire.',
  `retirement_priority_rank` INT COMMENT 'Dense rank from wire center scorecard. Rank 1 = retire first.',
  `_created_at` TIMESTAMP COMMENT 'UTC timestamp when this row was generated.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Per-wire-center retirement cost estimates for the copper retirement sequencing optimizer (P4-SEQ): fiber build, equipment removal and customer migration cost components, modeled from wire center attributes, device counts and customer impact. regulatory_filing_cost is NULL = PARTNER_DISCOVERY_INPUT (DEC-ROI-FILING-COST 2026-10-25; the unsourced flat USD 55K/WC was withdrawn) and total_retirement_cost excludes it. One row per wire center.'