"""Tests for repeat-safe report tables and paired comparisons."""

import pandas as pd
import pytest

from cutting_benchmark.comparison import compare_sheet_counts, validate_comparison_inputs
from cutting_benchmark.summaries import summarise_results


def counts(values, ids=("a", "b", "c")):
    return pd.DataFrame({"dataset_id": ids, "rotation": False, "sheets_used": values})


def test_pairing_counts_wins_ties_losses():
    result = compare_sheet_counts(counts([3, 4, 5]), counts([2, 4, 6]))
    row = result["summary"].iloc[0]
    assert (row.candidate_wins, row.ties, row.candidate_losses) == (1, 1, 1)
    assert row.sheets_saved == 0
    assert row.relative_reduction == 0


def test_pairing_rejects_unequal_coverage():
    with pytest.raises(ValueError, match="coverage"):
        compare_sheet_counts(counts([3, 4, 5]), counts([2, 4, 5], ids=("a", "b", "d")))


def test_pairing_rejects_duplicate_keys():
    baseline = counts([3, 4, 5])
    with pytest.raises(ValueError, match="Duplicate"):
        compare_sheet_counts(pd.concat([baseline, baseline]), counts([2, 4, 5]))


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan"), 1.5])
def test_pairing_rejects_invalid_counts(bad):
    with pytest.raises(ValueError):
        compare_sheet_counts(counts([3, 4, 5]), counts([bad, 4, 5]))


def raw_results():
    rows = []
    for repeat in [0, 1]:
        for solver, sheets in [("baseline", 3), ("candidate", 2)]:
            rows.append(dict(
                dataset_id="a", rotation=False, complete=True,
                seed=0, profile="mixed", n_parts=2, parts_total=2,
                sheet_width=10, sheet_height=10, available_sheets=3,
                requested_area=100, solver=solver, config_id="config",
                repeat=repeat, sheets_used=sheets, utilisation=1/sheets,
                area_fraction=1.0, part_fraction=1.0,
                sheet_gap_to_area_bound=sheets-1, runtime_seconds=1.0,
            ))
    return pd.DataFrame(rows)


def test_totals_do_not_count_repeats_as_orders():
    tables = summarise_results(raw_results())
    result = tables["summary"].set_index("solver")
    assert result.loc["baseline", "total_sheets"] == 3
    assert result.loc["candidate", "total_sheets"] == 2
    assert result.loc["candidate", "best_or_tied_datasets"] == 1


def test_metadata_conflict_is_rejected():
    frame = raw_results()
    frame.loc[0, "requested_area"] = 99
    with pytest.raises(ValueError, match="Conflicting"):
        validate_comparison_inputs(frame)


def test_missing_optional_validation_is_not_a_failure():
    frame = raw_results()
    frame["layout_valid"] = None
    validate_comparison_inputs(frame)
    frame.loc[0, "layout_valid"] = False
    with pytest.raises(ValueError, match="validation failure"):
        validate_comparison_inputs(frame)


def test_incomplete_run_is_rejected():
    frame = raw_results()
    frame.loc[0, "complete"] = False
    with pytest.raises(ValueError, match="Incomplete"):
        validate_comparison_inputs(frame)