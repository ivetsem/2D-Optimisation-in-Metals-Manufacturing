# cutting_benchmark package

## Purpose

`cutting_benchmark` contains reusable code for benchmarking
2D cutting and packing approaches.

The current implementation supports rectangular parts packed
onto identical rectangular sheets, using RectPack.

It separates input datasets, solver execution, metric calculation,
benchmark execution and summary statistics from exploratory notebooks.

## Package structure

```text
src/cutting_benchmark/
├── __init__.py
├── rectangle_datasets.py
├── rectangle_metrics.py
├── benchmark.py
├── summaries.py
└── solvers/
    ├── __init__.py
    └── rectpack_adapter.py
```

| Module | Responsibility |
|---|---|
| `rectangle_datasets.py` | Generate, save and load synthetic rectangle datasets |
| `rectangle_metrics.py` | Calculate metrics for one packing result |
| `solvers/rectpack_adapter.py` | Run RectPack and return a result dictionary |
| `benchmark.py` | Run a supplied solver across datasets, configurations and repeats |
| `summaries.py` | Aggregate benchmark results and compare configurations |

## Local setup

From the repository root, activate the project environment and
install the package in editable mode:

```bash
source .venv/bin/activate
python -m pip install -e .
```

Use the same virtual environment as the notebook kernel.

## Workflow

1. Generate and save datasets using
   `scripts/generate_rectangle_datasets.py`.
2. Load the saved datasets in a notebook or benchmark script.
3. Define solver configurations.
4. Run the benchmark.
5. Calculate summary tables.
6. Inspect, visualise and save results.

Reusable package functions perform calculations.
Notebooks and scripts choose experiments and manage output files.

## Dataset format

Each dataset is a dictionary:

```python
{
    "dataset_id": "rect_v1_mixed_sheet2500x1250_n35_seed0",
    "seed": 0,
    "profile": "mixed",
    "n_parts": 35,
    "sheet_size": (2500, 1250),
    "parts": [
        ("P00000", 400, 250),
        ("P00001", 600, 300),
        # ...
    ],
}
```

The example above abbreviates the parts list.

- Dimensions use millimetres in the current experiments.
- `sheet_size` is `(width, height)`.
- Each part is `(part_id, width, height)`.
- Each part represents one requested physical piece.
- Part IDs must be unique within a dataset.
- `n_parts` must equal the length of `parts`.
- Dataset IDs must be unique within a benchmark suite.

The ID records the geometry type, generator version, profile,
sheet dimensions, number of parts and random seed.

Increase the generator version when the generation logic changes.
Save the generated inputs so different solvers use identical instances.

## Shared layout format

Solver adapters provide placements using:

```python
(bin_id, x, y, width, height, part_id)
```

Here, `x` and `y` identify the bottom-left corner of the placed part.
Width and height describe its placed orientation.

Used sheets are represented as:

```python
(width, height)
```

with one entry per used sheet.

Future solver adapters should convert their outputs into this
representation before calling the shared rectangle metrics function.

## Benchmark interface

```python
results = run_benchmark(
    datasets=datasets,
    configurations=configurations,
    solver=run_pack,
    repeats=1,
    available_sheets=None,
    execution_seed=123,
)
```

The supplied solver must accept:

- `parts`
- `sheet_size`
- `available_sheets`
- The keyword arguments in each configuration dictionary

It must return a dictionary containing per-run results.

The benchmark returns a DataFrame with one row per
dataset–configuration–repeat combination.

`execution_seed` controls job ordering. It is not a solver random seed.

## Configuration identity

The default summary grouping uses:

```python
["solver", "config_id", "rotation"]
```

Together, these fields must identify a configuration unambiguously.

For RectPack, `config_id` records the packing algorithm,
sorting rule and bin-selection rule. Rotation is recorded separately.

If future experiments vary another solver setting, it must be
represented in the configuration identity or kept in a separate suite.

## Summary outputs

```python
tables = summarise_results(results)
```

The returned dictionary contains:

| Key | Contents |
|---|---|
| `dataset_config` | One row per dataset and configuration after repeat aggregation |
| `completion_summary` | Completion rates by configuration |
| `summary` | Overall performance by configuration |
| `summary_by_workload` | Performance grouped by profile and part count |

The current summary function requires:

- Complete orders.
- Identical quality metrics across repeated runs.
- Matching dataset coverage across configurations within each rotation setting.
- No duplicate dataset–configuration–repeat rows.

It raises an error if these requirements are not met.

Runtime is first reduced to the median across repeats.
Overall median and P95 runtime are then calculated across those
per-dataset values.

## Interpretation of metrics

- `complete`: the number of placements equals the requested part count.
  This is not, by itself, proof of layout validity.
- `utilisation`: packed part area divided by total used-sheet area.
- `area_lower_bound`: requested area divided by sheet area, rounded upwards.
- `sheet_gap_to_area_bound`: used sheets minus the area lower bound,
  reported only for complete orders.
- `relative_excess`: proportional sheet overhead versus the best
  observed configuration for the same dataset and rotation setting.
- `tied_best_rate`: fraction of datasets on which the configuration
  matches the fewest observed sheets.

The area-bound gap is not a proven optimality gap.

"Best observed" depends on the configurations included in the input table.
It is not necessarily the true optimum.

For complete orders on identical sheets, utilisation and sheet count
are mathematically linked rather than independent quality measures.

## Current scope and limitations

- Rectangular parts and identical rectangular sheets.
- Rotation is disabled or permits a 90-degree turn.
- No kerf or inter-part clearance is modelled in the current workflow.
- No material-grade or thickness matching is implemented.
- The shared metric function does not validate overlap, containment
  or exact part-ID coverage.
- Synthetic profiles are test scenarios, not validated manufacturing
  demand distributions.
- Repeated runs with varying solution quality need an explicit
  aggregation policy before they can use the current summaries.
- Layouts generated by different cutting constraints must not be
  treated as equivalent problem instances.

## Adding another solver

1. Add an adapter under `solvers/`.
2. Accept the common benchmark inputs.
3. Convert output placements into the shared layout format.
4. Calculate the shared rectangle metrics.
5. Return solver identity, configuration identity, settings,
   runtime and metrics.
6. Test on a small saved dataset before running the full benchmark.

Only combine results when their problem definitions match:
datasets, objectives, stock availability, rotation permissions
and manufacturing constraints.

## File locations

- Input instances: `data/synthetic/`
- RectPack results: `results/rectpack/`
- Exploration and analysis: `notebooks/`
- Runnable workflows: `scripts/`

Generated package metadata and Python caches are not source files
and should not be committed.