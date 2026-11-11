from itertools import product
from pathlib import Path

from cutting_benchmark.rectangle_datasets import (
    make_dataset,
    save_datasets,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    """Generate the pilot rectangle dataset suite and save it as JSON."""
    datasets = [
        make_dataset(
            seed=seed,
            n_parts=n_parts,
            profile=profile,
        )
        for n_parts, profile, seed in product(
            [35, 100],
            ["mixed", "strips", "large_and_small"],
            range(5),
        )
    ]

    output_path = (
        PROJECT_ROOT
        / "data"
        / "synthetic"
        / "pilot_v1.json"
    )

    save_datasets(datasets, output_path)

    print(f"Saved {len(datasets)} datasets to {output_path}")


if __name__ == "__main__":
    main()