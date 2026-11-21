"""Run PackingSolver benchmarks over saved rectangle datasets.

By default, this script loads ``data/synthetic/pilot_v1.json`` and runs
each dataset with rotation disabled and enabled, using a thirty-second
solver limit per run. The full benchmark results are written to
``results/packingsolver/<dataset-name>_results.csv``.

Use ``--datasets`` and ``--output`` to select different input and output
paths. Use ``--config-file`` to supply a JSON list of PackingSolver
configuration objects, or use ``--time-limit`` and ``--rotation`` to
generate configurations from the command line. The terminal summary
reports the number of runs that did not produce a complete packing, the
number that returned no solution, and the total elapsed time.

Example::

    python scripts/run_packingsolver_benchmark.py --time-limit 10
"""

import argparse
import json
import time
from pathlib import Path

from cutting_benchmark.benchmark import run_benchmark
from cutting_benchmark.rectangle_datasets import load_datasets
from cutting_benchmark.solvers.packingsolver_adapter import run_pack


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "data" / "synthetic" / "pilot_v1.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run PackingSolver benchmark configurations against a saved "
            "rectangle dataset JSON file and export the results to CSV."
        )
    )
    parser.add_argument(
        "--datasets",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help=(
            "Dataset JSON path (default: data/synthetic/pilot_v1.json)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "CSV output path (default: results/packingsolver/"
            "<dataset-name>_results.csv)."
        ),
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        help=(
            "Optional JSON file containing a list of solver configuration "
            "objects. Example: [{\"rotation\": false, \"time_limit\": 5}]."
        ),
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=30,
        help="Per-run solver time limit in seconds when using generated configs.",
    )
    parser.add_argument(
        "--rotation",
        choices=("both", "yes", "no"),
        default="both",
        help="Rotation configs to run when --config-file is not supplied.",
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

    if args.time_limit <= 0:
        raise ValueError("--time-limit must be positive")

    rotations = {
        "both": (False, True),
        "yes": (True,),
        "no": (False,),
    }[args.rotation]

    return [
        {"rotation": rotation, "time_limit": args.time_limit}
        for rotation in rotations
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
        / "packingsolver"
        / f"{args.datasets.stem}_results.csv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_path, index=False)

    incomplete = ~results["complete"].fillna(False).astype(bool)
    no_solution = results["run_status"].eq("no_solution_returned")
    print(f"Datasets: {len(datasets)}")
    print(f"Configurations: {len(configurations)}")
    print(f"Runs recorded: {len(results)}")
    print(f"Runs not completed: {int(incomplete.sum())}")
    print(f"Runs with no solution returned: {int(no_solution.sum())}")
    print(f"Results CSV: {output_path.resolve()}")
    print(f"Total elapsed time: {time.perf_counter() - started_at:.2f} seconds")


if __name__ == "__main__":
    main()
