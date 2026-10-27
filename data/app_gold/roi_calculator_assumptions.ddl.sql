CREATE TABLE IF NOT EXISTS {fq}.`roi_calculator_assumptions` (
  `param_code` STRING COMMENT 'Unique ROI input key',
  `param_group` STRING COMMENT 'copper_mass | recovery | price | cost | benefit',
  `cable_gauge_awg` INT COMMENT 'AWG gauge when the input is gauge-specific, else NULL',
  `low_value` DOUBLE COMMENT 'Low (conservative) scenario value; NULL = not available',
  `base_value` DOUBLE COMMENT 'Base scenario value; NULL = partner discovery input required',
  `high_value` DOUBLE COMMENT 'High scenario value; NULL = not available',
  `unit` STRING COMMENT 'Unit of low/base/high',
  `source_url` STRING COMMENT 'Official/public source URL, or PARTNER_DISCOVERY_INPUT / DEFINITIONAL_CONSTANT. Never invented',
  `is_synthetic` BOOLEAN COMMENT 'TRUE when any of low/base/high is an illustrative or unsourced placeholder',
  `comment` STRING COMMENT 'How the input is used and what a partner must validate',
  `updated_at` TIMESTAMP COMMENT 'Last update time'
) USING DELTA
COMMENT 'ROI calculator inputs (low/base/high) for PARTNER-PLAYBOOK.md section 3 and the unified app Commodity tab. Copper mass from NIST Handbook 100 wire tables; price = latest IMF PCOPPUSDM month (copper_commodity_price_official); recovery and cost bounds are PARTNER DISCOVERY INPUTS (illustrative, is_synthetic=TRUE). Owner @data-analyst (ACC-DA-ROI-CALC).'