# Contractor Performance — Synthetic Data Specification

**Task:** P0-DATAGEN-CONTRACTOR
**Author:** @data-engineer | **Date:** 2026-09-10
**Status:** Schema spec complete. Ready for implementation.

---

## Source Table Profiling Summary

### `tmf_businesspartner.bp_agreement` (10K rows) — Primary FK Target
- **ID range:** 10001–20000 (LONG), PK is `bp_agreement_id`
- **Distinct `party_id` values:** 6,351 (multiple agreements per party)
- **Types (9):** distribution (1,285), wholesale_access (1,278), reseller (1,267), mvno_hosting (1,260), roaming (1,254), supplier (1,232), revenue_sharing (1,220), interconnect (628), nra_regulated (576)
- **Statuses (9):** expired/approved/suspended/under_review/active/terminated/cancelled (~1.2K each), draft (628), superseded (576)
- **SLA tiers (6):** bronze (2,044), silver (2,040), gold (2,020), standard (1,948), platinum (1,005), custom (943)
- **`governing_law_jurisdiction`:** Currency codes (TRY, AED, BRL, etc.) — data gen artifact, not real jurisdictions
- **Financial columns:** `minimum_commitment_value` avg ~$50K, `total_contract_value` avg ~$50K — random uniform distribution
- **Contractor-relevant types for field work:** `supplier` (1,232), `distribution` (1,285) — these are the most plausible dig/construction contractors. Generator should weight these types more heavily in performance scoring.

### `tmf_enterprise.work` (100K rows) — Work Order Metrics Source
- **FK join:** `work.party_id` → `bp_agreement.party_id` = **67.3% match** (67,285 of 100K work orders). All 10K bp_agreements have at least 1 work order.
- **Work orders per contractor:** min=2, p25=9, median=11, p75=13, max=25, avg=11
- **Work types (10):** configuration (11K), decommission (11K), maintenance (10K), preventive (9K), inspection (8K), upgrade (8K), emergency (6K), repair (6K), installation (6K), corrective (6K)
- **SLA met flag:** 33,872/67,285 contractor work orders = **50.3% SLA compliance** (overall 50,190/100K)
- **Geographic address FK:** `work.geographic_address_id` → `geographic_address` = 100% match (100K/100K)
- **Geographic coverage per contractor:** Exactly 1 distinct `geographic_address_id` per contractor — deterministic mapping. **Must synthesize multi-location coverage.**
- **Lat/lon:** `site_latitude`/`site_longitude` are DECIMAL(18,2) synthetic garbage (0–99K). Use `geographic_address_id` FK path after FIX-COORDINATES.
- **`actual_duration_minutes`:** STRING type with random hashes — not numeric. Must independently synthesize resolution metrics.
- **Data gen artifact:** `party_id` = `physical_resource_id` = `geographic_address_id` in every row

### `tmf_businesspartner.project_partner_assignment` (10K rows)
- **Distinct partners:** 6,351 (same as bp_agreement.party_id cardinality)
- **`partner_performance_rating`:** Random hashes — **completely unusable** for performance scoring
- **`assignment_status`:** Random hashes — unusable
- **`revenue_share_percentage`:** DECIMAL(18,2) — has real-looking numeric values
- **`partner_commitment_level`:** Random hashes — unusable
- **Conclusion:** Cannot derive contractor performance from this table. Must synthesize.

### `tmf_businesspartner.party_sla` (1K rows)
- **938 distinct `service_provider_id` values** — near-unique
- **SLA tiers (6):** Same vocabulary as bp_agreement: bronze/silver/gold/standard/platinum/custom
- **SLA categories (9):** capacity, provisioning, compliance, support_response, security, fault_restoration, network_performance, billing_accuracy, other
- **Rich SLA metrics:** availability_target_pct, mttr_target_hours, latency_target_ms, jitter_target_ms, packet_loss_target_pct, provisioning_target_hours, support_response_target_hours
- **No direct FK to bp_agreement** — joins via `service_provider_id` (not `party_id`). Cannot reliably join.
- **Use case:** SLA metric ranges inform synthetic value bounds for contractor performance targets.

### `tmf_businesspartner.sales_project` (100K rows)
- **FK join:** `sales_project.party_id` → `bp_agreement.party_id` = 67.3% match
- **Has:** `estimated_annual_recurring_revenue_amount`, `estimated_contract_value_amount`, `win_probability_percentage`
- **Relevance:** Contractor project volume and revenue — can inform `total_project_value` and `active_project_count` columns.

### Cross-reference: `dig_safe_incident` (SPEC, 5K target rows)
- **Uses `bp_agreement_id` directly** (range 10001–20000) as contractor FK
- **~35% `contractor_at_fault`** — yields incident rate per contractor
- **`resolution_time_hours`:** 0.5–168.0, median ~8.0 hours
- **Feeds:** `incident_count` and `dig_strike_rate` in this table should be derivable from dig_safe_incident when both are generated. For initial synthesis, generate independently with consistent distributions.

---

## Synthetic Table Schema: `contractor_performance`

**Target catalog/schema:** `cdm_tmforum.tmf_businesspartner` (alongside bp_agreement)
**Recommended row count:** 10,000 records (one per `bp_agreement_id`)
**Determinism:** Follow `synthetic_assets.py` pattern — `random.Random(seed)`, no wall-clock or network calls.

| Column | Type | Description | Value Range / FK |
|---|---|---|---|
| `contractor_performance_id` | LONG | PK, synthetic sequence | 300001+ (avoids collision with other synthetic PKs) |
| `bp_agreement_id` | LONG | FK → `bp_agreement.bp_agreement_id` | 10001–20000. 1:1 mapping — one performance record per agreement. |
| `party_id` | LONG | FK → `bp_agreement.party_id` (denormalized) | Copy from bp_agreement for direct work-order joins. |
| `contractor_name` | STRING | Realistic contractor company name | Synthetic: "{prefix} {specialty} {suffix}" — e.g., "Western Underground Services LLC". Use state-appropriate prefixes. |
| `contractor_type` | STRING | Specialization category | {general_construction, fiber_splicing, aerial_line, underground_boring, trenching, cable_pulling, restoration, multi_discipline} — weighted by bp_agreement.type |
| `certification_status` | STRING | Current certification level | {fully_certified, provisionally_certified, expired_certification, under_review, revoked} — weighted: fully_certified 55%, provisional 20%, expired 12%, under_review 8%, revoked 5% |
| `safety_score` | DECIMAL(4,1) | OSHA-style safety rating (0-100) | 40.0–99.5, normal distribution mean=78.0, σ=12.0. Correlated with certification_status: fully_certified → mean 85, revoked → mean 50. |
| `osha_recordable_rate` | DECIMAL(5,2) | OSHA Total Recordable Incident Rate (per 200K hours) | 0.5–8.0, industry avg ~3.0. Inversely correlated with safety_score. |
| `incident_count` | INT | Total dig-safe incidents involving this contractor (all-time) | 0–15. Poisson λ=2.5. Should be consistent with dig_safe_incident table when both exist (~5K incidents / 10K contractors). |
| `at_fault_incident_count` | INT | Incidents where contractor was at fault | 0 to incident_count. ~35% of incident_count (matching dig_safe_incident.contractor_at_fault rate). |
| `avg_resolution_time_hours` | DECIMAL(6,1) | Average time to restore service after incident | 1.0–72.0, log-normal median ~8.0 hours. Correlated with contractor_type: fiber_splicing → faster, general_construction → slower. |
| `work_order_completion_rate` | DECIMAL(5,2) | % of assigned work orders completed on time | 60.0–99.9. Normal mean=85.0, σ=8.0. Correlated with safety_score. |
| `sla_compliance_pct` | DECIMAL(5,2) | % of work orders meeting SLA targets | 40.0–99.9. Inherit from bp_agreement.sla_tier: platinum → mean 95%, bronze → mean 70%. |
| `active_project_count` | INT | Current active projects | 0–12. Poisson λ=3.0. |
| `total_project_value` | DECIMAL(14,2) | Total value of active projects (USD) | 10,000–5,000,000. Log-normal, median ~250,000. Correlated with active_project_count. |
| `crew_size` | INT | Number of field crew members | 2–50. Log-normal, median ~8. Correlated with contractor_type: general_construction → larger, fiber_splicing → smaller. |
| `equipment_count` | INT | Number of major equipment units (bore rigs, bucket trucks, etc.) | 1–20. Correlated with crew_size (ratio ~0.3). |
| `years_in_business` | INT | Years of operation | 1–45. Uniform with slight right-tail. |
| `geographic_coverage_states` | STRING | Comma-separated US state codes of coverage area | Subset of all 50 US states. 1–6 states per contractor. LEGACY_STATES weighted 3× more likely. |
| `geographic_coverage_h3` | STRING | Comma-separated H3 res-7 cell IDs for coverage footprint | 1–15 H3 cells per contractor. Generate using `generate_coords_for_state()` from `synthetic_assets.py` → `h3_latlng_to_cell(lat, lon, 7)`. Cells should cluster within `geographic_coverage_states`. |
| `primary_state` | STRING | Contractor's primary operating state | One of `geographic_coverage_states`. Weighted toward LEGACY_STATES. |
| `bonded_amount` | DECIMAL(12,2) | Contractor's surety bond amount (USD) | 50,000–2,000,000. Log-normal, correlated with total_project_value. |
| `insurance_expiry_date` | DATE | Liability insurance expiration | 2026-01-01 to 2028-12-31. ~10% expired (before 2026-09-10). |
| `last_audit_date` | DATE | Last safety/compliance audit | 2024-01-01 to 2026-09-01. |
| `overall_rating` | DECIMAL(3,1) | Composite contractor score (1.0–5.0) | Derived: weighted average of safety_score (30%), sla_compliance_pct (25%), work_order_completion_rate (25%), inverse incident_rate (20%). Normalized to 1.0–5.0 scale. |
| `source` | STRING | Lineage marker | Constant: "synthetic" |
| `created_timestamp` | TIMESTAMP | Record creation time | Generator run timestamp |

---

## FK Join Strategy

```
contractor_performance.bp_agreement_id
  → tmf_businesspartner.bp_agreement.bp_agreement_id
    (1:1 — one scorecard per agreement)

contractor_performance.party_id
  → tmf_enterprise.work.party_id
    (1:many — all work orders for this contractor)

contractor_performance.geographic_coverage_h3
  → (H3 spatial join) → geographic_address.h3_res7
    (identifies which addresses/wire centers a contractor can serve)

contractor_performance.bp_agreement_id
  → dig_safe_incident.bp_agreement_id
    (validates incident_count and at_fault_incident_count)
```

**Cardinality:**
- 10K contractor_performance rows (1:1 with bp_agreement)
- ~67K work orders joinable via party_id (median 11 per contractor)
- ~5K dig_safe_incidents joinable via bp_agreement_id (~0.5 per contractor avg)
- ~1–15 H3 cells per contractor for geographic coverage

---

## Correlations & Business Logic

1. **safety_score ↔ certification_status:** Higher safety scores correlate with `fully_certified`. Revoked contractors have scores < 60.
2. **incident_count ↔ at_fault_incident_count:** at_fault = ~35% of total (consistent with dig_safe_incident spec).
3. **sla_compliance_pct ↔ bp_agreement.sla_tier:** Platinum-tier agreements demand higher compliance (mean 95%). Bronze allows lower (mean 70%).
4. **contractor_type ↔ avg_resolution_time:** Specialized contractors (fiber_splicing) resolve faster than general_construction.
5. **crew_size ↔ equipment_count:** Ratio ~0.3 (3 crew per 1 equipment unit). Both scale with total_project_value.
6. **geographic_coverage ↔ primary_state:** Contractors cover 1–6 states but have a weighted primary state from LEGACY_STATES.
7. **overall_rating derivation:** `0.3 × norm(safety_score) + 0.25 × norm(sla_compliance_pct) + 0.25 × norm(completion_rate) + 0.2 × norm(1 - incident_rate)`, scaled to 1.0–5.0.
8. **insurance_expiry_date:** ~10% expired creates a "contractor not insured" risk flag for P6-TRIAGE agent.

---

## Blockers & Notes

1. **`partner_performance_rating` is random hash** — Cannot derive from existing data. All performance metrics must be independently synthesized.
2. **Geographic coverage = 1 location per contractor in work table** — The `work.party_id → geographic_address_id` mapping is fully deterministic (every work order for a contractor points to the same address). Multi-location coverage must be synthesized using `generate_coords_for_state()` from `synthetic_assets.py`.
3. **`actual_duration_minutes` in work table is STRING with random hashes** — Cannot derive resolution times from work orders. Must synthesize `avg_resolution_time_hours` independently.
4. **H3 dependency:** `geographic_coverage_h3` column requires H3 functions. Generator should use `h3_latlng_to_cell()` if running on Databricks, or pre-compute H3 cells from lat/lon using the `h3` Python library.
5. **Consistency with dig_safe_incident:** When both tables are generated, `incident_count` per contractor should match `COUNT(*) FROM dig_safe_incident GROUP BY bp_agreement_id`. For initial independent generation, use Poisson(λ=2.5) which gives ~5K total incidents across 10K contractors (50% have 0 incidents).
6. **Feeds:** P6-TRIAGE agent (contractor selection/dispatch), P7-PLAN (contractor capacity planning), P3-DLP gold `contractor_scorecard` table.

---

## Implementation Notes

```python
# Generator pattern (follows synthetic_assets.py conventions):
# 1. Load bp_agreement_ids: spark.table('cdm_tmforum.tmf_businesspartner.bp_agreement').select('bp_agreement_id', 'party_id', 'sla_tier', 'type')
# 2. For each bp_agreement_id, generate one contractor_performance row
# 3. Use STATE_BOUNDS_FULL from synthetic_assets.py for coordinate generation
# 4. Compute H3 cells via h3_latlng_to_cell() or h3 Python library
# 5. Derive overall_rating from weighted composite
# 6. Write to cdm_tmforum.tmf_businesspartner.contractor_performance
```