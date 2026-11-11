import math
import random
import json
from pathlib import Path

def make_dataset(
    seed,
    n_parts,
    profile,
    sheet_size=(2500, 1250),
):
    """Generate a reproducible synthetic rectangle-packing dataset.

    Parameters
    ----------
    seed : int
        Seed for a local random-number generator.
    n_parts : int
        Number of individual parts to generate. Use a positive value
        for benchmark instances.
    profile : {"mixed", "strips", "large_and_small"}
        Distribution of part dimensions relative to the sheet dimensions.
        The profiles represent synthetic test scenarios, not validated
        manufacturing demand.
    sheet_size : tuple of int, optional
        Sheet dimensions as (width, height), in millimetres.
        Defaults to (2500, 1250).

    Returns
    -------
    dict
        Dataset containing dataset_id, seed, profile, n_parts,
        sheet_size and parts. Each part is represented as
        (part_id, width, height).

    Raises
    ------
    KeyError
        If profile is not one of the supported profiles.
    ValueError
        If the sheet dimensions produce an empty integer sampling range.

    Notes
    -----
    Each generated part fits the sheet in its original orientation.

    Repeating the call with the same arguments and generation logic
    reproduces the same parts without modifying the global random state.

    The dataset ID records the geometry type, generator version,
    profile, sheet dimensions, part count and seed. Update the generator
    version when changing the generation logic.
    """
    rng = random.Random(seed)
    sheet_w, sheet_h = sheet_size

    profiles = {
        "mixed": [
            (0.08, 0.55, 0.08, 0.55),
        ],
        "strips": [
            (0.45, 0.95, 0.03, 0.15),
            (0.03, 0.15, 0.45, 0.95),
        ],
        "large_and_small": [
            (0.45, 0.80, 0.45, 0.80),
            (0.05, 0.20, 0.05, 0.20),
        ],
    }

    ranges = profiles[profile]
    parts = []

    for i in range(n_parts):
        w_min, w_max, h_min, h_max = rng.choice(ranges)

        w = rng.randint(
            max(1, math.ceil(w_min * sheet_w)),
            math.floor(w_max * sheet_w),
        )
        h = rng.randint(
            max(1, math.ceil(h_min * sheet_h)),
            math.floor(h_max * sheet_h),
        )

        parts.append((f"P{i:05d}", w, h))

    return {
        "dataset_id": (
            f"rect_v1_{profile}"
            f"_sheet{sheet_w}x{sheet_h}"
            f"_n{n_parts}"
            f"_seed{seed}"
        ),
        "seed": seed,
        "profile": profile,
        "n_parts": n_parts,
        "sheet_size": sheet_size,
        "parts": parts,
    }


def save_datasets(datasets, path):
    """Save a collection of rectangle datasets to a JSON file.

    Parameters
    ----------
    datasets : list of dict
        Dataset dictionaries containing metadata, sheet dimensions
        and individual parts.
    path : str or pathlib.Path
        Destination JSON file. Missing parent directories are created.

    Returns
    -------
    None

    Raises
    ------
    TypeError
        If the supplied data cannot be serialised as JSON.
    OSError
        If the destination directory cannot be created or the file
        cannot be written.

    Notes
    -----
    The file stores schema_version, units and datasets. The current
    schema version is 1 and dimensions are labelled as millimetres.

    Existing files at the destination are overwritten. Python tuples
    are serialised as JSON arrays.

    This function does not validate dataset contents or convert units.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "units": "mm",
        "datasets": datasets,
    }

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def load_datasets(path):
    """Load rectangle datasets from a saved JSON file.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to a dataset file written using the supported JSON schema.

    Returns
    -------
    list of dict
        Loaded datasets. Sheet dimensions are restored to tuples,
        and each part is restored to a (part_id, width, height) tuple.

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    ValueError
        If the file contains invalid JSON or an unsupported schema version.
    KeyError
        If an expected field is missing.
    OSError
        If the file cannot be read.

    Notes
    -----
    The function checks the schema version but does not fully validate
    dimensions, part IDs, dataset IDs or metadata consistency.

    Dimensions are expected to use the project's millimetre convention.
    The function does not convert units.
    """
    payload = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    if payload["schema_version"] != 1:
        raise ValueError("Unsupported dataset schema version")

    datasets = payload["datasets"]

    for dataset in datasets:
        dataset["sheet_size"] = tuple(dataset["sheet_size"])
        dataset["parts"] = [
            tuple(part) for part in dataset["parts"]
        ]

    return datasets