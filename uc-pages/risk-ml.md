# Risk & ML

## Overview

The Risk & ML domain powers Lakelink Fiber's data-driven copper retirement prioritization. It encompasses the full ML lifecycle: feature engineering from network alarms, customer complaints, firmware age, and contract constraints; a V5 gradient-boosted tree model that classifies each of 2,672 copper devices into risk tiers (low/medium/high/critical); fairness testing across device type, geography, and service type demographics; and a real-time serving endpoint for on-demand risk scoring.

## Key Tables

### Prediction & Scoring Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.copper_risk_target` | Feature | One row per copper device | 2,672 | ML training/scoring target table — risk feature engineering per physical copper device with percentile-ranked alarm rates, SLA breaches, and problem counts. |
| `copper_retirement.gold_device_risk_predictions` | Gold | One row per copper device | 2,672 | Executive-ready risk predictions from the V5 GBT model with per-class probabilities and composite risk score. |
| `copper_retirement.copper_risk_predictions` | Gold | One row per copper device | 2,672 | Per-device predicted risk tier classification with model probabilities and feature set identifier. |
| `copper_retirement.copper_risk_scores` | Gold | One row per copper device | 2,672 | Champion-vs-challenger model comparison — side-by-side V5 and baseline risk scores for model governance. |

### Fairness & Governance Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.v5_fairness_report` | Gold | One row per sub-demographic | 20 | V5 model fairness/bias report: per-sub-demographic precision, recall, FPR, AUC with statistical parity and equalized odds testing. |
| `copper_retirement.v5_fairness_dimension_summary` | Gold | One row per slicing dimension | 4 | Dimension-level fairness summary: statistical parity and equalized odds pass/fail per slicing dimension (device_type, geography, service_type, customer_segment). |
| `copper_retirement.risk_model_inference_payload` | Gold | One row per inference request | 3 | Inference request/response logging for the copper-retirement-risk V5 serving endpoint. Grows with each API call. |

### ML Feature Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.feature_device_billing_dispute` | Feature | One row per physical device | 10,000 | Billing dispute rate per device. Join path: billing_dispute → CFS (customer_id) → physical_device via geographic_address. |
| `copper_retirement.feature_device_complaint_rate` | Feature | One row per physical device | 9,994 | Customer complaint rate per device. Join path: customer_problem → CFS → physical_device via geographic_address. |
| `copper_retirement.feature_device_contract_flag` | Feature | One row per copper device | 2,672 | Contract constraint status per device — flags active contracts that block device retirement during contract term. |
| `copper_retirement.feature_device_firmware_age` | Feature | One row per copper device | 2,672 | Firmware vintage and obsolescence risk per device — 27 columns covering EOL dates, patch freshness, software component counts, and vulnerability indicators. |

## Model Serving

| Component | Details |
|---|---|
| **Endpoint** | `copper-retirement-risk` (V5 GBT, status: READY) |
| **Model** | V5 Gradient Boosted Tree — risk tier classification (4-class: low/medium/high/critical) |
| **Features** | Alarm rate, SLA breach rate, firmware age, complaint rate, contract flags, service usage |
| **Inference Table** | Logging active — payloads stored in `risk_model_inference_payload` |
| **Fairness** | Tested across device_type, geography, service_type, customer_segment — all dimensions pass statistical parity |

## Entity Relationships

```
copper_risk_target (feature engineering hub)
  └── physical_device_id (PK) → tmf_enterprise.physical_device.physical_device_id
  └── Sources: tmf_resource.alarm, tmf_service.service_problem, tmf_resource.resource_test

gold_device_risk_predictions
  └── physical_device_id (PK) → copper_risk_target.physical_device_id
  └── Inputs: copper_risk_target + feature_device_* tables → V5 GBT model → predictions

copper_risk_predictions
  └── physical_device_id (PK) → copper_risk_target.physical_device_id
  └── Same model output as gold_device_risk_predictions (alternate format)

copper_risk_scores
  └── physical_device_id (PK) → copper_risk_target.physical_device_id
  └── champion_score (V5) vs challenger_score (baseline) per device

v5_fairness_report
  └── Sliced from gold_device_risk_predictions by device_type, geography, service_type, customer_segment

feature_device_billing_dispute
  └── physical_device_id → tmf_enterprise.physical_device.physical_device_id
  └── Sources: tmf_customer.billing_dispute → tmf_service.customer_facing_service → geographic_address (H3 spatial join)

feature_device_complaint_rate
  └── physical_device_id → tmf_enterprise.physical_device.physical_device_id
  └── Sources: tmf_customer.customer_problem → tmf_service.customer_facing_service → geographic_address (H3 spatial join)

feature_device_contract_flag
  └── physical_device_id → tmf_enterprise.physical_device.physical_device_id
  └── Sources: tmf_customer.commitment, salesforce_source.contract

feature_device_firmware_age
  └── physical_device_id → tmf_enterprise.physical_device.physical_device_id
  └── Sources: tmf_resource.installed_software, tmf_resource.resource_configuration
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Composite Risk Score | Weighted risk score (0.0–1.0); higher = more urgent retirement | `gold_device_risk_predictions.composite_risk_score` |
| Risk Tier Distribution | Count of devices per risk tier (low/medium/high/critical) | `gold_device_risk_predictions.risk_tier_predicted` |
| Model Accuracy | V5 model prediction accuracy vs ground-truth risk tier | `gold_device_risk_predictions.risk_tier_actual` vs `risk_tier_predicted` |
| Statistical Parity | Fairness metric — prediction rate equality across demographics | `v5_fairness_report.statistical_parity_ratio` |
| Equalized Odds | Fairness metric — TPR/FPR equality across demographics | `v5_fairness_report.equalized_odds_diff` |
| Billing Dispute Rate | Count and rate of billing disputes attributed to a device | `feature_device_billing_dispute.dispute_count`, `dispute_rate` |
| Complaint Rate | Customer complaint frequency per device | `feature_device_complaint_rate.complaint_rate` |
| Firmware Age (days) | Days since last firmware patch — proxy for maintenance neglect | `feature_device_firmware_age.days_since_last_patch` |
| Contract Block Flag | Whether an active contract prevents device retirement | `feature_device_contract_flag.has_active_contract` |

## Data Quality Notes

- **Entity key consistency:** All 11 tables use `physical_device_id` as entity key. Risk/prediction tables have exactly 2,672 rows (one per copper device). Feature tables have broader coverage (up to 10K) for ML completeness.
- **Feature tables are wider than expected:** `feature_device_firmware_age` has 27 columns — richest feature table with EOL dates, patch history, vulnerability scores, and software component counts.
- **Model governance:** `copper_risk_scores` provides champion (V5) vs challenger (baseline) comparison for model promotion decisions. `risk_model_inference_payload` currently has 3 rows — grows with serving endpoint usage.
- **Fairness testing:** V5 passes statistical parity and equalized odds across all 4 slicing dimensions. 20 sub-demographic combinations tested.
- **Synthetic data:** All feature tables are built from synthetic TMF SID data. Feature distributions are realistic but not sourced from production telco systems.

## Related Domains

- **Physical Plant** — `physical_device_id` is sourced from `bronze_copper_devices` / `tmf_enterprise.physical_device`; wire center context from `gold_wire_center_scorecard`
- **Circuits & Services** — `feature_device_service_usage` (in Circuits domain) feeds the risk model as a service-usage feature
- **Customers** — Complaint and billing dispute features are derived from customer tables (`tmf_customer.customer_problem`, `tmf_customer.billing_dispute`)
- **Financial** — Risk tier predictions drive retirement sequencing in `gold_ebitda_forecast` and `gold_circuit_revenue_at_risk`
