"""Compare results from one or more solver benchmark CSV files.

By default, this script discovers ``*_results.csv`` files one directory
below ``results/``. Pass ``--results`` to choose explicit files. Each
source file, solver and configuration remains separately identifiable
in the outputs.

The script writes a completion report for every run. It then applies the
shared validation and summary functions to complete, layout-valid results
with matching dataset coverage. Summary tables report sheet count,
utilisation, area and part fractions, relative excess, best-observed
rates, and runtime. A paired comparison also shows each setup's sheet
counts against the best observed count for each dataset and rotation.
That best-observed reference is retrospective; it is not a solver that
can be selected in advance.

Example::

    python scripts/compare_solver_benchmarks.py
    python scripts/compare_solver_benchmarks.py --results results/rectpack/pilot_v1_results.csv results/packingsolver/pilot_v1_results.csv

Generated files in the output directory:

``comparison_completion.csv``
    Completion, layout-validity and runtime counts for every input setup.
    This includes incomplete runs and is the file to use when checking
    the full benchmark completion rates.
``comparison_dataset_config.csv``
    Per-dataset results for each setup, including sheet count, packing
    metrics and difference from the best observed sheet count.
``comparison_summary.csv``
    Overall quality and runtime metrics for each setup and rotation.
``comparison_summary_by_mean_sheets.csv``
    The overall summary sorted by mean sheet count, then median runtime.
``comparison_summary_by_workload.csv``
    Quality and runtime summaries split by dataset profile and part count.
``comparison_completion_summary.csv``
    Completion rates on the matched dataset subset used for quality
    analysis. These rates are complete by construction; use the full
    completion report above to inspect failures.
``comparison_to_best_observed_paired.csv``
    Per-dataset sheet-count comparison of each setup with the lowest
    sheet count observed across all included setups.
``comparison_to_best_observed_summary.csv``
    Aggregated wins, ties, losses and sheet-count differences against
    that retrospective best-observed reference.

The quality and paired-comparison files use only complete, layout-valid
runs on dataset/rotation pairs shared by every setup. The best-observed
reference is calculated from the supplied results; it is retrospective
and does not represent a configuration selected before the benchmark.
"""

import argparse
from pathlib import Path

import pandas as pd

from cutting_benchmark.comparison import (
    compare_sheet_counts,
    validate_comparison_inputs,
)
from cutting_benchmark.summaries import summarise_results


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_OUTPUT_DIR = DEFAULT_RESULTS_DIR / "comparison"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Summarise and compare benchmark CSV results from any "
            "compatible rectangle-packing solvers."
        )
    )
    parser.add_argument(
        "--results",
        nargs="+",
        type=Path,
        help=(
            "One or more benchmark result CSV files. If omitted, discover "
            "*_results.csv files under results/<source>/."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for comparison CSV outputs.",
    )
    return parser.parse_args()


def discover_result_files():
    return sorted(
        path
        for path in DEFAULT_RESULTS_DIR.glob("*/*_results.csv")
        if path.is_file()
    )


def source_label(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def load_results(paths):
    frames = []
    for path in paths:
        frame = pd.read_csv(path)
        source = source_label(path)
        if "solver" not in frame:
            frame["solver"] = path.parent.name or path.stem
        else:
            frame["solver"] = frame["solver"].fillna(
                path.parent.name or path.stem
            )
        frame["source"] = source
        frames.append(frame)

    if not frames:
        raise ValueError("No benchmark result CSV files were supplied or found")
    return pd.concat(frames, ignore_index=True, sort=False)


def run_is_usable(results):
    usable = results["complete"].eq(True)
    if "layout_valid" in results:
        usable &= (
            results["layout_valid"].isna()
            | results["layout_valid"].eq(True)
        )
    if "run_status" in results:
        usable &= (
            results["run_status"].isna()
            | results["run_status"].eq("solution_returned")
        )
    return usable


def make_completion_report(results):
    usable = run_is_usable(results)
    report = results.assign(_usable=usable).groupby(
        ["source", "solver", "config_id", "rotation"],
        as_index=False,
        dropna=False,
    ).agg(
        runs=("dataset_id", "size"),
        datasets=("dataset_id", "nunique"),
        complete_runs=("complete", "sum"),
        complete_valid_runs=("_usable", "sum"),
        median_runtime_seconds=("runtime_seconds", "median"),
    )
    report["completion_rate"] = report["complete_runs"] / report["runs"]
    report["usable_run_rate"] = (
        report["complete_valid_runs"] / report["runs"]
    )
    report["runs_not_complete_or_valid"] = (
        report["runs"] - report["complete_valid_runs"]
    )

    if "run_status" in results:
        no_solution = results.assign(
            _no_solution=results["run_status"].eq("no_solution_returned")
        ).groupby(
            ["source", "solver", "config_id", "rotation"],
            as_index=False,
            dropna=False,
        ).agg(no_solution_runs=("_no_solution", "sum"))
        report = report.merge(
            no_solution,
            on=["source", "solver", "config_id", "rotation"],
            how="left",
            validate="one_to_one",
        )
    else:
        report["no_solution_runs"] = 0

    return report.sort_values(
        ["completion_rate", "median_runtime_seconds"],
        ascending=[False, True],
        na_position="last",
    ).reset_index(drop=True)


def select_common_complete_results(results):
    usable = run_is_usable(results)
    setup_columns = ["source", "solver", "config_id"]
    run_group_columns = ["dataset_id", *setup_columns, "rotation"]
    per_dataset_setup = results.assign(_usable=usable).groupby(
        run_group_columns,
        dropna=False,
        as_index=False,
    ).agg(all_repeats_usable=("_usable", "all"))

    # A fair aggregate compares setups on the same datasets for each
    # rotation. If one repeat fails, exclude that dataset/setup as a whole.
    common_by_rotation = {}
    for rotation, rotation_rows in results.groupby("rotation", dropna=False):
        setups = rotation_rows[
            [*setup_columns]
        ].drop_duplicates()
        coverages = []
        for setup in setups.itertuples(index=False, name=None):
            source, solver, config_id = setup
            good_datasets = per_dataset_setup.loc[
                per_dataset_setup["rotation"].eq(rotation)
                & per_dataset_setup["source"].eq(source)
                & per_dataset_setup["solver"].eq(solver)
                & per_dataset_setup["config_id"].eq(config_id)
                & per_dataset_setup["all_repeats_usable"],
                "dataset_id",
            ]
            coverages.append(set(good_datasets))

        common_by_rotation[rotation] = (
            set.intersection(*coverages) if coverages else set()
        )

    eligible_keys = set()
    for row in per_dataset_setup.itertuples(index=False):
        if (
            row.all_repeats_usable
            and row.dataset_id
            in common_by_rotation.get(row.rotation, set())
        ):
            eligible_keys.add(
                (
                    row.dataset_id,
                    row.source,
                    row.solver,
                    row.config_id,
                    row.rotation,
                )
            )

    row_keys = zip(
        results["dataset_id"],
        results["source"],
        results["solver"],
        results["config_id"],
        results["rotation"],
    )
    selected = results.loc[
        [key in eligible_keys for key in row_keys]
    ].copy()
    if selected.empty:
        raise ValueError(
            "No dataset/rotation pairs have complete, valid runs with "
            "coverage shared by every setup. Inspect the completion report."
        )
    return selected, common_by_rotation


def compare_each_setup_to_best(dataset_config):
    setup_columns = ["source", "solver", "config_id"]
    best_observed = (
        dataset_config
        .groupby(["dataset_id", "rotation"], as_index=False)
        .agg(sheets_used=("sheets_used", "min"))
    )

    paired_frames = []
    summary_frames = []
    for key, setup_results in dataset_config.groupby(
        [*setup_columns, "rotation"],
        dropna=False,
        sort=False,
    ):
        source, solver, config_id, rotation = key
        best_for_rotation = best_observed.loc[
            best_observed["rotation"].eq(rotation)
        ]
        comparison = compare_sheet_counts(
            best_for_rotation,
            setup_results,
        )
        paired_frames.append(
            comparison["paired"].assign(
                source=source,
                solver=solver,
                config_id=config_id,
            )
        )
        summary_frames.append(
            comparison["summary"].assign(
                source=source,
                solver=solver,
                config_id=config_id,
            )
        )

    return (
        pd.concat(paired_frames, ignore_index=True),
        pd.concat(summary_frames, ignore_index=True),
    )


def main():
    args = parse_args()
    result_paths = args.results or discover_result_files()
    if not result_paths:
        raise FileNotFoundError(
            "No *_results.csv files found under results/<source>/. "
            "Pass one or more files with --results."
        )

    results = load_results(result_paths)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    completion = make_completion_report(results)
    completion.to_csv(
        args.output_dir / "comparison_completion.csv",
        index=False,
    )

    comparable_results, common_by_rotation = select_common_complete_results(
        results
    )
    config_columns = ["source", "solver", "config_id", "rotation"]
    validate_comparison_inputs(comparable_results)
    tables = summarise_results(
        comparable_results,
        config_columns=config_columns,
    )

    summary_by_mean_sheets = (
        tables["summary"]
        .sort_values(
            ["rotation", "mean_sheets", "median_runtime"],
            na_position="last",
        )
        .reset_index(drop=True)
    )
    best_paired, best_summary = compare_each_setup_to_best(
        tables["dataset_config"]
    )

    outputs = {
        "comparison_dataset_config.csv": tables["dataset_config"],
        "comparison_summary.csv": tables["summary"],
        "comparison_summary_by_mean_sheets.csv": summary_by_mean_sheets,
        "comparison_summary_by_workload.csv": tables[
            "summary_by_workload"
        ],
        "comparison_completion_summary.csv": tables[
            "completion_summary"
        ],
        "comparison_to_best_observed_paired.csv": best_paired,
        "comparison_to_best_observed_summary.csv": best_summary,
    }
    for filename, table in outputs.items():
        table.to_csv(args.output_dir / filename, index=False)

    excluded_dataset_counts = {
        str(rotation): int(
            results.loc[
                results["rotation"].eq(rotation), "dataset_id"
            ].nunique()
            - len(dataset_ids)
        )
        for rotation, dataset_ids in common_by_rotation.items()
    }
    print(f"Input files: {len(result_paths)}")
    for path in result_paths:
        print(f"  {path}")
    print(f"Setup/rotation rows in completion report: {len(completion)}")
    print(
        "Runs not complete or layout-valid: "
        f"{int(completion['runs_not_complete_or_valid'].sum())}"
    )
    print(
        "Common comparable datasets by rotation: "
        + str({str(key): len(value) for key, value in common_by_rotation.items()})
    )
    print(f"Datasets excluded by rotation: {excluded_dataset_counts}")
    print(f"Comparison outputs: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
