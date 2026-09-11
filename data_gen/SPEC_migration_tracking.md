# SPEC: Copper-to-Fiber Migration Tracking

**Author:** @data-engineer | **Date:** 2026-09-11
**Task:** P0-DATAGEN-MIGRATION
**Feeds:** P7-PLAN (Gantt visualization), P4-SEQ (migration sequence optimizer), P3-DLP (gold_migration_readiness)

---

## Overview

One row per **copper customer migration project** — tracks the lifecycle of migrating a customer from copper-based services to fiber equivalents. Granularity is per-customer (not per-service) because profiling shows 1,786/1,787 copper customers have a single service type and single address. Multi-service migrations are captured via `copper_service_count` and `copper_service_types` columns.

## Target Table

- **Table name:** `copper_fiber_migration_tracking`
- **Target schema:** `copper_retirement` (pending @pm DECISION-SCHEMA; fallback: `tmf_service`)
- **Target rows:** ~1,800 (one per copper customer; 1,787 from CFS profiling, rounded up for headroom)

## Source Table Profiling Results

| Source Table | Rows | Key Finding |
| --- | --- | --- |
| `tmf_customer.customer` | 10K | PK 10001–20000. 1,787 have copper CFS. 6 types: residential (1,005), business (2,020), government (1,948), wholesale (2,040), mvno (2,044), ngo (943). Lifecycle: active 244, churned 247, dormant 239, others — among copper subset. |
| `tmf_service.customer_facing_service` | 100K | 17,655 copper-candidate rows (voice 7,140 + fixed_line 6,940 + broadband 3,575). 11,212 distinct service_ids. Status: feasibility_checked 6,272, designed 4,443, terminated 4,403, cancelled 2,537. **No 'active' status** — data-gen artifact. |
| `tmf_shared.geographic_address` | 10K | PK 10001–20000. 100% FK match from CFS. 1,787 distinct addresses serve copper customers (1:1 customer:address). |
| `tmf_customer.commitment` | 10K | 6,351 customers with commitments; 1,120 are copper customers (62.7%). **100% expired** (max end_date 2025-12-30). Blocked by FIX-COMMITMENT-DATES task. |
| `tmf_service.service_order_item` | 100K | 8,320 'migrate' action items (5,555 pendingCancellation + 2,765 assessingCancellation). 3,488 distinct CFS mapped. |
| `tmf_enterprise.work` | 100K | 11,159 decommission + 11,081 upgrade work orders. No explicit 'migration' type. |
| `tmf_resource.device_service_allocation` | 1K | Only 255/2,672 copper devices have allocations (9.5%) — sparse. 38 copper CFS allocations. |
| `ironclad_clm_source.contract_record` | 25 | 18 distinct TMF customers via crosswalk (SOURCE_SYSTEM='SALESFORCE'). Join path: `account_id` → `mdm_source.customer_crosswalk.SOURCE_PARTY_ID` → `MASTER_CUSTOMER_ID`. |

## FK References

| Column | Target Table | Target PK | Validated | Coverage |
| --- | --- | --- | --- | --- |
| `customer_id` | `tmf_customer.customer` | `customer_id` | Yes | 1,787 copper customers (BIGINT 10001–20000) |
| `geographic_address_id` | `tmf_shared.geographic_address` | `geographic_address_id` | Yes | 100% from CFS (BIGINT 10001–20000) |
| `old_service_id` | `tmf_service.customer_facing_service` | `service_id` | Yes | 11,212 copper service_ids (BIGINT 10002–106427) |
| `work_order_id` | `tmf_enterprise.work` | `work_id` | Yes | 11,159 decommission targets (BIGINT range) |
| `wave_id` | Synthetic (self-referencing batch grouping) | N/A | N/A | Generator creates 20–30 waves |

## Schema Definition (28 columns)

| # | Column | Type | Nullable | Description | Generation Rule |
| --- | --- | --- | --- | --- | --- |
| 1 | `migration_id` | BIGINT | No | Primary key | Sequential starting at 100001 |
| 2 | `customer_id` | BIGINT | No | FK → `tmf_customer.customer` | Sampled from 1,787 copper customers |
| 3 | `customer_type` | STRING | No | Denormalized from customer.type | Inherited from customer FK |
| 4 | `old_service_id` | BIGINT | No | FK → CFS copper service (primary) | Primary copper CFS service_id for this customer |
| 5 | `old_service_type` | STRING | No | voice / fixed_line / broadband | From CFS service_type |
| 6 | `new_service_id` | BIGINT | Yes | FK → CFS fiber service (if provisioned) | Synthetic BIGINT in 200001–300000 range; NULL if status < fiber_provisioned |
| 7 | `new_service_type` | STRING | Yes | Fiber equivalent service type | ftth_voice / ftth_data / ftth_broadband |
| 8 | `geographic_address_id` | BIGINT | No | FK → `tmf_shared.geographic_address` | Inherited from CFS copper service |
| 9 | `copper_service_count` | INT | No | Total copper CFS services for this customer | COUNT from CFS per customer (avg 9.9, but ~6.4 distinct service_ids per customer) |
| 10 | `copper_service_types` | STRING | No | Comma-separated service types | COLLECT from CFS per customer |
| 11 | `migration_status` | STRING | No | Current state (see state machine below) | Weighted distribution per state machine |
| 12 | `migration_priority` | STRING | No | critical / high / medium / low | Weighted: 10% critical, 25% high, 40% medium, 25% low |
| 13 | `wave_id` | INT | No | Migration wave/batch number | 1–30; clustered by geographic_address H3 res-7 cell |
| 14 | `wave_name` | STRING | No | Human-readable wave label | Format: "Wave-{wave_id}-{state_abbrev}" |
| 15 | `scheduled_start_date` | DATE | Yes | Planned migration start | 2026-03-01 to 2028-12-31; NULL if status = identified/assessed |
| 16 | `scheduled_completion_date` | DATE | Yes | Planned completion | scheduled_start + 14–90 days (varies by customer_type) |
| 17 | `actual_start_date` | DATE | Yes | Real start date | Non-NULL only if status ≥ in_progress |
| 18 | `actual_completion_date` | DATE | Yes | Real completion date | Non-NULL only if status = completed/verified |
| 19 | `work_order_id` | BIGINT | Yes | FK → `tmf_enterprise.work` (decommission) | Sampled from 11,159 decommission work orders; NULL if status < in_progress |
| 20 | `contract_lock_flag` | BOOLEAN | No | Active MSA blocks migration | True if customer matches CLM active contract via crosswalk; ~10% of rows |
| 21 | `contract_end_date` | DATE | Yes | When contract lock expires | From commitment.effective_end_date (pending FIX-COMMITMENT-DATES) |
| 22 | `revrec_lock_flag` | BOOLEAN | No | Active rev-rec schedule blocks migration | True if customer has open revenue_recognition_schedule; ~15% of rows |
| 23 | `estimated_revenue_impact` | DECIMAL(18,2) | Yes | Monthly revenue at risk (MRR) | Synthetic $25–$2,500/month based on customer_type + service_type |
| 24 | `estimated_migration_cost` | DECIMAL(18,2) | Yes | Per-migration cost estimate | $200–$5,000 based on service_type + geographic complexity |
| 25 | `fiber_readiness_score` | DECIMAL(5,2) | Yes | CO/area fiber readiness (0–100) | Correlated with wave_id; later waves = lower readiness |
| 26 | `risk_score` | DECIMAL(5,2) | Yes | Composite migration risk (0–100) | Weighted: contract_lock(30%) + revrec_lock(20%) + service_complexity(20%) + age(15%) + geography(15%) |
| 27 | `notes` | STRING | Yes | Free-text notes | Templated migration notes per status |
| 28 | `last_updated_timestamp` | TIMESTAMP | No | Row modification timestamp | NOW() at generation time |

## Migration Status State Machine

```
identified → assessed → scheduled → notified → in_progress → fiber_provisioned → cutover → completed → verified
                                                    ↘ on_hold (contract/revrec lock)
                                         ↘ cancelled
                           ↘ deferred (regulatory/capacity constraint)
```

**Target distribution (1,800 rows):**
- `identified`: 180 (10%) — newly flagged copper customers
- `assessed`: 270 (15%) — impact assessment complete
- `scheduled`: 360 (20%) — wave assigned, dates set
- `notified`: 180 (10%) — 90-day FCC notice sent
- `in_progress`: 270 (15%) — field work underway
- `fiber_provisioned`: 90 (5%) — fiber circuit active, copper still live
- `cutover`: 90 (5%) — traffic migrated to fiber
- `completed`: 180 (10%) — copper decommissioned
- `verified`: 90 (5%) — post-migration validation passed
- `on_hold`: 54 (3%) — blocked by contract or revrec constraint
- `cancelled`: 18 (1%) — customer churned or withdrew
- `deferred`: 18 (1%) — regulatory or capacity constraint

## Blockers & Dependencies

1. **FIX-COMMITMENT-DATES** — `commitment.effective_end_date` is 100% expired. `contract_end_date` column will have stale values until FIX-COMMITMENT-DATES is executed. Generator should use synthetic future dates (2026–2028) for contract_lock_flag=true rows regardless.
2. **FIX-COORDINATES** — Wave clustering by H3 cell requires valid coordinates. Generator should use `generate_coords_for_state()` from `synthetic_assets.py` for wave geographic grouping. **Depends on FIX-COORDINATES notebook being RUN first** for address-correlated wave assignment; without it, wave assignment will be random by state.
3. **Schema placement** — `copper_retirement` schema may not exist. Generator should `CREATE SCHEMA IF NOT EXISTS` or fall back to `tmf_service`. @pm decision pending.
4. **CFS status artifact** — No 'active' CFS status exists (only feasibility_checked/designed/terminated/cancelled). Migration generator should treat `feasibility_checked` + `designed` as active-equivalent for copper service selection.

## Downstream Consumers

- **P7-PLAN Gantt:** `scheduled_start_date`, `scheduled_completion_date`, `wave_id`, `migration_status` drive the Gantt chart bars
- **P4-SEQ optimizer:** `contract_lock_flag`, `revrec_lock_flag`, `fiber_readiness_score`, `risk_score` are constraint/objective inputs
- **P3-DLP gold_migration_readiness:** This table IS the gold target (or primary source for it)
- **P7-MAP:** `geographic_address_id` + `migration_status` for color-coded migration progress overlay
- **P6-TRIAGE agent:** Migration status context for customer-specific triage queries
