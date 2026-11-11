"""Tests for benchmark summary calculations."""

import pandas as pd
import pytest

from cutting_benchmark.summaries import summarise_results


@pytest.fixture
def benchmark_results():
    """Provide two datasets, two configurations and two repeats."""
    records = []

    datasets = [
        {
            "dataset_id": "dataset_1",
            "profile": "mixed",
            "n_parts": 10,
            "area_lower_bound": 2,
        },
        {
            "dataset_id": "dataset_2",
            "profile": "strips",
            "n_parts": 20,
            "area_lower_bound": 3,
        },
    ]

    sheets = {
        ("dataset_1", "A"): 2,
        ("dataset_1", "B"): 3,
        ("dataset_2", "A"): 4,
        ("dataset_2", "B"): 4,
    }

    runtimes = {
        ("dataset_1", "A"): [1.0, 3.0],
        ("dataset_1", "B"): [2.0, 4.0],
        ("dataset_2", "A"): [3.0, 5.0],
        ("dataset_2", "B"): [2.0, 4.0],
    }

    for dataset in datasets:
        dataset_id = dataset["dataset_id"]

        for config_id in ["A", "B"]:
            sheets_used = sheets[(dataset_id, config_id)]

            for repeat in range(2):
                records.append({
                    "dataset_id": dataset_id,
                    "profile": dataset["profile"],
                    "n_parts": dataset["n_parts"],
                    "solver": "test_solver",
                    "config_id": config_id,
                    "rotation": False,
                    "repeat": repeat,
                    "complete": True,
                    "sheets_used": sheets_used,
                    "utilisation": 1.0 / sheets_used,
                    "area_fraction": 1.0,
                    "part_fraction": 1.0,
                    "sheet_gap_to_area_bound": (
                        sheets_used - dataset["area_lower_bound"]
                    ),
                    "runtime_seconds": runtimes[
                        (dataset_id, config_id)
                    ][repeat],
                })

    return pd.DataFrame(records)


def test_summary_returns_expected_tables(benchmark_results):
    """The function returns the expected tables and row counts."""
    tables = summarise_results(benchmark_results)

    assert set(tables) == {
        "dataset_config",
        "completion_summary",
        "summary",
        "summary_by_workload",
    }

    assert len(tables["dataset_config"]) == 4
    assert len(tables["completion_summary"]) == 2
    assert len(tables["summary"]) == 2
    assert len(tables["summary_by_workload"]) == 4

    completion = tables["completion_summary"]

    assert completion["datasets"].eq(2).all()
    assert completion["completion_rate"].eq(1.0).all()

    workload = tables["summary_by_workload"]

    assert set(workload["profile"]) == {"mixed", "strips"}
    assert workload["datasets"].eq(1).all()


def test_best_observed_comparisons(benchmark_results):
    """Sheet overhead and ties use the best result on each dataset."""
    tables = summarise_results(benchmark_results)

    per_dataset = tables["dataset_config"].set_index(
        ["dataset_id", "config_id"]
    )

    assert (
        per_dataset.loc[
            ("dataset_1", "B"), "best_observed_sheets"
        ]
        == 2
    )

    assert (
        per_dataset.loc[
            ("dataset_1", "B"), "extra_sheets_vs_best"
        ]
        == 1
    )

    assert per_dataset.loc[
        ("dataset_1", "B"), "relative_excess"
    ] == pytest.approx(0.5)

    summary = tables["summary"].set_index("config_id")

    assert summary.loc["A", "mean_sheets"] == pytest.approx(3.0)
    assert summary.loc["B", "mean_sheets"] == pytest.approx(3.5)

    assert summary.loc[
        "A", "mean_relative_excess"
    ] == pytest.approx(0.0)

    assert summary.loc[
        "B", "mean_relative_excess"
    ] == pytest.approx(0.25)

    assert summary.loc["A", "tied_best_rate"] == pytest.approx(1.0)
    assert summary.loc["B", "tied_best_rate"] == pytest.approx(0.5)


def test_runtime_aggregation(benchmark_results):
    """Runtime is reduced across repeats before overall aggregation."""
    tables = summarise_results(benchmark_results)

    per_dataset = tables["dataset_config"].set_index(
        ["dataset_id", "config_id"]
    )

    assert per_dataset.loc[
        ("dataset_1", "A"), "runtime_seconds"
    ] == pytest.approx(2.0)

    assert per_dataset.loc[
        ("dataset_2", "A"), "runtime_seconds"
    ] == pytest.approx(4.0)

    summary = tables["summary"].set_index("config_id")

    assert summary.loc["A", "median_runtime"] == pytest.approx(3.0)
    assert summary.loc["A", "p95_runtime"] == pytest.approx(3.9)


def test_input_results_are_not_modified(benchmark_results):
    """Summary calculations leave the supplied DataFrame unchanged."""
    original = benchmark_results.copy(deep=True)

    summarise_results(benchmark_results)

    pd.testing.assert_frame_equal(
        benchmark_results,
        original,
    )


def test_incomplete_orders_are_rejected(benchmark_results):
    """Incomplete orders cannot enter complete-order comparisons."""
    results = benchmark_results.copy()

    mask = (
        results["dataset_id"].eq("dataset_1")
        & results["config_id"].eq("A")
    )

    # Change both repeats to avoid triggering repeat inconsistency first.
    results.loc[mask, "complete"] = False

    with pytest.raises(ValueError, match="full order"):
        summarise_results(results)


def test_duplicate_runs_are_rejected(benchmark_results):
    """A dataset–configuration–repeat combination must be unique."""
    results = pd.concat(
        [benchmark_results, benchmark_results.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        summarise_results(results)


def test_varying_repeat_quality_is_rejected(benchmark_results):
    """Different quality across repeats requires an explicit policy."""
    results = benchmark_results.copy()

    results.loc[0, "sheets_used"] = 99

    with pytest.raises(
        ValueError,
        match="different solution quality",
    ):
        summarise_results(results)


def test_mismatched_dataset_coverage_is_rejected(benchmark_results):
    """Configurations must cover the same datasets."""
    mask = (
        benchmark_results["dataset_id"].eq("dataset_2")
        & benchmark_results["config_id"].eq("B")
    )

    results = benchmark_results.loc[~mask].copy()

    with pytest.raises(
        ValueError,
        match="different dataset sets",
    ):
        summarise_results(results)


def test_missing_required_column_is_rejected(benchmark_results):
    """Missing required metrics produce a clear error."""
    results = benchmark_results.drop(
        columns=["runtime_seconds"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        summarise_results(results)