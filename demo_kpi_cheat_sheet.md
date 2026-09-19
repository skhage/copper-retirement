# Lakelink Fiber — Copper Retirement Demo-Day KPI Cheat Sheet

> **Generated:** 2026-09-19 by @data-analyst  
> **Source:** 4 metric views in `cdm_tmforum.copper_retirement`  
> **Purpose:** Quick-reference numbers for the presenter during demo day

---

## 1. Project Status
**Source:** `copper_retirement.copper_retirement_project_status`

| KPI | Value |
| --- | --- |
| Total Copper Devices | **2,672** |
| Active Devices | **1,825** (68.3%) |
| Faulty Devices | **660** (24.7%) |
| Critical Risk Devices | **383** (14.3%) |
| Fiber Ready Devices | **122** (4.6%) |
| Unique Wire Centers | **103** |
| Avg Alarm Count per Device | **10.08** |
| Total Problem Count | **27,027** |
| Avg SLA Breach Rate | **9.4%** |

### By Risk Tier
| Risk Tier | Devices | Fiber Ready | Fiber Ready % |
| --- | --- | --- | --- |
| Low | 956 | 44 | 4.6% |
| High | 812 | 29 | 3.6% |
| Medium | 521 | 26 | 5.0% |
| Critical | 383 | 23 | 6.0% |

### By Device Type
| Device Type | Devices | Active | Critical Risk |
| --- | --- | --- | --- |
| CPE | 688 | 688 | 93 |
| ONT | 663 | 663 | 90 |
| OLT | 661 | 474 | 94 |
| Patch Panel | 660 | 0 | 106 |

---

## 2. Customers Impacted
**Source:** `copper_retirement.copper_customers_impacted`

| KPI | Value |
| --- | --- |
| Customers Impacted | **288** |
| Services at Risk | **304** |
| Devices Impacting Customers | **440** |
| Voice Services at Risk | **141** |
| Broadband Services at Risk | **61** |
| Fixed Line Services at Risk | **102** |
| Residential Customers | **22** |
| Enterprise Customers | **50** |
| Critical Impact Customers | **64** |

### By Customer Segment
| Segment | Customers | Services |
| --- | --- | --- |
| Mid-Market | 50 | 55 |
| Enterprise | 50 | 52 |
| MVNO | 46 | 46 |
| SME | 38 | 39 |
| Wholesale | 36 | 37 |
| Carrier | 32 | 37 |
| Residential | 22 | 22 |
| Public Sector | 14 | 16 |

### By Risk Tier
| Risk Tier | Customers | Services | Critical |
| --- | --- | --- | --- |
| Low | 131 | 135 | 0 |
| High | 113 | 114 | 0 |
| Medium | 85 | 85 | 0 |
| Critical | 64 | 64 | 64 |

### Top 5 States
| State | Customers | Services |
| --- | --- | --- |
| DE | 21 | 21 |
| AK | 17 | 17 |
| AZ | 14 | 14 |
| NV | 14 | 14 |
| ND | 14 | 14 |

---

## 3. EBITDA Impact — Achieved
**Source:** `copper_retirement.copper_ebitda_impact_achieved`

| KPI | Value |
| --- | --- |
| Annual Revenue at Risk | **$603.8M** |
| Monthly Revenue at Risk | **$50.3M** |
| Total Billed Amount (OpEx) | **$125.7M** |
| Total Circuits | **14,777** |
| Avg Revenue per Circuit | **$40,864** |
| High Value Circuits | **1,777** |
| High Value Revenue | **$327.8M** |
| Immediate Action Revenue | **$214.1M** |
| Critical Risk Revenue | **$231.3M** |
| Avg ML Composite Risk Score | **0.362** |
| Fiber Ready Revenue | **$24.3M** |
| PUC Filing Revenue | **$53.9M** |

### Revenue by Risk Tier
| Risk Tier | Circuits | Annual Revenue |
| --- | --- | --- |
| Low | 9,265 | $372.6M |
| Critical | 5,512 | $231.3M |

### Revenue by Action Priority
| Action Priority | Circuits | Annual Revenue |
| --- | --- | --- |
| High Priority | 3,443 | $217.4M |
| Immediate Action | 3,152 | $214.1M |
| Monitor | 8,182 | $172.3M |

---

## 4. EBITDA Impact — Forecast
**Source:** `copper_retirement.copper_ebitda_impact_forecast`

### Overall (All Scenarios Combined)
| KPI | Value |
| --- | --- |
| Forecast Revenue at Risk | **$452.9M** |
| Forecast Annual Exposure | **$1.81B** |
| Forecast Cost Savings | **$94.2M** |
| Forecast Capex | **$236.3M** |
| Forecast Net Benefit | **$82.4M** |
| Forecast EBITDA Impact | **$96.6M** |
| Total Circuits (all scenarios) | **111,900** |
| Avg Capex per Circuit | **$2,112** |
| Avg Risk Score | **0.331** |
| Savings-to-Capex Ratio | **0.40** |

### By Scenario (Base)
| KPI | Base Scenario |
| --- | --- |
| Circuits | 37,300 |
| Revenue at Risk | $150.96M |
| EBITDA Impact | $32.19M |
| Net Benefit | $27.48M |
| Cost Savings | $31.42M |
| Capex | $78.78M |

### Quarterly Forecast (Base Scenario)
| Quarter | Circuits | Revenue at Risk | EBITDA Impact | Net Benefit |
| --- | --- | --- | --- | --- |
| 2026-Q4 | 1,902 | $14.9M | $3.2M | $2.7M |
| 2027-Q1 | 7,031 | $31.4M | $6.7M | $5.8M |
| 2027-Q2 | 10,695 | $43.1M | $9.2M | $7.9M |
| 2027-Q3 | 7,746 | $32.3M | $6.9M | $5.9M |
| 2027-Q4 | 7,746 | $20.2M | $4.3M | $3.6M |
| 2028-Q1 | 2,180 | $9.1M | $1.9M | $1.6M |

> **Peak quarter:** 2027-Q2 with 10,695 circuits and $9.2M EBITDA impact.

---

## Presenter Talking Points

1. **Scale:** 2,672 copper devices across 103 wire centers, impacting 288 customers and 304 services.
2. **Risk:** 14.3% of devices are Critical risk; 383 devices need immediate attention.
3. **Customer Impact:** 64 customers on critical-risk devices; Enterprise (50) and Mid-Market (50) are the largest affected segments.
4. **Financial Exposure:** $603.8M annual revenue at risk across 14,777 circuits. Average $40,864/circuit.
5. **High-Value Protection:** 1,777 high-value circuits represent $327.8M — must migrate carefully to retain.
6. **EBITDA Opportunity:** Base scenario projects $32.2M EBITDA improvement over 6 quarters, peaking at $9.2M in Q2 2027.
7. **Fiber Readiness:** Only 4.6% fiber ready today — significant build-out required.
8. **Regulatory:** $53.9M in revenue tied to circuits requiring PUC filings — longer retirement timelines.
