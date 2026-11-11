import random

import pandas as pd


def run_benchmark(
    datasets,
    configurations,
    solver,
    repeats=1,
    available_sheets=None,
    execution_seed=123,
):
    """Run a solver across datasets, configurations and repeats.

    Parameters
    ----------
    datasets : list of dict
        Input datasets containing parts, sheet dimensions and metadata.
    configurations : list of dict
        Solver settings passed as keyword arguments.
    solver : callable
        Function accepting parts, sheet_size, available_sheets
        and the configuration settings. Returns a result dictionary.
    repeats : int
        Number of runs per dataset and configuration.
    available_sheets : int or None
        Stock limit passed to the solver adapter.
        None uses the adapter's default.
    execution_seed : int
        Seed controlling shuffled execution order, not solver randomness.

    Returns
    -------
    pandas.DataFrame
        One row per dataset–configuration–repeat combination.

    Raises
    ------
    ValueError
        If repeats is less than one.
    """
    if repeats < 1:
        raise ValueError("repeats must be positive")

    rng = random.Random(execution_seed)

    jobs = [
        (dataset, configuration, repeat)
        for dataset in datasets
        for configuration in configurations
        for repeat in range(repeats)
    ]

    rng.shuffle(jobs)

    records = []

    for dataset, configuration, repeat in jobs:
        result = solver(
            parts=dataset["parts"],
            sheet_size=dataset["sheet_size"],
            available_sheets=available_sheets,
            **configuration,
        )

        records.append({
            **result,
            "dataset_id": dataset["dataset_id"],
            "seed": dataset["seed"],
            "profile": dataset["profile"],
            "n_parts": dataset["n_parts"],
            "repeat": repeat,
        })

    return pd.DataFrame(records)