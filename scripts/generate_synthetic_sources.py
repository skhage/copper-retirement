"""Generate deterministic SYNTHETIC source data for the copper retirement accelerator.

Modes:
  fixtures (default)  write offline CSV/JSON fixtures (data_gen/synthetic_sources.py).
  tables              seed every upstream UC source table the pipeline and app read
                      into a fresh partner catalog (data_gen/seed_source_tables.py).
                      Used by the bundle job seed_synthetic_sources_job, e.g.
                      --mode tables --catalog <catalog> --schema <schema> [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

# Make the bundle root importable when run as a spark_python_task (script dir is scripts/).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

DEFAULT_SEED = 42


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("fixtures", "tables"), default="fixtures")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    # fixtures mode
    parser.add_argument("--output", type=Path, default=Path("data/fixtures/synthetic"))
    parser.add_argument("--asset-count", type=int, default=None)
    parser.add_argument("--contractor-count", type=int, default=None)
    # tables mode
    parser.add_argument("--catalog", help="Target UC catalog (must exist).")
    parser.add_argument("--schema", default="copper_retirement", help="Accelerator schema (bundle var schema_name).")
    parser.add_argument("--max-rows", type=int, default=2000, help="Row cap per table.")
    parser.add_argument("--scale", type=float, default=1.0, help="Fraction of reference row counts (before cap).")
    parser.add_argument("--dry-run", action="store_true", help="Generate in memory and report; write nothing.")
    parser.add_argument("--force", action="store_true", help="Overwrite tables not written by this seeder.")
    return parser.parse_args(argv)


def run_tables(args):
    from pyspark.sql import SparkSession
    from data_gen.seed_source_tables import seed_tables

    if not args.catalog:
        raise SystemExit("--catalog is required with --mode tables")
    spark = SparkSession.builder.getOrCreate()
    manifest = seed_tables(spark, args.catalog, args.schema, max_rows=args.max_rows, scale=args.scale,
                           seed=args.seed, dry_run=args.dry_run, force=args.force)
    print(json.dumps(manifest, indent=2, default=str))
    empty = [k for k, v in manifest["coverage"].items() if not v]
    if manifest["refused"]:
        raise SystemExit(f"Refused to overwrite non-seed tables: {manifest['refused']} (use --force only on scratch catalogs)")
    if empty:
        raise SystemExit(f"Join coverage checks returned 0 rows: {empty}")


def main(argv=None):
    args = parse_args(argv)
    if args.mode == "tables":
        run_tables(args)
        return
    from data_gen.synthetic_sources import (  # needs h3; only for offline fixtures
        DEFAULT_ASSET_COUNT,
        DEFAULT_CONTRACTOR_COUNT,
        write_source_fixtures,
    )
    args.asset_count = args.asset_count or DEFAULT_ASSET_COUNT
    args.contractor_count = args.contractor_count or DEFAULT_CONTRACTOR_COUNT
    manifest = write_source_fixtures(
        args.output,
        asset_count=args.asset_count,
        contractor_count=args.contractor_count,
        seed=args.seed,
    )
    print(
        f"Wrote {len(manifest['files'])} deterministic synthetic source files "
        f"to {args.output} (generation_id={manifest['generation_id']})."
    )


if __name__ == "__main__":
    main()
