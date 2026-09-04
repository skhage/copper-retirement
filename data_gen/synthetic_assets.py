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

# Bounding box roughly covering legacy CenturyLink/Qwest Colorado Front Range
# territory. Used only to place synthetic points on a plausible map extent —
# no real addresses or plant locations are derived from this box.
LAT_RANGE = (39.4, 40.3)
LON_RANGE = (-105.4, -104.6)

LEGACY_STATES = ["CO", "MN", "WA", "OR", "ID", "AZ"]

# Fixed normalization ceilings so scoring stays deterministic and
# reviewable without needing the full generated distribution at hand.
MAX_ACTIVE_COPPER_LINES = 5000
MAX_POTS_ONLY_HOUSEHOLDS = 3000
MAX_RECOVERABLE_COPPER_LBS = 200_000
COPPER_PRICE_USD_PER_LB = 4.35  # fixed reference price, not a live feed
MAX_DIG_INCIDENT_RATE = 5.0


def _make_asset_id(index):
    return f"SA-{index:05d}"


def _sample_serving_area(rng, index):
    lat = rng.uniform(*LAT_RANGE)
    lon = rng.uniform(*LON_RANGE)
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

    state = rng.choice(LEGACY_STATES)
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
    rng = random.Random(seed)
    return [_sample_serving_area(rng, i) for i in range(count)]
