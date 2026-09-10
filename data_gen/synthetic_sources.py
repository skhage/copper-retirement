"""Deterministic, offline source datasets for the copper-retirement demo.

The generated records simulate private OSS/GIS, circuit, copper-recovery, and
contractor sources. They contain no real Lumen plant, customer, or vendor data.
All relationships are keyed from ``generate_serving_areas`` so the original
risk-scoring thin slice remains the authoritative asset path.
"""

import csv
import hashlib
import json
import random
from pathlib import Path

import h3

from data_gen.synthetic_assets import (
    COPPER_PRICE_USD_PER_LB,
    DATASET_VERSION,
    LEGACY_STATES,
    _validate_non_negative_integer,
    generate_serving_areas,
)

DEFAULT_ASSET_COUNT = 24
DEFAULT_CONTRACTOR_COUNT = 12
DEFAULT_SEED = 42
SYNTHETIC_NOTICE = "SYNTHETIC DEMO DATA - NOT REAL LUMEN PLANT OR OPERATIONS"

ASSET_COLUMNS = (
    "asset_id",
    "source",
    "source_system",
    "dataset_version",
    "generation_seed",
    "latitude",
    "longitude",
    "h3_cell",
    "h3_resolution",
    "state",
    "active_copper_lines",
    "pots_only_households",
    "fiber_overbuild_pct",
    "critical_service_flags",
    "puc_docket_active",
    "tribal_land_overlap",
    "soil_risk_score",
    "permitting_complexity",
    "colocated_utilities",
    "historical_dig_incident_rate",
    "recoverable_copper_lbs",
    "copper_price_usd_per_lb",
    "synthetic_data_notice",
)

CIRCUIT_COLUMNS = (
    "circuit_id",
    "asset_id",
    "h3_cell",
    "state",
    "service_class",
    "transport_medium",
    "status",
    "active_customer_count",
    "route_miles",
    "fiber_reroute_available",
    "reroute_asset_id",
    "source",
    "source_system",
    "dataset_version",
    "generation_seed",
    "synthetic_data_notice",
)

RECOVERY_COLUMNS = (
    "recovery_id",
    "asset_id",
    "h3_cell",
    "state",
    "recovery_status",
    "estimated_recoverable_lbs",
    "recovered_lbs",
    "recovery_yield_pct",
    "copper_grade",
    "reference_price_usd_per_lb",
    "estimated_material_value_usd",
    "source",
    "source_system",
    "dataset_version",
    "generation_seed",
    "synthetic_data_notice",
)

CONTRACTOR_COLUMNS = (
    "contractor_id",
    "contractor_name",
    "home_state",
    "coverage_states",
    "coverage_h3_cells",
    "license_status",
    "union_affiliation",
    "crew_capacity",
    "safety_score",
    "on_time_completion_pct",
    "copper_recovery_certified",
    "source",
    "source_system",
    "dataset_version",
    "generation_seed",
    "synthetic_data_notice",
)


def _dataset_rng(seed, dataset_name):
    digest = hashlib.sha256(f"{seed}:{dataset_name}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _provenance(source_system, seed):
    return {
        "source": "synthetic",
        "source_system": source_system,
        "dataset_version": DATASET_VERSION,
        "generation_seed": seed,
        "synthetic_data_notice": SYNTHETIC_NOTICE,
    }


def generate_gis_assets(count=DEFAULT_ASSET_COUNT, seed=DEFAULT_SEED):
    """Return risk-compatible GIS/asset rows with explicit provenance."""
    assets = generate_serving_areas(count=count, seed=seed)
    return [dict(asset, synthetic_data_notice=SYNTHETIC_NOTICE) for asset in assets]


def generate_circuit_inventory(assets, seed=DEFAULT_SEED):
    """Return a deterministic circuit inventory linked to serving-area assets."""
    _validate_non_negative_integer(seed, "seed")
    rng = _dataset_rng(seed, "circuit_inventory")
    records = []
    service_classes = ("pots", "dsl", "special_access", "alarm_transport")
    statuses = ("active", "active", "active", "pending_disconnect")

    for asset_index, asset in enumerate(assets):
        circuit_count = 1 + min(2, asset["active_copper_lines"] // 1800)
        for circuit_index in range(circuit_count):
            reroute_available = len(assets) > 1 and rng.random() < asset["fiber_overbuild_pct"]
            reroute_asset_id = None
            if reroute_available:
                reroute_asset_id = assets[(asset_index + 1 + circuit_index) % len(assets)]["asset_id"]
            records.append(
                {
                    "circuit_id": f"CKT-{asset_index:05d}-{circuit_index + 1:02d}",
                    "asset_id": asset["asset_id"],
                    "h3_cell": asset["h3_cell"],
                    "state": asset["state"],
                    "service_class": rng.choice(service_classes),
                    "transport_medium": "copper",
                    "status": rng.choice(statuses),
                    "active_customer_count": rng.randint(0, min(96, asset["active_copper_lines"])),
                    "route_miles": round(rng.uniform(0.2, 18.0), 2),
                    "fiber_reroute_available": reroute_available,
                    "reroute_asset_id": reroute_asset_id,
                    **_provenance("simulated_network_circuit_inventory", seed),
                }
            )
    return records


def generate_copper_recovery(assets, seed=DEFAULT_SEED):
    """Return deterministic recovery estimates and simulated completed loads."""
    _validate_non_negative_integer(seed, "seed")
    rng = _dataset_rng(seed, "copper_recovery")
    records = []
    grades = ("bare_bright", "number_1", "number_2", "insulated_wire")
    statuses = ("estimated", "scheduled", "completed")

    for index, asset in enumerate(assets):
        status = rng.choice(statuses)
        yield_pct = round(rng.uniform(0.58, 0.94), 3)
        recovered_lbs = 0.0
        if status == "completed":
            recovered_lbs = round(asset["recoverable_copper_lbs"] * yield_pct, 1)
        records.append(
            {
                "recovery_id": f"REC-{index:05d}",
                "asset_id": asset["asset_id"],
                "h3_cell": asset["h3_cell"],
                "state": asset["state"],
                "recovery_status": status,
                "estimated_recoverable_lbs": asset["recoverable_copper_lbs"],
                "recovered_lbs": recovered_lbs,
                "recovery_yield_pct": yield_pct,
                "copper_grade": rng.choice(grades),
                "reference_price_usd_per_lb": COPPER_PRICE_USD_PER_LB,
                "estimated_material_value_usd": round(
                    asset["recoverable_copper_lbs"] * COPPER_PRICE_USD_PER_LB, 2
                ),
                **_provenance("simulated_copper_recovery_operations", seed),
            }
        )
    return records


def generate_contractor_registry(
    assets, count=DEFAULT_CONTRACTOR_COUNT, seed=DEFAULT_SEED
):
    """Return deterministic fictional contractors with state and H3 coverage."""
    _validate_non_negative_integer(count, "count")
    _validate_non_negative_integer(seed, "seed")
    rng = _dataset_rng(seed, "contractor_registry")
    asset_cells_by_state = {state: [] for state in LEGACY_STATES}
    for asset in assets:
        asset_cells_by_state.setdefault(asset["state"], []).append(asset["h3_cell"])

    records = []
    state_list = tuple(sorted(asset_cells_by_state))
    for index in range(count):
        home_state = state_list[index % len(state_list)]
        secondary_state = state_list[(index + 1) % len(state_list)]
        coverage_states = sorted({home_state, secondary_state})
        coverage_cells = sorted(
            {
                cell
                for state in coverage_states
                for cell in asset_cells_by_state.get(state, [])
            }
        )
        records.append(
            {
                "contractor_id": f"CTR-{index:04d}",
                "contractor_name": f"Synthetic Field Partner {index + 1:02d}",
                "home_state": home_state,
                "coverage_states": coverage_states,
                "coverage_h3_cells": coverage_cells,
                "license_status": rng.choice(("active", "active", "provisional")),
                "union_affiliation": rng.choice(("union", "open_shop", "mixed")),
                "crew_capacity": rng.randint(2, 18),
                "safety_score": round(rng.uniform(0.78, 0.99), 3),
                "on_time_completion_pct": round(rng.uniform(0.72, 0.98), 3),
                "copper_recovery_certified": rng.random() < 0.75,
                **_provenance("simulated_contractor_registry", seed),
            }
        )
    return records


def generate_source_datasets(
    asset_count=DEFAULT_ASSET_COUNT,
    contractor_count=DEFAULT_CONTRACTOR_COUNT,
    seed=DEFAULT_SEED,
):
    """Generate all correlated source datasets without network access."""
    assets = generate_gis_assets(count=asset_count, seed=seed)
    return {
        "gis_assets": assets,
        "circuit_inventory": generate_circuit_inventory(assets, seed=seed),
        "copper_recovery": generate_copper_recovery(assets, seed=seed),
        "contractor_registry": generate_contractor_registry(
            assets, count=contractor_count, seed=seed
        ),
    }


def assets_to_geojson(assets):
    """Convert serving-area H3 cells into a GIS-ready FeatureCollection."""
    features = []
    for asset in assets:
        boundary = h3.cell_to_boundary(asset["h3_cell"])
        ring = [[round(lon, 6), round(lat, 6)] for lat, lon in boundary]
        ring.append(ring[0])
        properties = {key: value for key, value in asset.items() if key not in {"latitude", "longitude"}}
        features.append(
            {
                "type": "Feature",
                "id": asset["asset_id"],
                "geometry": {"type": "Polygon", "coordinates": [ring]},
                "properties": properties,
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "synthetic_copper_serving_areas",
        "synthetic_data_notice": SYNTHETIC_NOTICE,
        "features": features,
    }


def _csv_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return value


def _write_csv(path, rows, columns):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _csv_value(row[column]) for column in columns})


def _write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": ")) + "\n",
        encoding="utf-8",
    )


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_source_fixtures(
    output_dir,
    asset_count=DEFAULT_ASSET_COUNT,
    contractor_count=DEFAULT_CONTRACTOR_COUNT,
    seed=DEFAULT_SEED,
):
    """Write deterministic ingest fixtures and return their manifest."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    datasets = generate_source_datasets(asset_count, contractor_count, seed)

    files = {
        "gis_assets_csv": ("gis_assets.csv", datasets["gis_assets"], ASSET_COLUMNS),
        "circuit_inventory_csv": (
            "circuit_inventory.csv",
            datasets["circuit_inventory"],
            CIRCUIT_COLUMNS,
        ),
        "copper_recovery_csv": (
            "copper_recovery.csv",
            datasets["copper_recovery"],
            RECOVERY_COLUMNS,
        ),
        "contractor_registry_csv": (
            "contractor_registry.csv",
            datasets["contractor_registry"],
            CONTRACTOR_COLUMNS,
        ),
    }
    for filename, rows, columns in files.values():
        _write_csv(output_path / filename, rows, columns)

    geojson_path = output_path / "gis_assets.geojson"
    _write_json(geojson_path, assets_to_geojson(datasets["gis_assets"]))

    manifest_files = {}
    for dataset_name, (filename, rows, _columns) in files.items():
        path = output_path / filename
        manifest_files[dataset_name] = {
            "path": filename,
            "format": "csv",
            "record_count": len(rows),
            "sha256": _sha256(path),
        }
    manifest_files["gis_assets_geojson"] = {
        "path": geojson_path.name,
        "format": "geojson",
        "record_count": len(datasets["gis_assets"]),
        "sha256": _sha256(geojson_path),
    }

    generation_id = hashlib.sha256(
        f"{DATASET_VERSION}:{seed}:{asset_count}:{contractor_count}".encode("utf-8")
    ).hexdigest()[:16]
    manifest = {
        "dataset_version": DATASET_VERSION,
        "generation_id": generation_id,
        "generation_seed": seed,
        "synthetic_data_notice": SYNTHETIC_NOTICE,
        "offline_generation": True,
        "files": manifest_files,
    }
    _write_json(output_path / "manifest.json", manifest)
    return manifest
