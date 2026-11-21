"""Tests for PackingSolver certificate conversion with a fake solver."""

import csv
from types import SimpleNamespace

import pytest

CSV_COLUMNS = ["TYPE", "BIN", "COPIES", "LX", "LY", "ID", "X", "Y"]


class FakeSolution:
    def __init__(self, rows):
        self.rows = rows

    def write(self, path):
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_COLUMNS)
            writer.writerows(self.rows)


class FakeBuilder:
    def __init__(self):
        self.bin_types = []
        self.item_types = []

    def set_objective(self, objective):
        self.objective = objective

    def add_bin_type(self, width, height, copies):
        self.bin_types.append((width, height, copies))

    def add_item_type(self, width, height, copies, oriented):
        item_type_id = len(self.item_types)
        self.item_types.append((width, height, copies, oriented))
        return item_type_id

    def build(self):
        return self


class FakeParameters:
    def __init__(self):
        self.time_limit = None


@pytest.fixture
def adapter():
    pytest.importorskip("packingsolver.rectangle")
    from cutting_benchmark.solvers import packingsolver_adapter

    return packingsolver_adapter


def install_fake_solver(monkeypatch, adapter, certificate_rows):
    builders = []
    parameters = []

    def make_builder():
        builder = FakeBuilder()
        builders.append(builder)
        return builder

    def make_parameters():
        value = FakeParameters()
        parameters.append(value)
        return value

    def optimize(instance, optimize_parameters):
        return type(
            "FakeOutput",
            (),
            {"solution": FakeSolution(certificate_rows)},
        )()

    monkeypatch.setattr(
        adapter,
        "psr",
        SimpleNamespace(
            InstanceBuilder=make_builder,
            Objective=SimpleNamespace(BinPacking=object()),
            OptimizeParameters=make_parameters,
            optimize=optimize,
        ),
    )
    return builders, parameters


def test_populated_certificate_returns_valid_layout_and_metrics(
    monkeypatch,
    adapter,
):
    rows = [
        ["BIN", 0, 1, 10, 10, "", "", ""],
        ["ITEM", 0, "", 5, 10, 0, 0, 0],
        ["ITEM", 0, "", 5, 10, 1, 5, 0],
    ]
    builders, parameters = install_fake_solver(monkeypatch, adapter, rows)

    result = adapter.run_pack(
        parts=[("A", 5, 10), ("B", 5, 10)],
        rotation=False,
        time_limit=7,
        sheet_size=(10, 10),
        return_layout=True,
    )

    assert result["solver"] == "packingsolver"
    assert result["layout_valid"] is True
    assert result["parts_packed"] == 2
    assert result["complete"] is True
    assert result["sheets_used"] == 1
    assert result["placements"] == [
        (0, 0, 0, 5, 10, "A"),
        (0, 5, 0, 5, 10, "B"),
    ]
    assert builders[0].bin_types == [(10, 10, 2)]
    assert builders[0].item_types == [
        (5, 10, 1, True),
        (5, 10, 1, True),
    ]
    assert parameters[0].time_limit == 7


def test_empty_certificate_is_reported_as_no_solution(monkeypatch, adapter):
    install_fake_solver(monkeypatch, adapter, certificate_rows=[])

    result = adapter.run_pack(
        parts=[("A", 5, 10)],
        rotation=False,
        sheet_size=(10, 10),
    )

    assert result["run_status"] == "no_solution_returned"
    assert result["layout_valid"] is False
    assert result["parts_packed"] == 0
    assert result["complete"] is False
    assert result["sheets_used"] == 0


def test_overlapping_certificate_raises_validation_error(
    monkeypatch,
    adapter,
):
    rows = [
        ["BIN", 0, 1, 10, 10, "", "", ""],
        ["ITEM", 0, "", 6, 10, 0, 0, 0],
        ["ITEM", 0, "", 5, 10, 1, 5, 0],
    ]
    install_fake_solver(monkeypatch, adapter, rows)

    with pytest.raises(ValueError, match="Invalid PackingSolver layout"):
        adapter.run_pack(
            parts=[("A", 6, 10), ("B", 5, 10)],
            rotation=False,
            sheet_size=(10, 10),
        )
