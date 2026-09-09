# Copper Loop Plant — Synthetic Data Specification

**Task:** P0-DATAGEN-COPPER
**Author:** @data-engineer | **Date:** 2026-09-06
**Status:** Schema spec complete. Ready for implementation.

---

## Source Table Profiling Summary

### `tmf_enterprise.physical_device` (10K rows)
- **ID range:** 10001–20000 (LONG)
- **Copper-relevant device_types:**
  - `cpe`: 688 (547 active, 141 installed)
  - `ont`: 663 (all installed)
  - `olt`: 661 (474 installed, 187 in_stock)
  - `patch_panel`: 660 (all faulty)
  - **Total copper-endpoint devices (excl. OLT):** 2,011
  - **Total incl. OLT (aggregation point):** 2,672
- **FK coverage:** 100% `geographic_address_id` (0 orphans). 100% `equipment_holder_id`.
- **Key columns:** `device_type`, `status`, `technology_generation`, `installation_date`, `network_domain`, `vendor_name`
- **Note:** `technology_generation` values are modern (4g_lte, 5g_nr, gpon, ipv6) — no explicit "copper" indicator. The synthetic generator must add copper-era tech markers.

### `tmf_shared.geographic_address` (10K rows)
- **ID range:** 10001–20000 (LONG)
- **Lat/lon:** 100% coverage. Range: lat 34.23–99992.70, lon 3.42–99995.01 (synthetic, not geographically realistic).
- **State values:** Randomized strings (e.g., "BWTGCHMS6K14"), not real state codes. Each address has a unique state, exchange_location_code, and postal_code (10K distinct each).
- **Key columns:** `geographic_address_id`, `geographic_site_id`, `latitude`, `longitude`, `exchange_location_code`, `exchange_service_area_code`, `state_or_province`
- **Note:** `synthetic_assets.py` hardcodes LEGACY_STATES = ["CO","MN","WA","OR","ID","AZ"]. Copper loop generator should assign states from this same list for consistency with serving-area data.

### `tmf_resource.equipment_holder` (1K rows)
- **Holder types:** cabinet, chassis, slot, bay, subrack, frame, shelf, rack, panel
- **NO outside-plant types:** No pedestal, terminal, splice_closure, or cross-connect. These are all CO/hub equipment.
- **Implication:** Pedestal/terminal associations must be synthetic string IDs within the copper_loop_plant table, NOT FK references to equipment_holder.

### `tmf_resource.connection_point` (10K rows)
- **Types:** service_access_point, logical_connection_point, soft_connection_point, electronic_connection_point, physical_connection_point
- **FK columns:** `connection_point_id`, `logical_resource_id`, `topology_graph_id`. NO direct FK to physical_device.
- **Implication:** Copper pair termination should be modeled within copper_loop_plant, not by FK to connection_point.

---

## Synthetic Table Schema: `copper_loop_plant`

**Target catalog/schema:** `cdm_tmforum.tmf_resource` (or a new `cdm_tmforum.copper_retirement` schema)
**Recommended row count:** 50,000 records (~25 copper pairs per copper-endpoint device)
**Determinism:** Follow `synthetic_assets.py` pattern — `random.Random(seed)`, no wall-clock or network calls.

| Column | Type | Description | Value Range / FK |
|---|---|---|---|
| `copper_pair_id` | LONG | PK, synthetic sequence | 100001+ |
| `cable_segment_id` | STRING | Groups pairs into cable runs | "CS-{00001..02000}" |
| `physical_device_id` | LONG | FK → `tmf_enterprise.physical_device` | Filter: device_type IN ('cpe','ont','patch_panel'). 2,011 valid targets. |
| `geographic_address_id` | LONG | FK → `tmf_shared.geographic_address` | Inherited from physical_device.geographic_address_id (100% coverage). |
| `cable_gauge_awg` | INT | Wire gauge (American Wire Gauge) | {19, 22, 24, 26} — weighted: 24 AWG most common (60%), 26 AWG (20%), 22 AWG (15%), 19 AWG (5%) |
| `pair_count_in_cable` | INT | Total pairs in this cable segment | {25, 50, 100, 200, 400, 600, 900, 1200, 1800, 2400} |
| `pair_number` | INT | This pair's index within cable | 1..pair_count_in_cable |
| `segment_length_ft` | DECIMAL(10,1) | Length of this cable segment | 50–15,000 ft (log-normal, median ~2,000) |
| `loop_length_ft` | DECIMAL(10,1) | Total CO-to-demarc loop length | 500–18,000 ft (sum of segments) |
| `splice_point_count` | INT | Splices in this pair's path | 0–12 (correlated with loop_length) |
| `pedestal_id` | STRING (nullable) | Distribution pedestal | "PED-{00001..05000}" or NULL (aerial has none) |
| `terminal_id` | STRING (nullable) | Customer-side terminal | "TRM-{00001..10000}" or NULL |
| `cable_type` | STRING | Installation method | {aerial, buried_direct, underground_conduit} — weighted: buried 50%, aerial 30%, conduit 20% |
| `cable_vintage_year` | INT | Year cable was installed | 1960–2015 (bimodal: peak at 1975 and 1995) |
| `insulation_type` | STRING | Cable insulation material | {pulp, PIC, filled_PIC, gel_filled} — correlated with vintage (pulp pre-1975, PIC 1970-1990, filled_PIC/gel post-1985) |
| `pair_status` | STRING | Current operational status | {working, spare, defective, bonded, reserved} — weighted: working 55%, spare 20%, defective 15%, bonded 5%, reserved 5% |
| `last_test_date` | DATE | Last loop qualification test | 2020-01-01 to 2026-09-01 |
| `test_result_db_loss` | DECIMAL(5,2) | Insertion loss at 1 MHz | 0–40 dB (correlated with loop_length: ~1.3 dB/kft at 24 AWG) |
| `resistance_ohms_per_kft` | DECIMAL(7,2) | DC loop resistance | Gauge-dependent: 19→16.1, 22→32.4, 24→51.9, 26→83.5 Ω/kft |
| `moisture_detected` | BOOLEAN | Moisture ingress flag | ~12% TRUE (correlated with cable_vintage < 1985 AND insulation_type = 'pulp') |
| `source` | STRING | Lineage marker | Constant: "synthetic" |
| `created_timestamp` | TIMESTAMP | Record creation time | Generator run timestamp |

---

## FK Join Strategy

```
copper_loop_plant.physical_device_id
  → tmf_enterprise.physical_device.physical_device_id
    → physical_device.geographic_address_id
      → tmf_shared.geographic_address.geographic_address_id
```

- **Cardinality:** ~25 copper pairs per device (50K pairs / 2,011 devices)
- **Cable segments:** ~2,000 segments, each containing 25–2,400 pairs. One segment serves multiple devices on the same street/route.
- **Pedestal/terminal:** Generated as string IDs local to this table. One pedestal serves ~10 devices; one terminal serves 1–4 devices.

## Blockers & Notes

1. **No outside-plant holders in equipment_holder** — Pedestal/terminal modeled as local string IDs. If a dedicated `outside_plant_enclosure` table is needed later, refactor then.
2. **Geographic address states are randomized** — Generator must override with LEGACY_STATES from synthetic_assets.py for geographic consistency.
3. **No explicit copper technology marker on physical_device** — Generator should filter device_type IN ('cpe','ont','patch_panel') and treat these as copper-served endpoints. OLT (661 devices) is the fiber aggregation point and should NOT be in the copper loop plant.
4. **connection_point has no device FK** — Copper pair termination modeled within this table, not linked to connection_point.
5. **H3 indexing** — After generation, H3 cell columns should be added via join to geographic_address → lat/lon → `h3_latlng_to_cell()`. Defer to P2-H3 task.
