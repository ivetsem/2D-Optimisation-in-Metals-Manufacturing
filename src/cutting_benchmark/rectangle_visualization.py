"""Matplotlib visualisations for rectangle-packing adapter results.

Adapters expose placements in the shared format
``(sheet_index, x, y, width, height, part_id)`` when called with
``return_layout=True``. The functions here use that format directly.
"""


def _select_sheet_indices(sheet_count, sheets=None):
    """Resolve a Python-style sheet selector to zero-based indices.

    Parameters
    ----------
    sheet_count : int
        Number of available sheets.
    sheets : int, slice, iterable of int, or None
        Selector interpreted like indexing or slicing a Python list.
        Negative indices are supported; ``None`` selects every sheet.

    Returns
    -------
    list of int
        Selected zero-based sheet indices, in selector order.

    Raises
    ------
    TypeError
        If the selector is not an integer, slice, or iterable of indices.
    IndexError
        If an integer index is outside the available sheet range.
    """
    indices = range(sheet_count)
    if sheets is None:
        return list(indices)
    if isinstance(sheets, slice):
        return list(indices[sheets])
    if isinstance(sheets, int) and not isinstance(sheets, bool):
        return [indices[sheets]]
    try:
        return [indices[index] for index in sheets]
    except TypeError as exc:
        raise TypeError(
            "sheets must be None, an index, a slice, or an iterable of indices"
        ) from exc


def _layout_data(result):
    """Extract sheet dimensions and placements from an adapter result.

    Parameters
    ----------
    result : mapping
        Adapter result containing ``used_sheets`` and ``placements``.

    Returns
    -------
    tuple
        ``(used_sheets, placements)`` as lists.

    Raises
    ------
    ValueError
        If the result does not include layout data.
    """
    if "placements" not in result or "used_sheets" not in result:
        raise ValueError(
            "Result has no layout; call run_pack with return_layout=True"
        )

    used_sheets = list(result["used_sheets"])
    placements = list(result["placements"])
    return used_sheets, placements


def _result_title(result):
    """Build a label from solver and configuration metadata.

    Parameters
    ----------
    result : mapping
        Adapter result, optionally containing ``solver`` and ``config_id``.

    Returns
    -------
    str
        Combined solver and configuration label, with defaults for any
        missing metadata.
    """
    solver = result.get("solver", "Unknown solver")
    config = result.get("config_id", "Unknown configuration")
    return f"{solver} — {config}"


def _draw_sheet(ax, result, used_sheets, placements, sheet_index, show_ids):
    """Draw one sheet and its rectangles on a Matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axis on which to draw the sheet.
    result : mapping
        Adapter result (retained as part of the internal helper interface).
    used_sheets : sequence of tuple
        Sheet dimensions as ``(width, height)``.
    placements : sequence of tuple
        Placements as ``(sheet_index, x, y, width, height, part_id)``.
    sheet_index : int
        Zero-based sheet index to draw; its displayed label is one-based.
    show_ids : bool
        Whether to draw each part ID inside its rectangle.

    Notes
    -----
    The subplot title includes the sheet utilisation, calculated as the
    placed rectangle area divided by the sheet area.
    """
    from matplotlib.patches import Rectangle

    width, height = used_sheets[sheet_index]
    matching = [p for p in placements if p[0] == sheet_index]
    packed_area = sum(p[3] * p[4] for p in matching)
    utilisation = packed_area / (width * height) if width and height else 0.0

    ax.add_patch(Rectangle((0, 0), width, height, facecolor="#f7f8fa",
                           edgecolor="#333333", linewidth=1.5))
    for _, x, y, rect_w, rect_h, part_id in matching:
        colour = f"C{(hash(str(part_id)) % 10)}"
        ax.add_patch(Rectangle((x, y), rect_w, rect_h, facecolor=colour,
                               edgecolor="white", linewidth=0.8, alpha=0.82))
        if show_ids:
            ax.text(x + rect_w / 2, y + rect_h / 2, str(part_id),
                    ha="center", va="center", fontsize=7, clip_on=True)

    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Width")
    ax.set_ylabel("Height")
    ax.set_title(
        f"Sheet {sheet_index + 1} — {utilisation:.1%} utilisation\n"
        f"{len(matching)} parts · {width:g} × {height:g}"
    )
    ax.grid(False)


def plot_rectangle_result(result, sheets=None, show_ids=True, figsize=None):
    """Plot one adapter result, with one subplot per selected sheet.

    Parameters
    ----------
    result : dict
        Adapter output containing placements and used-sheet dimensions.
    sheets : int or iterable of int, optional
        Sheet selector using normal Python indexing: an integer, slice, or
        iterable of zero-based indices. For example, ``range(4)`` or
        ``slice(0, 4)`` selects the first four sheets. Negative indices work.
        ``None`` displays all sheets.
    show_ids : bool, optional
        Draw each part ID inside its rectangle.
    figsize : tuple, optional
        Matplotlib figure size. A compact size is chosen by default.

    Returns
    -------
    tuple
        ``(figure, axes)``; ``axes`` is a one-dimensional array.

    Raises
    ------
    ValueError
        If layout data is missing or the selector selects no sheets.
    TypeError
        If ``sheets`` is not a supported Python-style selector.
    IndexError
        If a selected integer index is outside the result's sheet range.

    Notes
    -----
    Sheet selectors use zero-based Python indexing. Sheet labels in the
    plot start at one. Matplotlib is imported when this function is called.
    """
    import matplotlib.pyplot as plt

    used_sheets, placements = _layout_data(result)
    selected = _select_sheet_indices(len(used_sheets), sheets)
    if not selected:
        raise ValueError("Select at least one sheet to plot")

    fig, axes = plt.subplots(1, len(selected), squeeze=False,
                             figsize=figsize or (5 * len(selected), 5))
    axes = axes.ravel()
    for ax, sheet_index in zip(axes, selected):
        _draw_sheet(ax, result, used_sheets, placements, sheet_index, show_ids)
    fig.suptitle(_result_title(result), fontsize=12)
    fig.tight_layout()
    return fig, axes


def compare_rectangle_results(results, sheets=None, show_ids=True, figsize=None):
    """Compare several adapter results using aligned per-sheet panels.

    Each result gets its own row and each selected sheet its own column.
    Solver/configuration names and sheet utilisation appear above the plots.
    Every result must contain layout data. If a result uses fewer sheets
    than the maximum, its unused panels are marked accordingly.

    Parameters
    ----------
    results : iterable of dict
        Adapter outputs containing placements and used-sheet dimensions.
    sheets : int, slice, iterable of int, or None, optional
        Sheet selector using normal Python indexing: an integer, slice, or
        iterable of zero-based indices. For example, ``range(4)`` or
        ``slice(0, 4)`` selects the first four sheets. Negative indices work.
        By default, shows every sheet used by any result; empty panels
        indicate when a result used fewer sheets.
    show_ids : bool, optional
        Draw each part ID inside its rectangle.
    figsize : tuple, optional
        Matplotlib figure size. A size based on the panel count is chosen
        by default.

    Returns
    -------
    tuple
        ``(figure, axes)``; ``axes`` is a two-dimensional array indexed by
        result row and selected-sheet column.

    Raises
    ------
    ValueError
        If ``results`` is empty, layout data is missing, or no sheets are
        selected.
    TypeError
        If ``sheets`` is not a supported Python-style selector.
    IndexError
        If a selected integer index is outside the maximum sheet range.

    Notes
    -----
    Sheet selectors use zero-based Python indexing; displayed labels start
    at one. Matplotlib is imported when this function is called.
    """
    import matplotlib.pyplot as plt

    results = list(results)
    if not results:
        raise ValueError("results must contain at least one result")
    layouts = [_layout_data(result) for result in results]
    max_sheets = max(len(layout[0]) for layout in layouts)
    selected = _select_sheet_indices(max_sheets, sheets)
    if not selected:
        raise ValueError("Select at least one sheet to plot")

    rows, cols = len(results), len(selected)
    fig, axes = plt.subplots(rows, cols, squeeze=False,
                             figsize=figsize or (5 * cols, 4.5 * rows))
    for row, (result, (used_sheets, placements)) in enumerate(zip(results, layouts)):
        for col, sheet_index in enumerate(selected):
            ax = axes[row, col]
            if sheet_index >= len(used_sheets):
                ax.set_axis_off()
                ax.set_title(
                    f"{_result_title(result)}\nSheet {sheet_index + 1} — not used"
                )
                continue
            _draw_sheet(ax, result, used_sheets, placements, sheet_index, show_ids)
            ax.set_title(f"{_result_title(result)}\n{ax.get_title()}")
    fig.suptitle("Packing comparison", fontsize=13)
    fig.tight_layout()
    return fig, axes
