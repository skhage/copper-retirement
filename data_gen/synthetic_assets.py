"""Deterministic synthetic copper-asset generator.

Produces synthetic Lumen-style copper serving-area records for the
copper-retirement demo. All output is SYNTHETIC — it does not represent
real Lumen plant, subscribers, or infrastructure. Every record carries a
``source: "synthetic"`` marker so downstream tables/UI can label it.

Determinism contract: calling ``generate_serving_areas`` twice with the same
``seed`` and ``count`` produces byte-identical output. No wall-clock time,
network calls, or unseeded randomness are used anywhere in this module.
"""

import random

import h3

H3_RESOLUTION = 9

STATE_BOUNDING_BOXES = {
    "AZ": ((32.9, 33.8), (-112.5, -111.6)),
    "CO": ((39.4, 40.3), (-105.4, -104.6)),
    "ID": ((43.1, 44.0), (-116.8, -115.7)),
    "MN": ((44.5, 45.4), (-94.0, -92.8)),
    "OR": ((44.6, 45.6), (-123.5, -122.3)),
    "WA": ((46.8, 47.8), (-122.8, -121.6)),
}

LEGACY_STATES = tuple(STATE_BOUNDING_BOXES)

# Per-state bounding boxes for realistic coordinate generation.
# Each state maps to (lat_min, lat_max, lon_min, lon_max).
# Used to place synthetic points within plausible geographic extents —
# no real addresses or plant locations are derived from these boxes.
STATE_BOUNDS = {
    "CO": (37.00, 41.00, -109.06, -102.04),
    "MN": (43.50, 49.38, -97.24, -89.49),
    "WA": (45.54, 49.00, -124.85, -116.92),
    "OR": (41.99, 46.29, -124.57, -116.46),
    "ID": (42.00, 49.00, -117.24, -111.04),
    "AZ": (31.33, 37.00, -114.81, -109.04),
}

# Full 50-state bounding boxes (used by fix_coordinates notebook and
# any generator that needs to place points across all US states).
STATE_BOUNDS_FULL = {
    "AL": (30.22, 35.01, -88.47, -84.89),
    "AK": (58.0, 64.85, -153.0, -134.0),
    "AZ": (31.33, 37.00, -114.81, -109.04),
    "AR": (33.00, 36.50, -94.62, -89.64),
    "CA": (32.53, 42.01, -124.48, -114.13),
    "CO": (37.00, 41.00, -109.06, -102.04),
    "CT": (40.95, 42.05, -73.73, -71.79),
    "DE": (38.45, 39.84, -75.79, -75.05),
    "FL": (24.52, 31.00, -87.63, -80.03),
    "GA": (30.36, 35.00, -85.61, -80.84),
    "HI": (18.91, 22.24, -160.24, -154.81),
    "ID": (42.00, 49.00, -117.24, -111.04),
    "IL": (36.97, 42.51, -91.51, -87.02),
    "IN": (37.77, 41.76, -88.10, -84.78),
    "IA": (40.38, 43.50, -96.64, -90.14),
    "KS": (36.99, 40.00, -102.05, -94.59),
    "KY": (36.50, 39.15, -89.57, -81.96),
    "LA": (28.93, 33.02, -94.04, -88.82),
    "ME": (43.06, 47.46, -71.08, -66.95),
    "MD": (37.91, 39.72, -79.49, -75.05),
    "MA": (41.24, 42.89, -73.51, -69.93),
    "MI": (41.70, 48.31, -90.42, -82.12),
    "MN": (43.50, 49.38, -97.24, -89.49),
    "MS": (30.17, 35.00, -91.66, -88.10),
    "MO": (36.00, 40.61, -95.77, -89.10),
    "MT": (44.36, 49.00, -116.05, -104.04),
    "NE": (40.00, 43.00, -104.05, -95.31),
    "NV": (35.00, 42.00, -120.01, -114.04),
    "NH": (42.70, 45.31, -72.56, -70.70),
    "NJ": (38.93, 41.36, -75.56, -73.89),
    "NM": (31.33, 37.00, -109.05, -103.00),
    "NY": (40.50, 45.02, -79.76, -71.86),
    "NC": (33.84, 36.59, -84.32, -75.46),
    "ND": (45.94, 49.00, -104.05, -96.56),
    "OH": (38.40, 42.33, -84.82, -80.52),
    "OK": (33.62, 37.00, -103.00, -94.43),
    "OR": (41.99, 46.29, -124.57, -116.46),
    "PA": (39.72, 42.27, -80.52, -74.69),
    "RI": (41.15, 42.02, -71.86, -71.12),
    "SC": (32.03, 35.22, -83.35, -78.54),
    "SD": (42.48, 45.95, -104.06, -96.44),
    "TN": (34.98, 36.68, -90.31, -81.65),
    "TX": (25.84, 36.50, -106.65, -93.51),
    "UT": (37.00, 42.00, -114.05, -109.04),
    "VT": (42.73, 45.02, -73.44, -71.46),
    "VA": (36.54, 39.47, -83.68, -75.24),
    "WA": (45.54, 49.00, -124.85, -116.92),
    "WV": (37.20, 40.64, -82.64, -77.72),
    "WI": (42.49, 47.08, -92.89, -86.25),
    "WY": (41.00, 45.00, -111.06, -104.05),
}

# Backward-compatible defaults (used if caller doesn't specify a state)
LAT_RANGE = STATE_BOUNDS["CO"][:2]  # (37.00, 41.00)
LON_RANGE = STATE_BOUNDS["CO"][2:]  # (-109.06, -102.04)

# Fixed normalization ceilings so scoring stays deterministic and
# reviewable without needing the full generated distribution at hand.
MAX_ACTIVE_COPPER_LINES = 5000
MAX_POTS_ONLY_HOUSEHOLDS = 3000
MAX_RECOVERABLE_COPPER_LBS = 200_000
COPPER_PRICE_USD_PER_LB = 4.35  # fixed reference price, not a live feed
MAX_DIG_INCIDENT_RATE = 5.0
DATASET_VERSION = "2026.09"


class GenerationError(ValueError):
    """Raised when a generator receives an invalid argument."""


def _validate_non_negative_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GenerationError(f"{name} must be a non-negative integer, got {value!r}")


def generate_coords_for_state(rng, state_abbrev):
    """Generate a (lat, lon) tuple within the bounding box for a US state.

    Uses ``STATE_BOUNDS`` for LEGACY_STATES, falls back to
    ``STATE_BOUNDS_FULL`` for all 50 states. Raises ``KeyError`` if the
    abbreviation is unrecognized.
    """
    bounds = STATE_BOUNDS.get(state_abbrev) or STATE_BOUNDS_FULL[state_abbrev]
    lat = round(rng.uniform(bounds[0], bounds[1]), 6)
    lon = round(rng.uniform(bounds[2], bounds[3]), 6)
    return lat, lon


def _make_asset_id(index):
    return f"SA-{index:05d}"


def _sample_serving_area(rng, index):
    state = rng.choice(LEGACY_STATES)
    lat_range, lon_range = STATE_BOUNDING_BOXES[state]
    lat = rng.uniform(*lat_range)
    lon = rng.uniform(*lon_range)
    h3_cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

    active_copper_lines = rng.randint(0, MAX_ACTIVE_COPPER_LINES)
    pots_only_households = rng.randint(0, min(active_copper_lines, MAX_POTS_ONLY_HOUSEHOLDS))
    fiber_overbuild_pct = round(rng.uniform(0.0, 1.0), 3)

    critical_service_flags = {
        "alarm_system": rng.random() < 0.15,
        "medical_monitoring": rng.random() < 0.08,
        "e911_backup": rng.random() < 0.05,
        "fax_or_credit_card": rng.random() < 0.10,
    }

    puc_docket_active = rng.random() < 0.20
    tribal_land_overlap = rng.random() < 0.05

    soil_risk_score = round(rng.uniform(0.0, 1.0), 3)
    permitting_complexity = round(rng.uniform(0.0, 1.0), 3)
    colocated_utilities = rng.randint(0, 3)
    historical_dig_incident_rate = round(rng.uniform(0.0, MAX_DIG_INCIDENT_RATE), 3)

    recoverable_copper_lbs = round(rng.uniform(0.0, MAX_RECOVERABLE_COPPER_LBS), 1)

    return {
        "asset_id": _make_asset_id(index),
        "source": "synthetic",
        "source_system": "simulated_lumen_oss_gis",
        "dataset_version": DATASET_VERSION,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "h3_cell": h3_cell,
        "h3_resolution": H3_RESOLUTION,
        "state": state,
        "active_copper_lines": active_copper_lines,
        "pots_only_households": pots_only_households,
        "fiber_overbuild_pct": fiber_overbuild_pct,
        "critical_service_flags": critical_service_flags,
        "puc_docket_active": puc_docket_active,
        "tribal_land_overlap": tribal_land_overlap,
        "soil_risk_score": soil_risk_score,
        "permitting_complexity": permitting_complexity,
        "colocated_utilities": colocated_utilities,
        "historical_dig_incident_rate": historical_dig_incident_rate,
        "recoverable_copper_lbs": recoverable_copper_lbs,
        "copper_price_usd_per_lb": COPPER_PRICE_USD_PER_LB,
    }


def generate_serving_areas(count=500, seed=42):
    """Generate `count` deterministic synthetic serving-area records.

    Same (count, seed) always yields the same list, in the same order.
    """
    _validate_non_negative_integer(count, "count")
    _validate_non_negative_integer(seed, "seed")
    rng = random.Random(seed)
    records = [_sample_serving_area(rng, i) for i in range(count)]
    for record in records:
        record["generation_seed"] = seed
    return records
