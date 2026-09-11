# Copper Commodity Price & Recovered Copper — Synthetic Data Specification

**Task:** P0-DATAGEN-COMMODITY
**Author:** @data-engineer | **Date:** 2026-09-10
**Status:** Schema spec complete. Ready for implementation.

---

## Source Table Profiling Summary

### Existing Financial Time-Series Pattern: `refinitiv_fx_source.gl_daily_rates` (23K rows)
- **Schema pattern:** `FROM_CURRENCY`, `TO_CURRENCY`, `CONVERSION_DATE` (DATE), `CONVERSION_RATE` (DOUBLE), `CONVERSION_TYPE`, `SOURCE`
- **Date range:** 2018-01-01 to 2025-12-29 (8 currencies × ~2,920 trading days)
- **Good template:** Daily time-series with date PK, rate value, source/type metadata. Our commodity price table should follow this pattern.

### `tmf_enterprise.project` (10K rows) — FK Target for Retirement Projects
- **PK range:** 10001–20000 (LONG)
- **Use case:** Scrap copper recovery is linked to retirement projects. Not all projects are copper retirement — generator should sample a subset.

### `tmf_enterprise.work` (100K rows) — Decommission Work Orders
- **Decommission type:** 11,159 work orders with `type = 'decommission'`
- **Work ID range:** 10002–109999
- **Party IDs:** 1,111 distinct contractors on decommission work
- **Geographic address FK:** 100% match to `geographic_address`
- **Use case:** Each scrap recovery event originates from a decommission work order. ~5K recovery records (subset of 11K decommission WOs — not every decommission yields recoverable copper).

### `tmf_enterprise.physical_device` — Copper Devices Being Retired
- **Copper-relevant:** CPE (688), ONT (663), OLT (661), patch_panel (660) = 2,672 devices
- **ID range:** 10004–19996
- **Use case:** Recovered copper weight correlates with device type (patch_panel > CPE in cable plant terms). Device linkage is via work order, not direct FK.

### `tmf_resource.stock_item` (10K rows) — Inventory Pattern Reference
- **Schema pattern:** `item_category` (CABLE_AND_CONNECTIVITY, PASSIVE_EQUIPMENT, etc.), `unit_cost` (DECIMAL(18,2)), `weight_kg` (DECIMAL(18,2)), `condition`, `status`
- **Categories relevant:** CABLE_AND_CONNECTIVITY (2,040), PASSIVE_EQUIPMENT (2,020) — these categories inform copper scrap material types
- **Use case:** Schema pattern for material tracking (inverse of stock — scrap out vs stock in)

### `tmf_shared.geographic_site` (10K rows)
- **site_type:** Random hashes (unusable). Use as geographic reference only.
- **Use case:** Scrap copper is aggregated at CO/site level for bulk sale.

### Catalog Check: No Existing Commodity Tables
- Searched `cdm_tmforum.information_schema.tables` for `%commod%`, `%copper_price%`, `%lme%`, `%scrap%`, `%recovered%` — **zero matches**. Gap confirmed.

---

## Real-World Domain Research: LME Copper Pricing

LME (London Metal Exchange) copper is the global benchmark for copper pricing:

- **Unit:** USD per metric ton (MT)
- **Historical range (2018–2026):**
  - 2018: ~$5,800–$7,300/MT
  - 2019: ~$5,500–$6,600/MT (trade war dip)
  - 2020: ~$4,600–$7,900/MT (COVID crash + recovery)
  - 2021: ~$7,800–$10,700/MT (post-COVID supply crunch)
  - 2022: ~$7,000–$10,700/MT (volatile, inflation)
  - 2023: ~$7,900–$9,400/MT (range-bound)
  - 2024: ~$8,000–$10,200/MT (energy transition demand)
  - 2025–2026: ~$8,500–$11,500/MT (projected, green demand + supply constraints)
- **Typical daily volatility:** ±0.5–2.0% daily moves
- **3-month forward vs spot:** Typically contango (forward > spot by $20–$150), occasionally backwardation during supply squeezes
- **15-month forward:** Extends the contango curve, typically $50–$300 above spot
- **Trading days per year:** ~252 (Mon–Fri excluding UK bank holidays)

### Scrap Copper Grades & Pricing
- **Bare Bright (#1 Bare):** 90–95% of LME spot (highest grade, stripped bright copper wire)
- **#1 Copper:** 85–92% of LME spot (clean, unalloyed, uncoated)
- **#2 Copper:** 75–85% of LME spot (solder-coated, with some oxidation)
- **Insulated Wire:** 40–65% of LME spot (needs stripping, copper content varies by gauge)
- **Telecom Cable (mixed):** 50–70% of LME spot (mixed copper/aluminum, plastic jacketing)
- **Typical telco scrap mix:** ~15% bare bright, ~30% #1, ~35% #2, ~20% insulated/telecom cable

---

## Synthetic Table 1: `copper_commodity_price`

**Target catalog/schema:** `cdm_tmforum.refinitiv_fx_source` (alongside gl_daily_rates — same source schema for market data)
**Recommended row count:** ~6,000 records (3 price types × ~2,000 trading days for 2018-01-02 through 2025-12-29)
**Determinism:** Follow `synthetic_assets.py` pattern — `random.Random(seed)`, no wall-clock or network calls.

| Column | Type | Description | Value Range / FK |
|---|---|---|---|
| `price_id` | LONG | PK, synthetic sequence | 400001+ (avoids collision with other synthetic PKs) |
| `price_date` | DATE | Trading day | 2018-01-02 to 2025-12-29. ~252 trading days/year (exclude weekends + ~8 UK bank holidays/year). |
| `price_type` | STRING | Instrument type | {`lme_spot`, `lme_3m_forward`, `lme_15m_forward`} |
| `price_usd_per_mt` | DECIMAL(10,2) | Price in USD per metric ton | LME spot: realistic walk with regime shifts (see generation notes below). 3M forward: spot + contango spread ($20–$150, occasionally negative). 15M forward: spot + extended spread ($50–$300). |
| `open_price` | DECIMAL(10,2) | Session open price | Spot ± 0.3% random jitter |
| `high_price` | DECIMAL(10,2) | Session high | MAX(open, close) + abs(normal(0, 0.5%)) |
| `low_price` | DECIMAL(10,2) | Session low | MIN(open, close) - abs(normal(0, 0.5%)) |
| `close_price` | DECIMAL(10,2) | Session close (= `price_usd_per_mt`) | Same as `price_usd_per_mt` |
| `volume_lots` | INT | Trading volume in lots (25MT each) | 5,000–25,000. Log-normal with weekly seasonality (Mon higher, Fri lower). |
| `open_interest` | INT | Open interest (contracts outstanding) | 200,000–400,000. Mean-reverting random walk. |
| `daily_change_pct` | DECIMAL(6,4) | Daily % change | Computed: (close - prev_close) / prev_close × 100 |
| `volatility_20d` | DECIMAL(6,4) | 20-day rolling annualized volatility | Computed: stdev(daily_returns, 20) × sqrt(252) × 100. Typical range 10–35%. |
| `currency` | STRING | Price currency | Always `USD` |
| `unit` | STRING | Price unit | Always `metric_ton` |
| `exchange` | STRING | Exchange identifier | Always `LME` |
| `source` | STRING | Data source identifier | `refinitiv_metals` (consistent with gl_daily_rates.SOURCE vocabulary) |
| `created_timestamp` | TIMESTAMP | Record creation time | `price_date` + random time 16:00–18:00 UTC (LME close) |

### Price Generation Algorithm
```
Base regime (annual mid-prices):
  2018: $6,500  |  2019: $6,000  |  2020: $6,200 (V-shape)
  2021: $9,300  |  2022: $8,800  |  2023: $8,500
  2024: $9,200  |  2025: $10,000

Daily walk:
  1. Start at regime base for Jan 2 of each year
  2. daily_return = normal(mu=0.0001, sigma=0.015) + mean_reversion_toward_regime_midpoint
  3. Apply ±2% clamp per day
  4. COVID dip: multiply by 0.75 ramp during Mar-Apr 2020, recover by Jul 2020
  5. Contango spread for forwards: 3M = spot × (1 + uniform(0.002, 0.015))
     15M = spot × (1 + uniform(0.005, 0.030))
  6. 5% chance of backwardation day (spread negative, clamped to -0.5%)
```

---

## Synthetic Table 2: `recovered_copper_tracking`

**Target catalog/schema:** `cdm_tmforum.tmf_resource` (resource domain — recovered materials from decommissioned resources)
**Recommended row count:** 5,000 records (subset of 11K decommission work orders — ~45% yield recoverable copper)
**Determinism:** Follow `synthetic_assets.py` pattern — `random.Random(seed)`, no wall-clock or network calls.

| Column | Type | Description | Value Range / FK |
|---|---|---|---|
| `recovery_id` | LONG | PK, synthetic sequence | 500001+ (avoids collision) |
| `work_id` | LONG | FK → `tmf_enterprise.work.work_id` (decommission type only) | Sample 5K from 11,159 decommission work_ids (type='decommission'). No duplicates — one recovery record per work order. |
| `project_id` | LONG | FK → `tmf_enterprise.project.project_id` | Sample from 10001–20000. Multiple recovery events per project. |
| `geographic_site_id` | LONG | FK → `tmf_shared.geographic_site.geographic_site_id` | Inherit via `work.geographic_address_id` → `geographic_address.geographic_site_id`. Scrap aggregated at site (CO/cabinet). |
| `geographic_address_id` | LONG | FK → `tmf_shared.geographic_address.geographic_address_id` | Inherit from `work.geographic_address_id` (100% valid FK). |
| `contractor_bp_agreement_id` | LONG | FK → `tmf_businesspartner.bp_agreement.bp_agreement_id` | Look up via `work.party_id` → `bp_agreement.party_id` (67.3% match). NULL for unmatched (set-aside for internal crews). |
| `recovery_date` | DATE | Date copper was recovered/weighed | Same as or 1–14 days after work order date. Range: 2018-01-15 to 2025-12-15. |
| `copper_grade` | STRING | Scrap grade classification | {`bare_bright`, `copper_1`, `copper_2`, `insulated_wire`, `telecom_cable`}. Weighted: bare_bright 15%, copper_1 30%, copper_2 35%, insulated_wire 12%, telecom_cable 8%. |
| `gross_weight_kg` | DECIMAL(10,2) | Total weight of recovered material (including non-copper) | 5.0–2,500.0 kg. Log-normal, median ~120 kg. Correlated with copper_grade: telecom_cable → heavier (includes jacket), bare_bright → lighter (pure copper). |
| `copper_content_pct` | DECIMAL(5,2) | Estimated pure copper % of gross weight | bare_bright: 99.0–99.9%, copper_1: 92.0–98.0%, copper_2: 80.0–92.0%, insulated_wire: 55.0–75.0%, telecom_cable: 40.0–65.0%. |
| `net_copper_weight_kg` | DECIMAL(10,2) | Pure copper weight | Computed: `gross_weight_kg × copper_content_pct / 100` |
| `lme_spot_price_usd_per_mt` | DECIMAL(10,2) | LME spot price on recovery_date | Look up from `copper_commodity_price` table (or generate inline using same regime). |
| `scrap_discount_pct` | DECIMAL(5,2) | Discount from LME spot for this grade | bare_bright: 5–10%, copper_1: 8–15%, copper_2: 15–25%, insulated_wire: 35–60%, telecom_cable: 30–50%. |
| `realized_price_usd_per_mt` | DECIMAL(10,2) | Actual sale price per metric ton | Computed: `lme_spot_price_usd_per_mt × (1 - scrap_discount_pct / 100)` |
| `recovery_value_usd` | DECIMAL(10,2) | Total dollar value of recovered copper | Computed: `net_copper_weight_kg / 1000 × realized_price_usd_per_mt` |
| `processing_cost_usd` | DECIMAL(10,2) | Cost to strip/sort/transport scrap | 50.0–500.0. Correlated with gross_weight and grade (insulated → higher processing cost). |
| `net_recovery_value_usd` | DECIMAL(10,2) | Net value after processing | Computed: `recovery_value_usd - processing_cost_usd` |
| `cable_type` | STRING | Type of cable/plant recovered | {`aerial_copper`, `buried_copper`, `building_copper`, `drop_wire`, `trunk_cable`, `distribution_cable`}. Correlated with copper_grade. |
| `cable_gauge_awg` | INT | Wire gauge of recovered copper | {19, 22, 24, 26}. Weighted: 24 gauge (40%), 22 gauge (30%), 26 gauge (20%), 19 gauge (10%). Consistent with SPEC_copper_loop_plant. |
| `segment_length_meters` | DECIMAL(8,1) | Length of cable segment recovered | 10.0–5,000.0. Log-normal, median ~200m. Aerial → shorter, trunk → longer. |
| `moisture_contamination` | BOOLEAN | Whether copper showed moisture damage | ~15% true. Correlated with `buried_copper` cable_type (30% for buried, 5% for aerial). |
| `recycler_name` | STRING | Scrap metal recycler/buyer | Synthetic: 10 recycler names, e.g., "Metro Metals Recycling", "Greenline Copper Recovery", "Atlas Scrap Solutions". |
| `sale_date` | DATE | Date copper was sold to recycler | `recovery_date` + 7–45 days (accumulation + transport time). |
| `batch_number` | STRING | Batch/lot identifier for bulk sale | Format: `RCU-{YYYY}-{site_id}-{seq:04d}`. Groups multiple recoveries into sale batches. |
| `status` | STRING | Recovery lifecycle status | {`recovered`, `weighed`, `graded`, `sold`, `disputed`}. Weighted: sold 65%, graded 15%, weighed 10%, recovered 7%, disputed 3%. |
| `notes` | STRING | Free-text operational notes | Nullable (~30% populated). Synthetic notes about condition, contamination, or special handling. |
| `created_timestamp` | TIMESTAMP | Record creation time | `recovery_date` + random hours 8:00–17:00 local. |

### Key Relationships
```
copper_commodity_price.price_date  ←→  recovered_copper_tracking.recovery_date  (date lookup)
recovered_copper_tracking.work_id  →  tmf_enterprise.work.work_id  (decommission WOs only)
recovered_copper_tracking.project_id  →  tmf_enterprise.project.project_id
recovered_copper_tracking.geographic_site_id  →  tmf_shared.geographic_site.geographic_site_id
recovered_copper_tracking.geographic_address_id  →  tmf_shared.geographic_address.geographic_address_id
recovered_copper_tracking.contractor_bp_agreement_id  →  tmf_businesspartner.bp_agreement.bp_agreement_id
```

### Expected Aggregates (for validation)
- **Total recovered copper:** ~5K records × median 120kg × median 85% copper = ~510 MT over 8 years
- **Annual recovery:** ~64 MT/year (realistic for a mid-size telco decommission program)
- **Total recovery value:** ~510 MT × ~$8,000/MT × ~80% realized = ~$3.3M total, ~$410K/year
- **Net after processing:** ~$2.8M total (~85% margin on scrap value)
- **Grade distribution value:** bare_bright dominates value (high price), telecom_cable dominates weight (low copper content)

---

## Dependencies & Blockers

1. **FIX-COORDINATES must be run first** — `geographic_address` lat/lon needed for site-level geographic aggregation of scrap recovery. Generator can work without this (uses FK IDs), but downstream analytics need valid coordinates.
2. **copper_commodity_price generates first** — `recovered_copper_tracking.lme_spot_price_usd_per_mt` looks up from the price table by date. Generator can use inline price regime as fallback.
3. **No LME API key needed for synthetic data** — P1-COMMODITY (real API ingestion) is a separate task. This spec produces realistic synthetic data that the P4-COMMODITY forecaster can train on.
4. **Consistent with SPEC_copper_loop_plant** — `cable_gauge_awg` values (19, 22, 24, 26) and cable types match the copper loop plant spec.

## Feeds
- **P4-COMMODITY** — Price forecaster trains on `copper_commodity_price` time series (GBT/Prophet, 3–18mo horizon)
- **P3-DLP gold** — `commodity_price_features` gold table aggregates price history + forward curve spreads
- **P7-PLAN** — Scrap revenue offsets retirement cost in wave planning optimizer (P4-SEQ)
- **P3-DLP gold** — `gold_circuit_revenue_at_risk` can incorporate scrap recovery value as offset
- **Dashboard** — P4-COMMODITY dashboard shows price trends, recovery volumes, net scrap value by site/grade