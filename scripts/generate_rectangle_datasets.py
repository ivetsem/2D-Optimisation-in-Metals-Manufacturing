from itertools import product

from cutting_benchmark.datasets import (
    make_dataset,
    save_datasets,
)

datasets = [
    make_dataset(
        seed=seed,
        n_parts=n_parts,
        profile=profile,
    )
    for n_parts, profile, seed in product(
        [35, 100],
        ["mixed", "strips", "large_and_small"],
        range(5),
    )
]

save_datasets(
    datasets,
    PROJECT_ROOT / "data" / "synthetic" / "pilot_v1.json",
)