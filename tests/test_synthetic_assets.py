import h3

from data_gen.synthetic_assets import H3_RESOLUTION, generate_serving_areas


def test_determinism_same_seed_same_count():
    a = generate_serving_areas(count=200, seed=42)
    b = generate_serving_areas(count=200, seed=42)
    assert a == b


def test_different_seed_produces_different_output():
    a = generate_serving_areas(count=50, seed=1)
    b = generate_serving_areas(count=50, seed=2)
    assert a != b


def test_count_and_unique_asset_ids():
    assets = generate_serving_areas(count=100, seed=42)
    assert len(assets) == 100
    ids = [a["asset_id"] for a in assets]
    assert len(set(ids)) == 100


def test_all_records_are_labeled_synthetic():
    assets = generate_serving_areas(count=25, seed=42)
    assert all(a["source"] == "synthetic" for a in assets)


def test_h3_cells_are_valid_and_at_configured_resolution():
    assets = generate_serving_areas(count=100, seed=42)
    for asset in assets:
        assert h3.is_valid_cell(asset["h3_cell"])
        assert h3.get_resolution(asset["h3_cell"]) == H3_RESOLUTION
        assert asset["h3_resolution"] == H3_RESOLUTION


def test_pots_only_households_never_exceeds_active_copper_lines():
    assets = generate_serving_areas(count=200, seed=42)
    for asset in assets:
        assert asset["pots_only_households"] <= asset["active_copper_lines"]


def test_fractional_fields_within_expected_bounds():
    assets = generate_serving_areas(count=200, seed=42)
    for asset in assets:
        assert 0.0 <= asset["fiber_overbuild_pct"] <= 1.0
        assert 0.0 <= asset["soil_risk_score"] <= 1.0
        assert 0.0 <= asset["permitting_complexity"] <= 1.0
        assert 0 <= asset["colocated_utilities"] <= 3
        assert 0.0 <= asset["historical_dig_incident_rate"]
        assert asset["recoverable_copper_lbs"] >= 0.0
