# Copper Retirement

A deterministic Databricks demo for prioritizing retirement of legacy copper serving areas.

The current thin slice generates clearly labeled synthetic serving-area records, scores retirement risk and readiness, assigns migration waves, estimates recoverable-copper value, and defines the initial Unity Catalog layout for later data, ML, operational, and agent workloads.

> **Data safety:** This repository does not contain real customer, subscriber, plant, address, or infrastructure data. Generated records carry `source: "synthetic"`. The copper price is a fixed demo constant, not a live market feed.

## What Works Today

- Deterministic synthetic serving-area generation using seeded randomness.
- H3 resolution 9 indexing for each generated location.
- Rule-based risk and readiness scoring across five dimensions.
- Wave assignment for low-risk-first retirement sequencing.
- Recoverable-copper commercial value calculation.
- A local command-line thin-slice demonstration.
- Databricks Asset Bundle resources for a catalog and six schemas.
- Automated tests for determinism, invariants, score bounds, wave ordering, and commercial-value calculations.

The broader architecture in `BUILD-PLAN.md` and `resources/` is a roadmap. Ingestion pipelines, production tables, ML models, Lakebase workflows, agents, and Databricks Apps are not implemented yet.

## Quick Start

### Prerequisites

- Python 3.12 is the currently tested interpreter.
- [`uv`](https://docs.astral.sh/uv/) is recommended for isolated local execution.
- Databricks CLI authentication is required only for bundle validation or deployment.

### Run the thin slice

```bash
uv run --with-requirements requirements.txt python scripts/run_thin_slice.py 500 42
```

Arguments are optional:

```text
python scripts/run_thin_slice.py [count] [seed]
```

- `count` defaults to `500`.
- `seed` defaults to `42`.
- The same `count` and `seed` produce the same records and scores.
- Use a positive integer count. The current script does not gracefully handle zero, negative, or malformed values.

The command prints the generated count, wave distribution, total estimated commercial value, and one scored sample.

### Run tests

```bash
uv run --with-requirements requirements.txt python -m pytest -q
```

The current suite collects 16 tests.

### Compile-check Python files

```bash
uv run --with-requirements requirements.txt python -m compileall -q data_gen risk scripts tests
```

## How the Thin Slice Works

```text
seed + count
    |
    v
data_gen.synthetic_assets.generate_serving_areas
    |  synthetic attributes + H3 cell
    v
risk.scoring.score_serving_areas
    |  dimension scores + risk/readiness + wave + value
    v
scripts/run_thin_slice.py summary
```

### Synthetic record contract

`generate_serving_areas(count, seed)` returns an ordered list of dictionaries. Important fields include:

| Field | Meaning |
|---|---|
| `asset_id` | Stable synthetic identifier such as `SA-00042` |
| `source` | Always `synthetic` |
| `latitude`, `longitude` | Synthetic point in the configured demo bounding box |
| `h3_cell`, `h3_resolution` | H3 spatial index and resolution |
| `active_copper_lines` | Synthetic active-line count |
| `pots_only_households` | Synthetic POTS-only household count, never above active lines |
| `fiber_overbuild_pct` | Synthetic alternative-coverage fraction from 0 to 1 |
| `critical_service_flags` | Alarm, medical monitoring, E911 backup, and fax/card flags |
| `puc_docket_active`, `tribal_land_overlap` | Synthetic regulatory-friction indicators |
| `soil_risk_score`, `permitting_complexity` | Synthetic excavation-risk inputs |
| `colocated_utilities` | Synthetic count from 0 to 3 |
| `historical_dig_incident_rate` | Synthetic normalized incident input |
| `recoverable_copper_lbs` | Synthetic recoverable copper estimate |
| `copper_price_usd_per_lb` | Fixed demo price used for value calculation |

Calling the generator twice with the same `count` and `seed` is expected to return identical output in identical order.

### Scoring model

Each dimension produces a risk score from `0` to `1`, where a larger number means greater retirement risk.

| Dimension | Weight | Inputs |
|---|---:|---|
| Subscriber dependency | 30% | Active copper lines and POTS-only households |
| Critical-service overlap | 25% | Critical-service flags |
| Fiber alternative gap | 15% | Complement of fiber overbuild |
| Regulatory friction | 15% | Active PUC docket and tribal-land overlap |
| Physical dig risk | 15% | Soil, permitting, colocated utilities, and incident rate |

The composite calculations are:

```text
risk_score = weighted sum of dimension risk scores
readiness_score = 1 - risk_score
commercial_value_usd = recoverable_copper_lbs * copper_price_usd_per_lb
```

Wave classification uses readiness:

| Wave | Readiness | Interpretation |
|---|---:|---|
| `wave_1` | `>= 0.66` | Earliest retirement candidates |
| `wave_2` | `>= 0.33` and `< 0.66` | Intermediate candidates |
| `wave_3` | `< 0.33` | Higher-risk or later candidates |

This is a transparent rule-based baseline, not a trained ML model or a production decision system.

## Databricks Bundle

`databricks.yml` defines the `copper_retirement` bundle and includes resources from `bundle/resources/`.

The default catalog is `lumen_copper`, with these schemas:

| Schema | Intended use |
|---|---|
| `bronze` | Raw landed synthetic and public-source data |
| `silver` | Cleaned, conformed, H3-indexed data |
| `gold` | Business-ready retirement and market features |
| `ml` | Training data, features, and model metadata |
| `ops` | Operational planning, incidents, and assignments |
| `agents` | Agent definitions, evaluations, and traces |

Validate the bundle without deploying:

```bash
databricks bundle validate -t dev
```

Inspect the proposed changes:

```bash
databricks bundle plan -t dev
```

The `dev` target currently names a specific demo workspace host. Change it before using another workspace. Do not deploy until the authenticated Databricks profile and target catalog have been confirmed.

## Repository Map

| Path | Purpose |
|---|---|
| `data_gen/synthetic_assets.py` | Deterministic synthetic serving-area generator and demo constants |
| `risk/scoring.py` | Rule-based dimension, composite, wave, and value scoring |
| `scripts/run_thin_slice.py` | Local end-to-end smoke command |
| `tests/` | Generator and scoring tests |
| `databricks.yml` | Bundle entry point and target configuration |
| `bundle/resources/unity_catalog.yml` | Catalog and schema resources |
| `BUILD-PLAN.md` | Phased implementation plan and delivery expectations |
| `resources/00-master-architecture.md` | System narrative and component map |
| `resources/zero-copper-plan.md` | Prioritization and wave-planning rationale |
| `resources/technical-reference.md` | Databricks component design reference |
| `resources/commodity-workforce.md` | Commodity and contractor planning reference |
| `resources/dig-safe-triage.md` | Incident-routing and dig-safe reference |
| `resources/regulatory-jurisdictions.md` | Regulatory workflow reference |

## Guidance for Code Agents

### Read first

1. Read this README for the executable scope and commands.
2. Read `BUILD-PLAN.md` before implementing a new phase.
3. Read the relevant file in `resources/` for domain intent.
4. Inspect the adjacent tests before changing behavior.
5. Keep changes scoped to one independently reviewable outcome.

### Preserve these invariants

- All demo-generated records remain explicitly labeled `source: "synthetic"`.
- Generation remains deterministic for the same `count` and `seed`.
- No wall-clock time, network calls, or unseeded randomness enters generation or scoring.
- H3 cells remain valid and match the declared resolution.
- `pots_only_households` never exceeds `active_copper_lines`.
- Dimension, risk, and readiness scores remain in `[0, 1]`.
- Dimension weights sum to `1.0`.
- Readiness remains the complement of risk unless the documented scoring contract changes.
- Output ordering matches input ordering.
- Monetary values use explicit units and deterministic reference prices.
- Real telco/customer data must not be introduced into the repository.

### Validation matrix

| Changed area | Minimum validation |
|---|---|
| `data_gen/` | Generator tests plus full test suite |
| `risk/` | Scoring tests plus hand-calculated boundary fixtures |
| `scripts/` | Full test suite and direct CLI smoke run |
| `databricks.yml`, `bundle/` | `databricks bundle validate -t dev` and inspect `bundle plan` |
| Documentation only | Verify paths, commands, terminology, and implemented-vs-roadmap claims |

Always run the full local gate before proposing a code change:

```bash
uv run --with-requirements requirements.txt python -m pytest -q
uv run --with-requirements requirements.txt python -m compileall -q data_gen risk scripts tests
```

### Known engineering gaps

As of September 5, 2026, contributors should account for these limitations:

- Public generator and scoring functions assume well-formed dictionaries and numeric values; malformed inputs are not validated consistently.
- Empty `critical_service_flags` causes division by zero.
- Non-finite numbers can produce misleading score or monetary results.
- The CLI exposes raw Python errors for malformed arguments and crashes when no records are generated.
- Synthetic state labels are independent of coordinates, which are sampled from a Colorado Front Range bounding box.
- `requirements.txt` pins direct dependencies, but the current `uv.lock` does not lock the project dependency graph because `pyproject.toml` has no project dependency metadata.
- Tests cover generated happy paths well but need hand-calculated scoring fixtures, exact wave-threshold cases, malformed inputs, and CLI boundary behavior.

Agents should fix these at the source and add focused regression tests rather than documenting around them.

## Design References

- Start with `resources/00-master-architecture.md` for the complete demo story.
- Use `resources/zero-copper-plan.md` when changing prioritization, scoring, or waves.
- Use `resources/technical-reference.md` when adding Databricks workloads.
- Treat `BUILD-PLAN.md` as sequencing guidance, not proof that a phase is implemented.

## Project Status

This repository is an early deterministic foundation for a larger copper-retirement demonstration. It is suitable for local exploration and continued development, but it is not production software and must not be used for real retirement, regulatory, safety, or customer-impact decisions without validated source data, domain review, and production controls.
