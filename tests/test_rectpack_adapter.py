"""Tests for Rectpack result conversion using a fake packer."""

import pytest

from cutting_benchmark.solvers import rectpack_adapter


class FakePacker:
    def __init__(self, placements, used_sheets):
        self.placements = placements
        self.used_sheets = used_sheets
        self.rectangles = []
        self.bins_added = []
        self.packed = False

    def add_rect(self, width, height, rid):
        self.rectangles.append((width, height, rid))

    def add_bin(self, width, height, count):
        self.bins_added.append((width, height, count))

    def pack(self):
        self.packed = True

    def rect_list(self):
        return self.placements

    def bin_list(self):
        return self.used_sheets


def make_fake_packer(monkeypatch, placements, used_sheets):
    created = []

    def new_packer(**kwargs):
        packer = FakePacker(placements, used_sheets)
        packer.options = kwargs
        created.append(packer)
        return packer

    monkeypatch.setattr(rectpack_adapter, "newPacker", new_packer)
    return created


def test_valid_complete_layout_returns_metrics_and_optional_layout(monkeypatch):
    placements = [
        (0, 0, 0, 5, 10, "A"),
        (0, 5, 0, 5, 10, "B"),
    ]
    packers = make_fake_packer(
        monkeypatch,
        placements=placements,
        used_sheets=[(10, 10)],
    )

    result = rectpack_adapter.run_pack(
        parts=[("A", 5, 10), ("B", 5, 10)],
        algorithm="MaxRectsBssf",
        sort="input_order",
        rotation=False,
        sheet_size=(10, 10),
        return_layout=True,
    )

    assert result["solver"] == "rectpack"
    assert result["layout_valid"] is True
    assert result["parts_packed"] == 2
    assert result["complete"] is True
    assert result["sheets_used"] == 1
    assert result["placements"] == placements
    assert result["used_sheets"] == [(10, 10)]
    assert packers[0].packed
    assert packers[0].rectangles == [(5, 10, "A"), (5, 10, "B")]
    assert packers[0].bins_added == [(10, 10, 2)]


def test_valid_partial_layout_is_not_marked_complete(monkeypatch):
    make_fake_packer(
        monkeypatch,
        placements=[(0, 0, 0, 5, 5, "A")],
        used_sheets=[(10, 10)],
    )

    result = rectpack_adapter.run_pack(
        parts=[("A", 5, 5), ("B", 5, 5)],
        algorithm="MaxRectsBssf",
        sort="area",
        rotation=False,
        sheet_size=(10, 10),
    )

    assert result["layout_valid"] is True
    assert result["parts_packed"] == 1
    assert result["complete"] is False
    assert "placements" not in result


def test_invalid_layout_raises_validation_error(monkeypatch):
    make_fake_packer(
        monkeypatch,
        placements=[
            (0, 0, 0, 6, 10, "A"),
            (0, 5, 0, 5, 10, "B"),
        ],
        used_sheets=[(10, 10)],
    )

    with pytest.raises(ValueError, match="Invalid Rectpack layout"):
        rectpack_adapter.run_pack(
            parts=[("A", 6, 10), ("B", 5, 10)],
            algorithm="MaxRectsBssf",
            sort="input_order",
            rotation=False,
            sheet_size=(10, 10),
        )
