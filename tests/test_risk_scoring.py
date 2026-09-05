from data_gen.synthetic_assets import generate_serving_areas
from risk.scoring import DIMENSION_WEIGHTS, score_serving_area, score_serving_areas


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
