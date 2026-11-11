"""Tests for rectangle dataset generation and JSON persistence."""

import pytest

from cutting_benchmark.rectangle_datasets import (
    make_dataset,
    save_datasets,
    load_datasets,
)


def test_make_dataset_is_reproducible():
    """Identical inputs produce identical datasets."""
    first = make_dataset(
        seed=42,
        n_parts=20,
        profile="mixed",
        sheet_size=(2500, 1250),
    )

    second = make_dataset(
        seed=42,
        n_parts=20,
        profile="mixed",
        sheet_size=(2500, 1250),
    )

    assert first == second


@pytest.mark.parametrize(
    "profile",
    ["mixed", "strips", "large_and_small"],
)
def test_generated_parts_are_valid(profile):
    """Each profile produces the requested number of valid parts."""
    sheet_size = (2500, 1250)

    dataset = make_dataset(
        seed=42,
        n_parts=20,
        profile=profile,
        sheet_size=sheet_size,
    )

    parts = dataset["parts"]
    sheet_width, sheet_height = sheet_size

    assert dataset["n_parts"] == 20
    assert len(parts) == 20
    assert dataset["profile"] == profile
    assert dataset["seed"] == 42
    assert dataset["sheet_size"] == sheet_size

    part_ids = [
        part_id
        for part_id, _, _ in parts
    ]

    assert len(set(part_ids)) == len(part_ids)

    for _, width, height in parts:
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert 0 < width <= sheet_width
        assert 0 < height <= sheet_height


def test_dataset_id_records_generation_settings():
    """The dataset ID includes the agreed identifying components."""
    dataset = make_dataset(
        seed=42,
        n_parts=20,
        profile="strips",
        sheet_size=(2000, 1000),
    )

    assert dataset["dataset_id"] == (
        "rect_v1_strips_sheet2000x1000_n20_seed42"
    )


def test_save_and_load_preserve_datasets(tmp_path):
    """Saving and loading restores the complete dataset collection."""
    datasets = [
        make_dataset(
            seed=seed,
            n_parts=10,
            profile=profile,
            sheet_size=(2500, 1250),
        )
        for seed, profile in [
            (0, "mixed"),
            (1, "strips"),
            (2, "large_and_small"),
        ]
    ]

    output_path = (
        tmp_path
        / "nested"
        / "datasets.json"
    )

    save_datasets(datasets, output_path)

    assert output_path.is_file()

    loaded_datasets = load_datasets(output_path)

    assert loaded_datasets == datasets