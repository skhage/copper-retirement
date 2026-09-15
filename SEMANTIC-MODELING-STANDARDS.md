# Semantic Modeling Standards — Lakelink Fiber Copper Retirement

> **Owner:** @data-planner | **Enforced by:** @qa | **Executed by:** @data-engineer, @data-analyst
> **Catalog:** `cdm_tmforum` | **Primary schema:** `copper_retirement`
> **Created:** 2026-09-15 | **CEO Directive:** Semantic Modeling Mandate (2026-09-14)

---

## 1. Table-Level Description Template

Every table MUST have a `COMMENT ON TABLE` that follows this structure:

```
<Layer> layer: <One-sentence purpose>. <Grain statement>. <Source lineage>. <Refresh frequency>.
```

**Fields:**

| Field | Required | Description | Example |
|---|---|---|---|
| Layer | Yes (if applicable) | Bronze / Silver / Gold / Feature / Source | `Gold layer:` |
| Purpose | Yes | What the table represents in 1 sentence | `Per-wire-center retirement readiness scorecard` |
| Grain | Yes | What one row represents | `One row per wire_center_id` |
| Source lineage | Yes | Upstream table(s) or system | `Sources: silver_copper_plant_enriched, silver_device_service_impact` |
| Refresh frequency | Recommended | How often data is updated | `Refreshed via DLP pipeline on schedule` |

**Example:**
```sql
COMMENT ON TABLE cdm_tmforum.copper_retirement.gold_wire_center_scorecard IS
'Gold layer: per-wire-center retirement readiness scorecard combining device risk, customer impact, and fiber capacity. One row per wire_center_id. Sources: silver_copper_plant_enriched, silver_device_service_impact, silver_resource_capacity. Refreshed via DLP pipeline.';
```

**Special table types:**
- **Metric views:** `Metric view: <KPI name> — <what it measures>. <Dimensions>. <Time grain>.`
- **Feature tables:** `ML feature: <feature name> per <entity>. Join path: <join logic>. Sources: <tables>.`
- **Source tables:** `Source: <system name> <entity>. Ingested from <source system>. <Row count context>.`
- **DLP materialization tables:** Inherit the description from the parent MV/ST. Prefix with `[DLP materialization]`.

---

## 2. Column-Level Description Template

Every column MUST have a `COMMENT ON COLUMN` that follows this structure:

```
<Business meaning>. <Unit/format if applicable>. <Valid range or enum values if applicable>. <FK reference if applicable>.
```

**Rules:**

| Rule | Detail |
|---|---|
| Business meaning | Required. Plain-English explanation of what the column represents. |
| Unit/format | Required for numeric, date, and coded columns. E.g., `USD`, `meters`, `ISO 8601`, `H3 resolution 8`. |
| Valid range | Recommended for numeric columns. E.g., `Range: 0.0–1.0`, `Non-negative`. |
| Enum values | Required for categorical columns with known values. E.g., `Values: low, medium, high, critical`. |
| FK reference | Required when column is a foreign key. E.g., `FK → tmf_customer.customer.customer_id`. |
| Derived/computed | Note if column is computed. E.g., `Computed: alarm_count / days_in_service`. |

**Example:**
```sql
COMMENT ON COLUMN cdm_tmforum.copper_retirement.gold_device_risk_predictions.risk_tier IS
'Predicted risk tier for copper device retirement urgency. Values: low, medium, high, critical. Assigned by V5 GBT model based on alarm rate, age, SLA breaches, and plant condition.';

COMMENT ON COLUMN cdm_tmforum.copper_retirement.gold_device_risk_predictions.composite_risk_score IS
'Weighted composite risk score combining model probability and operational factors. Range: 0.0–1.0 (higher = more urgent). Computed from risk_prob_critical * 0.4 + risk_prob_high * 0.3 + normalized alarm rate * 0.3.';

COMMENT ON COLUMN cdm_tmforum.copper_retirement.silver_copper_plant_enriched.physical_device_id IS
'Unique identifier for the physical network device. FK → tmf_enterprise.physical_device.physical_device_id.';
```

**Standard column description patterns:**

| Column pattern | Template |
|---|---|
| `*_id` (PK) | `Unique identifier for <entity>. Primary key.` |
| `*_id` (FK) | `Reference to <parent entity>. FK → <schema.table.column>.` |
| `*_date`, `*_at` | `<Event> timestamp. Format: <format>. Timezone: UTC.` |
| `*_flag`, `is_*` | `Boolean flag indicating <condition>. TRUE when <criteria>.` |
| `*_count` | `Count of <what>. Non-negative integer.` |
| `*_rate` | `<What> rate. <Numerator>/<Denominator>. Range: 0.0–1.0.` |
| `*_score` | `<What> score. Range: <min>–<max>. <Higher/lower> = <meaning>.` |
| `*_pct` | `Percentage of <what>. Range: 0–100.` |
| `*_amount`, `*_cost`, `*_revenue` | `<What> in <currency>. <Aggregation context>.` |
| `h3_res*` | `H3 hexagonal grid cell index at resolution <N>. Used for spatial aggregation.` |
| `state_code` | `US state FIPS or postal code. Values: 2-letter postal abbreviation.` |

---

## 3. Schema-Level Description Standards

Every schema MUST have a `COMMENT ON SCHEMA` describing its domain and role:

```sql
COMMENT ON SCHEMA cdm_tmforum.copper_retirement IS
'Lakelink Fiber copper retirement analytics — bronze/silver/gold medallion layers, ML features, risk predictions, and metric views for the copper-to-fiber migration program.';
```

---

## 4. Naming Conventions

### Table naming
| Layer | Pattern | Example |
|---|---|---|
| Bronze | `bronze_<source_entity>` | `bronze_copper_devices` |
| Silver | `silver_<enriched_entity>` | `silver_copper_plant_enriched` |
| Gold | `gold_<business_entity>` | `gold_wire_center_scorecard` |
| Feature | `feature_<entity>_<feature>` | `feature_device_firmware_age` |
| Source/reference | `<descriptive_name>` | `state_puc_jurisdiction_requirements` |
| Metric view | `copper_<kpi_domain>` | `copper_retirement_project_status` |

### Column naming
- Use `snake_case` exclusively.
- Suffix IDs with `_id` (e.g., `physical_device_id`, `customer_id`).
- Suffix dates/timestamps with `_date` or `_at` (e.g., `created_date`, `updated_at`).
- Suffix booleans with `_flag` or prefix with `is_` / `has_` (e.g., `is_copper_flag`, `has_active_contract`).
- Suffix monetary amounts with `_amount` or `_cost` or `_revenue`.
- Use `_pct` for percentages (0–100), `_rate` for ratios (0.0–1.0), `_score` for model outputs.

---

## 5. UC Pages Structure

Each of the 6 key data domains gets a **Unity Catalog Page** with this standard structure:

### Page template:

```markdown
# <Domain Name>

## Overview
<2-3 sentence business context: what this domain covers in the copper retirement program>

## Key Tables
| Table | Layer | Grain | Description |
|---|---|---|---|
| <full_table_name> | <Bronze/Silver/Gold> | <grain> | <one-liner> |

## Entity Relationships
<Mermaid diagram or text description of how tables join>
- <table_a>.column_x → <table_b>.column_y

## Key Metrics
| Metric | Definition | Metric View |
|---|---|---|
| <metric_name> | <plain-English definition> | <metric_view_table> |

## Data Quality Notes
- <Any known gaps, synthetic data flags, or coverage limitations>

## Related Domains
- Links to related domain pages
```

### The 6 domains and their scope:

1. **Physical Plant** — Copper devices, cable plant, equipment, connections. Core tables: `physical_device`, `copper_loop_plant`, `equipment`, bronze/silver copper device layers.
2. **Circuits & Services** — Customer-facing services, resource-facing services, service orders. Core tables: `customer_facing_service`, `resource_facing_service`, `service_order_item`, bronze/silver/gold service layers.
3. **Customers** — Customer records, churn, billing, complaints, contracts. Core tables: `customer`, `bill`, `churn_retention_statistic`, `commitment`, `customer_problem`.
4. **Risk & ML** — Risk model features, predictions, scorecards. Core tables: `copper_risk_target`, `gold_device_risk_predictions`, `feature_*` tables, `gold_wire_center_scorecard`.
5. **Regulatory** — FCC rules, state PUC requirements, regulatory documents, VS index. Core tables: `state_puc_jurisdiction_requirements`, `regulatory_doc_chunks`, `fcc_*` tables.
6. **Financial** — Revenue at risk, EBITDA forecasts, commodity prices, contractor costs. Core tables: `gold_circuit_revenue_at_risk`, `gold_ebitda_forecast`, `copper_commodity_price`, metric views.

---

## 6. Governed Tag Standard

All copper retirement tables, models, and assets must be tagged with:
- **Tag key:** `telco_project` (NOT the deprecated `project` tag)
- **Tag value:** `copper-retirement`

---

## 7. Priority Order for Description Backfill

1. **P0 — copper_retirement schema** (57 tables, currently 77.1% column coverage → target 100%)
2. **P1 — DLP materialized view tables** (8 MVs + materialization internals)
3. **P2 — TMF schemas used in DLP pipeline** (`tmf_enterprise`, `tmf_service`, `tmf_resource`, `tmf_shared`, `tmf_customer` — all at 0% column descriptions)
4. **P3 — Source schemas** (`oracle_erp_source`, `salesforce_source`, `refinitiv_fx_source`, `ironclad_clm_source`, `mdm_source`)
5. **P4 — Remaining TMF schemas** (`tmf_product`, `tmf_businesspartner`, `tmf_marketsales`)

---

## 8. Baseline Audit Metrics (2026-09-15)

| Metric | Current | Target |
|---|---|---|
| Table descriptions | 96.2% (559/581) | 100% |
| Column descriptions (overall) | 18.3% (2,801/15,297) | ≥80% for P0–P2 |
| Column descriptions (copper_retirement) | 77.1% (897/1,164) | 100% |
| Column descriptions (TMF core schemas) | 0% | ≥50% (P2 priority columns) |
| Schema descriptions | TBD (audit needed) | 100% |
| UC Pages created | 0/6 | 6/6 |
| Metric views with descriptions | 100% (71/71) | 100% (maintain) |

---

## 9. Compliance Checklist (for @qa)

- [ ] Every table in `copper_retirement` has a COMMENT ON TABLE following the template
- [ ] Every column in `copper_retirement` has a COMMENT ON COLUMN following the template
- [ ] All FK columns document their reference target
- [ ] All numeric columns document their unit and range
- [ ] All categorical columns document their valid values
- [ ] All 6 UC Pages exist and follow the template
- [ ] All 4 metric views have complete column descriptions
- [ ] Governed tag `telco_project=copper-retirement` applied to all project tables
