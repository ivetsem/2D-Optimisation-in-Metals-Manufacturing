"""Tests for metrics calculated from rectangle-packing layouts."""

import math

import pytest

from cutting_benchmark.rectangle_metrics import (
    calculate_rectangle_metrics,
)


def test_complete_layout_metrics():
    """A complete layout produces the expected counts and areas."""
    metrics = calculate_rectangle_metrics(
        parts=[
            ("A", 4, 5),
            ("B", 6, 5),
        ],
        placements=[
            (0, 0, 0, 4, 5, "A"),
            (0, 4, 0, 6, 5, "B"),
        ],
        used_sheets=[(10, 10)],
        sheet_size=(10, 10),
        rotation=False,
    )

    assert metrics["parts_total"] == 2
    assert metrics["parts_packed"] == 2
    assert metrics["complete"] is True
    assert metrics["individually_feasible"] is True

    assert metrics["sheets_used"] == 1
    assert metrics["requested_area"] == 50
    assert metrics["packed_area"] == 50

    assert metrics["part_fraction"] == pytest.approx(1.0)
    assert metrics["area_fraction"] == pytest.approx(1.0)
    assert metrics["utilisation"] == pytest.approx(0.5)

    assert metrics["area_lower_bound"] == 1
    assert metrics["sheet_gap_to_area_bound"] == 0


def test_incomplete_layout_metrics():
    """An incomplete layout records partial coverage and no sheet gap."""
    metrics = calculate_rectangle_metrics(
        parts=[
            ("A", 4, 5),
            ("B", 6, 5),
        ],
        placements=[
            (0, 0, 0, 4, 5, "A"),
        ],
        used_sheets=[(10, 10)],
        sheet_size=(10, 10),
        rotation=False,
    )

    assert metrics["parts_total"] == 2
    assert metrics["parts_packed"] == 1
    assert metrics["complete"] is False

    assert metrics["requested_area"] == 50
    assert metrics["packed_area"] == 20

    assert metrics["part_fraction"] == pytest.approx(0.5)
    assert metrics["area_fraction"] == pytest.approx(0.4)
    assert metrics["utilisation"] == pytest.approx(0.2)

    assert math.isnan(metrics["sheet_gap_to_area_bound"])


def test_empty_layout_metrics():
    """Packing no parts produces zero coverage and zero utilisation."""
    metrics = calculate_rectangle_metrics(
        parts=[
            ("A", 4, 5),
            ("B", 6, 5),
        ],
        placements=[],
        used_sheets=[],
        sheet_size=(10, 10),
        rotation=False,
    )

    assert metrics["complete"] is False
    assert metrics["parts_packed"] == 0
    assert metrics["sheets_used"] == 0
    assert metrics["packed_area"] == 0

    assert metrics["part_fraction"] == pytest.approx(0.0)
    assert metrics["area_fraction"] == pytest.approx(0.0)
    assert metrics["utilisation"] == pytest.approx(0.0)

    assert metrics["area_lower_bound"] == 1
    assert math.isnan(metrics["sheet_gap_to_area_bound"])


def test_area_lower_bound_rounds_up():
    """A requested area of 120 on 100-area sheets gives a bound of two."""
    metrics = calculate_rectangle_metrics(
        parts=[
            ("A", 10, 6),
            ("B", 10, 6),
        ],
        placements=[
            (0, 0, 0, 10, 6, "A"),
            (1, 0, 0, 10, 6, "B"),
        ],
        used_sheets=[
            (10, 10),
            (10, 10),
        ],
        sheet_size=(10, 10),
        rotation=False,
    )

    assert metrics["requested_area"] == 120
    assert metrics["sheets_used"] == 2
    assert metrics["area_lower_bound"] == 2
    assert metrics["sheet_gap_to_area_bound"] == 0
    assert metrics["utilisation"] == pytest.approx(0.6)


def test_sheet_gap_uses_area_bound_not_geometric_optimum():
    """A valid packing can require more sheets than the area bound."""
    metrics = calculate_rectangle_metrics(
        parts=[
            ("A", 6, 6),
            ("B", 6, 6),
        ],
        placements=[
            (0, 0, 0, 6, 6, "A"),
            (1, 0, 0, 6, 6, "B"),
        ],
        used_sheets=[
            (10, 10),
            (10, 10),
        ],
        sheet_size=(10, 10),
        rotation=False,
    )

    assert metrics["complete"] is True
    assert metrics["requested_area"] == 72
    assert metrics["area_lower_bound"] == 1
    assert metrics["sheets_used"] == 2
    assert metrics["sheet_gap_to_area_bound"] == 1
    assert metrics["utilisation"] == pytest.approx(0.36)


@pytest.mark.parametrize(
    "rotation, placements, used_sheets, expected_feasible",
    [
        (False, [], [], False),
        (
            True,
            [(0, 0, 0, 7, 9, "A")],
            [(8, 10)],
            True,
        ),
    ],
)
def test_individual_feasibility_respects_rotation(
    rotation,
    placements,
    used_sheets,
    expected_feasible,
):
    """A 9-by-7 part fits an 8-by-10 sheet only after rotation."""
    metrics = calculate_rectangle_metrics(
        parts=[("A", 9, 7)],
        placements=placements,
        used_sheets=used_sheets,
        sheet_size=(8, 10),
        rotation=rotation,
    )

    assert (
        metrics["individually_feasible"]
        is expected_feasible
    )