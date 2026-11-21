"""Tests for benchmark orchestration using stub solver functions."""

import pytest

from cutting_benchmark.benchmark import run_benchmark


def make_dataset(dataset_id, seed):
    return {
        "dataset_id": dataset_id,
        "seed": seed,
        "profile": "test",
        "n_parts": 1,
        "parts": [(f"part-{dataset_id}", 2, 3)],
        "sheet_size": (10, 10),
    }


def test_records_each_dataset_configuration_and_repeat():
    datasets = [make_dataset("A", 1), make_dataset("B", 2)]
    configurations = [
        {"setting": "first"},
        {"setting": "second"},
    ]
    calls = []

    def solver(parts, sheet_size, available_sheets, setting):
        calls.append((parts, sheet_size, available_sheets, setting))
        return {"parts_packed": 1, "complete": True}

    results = run_benchmark(
        datasets=datasets,
        configurations=configurations,
        solver=solver,
        repeats=2,
        available_sheets=4,
    )

    assert len(results) == 8
    assert len(calls) == 8
    assert set(results["dataset_id"]) == {"A", "B"}
    assert set(results["seed"]) == {1, 2}
    assert set(results["profile"]) == {"test"}
    assert set(results["n_parts"]) == {1}
    assert set(results["repeat"]) == {0, 1}
    assert set(results["run_status"]) == {"solution_returned"}
    assert all(call[2] == 4 for call in calls)


def test_preserves_no_solution_status():
    dataset = make_dataset("A", 1)

    results = run_benchmark(
        datasets=[dataset],
        configurations=[{"setting": "limited"}],
        solver=lambda **kwargs: {
            "run_status": "no_solution_returned",
            "complete": False,
            "parts_packed": 0,
        },
    )

    assert results.loc[0, "run_status"] == "no_solution_returned"
    assert not bool(results.loc[0, "complete"])
    assert results.loc[0, "parts_packed"] == 0


def test_wraps_solver_error_with_dataset_configuration_and_repeat():
    dataset = make_dataset("bad-dataset", 7)

    def solver(**kwargs):
        raise ValueError("invalid fake input")

    with pytest.raises(RuntimeError) as exc_info:
        run_benchmark(
            datasets=[dataset],
            configurations=[{"setting": "test"}],
            solver=solver,
            repeats=1,
        )

    message = str(exc_info.value)
    assert "dataset_id=bad-dataset" in message
    assert "configuration={'setting': 'test'}" in message
    assert "repeat=0" in message
    assert "Original error: invalid fake input" in message
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_rejects_nonpositive_repeats():
    with pytest.raises(ValueError, match="repeats must be positive"):
        run_benchmark([], [], lambda **kwargs: {}, repeats=0)

