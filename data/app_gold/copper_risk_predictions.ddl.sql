CREATE TABLE IF NOT EXISTS {fq}.`copper_risk_predictions` (
  `physical_device_id` BIGINT COMMENT 'FK to physical_device. The device being scored.',
  `device_type` STRING COMMENT 'Copper device type: cpe, ont, olt, or patch_panel.',
  `device_status` STRING COMMENT 'Operational status of the device.',
  `risk_tier` STRING COMMENT 'Ground truth risk tier label from copper_risk_target.',
  `predicted_risk_tier` STRING COMMENT 'ML model-predicted risk tier (low/medium/high/critical).',
  `prob_low` DOUBLE COMMENT 'Predicted probability for low risk tier (0.0-1.0).',
  `prob_medium` DOUBLE COMMENT 'Predicted probability for medium risk tier (0.0-1.0).',
  `prob_high` DOUBLE COMMENT 'Predicted probability for high risk tier (0.0-1.0).',
  `prob_critical` DOUBLE COMMENT 'Predicted probability for critical risk tier (0.0-1.0).',
  `max_confidence` DOUBLE COMMENT 'Maximum of prob_low/medium/high/critical. Model confidence in its prediction.',
  `model_version` BIGINT COMMENT 'Model version number that produced this prediction.',
  `model_run_id` STRING COMMENT 'MLflow run ID of the model that produced this prediction. Lineage link.',
  `scored_at` TIMESTAMP COMMENT 'Timestamp when this prediction was generated.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Gold layer: ML model predictions for copper device risk tier classification (2,672 devices). One row per physical_device_id. Source: copper_risk_target scored by V5 GBT model via copper-retirement-risk serving endpoint. Refreshed on model re-scoring.'