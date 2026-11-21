import time

from cutting_benchmark.rectangle_metrics import (
    calculate_rectangle_metrics,
)
from cutting_benchmark.rectangle_validation import (
    validate_rectangle_layout,
)

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
    """Pack rectangular parts using one RectPack configuration.

    Parameters
    ----------
    parts : iterable of tuple
        Requested parts as (part_id, width, height).
        Part IDs must be unique and dimensions must be positive.
    algorithm : str
        Packing algorithm name registered in ALGORITHMS.
    sort : str
        Sorting rule name registered in SORTS.
    rotation : bool
        Whether RectPack may rotate parts by 90 degrees.
    sheet_size : tuple of int or float, optional
        Identical sheet dimensions as (width, height).
        Defaults to (2500, 1250).
    available_sheets : int or None, optional
        Positive number of available sheets. If None, allows one
        sheet per requested part.
    return_layout : bool, optional
        Whether to include placements and used-sheet dimensions
        in the returned dictionary. Defaults to False.

    Returns
    -------
    dict
        Solver and configuration identifiers, solver settings,
        sheet dimensions, available stock, runtime, layout-validation
        status and shared rectangle-packing metrics.

        If return_layout is True, also includes:
        - placements: (bin_id, x, y, width, height, part_id) tuples.
        - used_sheets: (width, height) tuples.

    Raises
    ------
    ValueError
        If parts is empty, dimensions are nonpositive, part IDs
        are duplicated, available_sheets is less than one, or the
        extracted layout fails validation.
    KeyError
        If algorithm or sort is not registered.

    Notes
    -----
    Uses offline packing with BBF bin selection.

    Runtime includes packer construction, loading parts and sheets,
    and packing. It excludes output extraction and metric calculation.

    Parts that cannot be packed are reflected in the completion metrics;
    an incomplete order does not itself raise an exception.

    No kerf, inter-part clearance, material matching or sheet defects
    are modelled by this adapter.
    """
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
            "Invalid Rectpack layout:\n"
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
        "solver": "rectpack",
        "config_id": f"{algorithm}__{sort}__BBF",
        "algorithm": algorithm,
        "sort": sort,
        "rotation": rotation,
        "bin_selection": "BBF",
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
