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