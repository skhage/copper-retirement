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

Key columns: physical_device_id, device_type, device_status, alarm_count, critical_alarm_rate, service_affecting_rate, sla_breach_count, recurring_problem_rate, composite_risk_score, risk_tier (target label). Also includes percentile-ranked features: alarm_count_prank, critical_alarm_prank, svc_affecting_prank, sla_breach_prank, test_fail_prank, problem_count_prank, recurring_prob_prank. (20 cols, 2,672 rows)

### `copper_risk_scores` (Managed)

> Champion-vs-challenger model comparison for copper device risk scoring.

Key columns: physical_device_id, device_type, device_status, risk_tier, champion_prediction, champion_confidence, challenger_prediction, challenger_confidence, models_agree. (9 cols, 2,672 rows)

### `gold_device_risk_predictions` (Managed)

> Gold layer risk predictions from the V5 ML model. Per-device risk tier, class probabilities, and SHAP feature importance.

Key columns: physical_device_id, device_type, device_status, risk_tier_actual, risk_tier_predicted, prob_low, prob_medium, prob_high, prob_critical, composite_risk_score, model_version, feature_set, scored_date. (13 cols, 2,672 rows)

### `v5_fairness_report` (Managed)

> V5 model fairness/bias report: per-sub-demographic precision/recall/FPR/AUC with statistical parity checks.

Key columns: dimension, slice_value, n, precision, recall, fpr, f1, auc_roc, accuracy, stat_parity_rate, positive_rate, flag, model_version, mlflow_run_id. (16 cols, 20 rows)

### `feature_device_contract_flag` (Managed)

> ML feature: contract constraint status per copper device. Flags active contracts that may restrict retirement.

Key columns: physical_device_id, device_type, has_active_contract, contract_expiry_days_remaining, most_recent_contract_expiry, has_contract_history, total_contracts, active_contract_count, migration_constraint_status. (14 cols, 2,672 rows)

### `feature_device_firmware_age` (Managed)

> ML feature: firmware vintage and obsolescence risk per copper device.

Key columns: physical_device_id, device_type, firmware_version, software_version, device_age_days, device_age_years, is_past_eol, is_support_expired, newest_last_patch_date, firmware_obsolescence_score, primary_upgrade_status, has_vulnerabilities. (27 cols, 2,672 rows)
