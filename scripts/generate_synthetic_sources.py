"""Generate deterministic synthetic source fixtures for local or bundle upload."""

import argparse
from pathlib import Path

from data_gen.synthetic_sources import (
    DEFAULT_ASSET_COUNT,
    DEFAULT_CONTRACTOR_COUNT,
    DEFAULT_SEED,
    write_source_fixtures,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/fixtures/synthetic"))
    parser.add_argument("--asset-count", type=int, default=DEFAULT_ASSET_COUNT)
    parser.add_argument("--contractor-count", type=int, default=DEFAULT_CONTRACTOR_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def main():
    args = parse_args()
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
