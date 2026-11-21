import argparse
from itertools import product
from pathlib import Path

from cutting_benchmark.rectangle_datasets import (
    make_dataset,
    save_datasets,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    """Generate the pilot rectangle dataset suite and save it as JSON."""
    parser = argparse.ArgumentParser(
        description="Generate the pilot rectangle dataset suite."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "synthetic" / "pilot_v1_generated.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file.",
    )
    args = parser.parse_args()

    output_path = args.output
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    if output_path.exists() and not args.overwrite:
        parser.error(
            f"{output_path} already exists; choose another --output path "
            "or pass --overwrite"
        )

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

    save_datasets(datasets, output_path)
    print(f"Saved {len(datasets)} datasets to {output_path}")


if __name__ == "__main__":
    main()
