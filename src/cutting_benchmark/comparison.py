"""Checks and paired sheet-count comparisons for complete-order benchmarks."""

import pandas as pd


def validate_comparison_inputs(results):
    """Check metadata agreement before calling summarise_results.

    Parameters
    ----------
    results : pandas.DataFrame
        Combined raw results. Dataset IDs must identify the same input
        across configurations. All runs must be complete.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        For empty data, absent/null metadata, conflicting metadata,
        incomplete runs, explicit unsuccessful status or failed validation.

    Notes
    -----
    Missing optional status/validation fields are allowed for historic
    results. Passing does not imply those layouts were validated.
    Objectives and manufacturing restrictions still require manual review.
    Coverage and repeat checks are performed by summarise_results.
    """
    metadata = [
        "seed", "profile", "n_parts", "sheet_width", "sheet_height",
        "available_sheets", "requested_area", "parts_total",
    ]
    required = ["dataset_id", "rotation", "complete", *metadata]
    missing = set(required) - set(results.columns)
    if missing:
        raise ValueError(f"Missing comparison columns: {sorted(missing)}")
    if results.empty or results[required].isna().any().any():
        raise ValueError("Comparison inputs must be nonempty with non-null metadata")
    if not results["complete"].eq(True).all():
        raise ValueError("Incomplete runs: inspect completion before ranking")
    if "run_status" in results:
        status = results["run_status"].dropna()
        if not status.eq("solution_returned").all():
            raise ValueError("Unsuccessful run status: inspect before ranking")
    if "layout_valid" in results:
        if not results["layout_valid"].dropna().eq(True).all():
            raise ValueError("Explicit layout validation failure")
    variation = results.groupby("dataset_id")[metadata].nunique(dropna=False)
    if variation.gt(1).any().any():
        raise ValueError("Conflicting metadata for the same dataset_id")


def compare_sheet_counts(baseline, candidate):
    """Pair complete-order, repeat-aggregated sheet counts.

    Parameters
    ----------
    baseline, candidate : pandas.DataFrame
        One row per (dataset_id, rotation), with a positive finite
        sheets_used value. Select one configuration or compute a
        per-dataset hindsight minimum before calling. Inputs must have
        identical dataset/rotation coverage and matching problem settings.

    Returns
    -------
    dict of str to pandas.DataFrame
        paired: counts, candidate outcome, sheets saved and reduction.
        summary: totals, reductions and candidate wins/ties/losses by rotation.

    Raises
    ------
    ValueError
        For empty inputs, invalid counts, duplicate keys or unequal coverage.

    Notes
    -----
    Positive sheets_saved means the candidate uses fewer sheets.
    Total reduction is total savings / total baseline sheets, not an
    average of per-order percentages. Runtime is not used as a tie-break.
    Call validate_comparison_inputs and summarise_results on raw inputs first.
    """
    keys = ["dataset_id", "rotation"]
    inputs = []
    for label, frame in [("baseline", baseline), ("candidate", candidate)]:
        missing = set([*keys, "sheets_used"]) - set(frame.columns)
        if missing:
            raise ValueError(f"Missing {label} columns: {sorted(missing)}")
        if frame.empty or frame[[*keys, "sheets_used"]].isna().any().any():
            raise ValueError(f"Empty or missing {label} data")
        if frame.duplicated(keys).any():
            raise ValueError(f"Duplicate {label} dataset/rotation keys")
        counts = pd.to_numeric(frame["sheets_used"], errors="coerce")
        if not (counts.gt(0) & counts.lt(float("inf")) & counts.mod(1).eq(0)).all():
            raise ValueError("Sheet counts must be positive finite integers")
        clean = frame[[*keys, "sheets_used"]].copy()
        clean["sheets_used"] = counts
        inputs.append(clean)
    paired = inputs[0].merge(
        inputs[1], on=keys, how="outer", validate="one_to_one",
        suffixes=("_baseline", "_candidate"), indicator=True,
    )
    if not paired["_merge"].eq("both").all():
        raise ValueError("Baseline and candidate have different dataset coverage")
    paired = paired.drop(columns="_merge")
    paired["sheets_saved"] = paired["sheets_used_baseline"] - paired["sheets_used_candidate"]
    paired["relative_reduction"] = paired["sheets_saved"] / paired["sheets_used_baseline"]
    paired["candidate_outcome"] = "tie"
    paired.loc[paired["sheets_saved"].gt(0), "candidate_outcome"] = "win"
    paired.loc[paired["sheets_saved"].lt(0), "candidate_outcome"] = "loss"
    paired = paired.sort_values(keys).reset_index(drop=True)
    summary = paired.groupby("rotation", as_index=False).agg(
        datasets=("dataset_id", "size"),
        baseline_total_sheets=("sheets_used_baseline", "sum"),
        candidate_total_sheets=("sheets_used_candidate", "sum"),
        sheets_saved=("sheets_saved", "sum"),
        candidate_wins=("candidate_outcome", lambda x: x.eq("win").sum()),
        ties=("candidate_outcome", lambda x: x.eq("tie").sum()),
        candidate_losses=("candidate_outcome", lambda x: x.eq("loss").sum()),
    )
    summary["relative_reduction"] = summary["sheets_saved"] / summary["baseline_total_sheets"]
    return {"paired": paired, "summary": summary}