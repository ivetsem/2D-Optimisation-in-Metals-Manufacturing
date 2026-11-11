import math


def calculate_rectangle_metrics(
    parts,
    placements,
    used_sheets,
    sheet_size,
    rotation,
):
    """Calculate metrics for a rectangle-packing result.

    Parameters
    ----------
    parts : iterable of tuple
        Requested parts as (part_id, width, height).
        Must be nonempty and have positive dimensions.
    placements : iterable of tuple
        Placed parts as
        (bin_id, x, y, width, height, part_id).
        Dimensions describe the placed orientation.
    used_sheets : iterable of tuple
        Dimensions as (width, height), with one entry per used sheet.
        Sheets must match the identical-sheet problem defined by
        sheet_size.
    sheet_size : tuple of int or float
        Dimensions of the identical stock sheets as (width, height).
        Both values must be positive.
    rotation : bool
        Whether a 90-degree rotation is allowed when checking if
        individual requested parts can fit a sheet.

    Returns
    -------
    dict
        Requested and packed part counts, completion status,
        individual feasibility, sheet count, requested and packed areas,
        packed fractions, utilisation, area lower bound and sheet gap
        to that bound.

        The sheet gap is NaN for incomplete orders. Utilisation is
        zero when the total used-sheet area is zero.

    Notes
    -----
    Inputs are assumed to have been validated before this function
    is called. The function does not check overlaps, containment,
    permitted orientations or exact part-ID coverage.

    Completion is determined by comparing placement count with
    requested part count. This alone does not establish layout validity.

    The area lower bound is the ceiling of requested area divided
    by sheet area. Its sheet gap is not a proven optimality gap.

    Dimensions must use a consistent unit throughout the inputs.
    """
    parts = list(parts)
    placements = list(placements)
    used_sheets = list(used_sheets)

    sheet_w, sheet_h = sheet_size

    def fits_sheet(w, h):
        return (
            (w <= sheet_w and h <= sheet_h)
            or (
                rotation
                and h <= sheet_w
                and w <= sheet_h
            )
        )

    individually_feasible = all(
        fits_sheet(w, h)
        for _, w, h in parts
    )

    requested_area = sum(
        w * h for _, w, h in parts
    )

    packed_area = sum(
        w * h
        for _, _, _, w, h, _ in placements
    )

    used_area = sum(
        w * h for w, h in used_sheets
    )

    area_lower_bound = math.ceil(
        requested_area / (sheet_w * sheet_h)
    )

    complete = len(placements) == len(parts)

    return {
        "parts_total": len(parts),
        "parts_packed": len(placements),
        "complete": complete,
        "individually_feasible": individually_feasible,
        "sheets_used": len(used_sheets),
        "requested_area": requested_area,
        "packed_area": packed_area,
        "part_fraction": len(placements) / len(parts),
        "area_fraction": packed_area / requested_area,
        "utilisation": (
            packed_area / used_area if used_area else 0.0
        ),
        "area_lower_bound": area_lower_bound,
        "sheet_gap_to_area_bound": (
            len(used_sheets) - area_lower_bound
            if complete
            else float("nan")
        ),
    }