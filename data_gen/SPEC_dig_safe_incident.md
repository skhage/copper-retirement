# Dig-Safe Incident Registry — Synthetic Data Specification

**Task:** P0-DATAGEN-DIGSAFE
**Author:** @data-engineer | **Date:** 2026-09-08
**Status:** Schema spec complete. Ready for implementation.

---

## Source Table Profiling Summary

### `tmf_enterprise.work` (100K rows)
- **ID range:** 10001–110000 (LONG), PK is `work_id` (NOT `work_order_id` — task description corrected)
- **Dig-safe-relevant types:** `repair` (11,026), `emergency` (11,027) = 22,053 candidate FK targets
- **Categories:** network_operations (20K), customer_premises (20K), data_center (20K), noc (20K), field_service (10K), soc (10K)
- **Statuses:** dispatched/completed/on_hold/cancelled/in_progress/failed (~14K each), pending_approval/scheduled (~7K each)
- **FK columns:** `party_id` (→ bp_agreement.party_id, 67.3% match), `physical_resource_id`, `geographic_address_id`, `project_id`
- **Lat/lon:** `site_latitude`/`site_longitude` are DECIMAL(18,2) but synthetic garbage (range 1.57–99997). Generator must use LEGACY_STATES bounding boxes.
- **Data gen artifact:** `party_id` = `physical_resource_id` = `geographic_address_id` in every row (all FKs assigned same value per row)
- **`actual_duration_minutes`:** STRING type with random hash values (e.g., "P0N8URUY0069"), not numeric. Resolution time must be independently generated.

### `tmf_businesspartner.bp_agreement` (10K rows)
- **ID range:** 10001–20000 (LONG), PK is `bp_agreement_id`
- **Distinct `party_id` values:** 6,351 (multiple agreements per party)
- **Types:** distribution, wholesale_access, reseller, mvno_hosting, roaming, supplier, revenue_sharing, interconnect, nra_regulated
- **Statuses:** active (1,254), approved (1,278), expired (1,285), suspended (1,267), under_review (1,260), terminated (1,232), cancelled (1,220), draft (628), superseded (576)
- **Key columns:** `bp_agreement_id`, `party_id`, `type`, `status`, `sla_tier`, `governing_law_jurisdiction`
- **Note:** `partner_performance_rating` in `project_partner_assignment` is random hash — unusable.

### `tmf_shared.geographic_address` (10K rows)
- **ID range:** 10001–20000 (LONG)
- **Lat/lon:** 100% coverage, synthetic (0–99K range)
- **State values:** Random hashes, not real state codes. Generator must override with LEGACY_STATES.

### `tmf_shared.network_route` (1K rows)
- **ID range:** 10001–11000 (LONG)
- **`route_type` and `route_category`:** Both are random hashes (1K unique each). No meaningful route classification.
- **Has `geographic_site_id` FK** for location association.
- **Note:** Useful as optional FK for "affected route" but the data is structurally synthetic.

### `tmf_enterprise.project` (10K rows)
- Available for FK linking dig-safe incidents to copper retirement projects.

---

## Synthetic Table Schema: `dig_safe_incident`

**Target catalog/schema:** `cdm_tmforum.tmf_resource` (or `cdm_tmforum.copper_retirement` if created)
**Recommended row count:** 5,000 records (~1 incident per 4.4 repair/emergency work orders)
**Determinism:** Follow `synthetic_assets.py` pattern — `random.Random(seed)`, no wall-clock or network calls.

| Column | Type | Description | Value Range / FK |
|---|---|---|---|
| `incident_id` | LONG | PK, synthetic sequence | 200001+ |
| `work_id` | LONG | FK → `tmf_enterprise.work.work_id` | Sample from work rows WHERE type IN ('repair','emergency'). 22,053 valid targets. |
| `bp_agreement_id` | LONG | FK → `tmf_businesspartner.bp_agreement.bp_agreement_id` | Contractor responding to/causing incident. Range 10001–20000. |
| `geographic_address_id` | LONG | FK → `tmf_shared.geographic_address.geographic_address_id` | Incident location. Range 10001–20000. |
| `network_route_id` | LONG (nullable) | FK → `tmf_shared.network_route.network_route_id` | Affected network route. Range 10001–11000. ~60% populated, 40% NULL (not all incidents affect a known route). |
| `state` | STRING | US state code | LEGACY_STATES: {CO, MN, WA, OR, ID, AZ} — weighted: CO 35%, MN 20%, WA 15%, OR 12%, ID 10%, AZ 8% |
| `latitude` | DECIMAL(9,6) | Incident latitude | Per-state bounding boxes (CO: 39.4–40.3, extend for other states). Use realistic ranges. |
| `longitude` | DECIMAL(9,6) | Incident longitude | Per-state bounding boxes (CO: -105.4 to -104.6, extend for other states). |
| `incident_date` | DATE | Date incident occurred | 2020-01-01 to 2026-09-01 |
| `incident_timestamp` | TIMESTAMP | Full timestamp of incident | Derived from incident_date + random time-of-day (weighted: 70% weekday 07:00–17:00) |
| `severity` | STRING | Incident severity level | {critical, major, minor, informational} — weighted: minor 45%, major 30%, critical 15%, informational 10% |
| `cable_type` | STRING | Type of cable affected | {aerial, buried_direct, underground_conduit} — weighted: buried_direct 50%, aerial 30%, underground_conduit 20% (matches copper_loop_plant SPEC) |
| `cable_damage_type` | STRING | Nature of damage | {cut, nick, crush, displacement, moisture_ingress, abrasion} — weighted by cable_type |
| `root_cause` | STRING | What caused the incident | {excavation, boring, trenching, plowing, hand_dig, natural_event, vehicle_strike, utility_conflict} |
| `contractor_at_fault` | BOOLEAN | Whether contractor caused the dig strike | ~35% TRUE |
| `one_call_ticket_submitted` | BOOLEAN | Whether 811/one-call was filed before work | ~75% TRUE (when FALSE and contractor_at_fault=TRUE → violation) |
| `resolution_time_hours` | DECIMAL(6,1) | Hours from incident to service restoration | 0.5–168.0 (log-normal, median ~8.0 hours; correlated with severity: critical→shorter, minor→longer) |
| `reroute_required` | BOOLEAN | Whether traffic had to be rerouted | ~20% TRUE (correlated with severity=critical/major) |
| `service_interruption` | BOOLEAN | Whether customer service was interrupted | ~65% TRUE (correlated with severity) |
| `affected_pair_count` | INT | Number of copper pairs damaged | 1–200 (log-normal, median ~12; correlated with cable_type: buried_direct → more pairs) |
| `repair_cost_amount` | DECIMAL(10,2) | Repair cost in USD | 500–75,000 (log-normal, median ~5,000; correlated with severity + affected_pair_count) |
| `depth_of_cover_inches` | DECIMAL(5,1) (nullable) | Cable burial depth at incident point | 12–48 inches for buried/conduit; NULL for aerial |
| `source` | STRING | Lineage marker | Constant: "synthetic" |
| `created_timestamp` | TIMESTAMP | Record creation time | Generator run timestamp |

---

## FK Join Strategy

```
dig_safe_incident.work_id
  → tmf_enterprise.work.work_id
    (filter: work.type IN ('repair', 'emergency'))

dig_safe_incident.bp_agreement_id
  → tmf_businesspartner.bp_agreement.bp_agreement_id
    (contractor who responded to or caused the incident)

dig_safe_incident.geographic_address_id
  → tmf_shared.geographic_address.geographic_address_id
    (nearest address to incident location)

dig_safe_incident.network_route_id (nullable)
  → tmf_shared.network_route.network_route_id
    (affected network route segment, if known)
```

**Cardinality:**
- ~5K incidents linking to ~4.5K unique work orders (some work orders may have multiple incidents at nearby locations)
- Each incident references exactly 1 contractor agreement
- ~3K unique geographic addresses (incidents cluster near copper plant)
- ~600 unique network routes affected (out of 1K total)

**Cross-table join to copper_loop_plant (when generated):**
```
dig_safe_incident.geographic_address_id
  → copper_loop_plant.geographic_address_id
    (identifies which copper pairs were in the affected area)
```

---

## Correlations & Business Logic

1. **Severity ↔ resolution_time:** Critical incidents resolve faster (emergency response) — median 2h. Minor incidents queue longer — median 24h.
2. **Cable_type ↔ cable_damage_type:** Aerial → vehicle_strike/natural_event more common. Buried → excavation/boring/trenching.
3. **One-call compliance:** When `one_call_ticket_submitted=FALSE` AND `contractor_at_fault=TRUE` → regulatory violation. ~8% of incidents should be violations.
4. **Seasonal pattern:** `incident_date` should show spring/summer peak (construction season: Apr–Sep = 65% of incidents).
5. **Cost model:** `repair_cost_amount` = base_cost(severity) × pair_multiplier(affected_pair_count) × cable_type_factor × reroute_surcharge.
6. **Link to synthetic_assets.py:** The `historical_dig_incident_rate` field in serving areas should be derivable from the count of dig_safe_incidents per H3 cell per year.

---

## Blockers & Notes

1. **Task spec says `work_order_id` but actual PK is `work_id`** — This spec uses `work_id`. Generator should sample from `work` WHERE `type IN ('repair','emergency')` (22K valid targets).
2. **Lat/lon in source tables are synthetic garbage** — Generator must produce realistic coordinates within LEGACY_STATES bounding boxes. Extend beyond CO Front Range:
   - CO: lat 38.8–40.5, lon -105.5 to -104.5
   - MN: lat 44.5–45.2, lon -93.5 to -93.0
   - WA: lat 47.3–47.8, lon -122.5 to -122.0
   - OR: lat 45.3–45.7, lon -123.0 to -122.5
   - ID: lat 43.5–43.8, lon -116.5 to -116.0
   - AZ: lat 33.3–33.6, lon -112.2 to -111.8
3. **`actual_duration_minutes` in `work` is a random hash string** — Not numeric. `resolution_time_hours` is independently generated in this table.
4. **Contractor FK uses `bp_agreement_id`, not `party_id`** — More granular (agreement-level, not org-level). `work.party_id` → `bp_agreement.party_id` has only 67.3% match, so use `bp_agreement_id` directly.
5. **Network route data is random hashes** — `route_type`/`route_category` are gibberish (1K unique each). The FK is structurally valid but semantically empty.
6. **Depends on P0-DATAGEN-COPPER-EXECUTE** — Once copper_loop_plant is generated, dig_safe_incident should be cross-referenced via `geographic_address_id` to identify affected copper pairs.
7. **Feeds P6-TRIAGE agent** — This table is the primary data source for the dig-safe triage agent in BUILD-PLAN.md.
8. **Feeds P0-DATAGEN-CONTRACTOR** — Incident counts per `bp_agreement_id` will feed the contractor performance scorecard.
