import math
import tempfile
import time
from pathlib import Path

import pandas as pd
import packingsolver.rectangle as psr

from cutting_benchmark.rectangle_metrics import (
    calculate_rectangle_metrics,
)
from cutting_benchmark.rectangle_validation import (
    validate_rectangle_layout,
)


def run_pack(
    parts,
    rotation,
    time_limit=5,
    sheet_size=(2500, 1250),
    available_sheets=None,
    return_layout=False,
):
    """Pack rectangles using PackingSolver's bin-packing objective.

    Parameters
    ----------
    parts : iterable of tuple
        Requested parts as (part_id, width, height).
        IDs must be unique and dimensions must be positive integers.
    rotation : bool
        Whether parts may rotate by 90 degrees.
    time_limit : int or float, optional
        Positive solver time limit in seconds.
    sheet_size : tuple of int, optional
        Identical sheet dimensions as (width, height).
    available_sheets : int or None, optional
        Positive stock limit. None allows one sheet per part.
    return_layout : bool, optional
        Include shared placements and used-sheet dimensions.

    Returns
    -------
    dict
        Solver settings, runtime, validation status and shared metrics.

    Raises
    ------
    ValueError
        For invalid inputs, unsupported certificate multiplicities,
        or an invalid extracted layout.
    RuntimeError
        If the exported solution contains no placed items or sheets.

    Notes
    -----
    Uses the BinPacking objective, with one item type per requested
    part. This adapter initially supports integer dimensions only.

    Runtime includes instance construction and optimisation. It
    excludes CSV export, extraction, validation and shared metrics.

    The CSV converter currently requires one physical sheet per
    BIN row. Unsupported multiplicities raise an error rather than
    producing misleading metrics.

    A missing solution is not converted into a partial-order result.
    No kerf, clearance, material matching or defects are modelled.
    """
    parts = list(parts)

    if not parts:
        raise ValueError("parts must not be empty")

    sheet_w, sheet_h = sheet_size

    dimensions = [
        sheet_w,
        sheet_h,
        *(dimension for _, w, h in parts for dimension in (w, h)),
    ]

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not value > 0
        or not float(value).is_integer()
        for value in dimensions
    ):
        raise ValueError("Dimensions must be positive integers")

    sheet_w, sheet_h = int(sheet_w), int(sheet_h)
    sheet_size = (sheet_w, sheet_h)

    parts = [
        (part_id, int(width), int(height))
        for part_id, width, height in parts
    ]

    ids = [part_id for part_id, _, _ in parts]

    if len(set(ids)) != len(ids):
        raise ValueError("Part IDs must be unique")

    if available_sheets is None:
        available_sheets = len(parts)

    if (
        isinstance(available_sheets, bool)
        or not isinstance(available_sheets, int)
        or available_sheets < 1
    ):
        raise ValueError("available_sheets must be a positive integer")

    if (
        isinstance(time_limit, bool)
        or not isinstance(time_limit, (int, float))
        or not 0 < time_limit < float("inf")
    ):
        raise ValueError("time_limit must be positive and finite")

    if not isinstance(rotation, bool):
        raise ValueError("rotation must be a boolean")

    start = time.perf_counter()

    builder = psr.InstanceBuilder()
    builder.set_objective(psr.Objective.BinPacking)

    builder.add_bin_type(
        sheet_w,
        sheet_h,
        copies=available_sheets,
    )

    item_type_to_part_id = {}

    for part_id, width, height in parts:
        item_type_id = builder.add_item_type(
            width,
            height,
            copies=1,
            oriented=not rotation,
        )

        item_type_to_part_id[item_type_id] = part_id

    instance = builder.build()

    parameters = psr.OptimizeParameters()
    parameters.time_limit = time_limit

    output = psr.optimize(instance, parameters)

    runtime = time.perf_counter() - start

    with tempfile.TemporaryDirectory() as directory:
        solution_path = Path(directory) / "solution.csv"
        output.solution.write(str(solution_path))
        solution_df = pd.read_csv(solution_path)

    bin_rows = (
        solution_df.loc[solution_df["TYPE"] == "BIN"]
        .sort_values("BIN")
    )
    item_rows = solution_df.loc[solution_df["TYPE"] == "ITEM"]

    if bin_rows.empty or item_rows.empty:
        return {
            "solver": "packingsolver",
            "config_id": f"BinPacking__time{time_limit:g}s",
            "objective": "BinPacking",
            "rotation": rotation,
            "time_limit_seconds": time_limit,
            "sheet_width": sheet_w,
            "sheet_height": sheet_h,
            "available_sheets": available_sheets,
            "runtime_seconds": runtime,
            "run_status": "no_solution_returned",
            "layout_valid": False,
            "parts_total": len(parts),
            "parts_packed": 0,
            "complete": False,
            "individually_feasible": all(
                (w <= sheet_w and h <= sheet_h)
                or (
                    rotation
                    and h <= sheet_w
                    and w <= sheet_h
                )
                for _, w, h in parts
            ),
            "sheets_used": 0,
            "requested_area": sum(w * h for _, w, h in parts),
            "packed_area": 0.0,
            "part_fraction": 0.0,
            "area_fraction": 0.0,
            "utilisation": 0.0,
            "area_lower_bound": math.ceil(
                sum(w * h for _, w, h in parts)
                / (sheet_w * sheet_h)
            ),
            "sheet_gap_to_area_bound": float("nan"),
        }

    if not bin_rows["COPIES"].eq(1).all():
        raise ValueError(
            "The converter requires one physical sheet per BIN row"
        )

    if bin_rows["BIN"].duplicated().any():
        raise ValueError("Duplicate BIN identifiers in the certificate")

    bin_id_map = {
        int(original_id): new_id
        for new_id, original_id in enumerate(bin_rows["BIN"])
    }

    used_sheets = [
        (int(row.LX), int(row.LY))
        for row in bin_rows.itertuples(index=False)
    ]

    placements = [
        (
            bin_id_map[int(row.BIN)],
            int(row.X),
            int(row.Y),
            int(row.LX),
            int(row.LY),
            item_type_to_part_id[int(row.ID)],
        )
        for row in item_rows.itertuples(index=False)
    ]

    validation = validate_rectangle_layout(
        parts=parts,
        placements=placements,
        used_sheets=used_sheets,
        sheet_size=sheet_size,
        rotation=rotation,
        available_sheets=available_sheets,
    )

    if not validation["layout_valid"]:
        raise ValueError(
            "Invalid PackingSolver layout:\n"
            + "\n".join(validation["validation_errors"])
        )

    metrics = calculate_rectangle_metrics(
        parts=parts,
        placements=placements,
        used_sheets=used_sheets,
        sheet_size=sheet_size,
        rotation=rotation,
    )

    result = {
        "solver": "packingsolver",
        "config_id": f"BinPacking__time{time_limit:g}s",
        "objective": "BinPacking",
        "rotation": rotation,
        "time_limit_seconds": time_limit,
        "sheet_width": sheet_w,
        "sheet_height": sheet_h,
        "available_sheets": available_sheets,
        "runtime_seconds": runtime,
        "layout_valid": True,
        **metrics,
    }

    if return_layout:
        result["placements"] = placements
        result["used_sheets"] = used_sheets

    return result