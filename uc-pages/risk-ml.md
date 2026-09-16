# Risk & ML

## Overview

The Risk & ML domain powers Lakelink Fiber's data-driven copper retirement prioritization — answering "which devices are most likely to fail, which wire centers should retire first, and is the model fair across device types and geographies." A V5 gradient-boosted risk model scores every copper device, with features drawn from alarms, performance metrics, firmware age, complaints, and service usage. Fairness testing ensures equitable treatment across sub-demographics.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.silver_copper_plant_enriched` | Silver (MV) | One row per copper device | 2,672 | Copper devices enriched with alarm rates, critical alarm rate, SLA breach rate, performance metrics, and risk features. DLP materialized view. |
| `copper_retirement.copper_risk_target` | Reference | One row per copper device | 2,672 | Binary risk labels (target variable) for model training — derived from alarm and performance thresholds. |
| `copper_retirement.copper_risk_scores` | Reference | One row per copper device | 2,672 | Pre-computed risk scores used for model validation and feature engineering baseline. |
| `copper_retirement.copper_risk_predictions` | Gold | One row per copper device | 2,672 | V5 model predictions — risk_score, risk_tier (critical/high/medium/low), confidence interval. |
| `copper_retirement.gold_device_risk_predictions` | Gold | One row per copper device | 2,672 | Final risk predictions with wire center context, device metadata, and retirement recommendation. |
| `copper_retirement.gold_wire_center_scorecard` | Gold (MV) | One row per wire_center_id | 103 | Aggregated wire center scorecard — composite 0–100 retirement readiness score from risk, alarm, fiber, and priority signals. |
| `copper_retirement.risk_model_inference_payload` | Monitoring | One row per inference batch | 6 | Model serving inference payloads for monitoring and drift detection. |
| `copper_retirement.v5_fairness_report` | Monitoring | One row per fairness test | 20 | V5 model fairness test results across device_type, geography, service_type, and customer segment. |
| `copper_retirement.v5_fairness_dimension_summary` | Monitoring | One row per fairness dimension | 4 | Summary fairness metrics per demographic dimension — pass/fail status. |

### Feature Tables

| Table | Rows | Description |
|---|---|---|
| `copper_retirement.feature_device_billing_dispute` | 10,000 | Billing dispute count and rate per device — quality degradation signal. |
| `copper_retirement.feature_device_complaint_rate` | 9,994 | Customer complaint rate per device — customer experience signal. |
| `copper_retirement.feature_device_contract_flag` | 2,672 | Contract constraint flag per copper device — migration eligibility indicator. |
| `copper_retirement.feature_device_firmware_age` | 2,672 | Firmware age in days per device — obsolescence and vulnerability signal. |
| `copper_retirement.feature_device_service_usage` | 6,351 | Service usage metrics per device — bandwidth utilization, session counts. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_resource.alarm` | 100,000 | Network alarms — severity, duration, device association. Primary risk signal. |
| `tmf_resource.anomaly` | 10,000 | Detected anomalies in resource behavior — statistical outliers in performance. |
| `tmf_resource.resource_performance` | 10,000 | Resource performance measurements — throughput, latency, error rates. |
| `tmf_service.service_problem` | 100,000 | Service-level problems — outages, degradations, customer-impacting incidents. |
| `tmf_service.service_performance` | 100,000 | Service performance metrics — availability, quality scores, SLA compliance. |

## Entity Relationships

```
silver_copper_plant_enriched
  └── physical_device_id → bronze_copper_devices.physical_device_id
  └── wire_center_id → wire_center_boundary.wire_center_id
  └── physical_device_id → copper_risk_target.physical_device_id

copper_risk_predictions
  └── physical_device_id → silver_copper_plant_enriched.physical_device_id

gold_device_risk_predictions
  └── physical_device_id → copper_risk_predictions.physical_device_id
  └── wire_center_id → gold_wire_center_scorecard.wire_center_id

gold_wire_center_scorecard
  └── wire_center_id → wire_center_boundary.wire_center_id
  (aggregated from silver_copper_plant_enriched by wire_center_id)

feature_device_* tables
  └── physical_device_id → silver_copper_plant_enriched.physical_device_id
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Retirement Readiness Score | Composite 0–100 per wire center: fiber_ready (30pts) + risk_severity (20pts) + alarm_rate (20pts) + priority (30pts) | `gold_wire_center_scorecard.retirement_readiness_score` |
| Critical Risk Devices | Count of devices classified as critical risk tier | `gold_wire_center_scorecard.critical_risk_devices` |
| Avg Critical Alarm Rate | Mean critical alarm rate across copper devices at a wire center | `gold_wire_center_scorecard.avg_critical_alarm_rate` |
| Model Fairness Pass Rate | Percentage of fairness tests passing across all demographic dimensions | `v5_fairness_report` WHERE result = 'pass' |
| Prediction Confidence | Mean confidence score of V5 risk model predictions | `copper_risk_predictions` AVG(confidence) |

## Data Quality Notes

- **Model version:** V5 GBT model trained on 2,672 copper devices. Served via `copper-retirement-risk` endpoint (READY, inference table logging enabled).
- **Feature coverage:** 5 feature tables with 2,672–10,000 rows each. All join on `physical_device_id`.
- **Fairness testing:** 20 tests across 4 dimensions (device_type, geography, service_type, customer_segment). Summary in `v5_fairness_dimension_summary`.
- **Alarm data:** 100K alarms provide the primary risk signal. Enriched into `silver_copper_plant_enriched` as alarm_count, critical_alarm_rate, sla_breach_rate.
- **Monitoring:** Inference payloads logged for drift detection. 6 batch records in `risk_model_inference_payload`.
- **Refresh:** Silver enriched layer and wire center scorecard are DLP materialized views, auto-refreshed.

## Related Domains

- **Physical Plant** — Device inventory and wire center boundaries are the scoring dimensions
- **Circuits & Services** — Device risk informs circuit-level migration urgency
- **Customer Impact** — Complaint and churn data are risk model features
- **Financial Operations** — Risk-driven retirement sequencing feeds EBITDA forecasting
