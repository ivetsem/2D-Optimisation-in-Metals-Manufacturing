# `cutting_benchmark` package guide

## Purpose and scope

`cutting_benchmark` provides reusable code for comparing rectangular-packing solvers on shared datasets. It separates dataset generation, solver-specific integration, geometric validation, metric calculation, benchmark execution and summary statistics from exploratory notebooks.

The current adapters integrate Rectpack and PackingSolver. Both work with rectangular parts on identical rectangular sheets and optional 90-degree rotation. Material matching, traceability, kerf, clearances, defects, remnant management and production scheduling are not implemented.

This guide documents the current code, including limitations and differences between adapters. For project context, installation overview and findings, see the [README](../README.md) and [research report](report.md).

## Package structure

```text
src/cutting_benchmark/
├── __init__.py
├── benchmark.py
├── rectangle_datasets.py
├── rectangle_metrics.py
├── rectangle_validation.py
├── summaries.py
└── solvers/
    ├── __init__.py
    ├── packingsolver_adapter.py
    └── rectpack_adapter.py
```

| Module | Responsibility |
|---|---|
| `rectangle_datasets.py` | Generate, save and load synthetic datasets |
| `rectangle_metrics.py` | Calculate metrics from requested parts and returned layouts |
| `rectangle_validation.py` | Check geometry, identities, orientations and stock limits |
| `rectangle_visualization.py` | Plot and compare returned rectangular layouts |
| `solvers/rectpack_adapter.py` | Execute registered Rectpack configurations |
| `solvers/packingsolver_adapter.py` | Build PackingSolver instances and convert exported certificates |
| `benchmark.py` | Execute dataset–configuration–repeat combinations |
| `comparison.py` | Validate comparison inputs and calculate paired sheet-count comparisons |
| `summaries.py` | Aggregate complete-order results and calculate best-observed comparisons |

## Local setup

From the repository root, with the project virtual environment activated:

```bash
python -m pip install -e ".[dev,notebooks]"
python -m pip install "rectpack==0.2.2"
```

For PackingSolver experiments, also install:

```bash
python -m pip install "packingsolver==0.1.1340"
```

The reported development environment is Python 3.14.2 in GitHub Codespaces. These solver versions identify the benchmark environment, not a complete dependency lock. In addition to the original Codespaces environment, the setup was recreated in a fresh Windows virtual environment using Python 3.14.6. All the tests and scripts were run successfully. This verifies the listed workflow on Windows; other platforms and untested workflows remain unverified.

The current `pyproject.toml` declares pandas and Rectpack as runtime dependencies, pytest in the `dev` extra, and ipykernel and matplotlib in the `notebooks` extra. PackingSolver must currently be installed separately. Use the same environment for terminal execution and notebook kernels.

The notebook extra provides a kernel, not a notebook frontend. PackingSolver visualisation is separate from adapter execution and requires Plotly and `nbformat>=4.2.0`.

## Dataset generation and persistence

### Generate the pilot suite

From the repository root:

```bash
python scripts/generate_rectangle_datasets.py
```

This writes `data/synthetic/pilot_v1_generated.json`, if the output file already exists, the script stops without replacing it. Choose another path with --output, or pass --overwrite to replace the selected file. The script generates 30 datasets: two order sizes (35 and 100), three profiles and five seeds (0–4), using 2500 × 1250 mm sheets.

### Generate an individual dataset

```python
from cutting_benchmark.rectangle_datasets import make_dataset

dataset = make_dataset(
    seed=0,
    n_parts=35,
    profile="mixed",
    sheet_size=(2500, 1250),
)
```

Supported profiles are `mixed`, `strips` and `large_and_small`. Their dimension distributions are defined in the generator. They are synthetic test scenarios, not validated manufacturing demand distributions.

Generation uses a local random-number generator. Repeating the arguments with the same generation logic produces the same dataset without changing global random state. Each generated part fits the sheet in its original orientation.

### In-memory format

A small complete example of the dataset structure is:

```python
{
    "dataset_id": "example_two_parts",
    "seed": 0,
    "profile": "example",
    "n_parts": 2,
    "sheet_size": (2500, 1250),
    "parts": [
        ("P00000", 400, 250),
        ("P00001", 600, 300),
    ],
}
```

Here, `example` is descriptive metadata for a manually constructed instance, not a supported generation profile.

Conventions:

- Dimensions use millimetres in current experiments.
- `sheet_size` is `(width, height)`.
- Each part is `(part_id, width, height)` and represents one physical piece.
- Part IDs must be unique within a dataset.
- `n_parts` must equal the number of requested parts.
- Dataset IDs must uniquely identify instances within a comparison.

Generated IDs record geometry, generator version, profile, sheet dimensions, part count and seed, for example `rect_v1_mixed_sheet2500x1250_n35_seed0`. Update the generator version when generation logic changes.

### Save and load

```python
from cutting_benchmark.rectangle_datasets import load_datasets, save_datasets

save_datasets([dataset], "data/synthetic/example.json")
datasets = load_datasets("data/synthetic/example.json")
```

The JSON envelope contains `schema_version`, `units` and `datasets`. The current schema version is 1 and the units label is `mm`. Missing output directories are created; existing destination files are overwritten.

JSON stores tuples as arrays. Loading restores sheet dimensions and part records to tuples. The loader checks the schema version but does not fully validate dimensions, identifiers or metadata consistency. Persistence functions do not convert units; callers must supply consistent data.

## Shared layout format

Placements use:

```python
(bin_id, x, y, width, height, part_id)
```

Coordinates identify the bottom-left corner. Width and height describe the placed orientation, not necessarily the original orientation.

Used sheets are a list of `(width, height)` records, one per physical used sheet. `bin_id` refers to the zero-based index in that list. Solver-specific sheet identifiers must be converted to this convention.

Both adapters default to returning metrics without layouts. On populated results, set `return_layout=True` to include `placements` and `used_sheets`.

## Rectangle layout visualisation

`rectangle_visualization.py` consumes the shared result fields rather than
solver-specific result types. Any adapter can use these functions if its
result includes `placements` and `used_sheets` in the shared layout format.
The optional `solver` and `config_id` fields provide descriptive plot labels;
missing fields receive generic labels.

```python
from cutting_benchmark.rectangle_visualization import (
    compare_rectangle_results,
    plot_rectangle_result,
)

# `result` and `other_result` are populated adapter outputs.
plot_rectangle_result(result)
compare_rectangle_results([result, other_result], sheets=slice(0, 4))
```

Both functions return `(figure, axes)` and require Matplotlib, available in
the `notebooks` optional dependency group. Pass `return_layout=True` to the
adapter; results without layout fields raise `ValueError`.

The `sheets` argument follows Python sequence selection: an integer selects
one zero-based index, a slice selects a range, and an iterable selects
specific indices. Negative indices are supported. For example, `range(4)`
or `slice(0, 4)` selects the first four sheets. Display labels are one-based.
With no selector, a single result displays all its sheets. A comparison
displays every sheet used by any result and leaves marked empty panels where
a particular result used fewer sheets.

Plots read the solver and configuration labels from `solver` and
`config_id`, draw part IDs by default, and report each sheet's utilisation
(placed part area divided by that sheet's area). Use `show_ids=False` to
hide part labels. The comparison function lays results out in rows and
sheets in columns so configurations can be inspected on the same dataset.

## Solver adapters

Import the two `run_pack` functions with aliases when using both:

```python
from cutting_benchmark.solvers.rectpack_adapter import run_pack as run_rectpack
from cutting_benchmark.solvers.packingsolver_adapter import run_pack as run_packingsolver
```

Importing the PackingSolver adapter requires PackingSolver to be installed. Rectpack-only workflows can import their adapter without importing the PackingSolver adapter.

### Rectpack

```python
from cutting_benchmark.solvers.rectpack_adapter import run_pack as run_rectpack

result = run_rectpack(
    parts=[("A", 400, 250), ("B", 600, 300)],
    algorithm="MaxRectsBssf",
    sort="long_side",
    rotation=True,
    sheet_size=(2500, 1250),
    available_sheets=None,
    return_layout=True,
)
```

Required solver settings are `algorithm`, `sort` and `rotation`.

| Setting | Registered values |
|---|---|
| `algorithm` | `MaxRectsBssf`, `MaxRectsBaf`, `SkylineBl`, `GuillotineBafSas` |
| `sort` | `input_order`, `area`, `short_side`, `long_side` |

The adapter uses offline packing and BBF bin selection. `sheet_size` defaults to `(2500, 1250)`. With `available_sheets=None`, it supplies one sheet per requested part.

It rejects empty requests, duplicate part IDs, nonpositive dimensions and stock limits below one. Unregistered algorithm or sorting names raise `KeyError`. Parts not packed are reflected in completion metrics; incomplete orders do not automatically raise an exception.

The adapter passes extracted placements and used sheets through the shared validator before calculating metrics. Invalid geometry raises `ValueError`; a valid partial layout is returned with `layout_valid=True` and `complete=False`.

### PackingSolver

```python
from cutting_benchmark.solvers.packingsolver_adapter import run_pack as run_packingsolver

result = run_packingsolver(
    parts=[("A", 400, 250), ("B", 600, 300)],
    rotation=True,
    time_limit=30,
    sheet_size=(2500, 1250),
    available_sheets=None,
    return_layout=True,
)
```

The adapter uses `BinPacking`, one item type per requested part and explicit orientation permissions. A direct adapter call defaults to a 5-second solver limit; the command-line benchmark script defaults to 30 seconds, matching the current pilot configuration. The default sheet size is `(2500, 1250)` and default stock is one sheet per part.

Input requirements include unique IDs, nonempty parts, positive integer-valued dimensions, a boolean rotation flag, a positive integer stock limit and a positive finite time limit. Dimensions accepted as integer-valued floats are converted to integers.

The adapter exports a temporary CSV certificate, maps item types back to original part IDs and converts sheet identifiers into consecutive indices. It requires one physical sheet per certificate `BIN` row and rejects unsupported multiplicities or duplicate sheet identifiers. Temporary certificate files are not retained as benchmark artefacts.

Populated layouts pass through the shared validator before metrics are returned. An invalid extracted layout raises `ValueError`.

If the exported certificate contains no bin rows or no item rows, the implementation returns a record with `run_status="no_solution_returned"`, `complete=False` and `layout_valid=False`. This branch returns no layout arrays even when `return_layout=True`. It does not prove infeasibility.

### Adapter timing

| Adapter | Timed work | Excluded work |
|---|---|---|
| Rectpack | Packer construction, loading and packing | Output extraction and shared metrics |
| PackingSolver | Instance construction and optimisation | Certificate export/parsing, validation and shared metrics |

These are not end-to-end workflow timings. A PackingSolver time limit is a search setting, not a guaranteed complete wall-clock maximum.

## Geometric validation

```python
from cutting_benchmark.rectangle_validation import validate_rectangle_layout

validation = validate_rectangle_layout(
    parts=[("A", 400, 250), ("B", 600, 300)],
    placements=result["placements"],
    used_sheets=result["used_sheets"],
    sheet_size=(2500, 1250),
    rotation=True,
    available_sheets=2,
)

print(validation["layout_valid"])
print(validation["validation_errors"])
```

Here, `result` must be a populated layout returned for those same parts and settings. For PackingSolver, check unsuccessful-search status before accessing layout arrays.

The validator checks:

- Duplicate requested IDs, duplicate placements and unknown placed IDs.
- Requested dimensions and permitted orientation.
- References to existing sheets and agreement with identical-stock dimensions.
- Finite coordinates and placed dimensions, with positive placed dimensions.
- Containment within sheets and non-overlap.
- Stock limits and absence of empty entries in `used_sheets`.

Touching edges are permitted. The default tolerance is `1e-9`, an absolute length tolerance in the input units.

Partial layouts are allowed, so `layout_valid=True` does not mean the order is complete. The validator is not a general dataset-schema parser or a check of manufacturing cutting feasibility; callers must supply correctly structured numeric records.

## Shared metrics

`calculate_rectangle_metrics(parts, placements, used_sheets, sheet_size, rotation)` assumes valid, consistently dimensioned inputs. It does not perform geometric validation.

| Field | Meaning |
|---|---|
| `parts_total`, `parts_packed` | Requested and placed counts |
| `complete` | Placement count equals requested count |
| `individually_feasible` | Every requested part fits one sheet under the rotation setting |
| `sheets_used` | Number of used-sheet records |
| `requested_area`, `packed_area` | Requested and placed area totals |
| `part_fraction` | Placed count / requested count |
| `area_fraction` | Packed area / requested area |
| `utilisation` | Packed area / total used-sheet area; zero if that denominator is zero |
| `area_lower_bound` | Ceiling of requested area / one sheet’s area |
| `sheet_gap_to_area_bound` | Used sheets minus area bound; NaN for incomplete orders |

Requests must be nonempty with positive dimensions. Count-based completion does not prove exact ID coverage or validity. Individual feasibility does not guarantee completion under limited stock or a particular search budget.

The area bound ignores geometry. A positive gap to it is not a proven optimality gap. For a valid complete order on identical sheets, utilisation and sheet count are mathematically linked.

## Benchmark execution

Run each adapter with its own configuration dictionaries:

```python
from cutting_benchmark.benchmark import run_benchmark
from cutting_benchmark.rectangle_datasets import load_datasets
from cutting_benchmark.solvers.rectpack_adapter import run_pack as run_rectpack

datasets = load_datasets("data/synthetic/pilot_v1.json")
configurations = [
    {"algorithm": "MaxRectsBssf", "sort": "long_side", "rotation": False},
    {"algorithm": "MaxRectsBssf", "sort": "long_side", "rotation": True},
]

results = run_benchmark(
    datasets=datasets,
    configurations=configurations,
    solver=run_rectpack,
    repeats=1,
    available_sheets=None,
    execution_seed=123,
)
```

This example uses paths relative to the repository root. For PackingSolver, use its adapter and configurations such as `{"rotation": True, "time_limit": 30}` instead.

The supplied callable receives `parts`, `sheet_size`, `available_sheets` and configuration keywords. Do not repeat those three explicitly supplied arguments inside a configuration dictionary.

The runner shuffles the full job list and returns one DataFrame row per dataset–configuration–repeat combination. `execution_seed` controls execution order, not solver randomness. Repeat identifiers start at zero.

Rows contain the adapter’s fields plus `dataset_id`, `seed`, `profile`, `n_parts`, `repeat` and `run_status`. If the adapter omits `run_status`, the runner assigns `solution_returned`. That default indicates a returned result, not proven completion, validity or optimality. Direct successful adapter calls currently need not include this status field.

A solver exception is wrapped in `RuntimeError` with dataset, configuration and repeat context, and stops execution. The runner does not save partial progress or catch errors as failed-run rows. Save outputs in the calling script or notebook.

### Command-line benchmark and comparison scripts

Run the pilot suite from the repository root:

```bash
python scripts/run_rectpack_benchmark.py
python scripts/run_packingsolver_benchmark.py
```

The Rectpack script defaults to all four registered algorithms, all four
sorting rules and both rotation settings: 32 configurations per dataset.
The PackingSolver script defaults to both rotation settings with a
30-second time limit. Both default to `data/synthetic/pilot_v1.json`,
write per-run results to their respective `results/<solver>/` folders,
and accept `--datasets`, `--output`, `--repeats` and
`--available-sheets`. Rectpack also accepts algorithm/sort/rotation
selection; both scripts accept a JSON configuration list with
`--config-file`. Matching output files are overwritten, but other files
already in the destination directory are left alone.

Compare compatible result files with:

```bash
python scripts/compare_solver_benchmarks.py
```

Without `--results`, the comparison script discovers files matching
`results/*/*_results.csv`. Pass explicit paths after `--results` to choose
the input set. Each source file, solver and configuration is kept distinct.
The completion report includes all runs. Quality summaries use only
complete, layout-valid results on dataset/rotation pairs shared by every
included setup. The script uses `validate_comparison_inputs`,
`summarise_results` and `compare_sheet_counts`; its best-observed
comparison is retrospective across the supplied methods, not a
configuration selected in advance.

The comparison output directory is `results/comparison/`. It contains a
full completion report, per-dataset results, overall and workload
summaries, and paired and aggregate comparisons against the best observed
sheet count. See the comparison script's module docstring for the exact
filenames and field meanings.

### Configuration identity

Summary grouping defaults to `["solver", "config_id", "rotation"]`.

- Rectpack IDs follow `algorithm__sort__BBF`.
- PackingSolver IDs follow `BinPacking__time{budget}s`, for example `BinPacking__time30s`.
- Rotation is recorded separately.

If additional settings vary, include them in configuration identity or keep results in a separate suite. Dataset IDs must refer to the same actual input wherever reused.

## Status and incomplete results

Keep these concepts separate:

- `run_status`: whether a populated result was returned or no populated solution was available.
- `complete`: whether placement count matches requested count.
- `layout_valid`: geometric validation outcome where the adapter records it.

PackingSolver’s empty-result branch currently includes zero-valued quality fields. Those are not evidence of a zero-sheet solution and must not enter quality rankings. Its `layout_valid=False` should not be interpreted as proof that a returned geometry was invalid: no populated geometry was available.

Inspect unsuccessful and incomplete runs before aggregation:

```python
print(results.groupby(["solver", "config_id", "rotation"])["complete"].agg(["count", "mean"]))
print(results.loc[results["run_status"].ne("solution_returned")])
```

Historical CSVs may predate status fields. Do not silently infer more information than their recorded completion and validation columns establish.

## Summary tables

```python
from cutting_benchmark.summaries import summarise_results

tables = summarise_results(results)
print(tables["summary"])
```

| Key | Contents |
|---|---|
| `dataset_config` | Per-dataset/configuration repeat aggregation and best-observed comparisons |
| `completion_summary` | Dataset counts and completion rates by configuration |
| `summary` | Overall quality and runtime statistics |
| `summary_by_workload` | Aggregation additionally grouped by profile and part count |

The function rejects empty input, missing required columns, missing identifiers, duplicate run keys, inconsistent quality across repeats, unequal dataset coverage within a rotation setting, incomplete orders and missing/nonpositive sheet counts for complete orders. Custom `config_columns` must include `rotation`.

`completion_summary` is returned only if all checks pass; the function is not a general failure-reporting utility. Inspect raw completion separately when runs fail.

Runtime is reduced to the median over repeats per dataset/configuration. Overall median and P95 are then computed across those per-dataset values. Quality measures must agree across repeats; stochastic quality variation needs a separately chosen aggregation policy. The function does not enforce a common repeat count across groups.

Best-observed sheet count is computed per dataset and rotation setting across configurations in the input:

- `extra_sheets_vs_best`: sheets used minus best observed.
- `relative_excess`: sheets used / best observed minus one.
- `tied_best`: whether a dataset result matches the best observed count.
- `tied_best_rate`: fraction of datasets tying that count.

The overall table is sorted by rotation, mean relative excess and median runtime. This is not necessarily the same ranking as lowest total sheet count. “Best observed” is not a proven optimum.

Each dataset has equal weight after repeat aggregation. The function neither validates placements nor automatically verifies matching stock, objectives, units or process constraints. It does not modify inputs, format display values or save files.

## Saving results

Scripts and notebooks own file output:

```python
from pathlib import Path

output_dir = Path("results/rectpack")
output_dir.mkdir(parents=True, exist_ok=True)
results.to_csv(output_dir / "pilot_v1_results.csv", index=False)
```

Repository locations include:

- Inputs: `data/synthetic/pilot_v1.json`.
- Rectpack script output: `results/rectpack/pilot_v1_results.csv` by default.
- PackingSolver script output: `results/packingsolver/pilot_v1_results.csv` by default.
- Comparison script output: `results/comparison/`.
- Exploratory and comparison workflows: `notebooks/`.

Record the producing code revision, versions, settings and input identity with published experiments. CSV export overwrites an existing destination. Layout arrays are normally unnecessary in benchmark CSVs; request them separately for visualisation and validation.

## Adding another solver

1. Add an adapter under `solvers/` with the common benchmark inputs.
2. Define supported objectives, geometry, stock rules, dimensions and rotation semantics.
3. Preserve physical part identities and translate solver outputs into the shared layout format.
4. Validate populated layouts and calculate shared metrics outside the timed section if retaining current timing conventions.
5. Return solver/configuration identity, settings, runtime and explicit unsuccessful-search status where applicable.
6. Make configuration identity distinguish all varied settings.
7. Add small adapter tests covering successful and unsuccessful outcomes before large runs.
8. Document installation separately if the dependency is optional.

Only combine results representing equivalent problem definitions. Different objectives, guillotine restrictions, clearances, stock rules or rotation permissions can change the problem rather than merely the solver.

## Tests and current limitations

Run from the repository root:

```bash
python -m pytest
```

The supplied tests cover dataset generation and persistence, metrics,
validation cases, summary safeguards, benchmark record construction,
and mocked Rectpack and PackingSolver adapter result conversion. The
adapter tests do not run the external solvers and are not end-to-end tests
of the solver packages or notebooks. The PackingSolver adapter tests are
skipped when its Python binding is not installed.

GitHub Actions is configured to run `python -m pytest` on pushes and pull
requests. It uses Python 3.14 and installs the project with the `dev` extra;
it does not run notebooks or benchmark workloads. See the
[test workflow](../.github/workflows/tests.yml).

Current limitations include limited certificate conversion, no automatic
progress persistence, incomplete-result handling requiring care, and no
manufacturing-specific feasibility model. The framework supports repeat
execution, but the current pilot comparison uses one recorded run per
dataset/configuration.

The present package is an experimental foundation. Further solvers and manufacturing constraints are extension points, not existing capabilities.
