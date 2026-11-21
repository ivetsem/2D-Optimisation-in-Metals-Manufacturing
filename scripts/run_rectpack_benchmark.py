"""Run Rectpack benchmarks over saved rectangle datasets.

By default, this script loads ``data/synthetic/pilot_v1.json`` and runs
all four registered packing algorithms with all four sorting rules,
with rotation disabled and enabled. This produces 32 configurations per
dataset. The full benchmark results are written to
``results/rectpack/<dataset-name>_results.csv``.

Use ``--datasets`` and ``--output`` to select different input and output
paths. Use ``--config-file`` to supply a JSON list of Rectpack
configuration objects, or select algorithms, sorting rules and rotation
settings from the command line. The terminal summary reports runs that
did not pack every requested part and the total elapsed time.

Example::

    python scripts/run_rectpack_benchmark.py --algorithms MaxRectsBssf --sorts long_side
"""

import argparse
import json
import time
from itertools import product
from pathlib import Path

from cutting_benchmark.benchmark import run_benchmark
from cutting_benchmark.rectangle_datasets import load_datasets
from cutting_benchmark.solvers.rectpack_adapter import (
    ALGORITHMS,
    SORTS,
    run_pack,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "data" / "synthetic" / "pilot_v1.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run Rectpack benchmark configurations against a saved "
            "rectangle dataset JSON file and export the results to CSV."
        )
    )
    parser.add_argument(
        "--datasets",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Dataset JSON path (default: data/synthetic/pilot_v1.json).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "CSV output path (default: results/rectpack/"
            "<dataset-name>_results.csv)."
        ),
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        help=(
            "Optional JSON file containing a list of solver configuration "
            "objects. Example: [{\"algorithm\": \"MaxRectsBssf\", "
            "\"sort\": \"long_side\", \"rotation\": false}]."
        ),
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        choices=tuple(ALGORITHMS),
        help="Algorithms to run (default: all registered algorithms).",
    )
    parser.add_argument(
        "--sorts",
        nargs="+",
        choices=tuple(SORTS),
        help="Sorting rules to run (default: all registered rules).",
    )
    parser.add_argument(
        "--rotation",
        choices=("both", "yes", "no"),
        default="both",
        help="Rotation settings to run (default: both).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repetitions per dataset/configuration (default: 1).",
    )
    parser.add_argument(
        "--available-sheets",
        type=int,
        help="Optional stock limit passed to the solver for every run.",
    )
    parser.add_argument(
        "--execution-seed",
        type=int,
        default=123,
        help="Seed used to shuffle benchmark execution order (default: 123).",
    )
    return parser.parse_args()


def load_configurations(args):
    if args.config_file is not None:
        configurations = json.loads(
            args.config_file.read_text(encoding="utf-8")
        )
        if not isinstance(configurations, list) or not configurations:
            raise ValueError(
                "The configuration file must contain a non-empty JSON list."
            )
        if not all(isinstance(config, dict) for config in configurations):
            raise ValueError(
                "Each solver configuration must be a JSON object."
            )
        return configurations

    algorithms = args.algorithms or tuple(ALGORITHMS)
    sorts = args.sorts or tuple(SORTS)
    rotations = {
        "both": (False, True),
        "yes": (True,),
        "no": (False,),
    }[args.rotation]

    return [
        {
            "algorithm": algorithm,
            "sort": sort,
            "rotation": rotation,
        }
        for algorithm, sort, rotation in product(
            algorithms,
            sorts,
            rotations,
        )
    ]


def main():
    started_at = time.perf_counter()
    args = parse_args()
    datasets = load_datasets(args.datasets)
    if not datasets:
        raise ValueError(f"No datasets found in {args.datasets}")

    configurations = load_configurations(args)
    results = run_benchmark(
        datasets=datasets,
        configurations=configurations,
        solver=run_pack,
        repeats=args.repeats,
        available_sheets=args.available_sheets,
        execution_seed=args.execution_seed,
    )

    output_path = args.output or (
        PROJECT_ROOT
        / "results"
        / "rectpack"
        / f"{args.datasets.stem}_results.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)

    incomplete = ~results["complete"].fillna(False).astype(bool)
    print(f"Datasets: {len(datasets)}")
    print(f"Configurations: {len(configurations)}")
    print(f"Runs recorded: {len(results)}")
    print(f"Runs not completed: {int(incomplete.sum())}")
    print(f"Results CSV: {output_path.resolve()}")
    print(f"Total elapsed time: {time.perf_counter() - started_at:.2f} seconds")


if __name__ == "__main__":
    main()
