"""Manual smoke-run of the P0 thin slice: synthetic data gen -> risk scoring.

Usage: python scripts/run_thin_slice.py [count] [seed]

Prints a summary so a human can sanity-check the deterministic pipeline
without needing a notebook or cluster.

CLI contract: malformed `count`/`seed` arguments, invalid generator counts,
and empty generated output all produce a concise one-line message on
stderr and a nonzero exit code — never a raw Python traceback.
"""

import os
import sys

# Allow `python scripts/run_thin_slice.py` to be invoked directly (Python
# only puts `scripts/` on sys.path in that case, not the repo root where
# `data_gen`/`risk` live).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_gen.synthetic_assets import GenerationError, generate_serving_areas
from risk.scoring import ScoringError, score_serving_areas

EXIT_USAGE_ERROR = 2
EXIT_EMPTY_OUTPUT = 1


class _ArgParseError(Exception):
    pass


def _parse_int_arg(raw_value, arg_name):
    try:
        return int(raw_value)
    except ValueError:
        raise _ArgParseError(f"{arg_name} must be an integer, got {raw_value!r}")


def main():
    if len(sys.argv) > 3:
        print(
            "error: too many arguments; usage: run_thin_slice.py [count] [seed]",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        count = _parse_int_arg(sys.argv[1], "count") if len(sys.argv) > 1 else 500
        seed = _parse_int_arg(sys.argv[2], "seed") if len(sys.argv) > 2 else 42
        assets = generate_serving_areas(count=count, seed=seed)
        scored = score_serving_areas(assets)
    except (_ArgParseError, GenerationError, ScoringError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    if not scored:
        print(
            "error: no serving areas were generated (count=0); nothing to score",
            file=sys.stderr,
        )
        return EXIT_EMPTY_OUTPUT

    wave_counts = {"wave_1": 0, "wave_2": 0, "wave_3": 0}
    total_commercial_value = 0.0
    for record in scored:
        wave_counts[record["wave"]] += 1
        total_commercial_value += record["commercial_value_usd"]

    print(f"Generated {count} synthetic serving areas (seed={seed}).")
    print(f"Wave distribution: {wave_counts}")
    print(f"Total recoverable-copper commercial value: ${total_commercial_value:,.2f}")
    print("Sample scored record:")
    print(scored[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
