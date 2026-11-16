import math


def validate_rectangle_layout(
    parts,
    placements,
    used_sheets,
    sheet_size,
    rotation,
    available_sheets=None,
    tolerance=1e-9,
):
    """Validate a packing of rectangles on identical sheets.

    Partial layouts are allowed. Every placed part must:
    - Refer to a unique requested part.
    - Have its requested dimensions in an allowed orientation.
    - Refer to an existing sheet.
    - Lie within that sheet.
    - Not overlap another part.

    Touching edges are allowed. All listed used sheets must contain
    at least one part.

    Returns
    -------
    dict
        Layout validity and a list of validation errors.

    Notes
    -----
    Tolerance is an absolute length tolerance in the input units.
    """
    parts = list(parts)
    placements = list(placements)
    used_sheets = list(used_sheets)

    errors = []
    requested = {}

    def close(a, b):
        return math.isclose(
            a,
            b,
            rel_tol=0.0,
            abs_tol=tolerance,
        )

    for part_id, width, height in parts:
        if part_id in requested:
            errors.append(f"Duplicate requested part ID: {part_id!r}")

        requested[part_id] = (width, height)

    if (
        available_sheets is not None
        and len(used_sheets) > available_sheets
    ):
        errors.append("Used-sheet count exceeds available stock")

    sheet_w, sheet_h = sheet_size

    for bin_id, (width, height) in enumerate(used_sheets):
        if not (close(width, sheet_w) and close(height, sheet_h)):
            errors.append(
                f"Sheet {bin_id} does not match the stock dimensions"
            )

    seen_ids = set()
    items_by_bin = {
        bin_id: []
        for bin_id in range(len(used_sheets))
    }

    for bin_id, x, y, width, height, part_id in placements:
        if part_id in seen_ids:
            errors.append(f"Duplicate placed part ID: {part_id!r}")

        seen_ids.add(part_id)

        if part_id not in requested:
            errors.append(f"Unknown placed part ID: {part_id!r}")
        else:
            requested_w, requested_h = requested[part_id]

            original = (
                close(width, requested_w)
                and close(height, requested_h)
            )

            rotated = (
                rotation
                and close(width, requested_h)
                and close(height, requested_w)
            )

            if not (original or rotated):
                errors.append(
                    f"Invalid dimensions or orientation: {part_id!r}"
                )

        if bin_id not in items_by_bin:
            errors.append(
                f"Invalid sheet reference for {part_id!r}: {bin_id}"
            )
            continue

        if not all(
            math.isfinite(value)
            for value in (x, y, width, height)
        ):
            errors.append(
                f"Non-finite placement values: {part_id!r}"
            )
            continue

        if width <= 0 or height <= 0:
            errors.append(
                f"Nonpositive placed dimensions: {part_id!r}"
            )
            continue

        bin_w, bin_h = used_sheets[bin_id]

        if (
            x < -tolerance
            or y < -tolerance
            or x + width > bin_w + tolerance
            or y + height > bin_h + tolerance
        ):
            errors.append(f"Part outside sheet: {part_id!r}")

        items_by_bin[bin_id].append(
            (x, y, width, height, part_id)
        )

    for bin_id, items in items_by_bin.items():
        if not items:
            errors.append(f"Used sheet {bin_id} has no placed parts")

        for i, (x1, y1, w1, h1, id1) in enumerate(items):
            for x2, y2, w2, h2, id2 in items[i + 1:]:
                overlap_x = min(x1 + w1, x2 + w2) - max(x1, x2)
                overlap_y = min(y1 + h1, y2 + h2) - max(y1, y2)

                if overlap_x > tolerance and overlap_y > tolerance:
                    errors.append(
                        f"Overlapping parts on sheet {bin_id}: "
                        f"{id1!r} and {id2!r}"
                    )

    return {
        "layout_valid": not errors,
        "validation_errors": errors,
    }