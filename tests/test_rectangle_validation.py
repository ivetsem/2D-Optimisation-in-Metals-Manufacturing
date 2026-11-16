"""Test the shared rectangle-layout validator.

These tests use deliberately constructed layouts to check that the
validator accepts valid layouts and rejects specific invalid ones.
They do not run a solver or assess packing quality.

Covered cases:
- Rectangles touching at their edges are accepted.
- Overlapping rectangles are rejected.
- Partial layouts are accepted; completion is assessed separately.
- Duplicate part placements are rejected.
- Rotated parts are accepted only when rotation is allowed.
- Parts extending outside their sheet are rejected.

A passing rejection test means the validator correctly identified
the deliberately invalid layout.
"""

from cutting_benchmark.rectangle_validation import (
    validate_rectangle_layout,
)


def check(parts, placements, rotation=False):
    return validate_rectangle_layout(
        parts=parts,
        placements=placements,
        used_sheets=[(10, 10)],
        sheet_size=(10, 10),
        rotation=rotation,
    )


def test_edge_touching_is_valid():
    result = check(
        parts=[("A", 5, 10), ("B", 5, 10)],
        placements=[
            (0, 0, 0, 5, 10, "A"),
            (0, 5, 0, 5, 10, "B"),
        ],
    )

    assert result["layout_valid"]


def test_overlap_is_invalid():
    result = check(
        parts=[("A", 6, 10), ("B", 5, 10)],
        placements=[
            (0, 0, 0, 6, 10, "A"),
            (0, 5, 0, 5, 10, "B"),
        ],
    )

    assert not result["layout_valid"]


def test_partial_layout_is_valid():
    result = check(
        parts=[("A", 5, 5), ("B", 5, 5)],
        placements=[(0, 0, 0, 5, 5, "A")],
    )

    assert result["layout_valid"]


def test_duplicate_placement_is_invalid():
    result = check(
        parts=[("A", 5, 5), ("B", 5, 5)],
        placements=[
            (0, 0, 0, 5, 5, "A"),
            (0, 5, 0, 5, 5, "A"),
        ],
    )

    assert not result["layout_valid"]


def test_rotation_must_be_allowed():
    parts = [("A", 3, 7)]
    placements = [(0, 0, 0, 7, 3, "A")]

    assert not check(parts, placements, rotation=False)["layout_valid"]
    assert check(parts, placements, rotation=True)["layout_valid"]


def test_outside_sheet_is_invalid():
    result = check(
        parts=[("A", 5, 5)],
        placements=[(0, 6, 0, 5, 5, "A")],
    )

    assert not result["layout_valid"]