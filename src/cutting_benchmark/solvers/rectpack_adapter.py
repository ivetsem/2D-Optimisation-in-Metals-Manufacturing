import math
import time

from rectpack import (
    newPacker,
    PackingMode,
    PackingBin,
    MaxRectsBssf,
    MaxRectsBaf,
    SkylineBl,
    GuillotineBafSas,
    SORT_NONE,
    SORT_AREA,
    SORT_SSIDE,
    SORT_LSIDE,
)


ALGORITHMS = {
    "MaxRectsBssf": MaxRectsBssf,
    "MaxRectsBaf": MaxRectsBaf,
    "SkylineBl": SkylineBl,
    "GuillotineBafSas": GuillotineBafSas,
}

SORTS = {
    "input_order": SORT_NONE,
    "area": SORT_AREA,
    "short_side": SORT_SSIDE,
    "long_side": SORT_LSIDE,
}


def run_pack(
    parts,
    algorithm,
    sort,
    rotation,
    sheet_size=(2500, 1250),
    available_sheets=None,
    return_layout=False,
):
    """Run one RectPack configuration on rectangular parts."""
    parts = list(parts)

    if not parts:
        raise ValueError("parts must not be empty")

    sheet_w, sheet_h = sheet_size

    if sheet_w <= 0 or sheet_h <= 0:
        raise ValueError("Sheet dimensions must be positive")

    if any(w <= 0 or h <= 0 for _, w, h in parts):
        raise ValueError("Part dimensions must be positive")

    ids = [part_id for part_id, _, _ in parts]

    if len(set(ids)) != len(ids):
        raise ValueError("Part IDs must be unique")

    if available_sheets is None:
        available_sheets = len(parts)

    if available_sheets < 1:
        raise ValueError("available_sheets must be positive")

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
        fits_sheet(w, h) for _, w, h in parts
    )

    total_area = sum(w * h for _, w, h in parts)
    sheet_area = sheet_w * sheet_h
    area_lower_bound = math.ceil(total_area / sheet_area)

    start = time.perf_counter()

    packer = newPacker(
        mode=PackingMode.Offline,
        bin_algo=PackingBin.BBF,
        pack_algo=ALGORITHMS[algorithm],
        sort_algo=SORTS[sort],
        rotation=rotation,
    )

    for part_id, w, h in parts:
        packer.add_rect(w, h, rid=part_id)

    packer.add_bin(
        sheet_w,
        sheet_h,
        count=available_sheets,
    )

    packer.pack()

    runtime = time.perf_counter() - start

    placements = packer.rect_list()
    used_sheets = packer.bin_list()

    packed_area = sum(
        w * h for _, _, _, w, h, _ in placements
    )
    used_area = sum(w * h for w, h in used_sheets)

    complete = len(placements) == len(parts)

    result = {
        "solver": "rectpack",
        "config_id": f"{algorithm}__{sort}__BBF",
        "algorithm": algorithm,
        "sort": sort,
        "rotation": rotation,
        "bin_selection": "BBF",
        "sheet_width": sheet_w,
        "sheet_height": sheet_h,
        "available_sheets": available_sheets,
        "parts_total": len(parts),
        "parts_packed": len(placements),
        "complete": complete,
        "individually_feasible": individually_feasible,
        "sheets_used": len(used_sheets),
        "requested_area": total_area,
        "packed_area": packed_area,
        "part_fraction": len(placements) / len(parts),
        "area_fraction": packed_area / total_area,
        "utilisation": (
            packed_area / used_area if used_area else 0.0
        ),
        "area_lower_bound": area_lower_bound,
        "sheet_gap_to_area_bound": (
            len(used_sheets) - area_lower_bound
            if complete
            else float("nan")
        ),
        "runtime_seconds": runtime,
    }

    if return_layout:
        result["placements"] = placements
        result["used_sheets"] = used_sheets

    return result