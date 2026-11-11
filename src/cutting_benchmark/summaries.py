def summarise_results(results, config_columns=None):
    """Build summary tables for complete-order packing benchmarks.

    Parameters
    ----------
    results : pandas.DataFrame
        Per-run benchmark results containing dataset metadata,
        configuration identifiers, repeat identifiers, quality metrics
        and runtime_seconds.
    config_columns : sequence of str or None, optional
        Columns that jointly identify each configuration.
        Defaults to ["solver", "config_id", "rotation"].
        Must include rotation.

    Returns
    -------
    dict of str to pandas.DataFrame
        Dictionary containing:

        dataset_config
            One row per dataset and configuration. Identical quality
            metrics are retained and runtime is reduced to the median
            across repeats. Includes best-observed comparisons.
        completion_summary
            Dataset counts and completion rates by configuration.
            Returned only when all summary checks succeed.
        summary
            Overall metrics by configuration, including sheet count,
            utilisation, relative excess, tied-best rate and runtime.
        summary_by_workload
            The same aggregate metrics grouped additionally by profile
            and n_parts.

    Raises
    ------
    ValueError
        If results is empty, required columns are missing, rotation
        is absent from config_columns, identifiers contain missing
        values or duplicate run identifiers are found.
    ValueError
        If repeated runs have different quality metrics, configurations
        have different dataset coverage within a rotation setting,
        any order is incomplete or a complete order has a missing
        or nonpositive sheet count.

    Notes
    -----
    Best-observed sheet count is calculated separately for each
    dataset and rotation setting across the supplied configurations.

    Relative excess is sheets_used / best_observed_sheets - 1.
    Every configuration matching the best observed count receives
    credit in the tied-best rate.

    Overall metrics weight each dataset equally after repeat aggregation.
    Median and P95 runtime are calculated across per-dataset median
    runtimes, not directly across all individual runs.

    Only compare results with matching problem definitions, including
    objectives, stock availability and cutting constraints. The function
    does not automatically verify these assumptions.

    Best observed does not imply proven optimality. The gap to the
    area lower bound is also not a proven optimality gap.

    The function does not modify the input DataFrame, save files
    or format values for display.
    """
    if config_columns is None:
        config_columns = ["solver", "config_id", "rotation"]
    else:
        config_columns = list(config_columns)

    if results.empty:
        raise ValueError("The results table is empty")

    if "rotation" not in config_columns:
        raise ValueError("config_columns must include rotation")

    dataset_columns = ["dataset_id", "profile", "n_parts"]

    quality_columns = [
        "complete",
        "sheets_used",
        "utilisation",
        "area_fraction",
        "part_fraction",
        "sheet_gap_to_area_bound",
    ]

    required_columns = {
        *dataset_columns,
        *config_columns,
        *quality_columns,
        "repeat",
        "runtime_seconds",
    }

    missing = required_columns - set(results.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    keys = [*dataset_columns, *config_columns]

    if results[keys + ["repeat"]].isna().any().any():
        raise ValueError(
            "Dataset, configuration and repeat identifiers "
            "must not contain missing values"
        )

    run_keys = ["dataset_id", *config_columns, "repeat"]

    if results.duplicated(run_keys).any():
        raise ValueError(
            "Duplicate dataset–configuration–repeat rows found"
        )

    grouped = results.groupby(
        keys,
        dropna=False,
        sort=False,
    )

    variation = grouped[quality_columns].nunique(dropna=False)

    if variation.gt(1).any().any():
        raise ValueError(
            "Repeated runs have different solution quality. "
            "Choose a repeat-aggregation policy before summarising."
        )

    dataset_config = grouped.agg(
        complete=("complete", "first"),
        sheets_used=("sheets_used", "first"),
        utilisation=("utilisation", "first"),
        area_fraction=("area_fraction", "first"),
        part_fraction=("part_fraction", "first"),
        sheet_gap_to_area_bound=(
            "sheet_gap_to_area_bound", "first"
        ),
        runtime_seconds=("runtime_seconds", "median"),
    ).reset_index()

    completion_summary = (
        dataset_config
        .groupby(
            config_columns,
            as_index=False,
            dropna=False,
        )
        .agg(
            datasets=("dataset_id", "nunique"),
            completion_rate=("complete", "mean"),
        )
    )

    # Check coverage separately for each rotation setting.
    method_columns = [
        column
        for column in config_columns
        if column != "rotation"
    ]

    if method_columns:
        for _, rotation_results in dataset_config.groupby(
            "rotation",
            dropna=False,
        ):
            coverage = [
                frozenset(group["dataset_id"])
                for _, group in rotation_results.groupby(
                    method_columns,
                    dropna=False,
                )
            ]

            if any(ids != coverage[0] for ids in coverage[1:]):
                raise ValueError(
                    "Configurations cover different dataset sets "
                    "within a rotation setting."
                )

    if not dataset_config["complete"].eq(True).all():
        raise ValueError(
            "Some runs did not pack the full order. "
            "Inspect results where complete is False "
            "before comparing sheet counts."
        )

    if (
        dataset_config["sheets_used"].isna().any()
        or dataset_config["sheets_used"].le(0).any()
    ):
        raise ValueError(
            "Complete nonempty orders must use at least one sheet"
        )

    comparison_columns = ["dataset_id", "rotation"]

    dataset_config["best_observed_sheets"] = (
        dataset_config
        .groupby(comparison_columns)["sheets_used"]
        .transform("min")
    )

    dataset_config["extra_sheets_vs_best"] = (
        dataset_config["sheets_used"]
        - dataset_config["best_observed_sheets"]
    )

    dataset_config["relative_excess"] = (
        dataset_config["sheets_used"]
        / dataset_config["best_observed_sheets"]
        - 1
    )

    dataset_config["tied_best"] = (
        dataset_config["extra_sheets_vs_best"].eq(0)
    )

    def aggregate(group_columns):
        return (
            dataset_config
            .groupby(
                group_columns,
                as_index=False,
                dropna=False,
            )
            .agg(
                datasets=("dataset_id", "nunique"),
                mean_sheets=("sheets_used", "mean"),
                mean_utilisation=("utilisation", "mean"),
                mean_extra_sheets=(
                    "extra_sheets_vs_best", "mean"
                ),
                mean_relative_excess=(
                    "relative_excess", "mean"
                ),
                tied_best_rate=("tied_best", "mean"),
                mean_gap_to_area_bound=(
                    "sheet_gap_to_area_bound", "mean"
                ),
                median_runtime=("runtime_seconds", "median"),
                p95_runtime=(
                    "runtime_seconds",
                    lambda values: values.quantile(0.95),
                ),
            )
        )

    summary = (
        aggregate(config_columns)
        .sort_values(
            ["rotation", "mean_relative_excess", "median_runtime"]
        )
        .reset_index(drop=True)
    )

    summary_by_workload = (
        aggregate(["profile", "n_parts", *config_columns])
        .sort_values(
            [
                "profile",
                "n_parts",
                "rotation",
                "mean_relative_excess",
                "median_runtime",
            ]
        )
        .reset_index(drop=True)
    )

    return {
        "dataset_config": dataset_config,
        "completion_summary": completion_summary,
        "summary": summary,
        "summary_by_workload": summary_by_workload,
    }