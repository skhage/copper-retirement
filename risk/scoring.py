"""Deterministic copper-retirement risk/readiness scoring.

Implements the composite "retirement readiness score" described in
`resources/zero-copper-plan.md`, as a rule-based (non-ML) function over the
synthetic serving-area records produced by `data_gen.synthetic_assets`. This
is the P0 thin-slice risk path; the Phase 4 GBT classifier is a later,
separate workstream and is not implemented here.

Determinism contract: `score_serving_area` and `score_serving_areas` are pure
functions of their input records — same input always produces the same
output, with no randomness or wall-clock dependence.

Score interpretation:
  - Each dimension score is in [0, 1], where higher means higher risk.
  - `risk_score` is the weighted composite of the five dimensions below.
  - `readiness_score = 1 - risk_score`: higher means safer/more ready to
    retire first, per the "low-risk first" Wave 1 guidance.
  - `wave` buckets `readiness_score` into the three milestone waves from
    zero-copper-plan.md.

Input validation contract: every numeric/monetary field consumed by scoring
must be a finite, non-negative real number. Malformed values (wrong type,
negative, NaN, or infinite) raise `ScoringError` naming the offending asset
and field, rather than crashing with a raw `TypeError`/`ValueError`/
`ZeroDivisionError`. An empty `critical_service_flags` mapping is a valid
input (zero critical-service overlap), not an error.
"""

import math

from data_gen.synthetic_assets import (
    MAX_DIG_INCIDENT_RATE,
    MAX_ACTIVE_COPPER_LINES,
    MAX_POTS_ONLY_HOUSEHOLDS,
)

# Weights sum to 1.0; tuned to reflect zero-copper-plan.md's emphasis on
# subscriber impact and critical-service overlap over pure dig logistics.
DIMENSION_WEIGHTS = {
    "subscriber_dependency": 0.30,
    "critical_service_overlap": 0.25,
    "fiber_alternative_gap": 0.15,
    "regulatory_friction": 0.15,
    "physical_dig_risk": 0.15,
}

WAVE_THRESHOLDS = (
    ("wave_1", 0.66),  # readiness_score >= 0.66
    ("wave_2", 0.33),  # 0.33 <= readiness_score < 0.66
)
DEFAULT_WAVE = "wave_3"

# Numeric fields consumed by scoring arithmetic, validated as finite and
# non-negative before use. Values above the natural [0, 1] range for
# fractional fields are still clamped downstream by `_clamp01` rather than
# rejected, matching prior tolerant behavior for the upper bound.
_REQUIRED_NUMERIC_FIELDS = (
    "active_copper_lines",
    "pots_only_households",
    "fiber_overbuild_pct",
    "soil_risk_score",
    "permitting_complexity",
    "colocated_utilities",
    "historical_dig_incident_rate",
    "recoverable_copper_lbs",
    "copper_price_usd_per_lb",
)


class ScoringError(ValueError):
    """Raised when a serving-area record fails scoring input validation."""


def _clamp01(x):
    return max(0.0, min(1.0, x))


def _asset_label(asset):
    asset_id = asset.get("asset_id") if isinstance(asset, dict) else None
    return str(asset_id) if asset_id is not None else "<unknown asset>"


def _require_finite_nonnegative(asset, field_name):
    if field_name not in asset:
        raise ScoringError(
            f"asset {_asset_label(asset)} is missing required field {field_name!r}"
        )
    value = asset[field_name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScoringError(
            f"asset {_asset_label(asset)} field {field_name!r} must be a "
            f"finite non-negative number, got {value!r}"
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise ScoringError(
            f"asset {_asset_label(asset)} field {field_name!r} must be finite, "
            f"got {value!r}"
        )
    if value < 0:
        raise ScoringError(
            f"asset {_asset_label(asset)} field {field_name!r} must be "
            f"non-negative, got {value!r}"
        )
    return value


def _validate_asset(asset):
    if not isinstance(asset, dict):
        raise ScoringError(f"asset must be a dict, got {type(asset).__name__}")

    for field_name in _REQUIRED_NUMERIC_FIELDS:
        _require_finite_nonnegative(asset, field_name)

    flags = asset.get("critical_service_flags")
    if not isinstance(flags, dict):
        raise ScoringError(
            f"asset {_asset_label(asset)} field 'critical_service_flags' "
            f"must be a dict, got {type(flags).__name__}"
        )


def _subscriber_dependency_score(asset):
    lines_component = asset["active_copper_lines"] / MAX_ACTIVE_COPPER_LINES
    pots_component = asset["pots_only_households"] / MAX_POTS_ONLY_HOUSEHOLDS
    return _clamp01((lines_component + pots_component) / 2)


def _critical_service_score(asset):
    flags = asset["critical_service_flags"]
    if not flags:
        # No flags to check means no observed critical-service overlap, not
        # an undefined (division-by-zero) result.
        return 0.0
    return sum(1 for v in flags.values() if v) / len(flags)


def _fiber_alternative_gap_score(asset):
    # Fiber/FWA overbuild reduces risk; gap is the complement.
    return _clamp01(1 - asset["fiber_overbuild_pct"])


def _regulatory_friction_score(asset):
    score = 0.0
    if asset["puc_docket_active"]:
        score += 0.6
    if asset["tribal_land_overlap"]:
        score += 0.4
    return _clamp01(score)


def _physical_dig_risk_score(asset):
    incident_component = asset["historical_dig_incident_rate"] / MAX_DIG_INCIDENT_RATE
    utilities_component = asset["colocated_utilities"] / 3
    components = [
        asset["soil_risk_score"],
        asset["permitting_complexity"],
        _clamp01(utilities_component),
        _clamp01(incident_component),
    ]
    return _clamp01(sum(components) / len(components))


def _wave_for_readiness(readiness_score):
    for wave, threshold in WAVE_THRESHOLDS:
        if readiness_score >= threshold:
            return wave
    return DEFAULT_WAVE


def score_serving_area(asset):
    """Score a single synthetic serving-area record.

    Returns a dict with per-dimension scores, the composite `risk_score`,
    `readiness_score`, `wave` bucket, and `commercial_value_usd`.

    Raises `ScoringError` if `asset` is missing a required field or any
    numeric/monetary field is malformed, negative, NaN, or infinite.
    """
    _validate_asset(asset)

    dimension_scores = {
        "subscriber_dependency": _subscriber_dependency_score(asset),
        "critical_service_overlap": _critical_service_score(asset),
        "fiber_alternative_gap": _fiber_alternative_gap_score(asset),
        "regulatory_friction": _regulatory_friction_score(asset),
        "physical_dig_risk": _physical_dig_risk_score(asset),
    }

    risk_score_raw = _clamp01(
        sum(
            dimension_scores[dimension] * weight
            for dimension, weight in DIMENSION_WEIGHTS.items()
        )
    )
    readiness_score_raw = 1 - risk_score_raw

    # Wave classification uses full-precision readiness so boundary values
    # (e.g. exactly 0.66) are never nudged across a threshold by the display
    # rounding applied below.
    wave = _wave_for_readiness(readiness_score_raw)

    risk_score = round(risk_score_raw, 6)
    # Derive from the already-rounded risk_score (not readiness_score_raw)
    # so risk_score + readiness_score always sums to exactly 1.0 after
    # rounding, matching the documented complement invariant.
    readiness_score = round(1 - risk_score, 6)

    commercial_value_usd = round(
        asset["recoverable_copper_lbs"] * asset["copper_price_usd_per_lb"], 2
    )

    return {
        "asset_id": asset["asset_id"],
        "h3_cell": asset["h3_cell"],
        "h3_resolution": asset["h3_resolution"],
        "dimension_scores": {k: round(v, 6) for k, v in dimension_scores.items()},
        "risk_score": risk_score,
        "readiness_score": readiness_score,
        "wave": wave,
        "commercial_value_usd": commercial_value_usd,
    }


def score_serving_areas(assets):
    """Score a list of synthetic serving-area records, preserving order."""
    return [score_serving_area(asset) for asset in assets]
