CREATE TABLE IF NOT EXISTS {fq}.`gold_device_risk_predictions` (
  `physical_device_id` BIGINT COMMENT 'FK to physical_device. The device being scored. PK.',
  `device_type` STRING COMMENT 'Copper device type.',
  `device_status` STRING COMMENT 'Device operational status.',
  `risk_tier_actual` STRING COMMENT 'Ground truth risk tier from copper_risk_target.',
  `risk_tier_predicted` STRING COMMENT 'V5 ML model-predicted risk tier (low/medium/high/critical). Used in gold_retirement_executive_summary.',
  `prob_low` DOUBLE COMMENT 'Predicted probability for low risk tier.',
  `prob_medium` DOUBLE COMMENT 'Predicted probability for medium risk tier.',
  `prob_high` DOUBLE COMMENT 'Predicted probability for high risk tier.',
  `prob_critical` DOUBLE COMMENT 'Predicted probability for critical risk tier.',
  `composite_risk_score` DOUBLE COMMENT 'Weighted composite risk score (0.0-1.0). Higher = higher risk.',
  `model_version` STRING COMMENT 'V5 model version identifier.',
  `feature_set` STRING COMMENT 'Feature set identifier used for this prediction.',
  `scored_date` STRING COMMENT 'Date the prediction was scored.'
) USING DELTA
COMMENT 'SYNTHETIC DATA — Gold layer: V5 ML model risk predictions for 2,672 copper devices with per-device risk tier, class probabilities, and composite risk score. One row per physical_device_id. Sources: copper_risk_target features scored by copper-retirement-risk serving endpoint. Refreshed on model re-scoring.'
