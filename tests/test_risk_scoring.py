import math

import pytest

from data_gen.synthetic_assets import generate_serving_areas
from risk.scoring import (
    DIMENSION_WEIGHTS,
    ScoringError,
    score_serving_area,
    score_serving_areas,
)


def test_determinism_same_input_same_output():
    assets = generate_serving_areas(count=100, seed=42)
    scored_a = score_serving_areas(assets)
    scored_b = score_serving_areas(assets)
    assert scored_a == scored_b


def test_output_order_matches_input_order():
    assets = generate_serving_areas(count=50, seed=42)
    scored = score_serving_areas(assets)
    assert [s["asset_id"] for s in scored] == [a["asset_id"] for a in assets]


def test_scores_are_bounded_zero_to_one():
    assets = generate_serving_areas(count=200, seed=42)
    for record in score_serving_areas(assets):
        assert 0.0 <= record["risk_score"] <= 1.0
        assert 0.0 <= record["readiness_score"] <= 1.0
        for dim_score in record["dimension_scores"].values():
            assert 0.0 <= dim_score <= 1.0


def test_readiness_is_complement_of_risk():
    assets = generate_serving_areas(count=50, seed=42)
    for record in score_serving_areas(assets):
        assert round(record["risk_score"] + record["readiness_score"], 6) == 1.0


def test_wave_bucket_is_one_of_expected_values():
    assets = generate_serving_areas(count=200, seed=42)
    for record in score_serving_areas(assets):
        assert record["wave"] in {"wave_1", "wave_2", "wave_3"}


def test_higher_readiness_maps_to_earlier_wave():
    # A wave with a lower number (faster to retire) should never have a
    # lower average readiness score than a higher-numbered wave, for any
    # waves that are actually populated in the sample.
    assets = generate_serving_areas(count=500, seed=42)
    scored = score_serving_areas(assets)
    by_wave = {"wave_1": [], "wave_2": [], "wave_3": []}
    for record in scored:
        by_wave[record["wave"]].append(record["readiness_score"])

    populated = [wave for wave, scores in by_wave.items() if scores]
    assert len(populated) >= 2, "expected at least two waves populated at n=500"
    avg = {wave: sum(scores) / len(scores) for wave, scores in by_wave.items() if scores}
    ordered_avgs = [avg[wave] for wave in ("wave_1", "wave_2", "wave_3") if wave in avg]
    assert ordered_avgs == sorted(ordered_avgs, reverse=True)


def test_dimension_weights_sum_to_one():
    assert round(sum(DIMENSION_WEIGHTS.values()), 6) == 1.0


def test_commercial_value_matches_recoverable_lbs_times_price():
    assets = generate_serving_areas(count=20, seed=42)
    scored = score_serving_areas(assets)
    for asset, record in zip(assets, scored):
        expected = round(
            asset["recoverable_copper_lbs"] * asset["copper_price_usd_per_lb"], 2
        )
        assert record["commercial_value_usd"] == expected


def test_zero_risk_inputs_score_full_readiness():
    zero_risk_asset = {
        "asset_id": "SA-TEST",
        "h3_cell": "89268cc432bffff",
        "h3_resolution": 9,
        "active_copper_lines": 0,
        "pots_only_households": 0,
        "fiber_overbuild_pct": 1.0,
        "critical_service_flags": {
            "alarm_system": False,
            "medical_monitoring": False,
            "e911_backup": False,
            "fax_or_credit_card": False,
        },
        "puc_docket_active": False,
        "tribal_land_overlap": False,
        "soil_risk_score": 0.0,
        "permitting_complexity": 0.0,
        "colocated_utilities": 0,
        "historical_dig_incident_rate": 0.0,
        "recoverable_copper_lbs": 0.0,
        "copper_price_usd_per_lb": 4.35,
    }
    record = score_serving_area(zero_risk_asset)
    assert record["risk_score"] == 0.0
    assert record["readiness_score"] == 1.0
    assert record["wave"] == "wave_1"


def _base_asset(**overrides):
    asset = {
        "asset_id": "SA-TEST",
        "h3_cell": "89268cc432bffff",
        "h3_resolution": 9,
        "active_copper_lines": 0,
        "pots_only_households": 0,
        "fiber_overbuild_pct": 1.0,
        "critical_service_flags": {
            "alarm_system": False,
            "medical_monitoring": False,
            "e911_backup": False,
            "fax_or_credit_card": False,
        },
        "puc_docket_active": False,
        "tribal_land_overlap": False,
        "soil_risk_score": 0.0,
        "permitting_complexity": 0.0,
        "colocated_utilities": 0,
        "historical_dig_incident_rate": 0.0,
        "recoverable_copper_lbs": 0.0,
        "copper_price_usd_per_lb": 4.35,
    }
    asset.update(overrides)
    return asset


# --- Empty critical_service_flags -------------------------------------


def test_empty_critical_service_flags_scores_zero_overlap_without_crashing():
    asset = _base_asset(critical_service_flags={})
    record = score_serving_area(asset)
    assert record["dimension_scores"]["critical_service_overlap"] == 0.0
    assert record["risk_score"] == 0.0
    assert record["readiness_score"] == 1.0


def test_non_dict_critical_service_flags_raises_scoring_error():
    asset = _base_asset(critical_service_flags=None)
    with pytest.raises(ScoringError):
        score_serving_area(asset)


# --- Hand-calculated scoring assertions ---------------------------------


def test_hand_calculated_partial_risk_asset():
    # subscriber_dependency: (2500/5000 + 1500/3000) / 2 = 0.5
    # critical_service_overlap: 1 flag true out of 4 = 0.25
    # fiber_alternative_gap: 1 - 0.4 = 0.6
    # regulatory_friction: puc_docket_active only = 0.6
    # physical_dig_risk: mean(0.2, 0.4, 2/3, 2.5/5.0) = mean(0.2, 0.4, 0.666667, 0.5)
    #   = 1.766667 / 4 = 0.441667
    # risk = 0.30*0.5 + 0.25*0.25 + 0.15*0.6 + 0.15*0.6 + 0.15*0.441667
    #      = 0.15 + 0.0625 + 0.09 + 0.09 + 0.0662500
    #      = 0.4587500
    asset = _base_asset(
        active_copper_lines=2500,
        pots_only_households=1500,
        fiber_overbuild_pct=0.4,
        critical_service_flags={
            "alarm_system": True,
            "medical_monitoring": False,
            "e911_backup": False,
            "fax_or_credit_card": False,
        },
        puc_docket_active=True,
        tribal_land_overlap=False,
        soil_risk_score=0.2,
        permitting_complexity=0.4,
        colocated_utilities=2,
        historical_dig_incident_rate=2.5,
        recoverable_copper_lbs=1000.0,
        copper_price_usd_per_lb=4.35,
    )
    record = score_serving_area(asset)
    assert record["dimension_scores"]["subscriber_dependency"] == pytest.approx(0.5)
    assert record["dimension_scores"]["critical_service_overlap"] == pytest.approx(0.25)
    assert record["dimension_scores"]["fiber_alternative_gap"] == pytest.approx(0.6)
    assert record["dimension_scores"]["regulatory_friction"] == pytest.approx(0.6)
    assert record["dimension_scores"]["physical_dig_risk"] == pytest.approx(0.441667, abs=1e-6)
    assert record["risk_score"] == pytest.approx(0.45875, abs=1e-6)
    assert record["readiness_score"] == pytest.approx(0.54125, abs=1e-6)
    assert record["wave"] == "wave_2"
    assert record["commercial_value_usd"] == pytest.approx(4350.0)


def test_hand_calculated_full_regulatory_friction_both_flags():
    asset = _base_asset(puc_docket_active=True, tribal_land_overlap=True)
    record = score_serving_area(asset)
    assert record["dimension_scores"]["regulatory_friction"] == pytest.approx(1.0)


# --- Exact wave-threshold boundary cases ---------------------------------


def test_wave_boundary_exact_066_readiness_is_wave_1():
    # risk = 0.34 exactly -> readiness = 0.66 exactly -> wave_1 (>= 0.66)
    asset = _base_asset(
        active_copper_lines=5000,
        pots_only_households=750,
        fiber_overbuild_pct=1.0,
        critical_service_flags={
            "alarm_system": True,
            "medical_monitoring": False,
            "e911_backup": False,
            "fax_or_credit_card": False,
        },
        puc_docket_active=True,
        tribal_land_overlap=False,
        soil_risk_score=0.0,
        permitting_complexity=0.0,
        colocated_utilities=0,
        historical_dig_incident_rate=0.0,
    )
    record = score_serving_area(asset)
    assert record["risk_score"] == pytest.approx(0.34)
    assert record["readiness_score"] == pytest.approx(0.66)
    assert record["wave"] == "wave_1"


def test_wave_boundary_just_below_066_readiness_is_wave_2():
    # Same as the 0.66 boundary case but with a small extra incident-rate
    # nudge so readiness falls just under 0.66.
    asset = _base_asset(
        active_copper_lines=5000,
        pots_only_households=750,
        fiber_overbuild_pct=1.0,
        critical_service_flags={
            "alarm_system": True,
            "medical_monitoring": False,
            "e911_backup": False,
            "fax_or_credit_card": False,
        },
        puc_docket_active=True,
        tribal_land_overlap=False,
        soil_risk_score=0.0,
        permitting_complexity=0.0,
        colocated_utilities=0,
        historical_dig_incident_rate=0.02,
    )
    record = score_serving_area(asset)
    assert record["readiness_score"] < 0.66
    assert record["wave"] == "wave_2"


def test_wave_boundary_exact_033_readiness_is_wave_2():
    # risk = 0.67 exactly -> readiness = 0.33 exactly -> wave_2 (>= 0.33)
    asset = _base_asset(
        active_copper_lines=2000,
        pots_only_households=1200,
        fiber_overbuild_pct=1.0,
        critical_service_flags={
            "alarm_system": True,
            "medical_monitoring": True,
            "e911_backup": True,
            "fax_or_credit_card": True,
        },
        puc_docket_active=True,
        tribal_land_overlap=True,
        soil_risk_score=1.0,
        permitting_complexity=1.0,
        colocated_utilities=3,
        historical_dig_incident_rate=5.0,
    )
    record = score_serving_area(asset)
    assert record["risk_score"] == pytest.approx(0.67)
    assert record["readiness_score"] == pytest.approx(0.33)
    assert record["wave"] == "wave_2"


def test_wave_boundary_below_033_readiness_is_wave_3():
    asset = _base_asset(
        active_copper_lines=5000,
        pots_only_households=3000,
        fiber_overbuild_pct=0.0,
        critical_service_flags={
            "alarm_system": True,
            "medical_monitoring": True,
            "e911_backup": True,
            "fax_or_credit_card": False,
        },
        puc_docket_active=True,
        tribal_land_overlap=True,
        soil_risk_score=1.0,
        permitting_complexity=1.0,
        colocated_utilities=3,
        historical_dig_incident_rate=5.0,
    )
    record = score_serving_area(asset)
    assert record["readiness_score"] < 0.33
    assert record["wave"] == "wave_3"


def test_wave_classification_not_skewed_by_premature_rounding():
    # A readiness score that rounds up to 0.66 at 2 decimal places but is
    # actually just under the true 0.66 threshold at full precision must
    # still classify as wave_2, not wave_1 -- i.e. wave assignment must use
    # full-precision readiness, not a rounded display value.
    asset = _base_asset(
        active_copper_lines=5000,
        pots_only_households=750,
        fiber_overbuild_pct=1.0,
        critical_service_flags={
            "alarm_system": True,
            "medical_monitoring": False,
            "e911_backup": False,
            "fax_or_credit_card": False,
        },
        puc_docket_active=True,
        tribal_land_overlap=False,
        soil_risk_score=0.0,
        permitting_complexity=0.0,
        colocated_utilities=0,
        historical_dig_incident_rate=0.02,
    )
    record = score_serving_area(asset)
    # readiness_score is 0.65985, which rounds to 0.66 at 2dp but must not
    # be treated as >= 0.66 for wave purposes.
    assert round(record["readiness_score"], 2) == 0.66
    assert record["readiness_score"] < 0.66
    assert record["wave"] == "wave_2"


# --- Malformed / negative / NaN / infinite numeric inputs ----------------


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("active_copper_lines", -1),
        ("active_copper_lines", float("nan")),
        ("active_copper_lines", float("inf")),
        ("active_copper_lines", "500"),
        ("active_copper_lines", None),
        ("pots_only_households", -5),
        ("pots_only_households", float("nan")),
        ("fiber_overbuild_pct", float("inf")),
        ("fiber_overbuild_pct", float("-inf")),
        ("fiber_overbuild_pct", float("nan")),
        ("soil_risk_score", -0.01),
        ("permitting_complexity", float("nan")),
        ("colocated_utilities", -1),
        ("historical_dig_incident_rate", float("-inf")),
        ("recoverable_copper_lbs", -100.0),
        ("recoverable_copper_lbs", float("nan")),
        ("copper_price_usd_per_lb", float("inf")),
        ("copper_price_usd_per_lb", -4.35),
    ],
)
def test_malformed_numeric_field_raises_scoring_error(field_name, bad_value):
    asset = _base_asset(**{field_name: bad_value})
    with pytest.raises(ScoringError):
        score_serving_area(asset)


def test_missing_required_field_raises_scoring_error():
    asset = _base_asset()
    del asset["recoverable_copper_lbs"]
    with pytest.raises(ScoringError):
        score_serving_area(asset)


def test_non_dict_asset_raises_scoring_error():
    with pytest.raises(ScoringError):
        score_serving_area(["not", "a", "dict"])


def test_boolean_is_not_accepted_as_numeric_field():
    # bool is technically an int subclass in Python; scoring must not treat
    # True/False as valid numeric inputs for these fields.
    asset = _base_asset(active_copper_lines=True)
    with pytest.raises(ScoringError):
        score_serving_area(asset)


def test_score_serving_areas_propagates_scoring_error_with_asset_context():
    good = _base_asset(asset_id="SA-GOOD")
    bad = _base_asset(asset_id="SA-BAD", active_copper_lines=float("nan"))
    with pytest.raises(ScoringError) as exc_info:
        score_serving_areas([good, bad])
    assert "SA-BAD" in str(exc_info.value)


def test_scoring_error_message_names_field_and_asset():
    asset = _base_asset(asset_id="SA-42", recoverable_copper_lbs=-1.0)
    with pytest.raises(ScoringError) as exc_info:
        score_serving_area(asset)
    message = str(exc_info.value)
    assert "SA-42" in message
    assert "recoverable_copper_lbs" in message
