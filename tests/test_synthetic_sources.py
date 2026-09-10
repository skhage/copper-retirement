import hashlib
import json
from pathlib import Path

import h3

from data_gen.synthetic_assets import STATE_BOUNDING_BOXES
from data_gen.synthetic_sources import (
    DEFAULT_ASSET_COUNT,
    DEFAULT_CONTRACTOR_COUNT,
    SYNTHETIC_NOTICE,
    assets_to_geojson,
    generate_source_datasets,
    write_source_fixtures,
)
from risk.scoring import score_serving_areas

FIXTURE_DIR = Path(__file__).parents[1] / "data" / "fixtures" / "synthetic"


def test_source_datasets_are_repeatable_and_risk_compatible():
    first = generate_source_datasets(asset_count=18, contractor_count=8, seed=17)
    second = generate_source_datasets(asset_count=18, contractor_count=8, seed=17)

    assert first == second
    assert len(score_serving_areas(first["gis_assets"])) == 18


def test_gis_assets_have_consistent_state_coordinates_and_provenance():
    datasets = generate_source_datasets(asset_count=60, contractor_count=6, seed=42)

    for asset in datasets["gis_assets"]:
        lat_range, lon_range = STATE_BOUNDING_BOXES[asset["state"]]
        assert lat_range[0] <= asset["latitude"] <= lat_range[1]
        assert lon_range[0] <= asset["longitude"] <= lon_range[1]
        assert asset["source"] == "synthetic"
        assert asset["source_system"] == "simulated_lumen_oss_gis"
        assert asset["synthetic_data_notice"] == SYNTHETIC_NOTICE


def test_circuits_reference_assets_and_valid_reroute_targets():
    datasets = generate_source_datasets(asset_count=20, contractor_count=6, seed=42)
    asset_ids = {asset["asset_id"] for asset in datasets["gis_assets"]}

    assert datasets["circuit_inventory"]
    for circuit in datasets["circuit_inventory"]:
        assert circuit["asset_id"] in asset_ids
        assert circuit["transport_medium"] == "copper"
        if circuit["fiber_reroute_available"]:
            assert circuit["reroute_asset_id"] in asset_ids
            assert circuit["reroute_asset_id"] != circuit["asset_id"]
        else:
            assert circuit["reroute_asset_id"] is None


def test_recovery_estimates_preserve_asset_copper_volume():
    datasets = generate_source_datasets(asset_count=20, contractor_count=6, seed=42)
    assets = {asset["asset_id"]: asset for asset in datasets["gis_assets"]}

    for recovery in datasets["copper_recovery"]:
        asset = assets[recovery["asset_id"]]
        assert recovery["estimated_recoverable_lbs"] == asset["recoverable_copper_lbs"]
        assert recovery["estimated_material_value_usd"] == round(
            asset["recoverable_copper_lbs"] * asset["copper_price_usd_per_lb"], 2
        )
        if recovery["recovery_status"] == "completed":
            assert recovery["recovered_lbs"] > 0
        else:
            assert recovery["recovered_lbs"] == 0


def test_contractors_are_fictional_and_cover_valid_asset_cells():
    datasets = generate_source_datasets(asset_count=30, contractor_count=12, seed=42)
    asset_cells = {asset["h3_cell"] for asset in datasets["gis_assets"]}

    assert len(datasets["contractor_registry"]) == 12
    for contractor in datasets["contractor_registry"]:
        assert contractor["contractor_name"].startswith("Synthetic Field Partner")
        assert set(contractor["coverage_h3_cells"]).issubset(asset_cells)
        assert all(h3.is_valid_cell(cell) for cell in contractor["coverage_h3_cells"])
        assert 0.0 <= contractor["safety_score"] <= 1.0
        assert contractor["source_system"] == "simulated_contractor_registry"


def test_geojson_uses_closed_h3_polygon_features():
    datasets = generate_source_datasets(asset_count=5, contractor_count=2, seed=42)
    geojson = assets_to_geojson(datasets["gis_assets"])

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 5
    for feature in geojson["features"]:
        ring = feature["geometry"]["coordinates"][0]
        assert feature["geometry"]["type"] == "Polygon"
        assert ring[0] == ring[-1]
        assert feature["properties"]["source"] == "synthetic"


def test_fixture_writer_is_byte_repeatable_and_manifest_hashes_match(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_manifest = write_source_fixtures(first_dir, 9, 4, 7)
    second_manifest = write_source_fixtures(second_dir, 9, 4, 7)

    assert first_manifest == second_manifest
    assert sorted(path.name for path in first_dir.iterdir()) == sorted(
        path.name for path in second_dir.iterdir()
    )
    for first_path in first_dir.iterdir():
        assert first_path.read_bytes() == (second_dir / first_path.name).read_bytes()

    for file_metadata in first_manifest["files"].values():
        payload = (first_dir / file_metadata["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == file_metadata["sha256"]


def test_committed_fixtures_match_default_generator(tmp_path):
    generated_dir = tmp_path / "synthetic"
    manifest = write_source_fixtures(generated_dir)

    assert manifest["files"]["gis_assets_csv"]["record_count"] == DEFAULT_ASSET_COUNT
    assert (
        manifest["files"]["contractor_registry_csv"]["record_count"]
        == DEFAULT_CONTRACTOR_COUNT
    )
    committed_files = sorted(path.name for path in FIXTURE_DIR.iterdir())
    generated_files = sorted(path.name for path in generated_dir.iterdir())
    assert generated_files == committed_files
    for filename in generated_files:
        assert (generated_dir / filename).read_bytes() == (FIXTURE_DIR / filename).read_bytes()

    committed_manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())
    assert committed_manifest["offline_generation"] is True
    assert committed_manifest["synthetic_data_notice"] == SYNTHETIC_NOTICE
