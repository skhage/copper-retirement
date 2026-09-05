"""Manual smoke-run of the P0 thin slice: synthetic data gen -> risk scoring.

Usage: python scripts/run_thin_slice.py [count] [seed]

Prints a summary so a human can sanity-check the deterministic pipeline
without needing a notebook or cluster.
"""

import sys

from data_gen.synthetic_assets import generate_serving_areas
from risk.scoring import score_serving_areas


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    assets = generate_serving_areas(count=count, seed=seed)
    scored = score_serving_areas(assets)

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


if __name__ == "__main__":
    main()
