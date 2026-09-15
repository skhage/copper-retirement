# Risk & ML Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

ML model training targets, predictions, champion/challenger scoring, fairness reports, and feature engineering inputs.

## Tables (9)

| Table | Type | Description |
|-------|------|-------------|
| `copper_risk_target` | MANAGED | ML training/scoring target table -- risk feature engineering per physical device |
| `copper_risk_scores` | MANAGED | Champion-vs-challenger model comparison for copper device risk scoring |
| `copper_risk_predictions` | MANAGED | ML model predictions for copper device risk tier classification |
| `gold_device_risk_predictions` | MANAGED | Gold layer risk predictions from the V5 ML model |
| `feature_device_contract_flag` | MANAGED | ML feature: contract constraint status per copper device |
| `feature_device_firmware_age` | MANAGED | ML feature: firmware vintage and obsolescence risk per copper device |
| `v5_fairness_report` | MANAGED | V5 model fairness/bias report: per-sub-demographic precision/recall/FPR/AUC |
| `v5_fairness_dimension_summary` | MANAGED | V5 fairness dimension-level summary: statistical parity and equalized odds |
| `risk_model_inference_payload` | MANAGED | Inference payload logging from the copper-retirement-risk serving endpoint |

## Key Relationships

* physical_device_id is the primary key linking all risk/ML tables
* copper_risk_scores contains champion + challenger model outputs
* gold_device_risk_predictions is the V5 production model output

## ML Pipeline

1. **Feature Engineering**: copper_risk_target aggregates device features from multiple sources
2. **Training**: Models trained via MLflow experiments in copper-retirement/experiments/
3. **Scoring**: copper_risk_scores shows champion vs challenger comparison
4. **Production**: gold_device_risk_predictions contains V5 model output served via `copper-retirement-risk` endpoint
5. **Fairness**: v5_fairness_report and v5_fairness_dimension_summary track model bias metrics

## Table Details

### `copper_risk_target` (Managed)

> ML training/scoring target table -- risk feature engineering per physical device.

Key columns: physical_device_id, device_type, device_age_years, alarm_count_90d, mean_time_between_failures, outage_count_12m, complaint_rate, revenue_at_risk, risk_tier (target label)

### `copper_risk_scores` (Managed)

> Champion-vs-challenger model comparison for copper device risk scoring.

Key columns: physical_device_id, champion_risk_tier, champion_probability, challenger_risk_tier, challenger_probability, model_version, scored_at

### `gold_device_risk_predictions` (Managed)

> Gold layer risk predictions from the V5 ML model. Per-device risk tier, class probabilities, and SHAP feature importance.

Key columns: physical_device_id, risk_tier, risk_probability, shap_top_features, model_version, prediction_timestamp, state_code

### `v5_fairness_report` (Managed)

> V5 model fairness/bias report: per-sub-demographic precision/recall/FPR/AUC with statistical parity checks.

Key columns: dimension, sub_group, sample_count, precision, recall, fpr, auc, statistical_parity_ratio, equalized_odds_ratio

### `feature_device_contract_flag` (Managed)

> ML feature: contract constraint status per copper device. Flags active contracts that may restrict retirement.

Key columns: physical_device_id, has_active_contract, contract_end_date, months_to_expiry, penalty_amount

### `feature_device_firmware_age` (Managed)

> ML feature: firmware vintage and obsolescence risk per copper device.

Key columns: physical_device_id, firmware_version, firmware_age_days, is_end_of_life, last_update_date
