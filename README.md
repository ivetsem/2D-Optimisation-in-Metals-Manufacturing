# 2D Optimisation in Metals Manufacturing

A research and benchmarking project exploring open-source approaches
to rectangular sheet packing, motivated by production-planning
challenges in metals manufacturing.

The project provides a reusable Python benchmark with shared synthetic
datasets, solver adapters, packing metrics and analysis workflows.
Rectpack and PackingSolver are currently integrated through a common
benchmark interface intended to accommodate additional solvers.

The emphasis is on comparing solution quality, completion and runtime
under explicit assumptions—not on developing a new packing algorithm.

This is a portfolio research prototype, not a production cutting or
scheduling system.

## Background and scope

The investigation was motivated by a research brief concerning the
extension of GoSmarter.ai's 1D cutting optimisation capabilities to
2D sheet and plate planning.

This repository presents my own implementation and analysis. The original
brief considered a wider range of topics, including irregular nesting,
material matching, traceability, offcut reuse and production scheduling.
The implemented proof of concept focuses on rectangular packing and
reusable benchmarking infrastructure.

### Implemented

- Reproducible synthetic datasets with saved JSON inputs.
- A Rectpack adapter supporting four packing algorithms, four sorting
  rules and optional 90-degree rotation.
- A PackingSolver adapter using its `BinPacking` objective with a
  configurable time limit.
- A benchmark runner covering datasets, configurations and repeated runs.
- Shared metrics for completion, sheet count, utilisation and comparison
  with an area lower bound.
- Shared geometric validation in both solver adapters, covering part
  identity, orientation, containment, overlap and stock limits.
- Command-line scripts to run each solver and compare compatible result
  CSVs from multiple solvers and configurations.
- Summary tables, visualisations and cross-solver analysis notebooks.
- Mocked tests for benchmark record construction and both adapter result
  conversion paths, alongside dataset, metric, validation and summary tests.

### Not implemented

- Irregular polygon nesting.
- Material-grade, thickness or certification matching.
- Heat/batch traceability.
- Offcut inventory management and reuse.
- Kerf, inter-part clearance, edge margins or sheet defects.
- Machine toolpaths, cutting sequences or production scheduling.
- Cost-based planning or integration with a production application.

These are potential extensions rather than current capabilities.

## Benchmark findings

The current pilot result files cover 30 synthetic datasets, each tested
with and without 90-degree rotation:

- Rectpack: 16 algorithm–sorting configurations per rotation setting,
  giving 960 recorded runs.
- PackingSolver: one configuration with a 30-second time limit per
  rotation setting, giving 60 recorded runs.

All 960 Rectpack runs completed. PackingSolver completed all 30 runs
without rotation and 29 of 30 with rotation. The remaining run returned
no populated solution; the comparison therefore uses 30 shared datasets
without rotation and 29 with rotation.

| Rotation | Fixed Rectpack baseline: total sheets | PackingSolver: total sheets | Reduction relative to baseline |
|---|---:|---:|---:|
| Prohibited | 414 | 402 | 2.90% |
| Permitted | 387 | 377 | 2.58% |

The rotation-prohibited totals use 30 separate synthetic orders. The
rotation-permitted totals use the 29 orders completed by every setup.

The fixed Rectpack baseline was `MaxRectsBssf` with long-side sorting
and BBF bin selection. PackingSolver used fewer sheets in aggregate in
both settings, but this does not establish a globally optimal method or
predict performance on manufacturing orders.

PackingSolver was substantially slower. Its median recorded runtime
was about 0.74 seconds without rotation and 5.01 seconds with rotation;
the fixed Rectpack baseline medians were about 2.1 and 1.4 milliseconds.
PackingSolver's P95 runtime was about 30 seconds in both settings.

These results describe the tested synthetic instances, not customer
savings or production readiness. The benchmark uses one recorded run
per dataset and configuration, so it does not quantify runtime
variability.

Recorded runtimes exclude output extraction and shared metric
calculation. PackingSolver certificate export and geometric validation
are also outside its timed section. See [the research report](docs/report.md)
for the methods and [the package guide](docs/cutting_benchmark.md) for
the current command-line workflow and comparison rules.

The pilot inputs are synthetic. These results are not customer savings,
manufacturing feasibility or production-readiness evidence.

## Problem assumptions

The implemented experiments use:

- Rectangular parts and identical rectangular stock sheets.
- Integer dimensions in millimetres for generated datasets.
- One unique identifier per requested physical part.
- Either fixed orientation or permission to rotate parts by 90 degrees.
- Material compatibility assumed in advance.
- No kerf, clearance, edge margins, defects or machine constraints.

Both adapters accept an `available_sheets` stock limit.
If omitted, they provide one sheet per requested part.

The PackingSolver adapter requires positive integer dimensions.
Its current certificate converter requires one physical sheet per
exported `BIN` row.

## Installation

### Development environment

The project was developed in GitHub Codespaces using:

- Python 3.14.2
- Rectpack 0.2.2
- PackingSolver 0.1.1340

Compatibility with other Python versions and platforms has not been
verified. These solver versions identify the environment used for the
reported results; the complete dependency environment is not currently
locked in `pyproject.toml`.

### Create a virtual environment

From the repository root, on Linux, macOS or WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install the local package

For the core Rectpack workflow:

```bash
python -m pip install -e .
python -m pip install "rectpack==0.2.2"
```

For development and notebook use:

```bash
python -m pip install -e ".[dev,notebooks]"
python -m pip install "rectpack==0.2.2"
```

The package declares `pandas` and `rectpack` as runtime dependencies.
The optional extras provide:

- `dev`: pytest.
- `notebooks`: ipykernel and matplotlib.

Use the project virtual environment as your notebook kernel.
The notebook extra supplies a kernel, not a complete Jupyter frontend.
Use a notebook interface such as VS Code, or install JupyterLab
separately:

```bash
python -m pip install jupyterlab
jupyter lab
```

### Install PackingSolver

PackingSolver is not currently included in the package dependency
declarations. To run its adapter and related experiments, install the
version used for the reported benchmark:

```bash
python -m pip install "packingsolver==0.1.1340"
```

The PackingSolver visualisation cells additionally require:

```bash
python -m pip install plotly "nbformat>=4.2.0"
```

PackingSolver is not required for the Rectpack-only workflow.

## Quick start

### Run a small packing example

After installing the local package:

```python
from cutting_benchmark.solvers.rectpack_adapter import run_pack

parts = [
    ("P00000", 400, 250),
    ("P00001", 600, 300),
    ("P00002", 800, 500),
]

result = run_pack(
    parts=parts,
    algorithm="MaxRectsBssf",
    sort="area",
    rotation=True,
    sheet_size=(2500, 1250),
    return_layout=True,
)

print("Complete:", result["complete"])
print("Sheets used:", result["sheets_used"])
print("Utilisation:", f"{result['utilisation']:.1%}")
print("Placements:", result["placements"])
```

Each requested part is represented as:

```python
(part_id, width, height)
```

Each returned placement is represented as:

```python
(bin_id, x, y, width, height, part_id)
```

The coordinates identify the bottom-left corner of the placed part.
Width and height describe its placed orientation.

### Generate synthetic datasets

From the repository root:

```bash
python scripts/generate_rectangle_datasets.py
```

This writes:

```text
data/synthetic/pilot_v1.json
```

The script generates 30 datasets from:

- Two order sizes: 35 and 100 parts.
- Three profiles: `mixed`, `strips` and `large_and_small`.
- Five random seeds: 0–4.
- A default sheet size of 2500 × 1250 mm.

Running the script again overwrites the destination file.

The profiles are synthetic test scenarios, not validated manufacturing
demand distributions. Saved inputs allow different solvers to be
evaluated on the same instances.

### Run the command-line benchmarks

From the repository root, run the default Rectpack suite:

```bash
python scripts/run_rectpack_benchmark.py
```

This runs 32 configurations per dataset (four algorithms, four sorting
rules and two rotation settings) and writes
`results/rectpack/pilot_v1_results.csv`. Select a smaller run with options
such as `--algorithms MaxRectsBssf --sorts long_side`, or provide
configurations in a JSON file with `--config-file`.

Run PackingSolver with its default 30-second time limit and both rotation
settings:

```bash
python scripts/run_packingsolver_benchmark.py
```

This writes `results/packingsolver/pilot_v1_results.csv`. Both benchmark
scripts accept `--datasets` to use another dataset JSON, `--output` to
choose the CSV path, `--repeats` to repeat runs, and `--available-sheets`
to impose a stock limit. They report incomplete runs in the terminal;
PackingSolver also reports runs where no solution was returned.

### Compare benchmark result files

```bash
python scripts/compare_solver_benchmarks.py
```

By default, the comparison script discovers `*_results.csv` files under
`results/<source>/`. To select inputs explicitly, pass paths after
`--results`. It keeps each source and configuration distinct, reports
completion for all runs, and compares solution quality only on complete,
layout-valid datasets shared by all included setups. It writes summary,
workload and per-dataset CSVs to `results/comparison/`. The best-observed
comparison is retrospective across the supplied configurations, not a
deployable solver-selection policy.

The scripts overwrite their matching output CSVs. They do not remove
unrelated or stale files already in the output directories.

### Run the package-based Rectpack benchmark

Open:

```text
notebooks/rectpack_demo.ipynb
```

Select the project environment as the kernel and run the cells in order.

The notebook:

1. Loads the saved datasets.
2. Defines algorithm, sorting and rotation configurations.
3. Runs the shared benchmark.
4. Calculates summary tables.
5. Saves CSV outputs under `results/rectpack/`.

The current notebook locates the repository root by searching for
`.git`. Run it from a Git checkout, with the notebook working directory
at the repository root or inside it.

Rerunning notebooks may overwrite existing result files. Preserve any
outputs you want to retain before running experiments.

## Notebooks

| Notebook | Purpose |
|---|---|
| [`rectpack_demo.ipynb`](notebooks/rectpack_demo.ipynb) | Package-based Rectpack benchmark; recommended starting point |
| [`01_rectpack_exploration.ipynb`](notebooks/01_rectpack_exploration.ipynb) | Early algorithm experiments and packing visualisations |
| [`02_rectpack_summary.ipynb`](notebooks/02_rectpack_summary.ipynb) | Earlier self-contained benchmarking and summary exploration |
| [`03_packingsolver_exploration.ipynb`](notebooks/03_packingsolver_exploration.ipynb) | PackingSolver integration, certificate conversion, validation and time-limit investigation |
| [`04_package_comparison.ipynb`](notebooks/04_package_comparison.ipynb) | Dataset-level comparison of saved Rectpack and PackingSolver results |

The notebooks record the development process and are not a single
sequential pipeline. Earlier exploration notebooks contain historical
code, diagnostic cells and stored outputs; they are not all verified
as clean top-to-bottom workflows.

The comparison notebook is an earlier workflow and reads its own saved
benchmark CSV paths. For current multi-file comparisons, use
`scripts/compare_solver_benchmarks.py` or check the notebook's input
paths against the files being analysed.

## Architecture

Reusable code lives in `src/cutting_benchmark/`.
Scripts and notebooks define experiments, manage files and present
results.

| Module | Responsibility |
|---|---|
| `rectangle_datasets.py` | Generate, save and load synthetic datasets |
| `solvers/rectpack_adapter.py` | Execute registered Rectpack configurations |
| `solvers/packingsolver_adapter.py` | Build PackingSolver instances and convert solution certificates |
| `rectangle_validation.py` | Validate shared rectangular layouts |
| `rectangle_metrics.py` | Calculate shared counts, areas and packing metrics |
| `benchmark.py` | Execute datasets, configurations and repeats in shuffled order |
| `summaries.py` | Aggregate complete-order results and compare configurations |
| `comparison.py` | Validate comparison inputs and calculate paired sheet-count differences |

The benchmark separates solver-specific integration from shared
datasets, metrics and analysis. Adding a solver requires an adapter
that accepts the common benchmark inputs and translates its results
into the shared representation.

A common interface does not automatically make experiments comparable.
Objectives, stock availability, rotation permissions and cutting
constraints must also match.

See [the package guide](docs/cutting_benchmark.md) for additional
workflow and data-format documentation.

## Metrics and correctness

| Field | Meaning |
|---|---|
| `complete` | Placement count equals requested part count |
| `sheets_used` | Number of used sheets |
| `part_fraction` | Placed part count divided by requested part count |
| `area_fraction` | Packed area divided by requested area |
| `utilisation` | Packed area divided by total used-sheet area |
| `area_lower_bound` | Requested area divided by sheet area, rounded upwards |
| `sheet_gap_to_area_bound` | Used sheets minus the area lower bound, reported for complete orders |

### Completion and validation

Completion and layout validity are separate properties:

- Count-based completion alone does not establish geometric validity.
- The shared validator checks part identities, dimensions, permitted
  orientations, containment, overlap, stock dimensions and stock limits.
- Touching edges and valid partial layouts are allowed.
- Both solver adapters validate populated layouts before returning metrics.

Historical Rectpack CSVs created before validator integration do not gain
validation retroactively; use new benchmark runs to record
`layout_valid`.

### Bounds and unsuccessful searches

The area lower bound ignores geometric incompatibilities.
A positive gap to this bound is not a proven optimality gap.

“Best observed” means best among the supplied configurations,
not necessarily globally optimal.

A solver returning no populated layout within its budget does not
prove infeasibility. Such outcomes must be reported separately and
excluded from solution-quality rankings; zero sheets without a
completed order is not an improved packing result.

### Summary requirements

`summarise_results` is designed for complete-order comparisons.
It requires:

- Complete orders.
- Identical quality metrics across repeats of a dataset and configuration.
- Matching dataset coverage across configurations within a rotation setting.
- Unique dataset–configuration–repeat records.

Runtime is first reduced to a median across repeats for each dataset
and configuration. Overall median and P95 runtime are then calculated
across those per-dataset values.

The runner supports repeats, but the reported cross-solver benchmark
contains one recorded run per dataset and configuration.

## Tests

After installing the development extra, run:

```bash
python -m pytest
```

The supplied tests cover:

- Reproducible dataset generation.
- Dataset identifiers and generated dimensions.
- JSON save/load round-tripping.
- Complete, incomplete and empty-layout metrics.
- Area-bound interpretation.
- Valid and deliberately invalid layout cases.
- Summary calculations and comparison safeguards.
- Benchmark record construction, status propagation and error context.
- Mocked Rectpack and PackingSolver adapter conversion, validation and
  unsuccessful-result behavior.

The adapter tests use fake solver outputs; they do not constitute
end-to-end tests of the external solver packages or every notebook.

## Repository structure

```text
.
├── README.md
├── pyproject.toml
├── requirements.txt
├── data/
│   ├── private/
│   ├── sample/
│   └── synthetic/
│       └── pilot_v1.json
├── docs/
│   ├── cutting_benchmark.md
│   ├── report.md
│   ├── research-notes.md
│   └── tool-comparison.md
├── notebooks/
│   ├── 01_rectpack_exploration.ipynb
│   ├── 02_rectpack_summary.ipynb
│   ├── 03_packingsolver_exploration.ipynb
│   ├── 04_package_comparison.ipynb
│   └── rectpack_demo.ipynb
├── results/
│   ├── packingsolver/
│   └── rectpack/
├── scripts/
│   ├── generate_rectangle_datasets.py
│   ├── run_rectpack_benchmark.py
│   ├── run_packingsolver_benchmark.py
│   └── compare_solver_benchmarks.py
├── src/
│   └── cutting_benchmark/
│       ├── __init__.py
│       ├── benchmark.py
│       ├── rectangle_datasets.py
│       ├── rectangle_metrics.py
│       ├── rectangle_validation.py
│       ├── summaries.py
│       └── solvers/
│           ├── __init__.py
│           ├── packingsolver_adapter.py
│           └── rectpack_adapter.py
└── tests/
    ├── test_benchmark.py
    ├── test_packingsolver_adapter.py
    ├── test_rectpack_adapter.py
    ├── test_comparison.py
    ├── test_rectangle_datasets.py
    ├── test_rectangle_metrics.py
    ├── test_rectangle_validation.py
    └── test_summaries.py
```

Python caches and generated package metadata are omitted from this tree.

## Documentation

- [Research report](docs/report.md): benchmark design, findings,
  interpretation and proposed next steps.
- [Package guide](docs/cutting_benchmark.md): architecture, interfaces,
  dataset formats and metrics.
- [Research notes](docs/research-notes.md): brief exploratory observations.

The current reusable comparison workflow is
`scripts/compare_solver_benchmarks.py`; the report summarizes the pilot
results and notebook 04 preserves the earlier exploratory workflow.

## Limitations and future work

The current stopping point is an implemented rectangular-packing
benchmark and research investigation.

The results do not establish manufacturing feasibility, production
readiness or performance on representative customer workloads.
In particular:

- Synthetic profiles are not validated demand distributions.
- A single recorded run does not quantify runtime variability.
- Existing results produced before Rectpack validator integration have
  not been independently revalidated.
- Timings exclude parts of the end-to-end workflow.
- Geometric packing does not establish a feasible machine cutting plan.
- Results from different cutting constraints must not be treated as
  equivalent problem instances.

Potential next steps include:

- Verifying the complete workflow in a fresh environment and recording
  a reproducible dependency snapshot.
- Repeating runs to quantify runtime and solution variability.
- Strengthening unsuccessful-run handling and comparison safeguards.
- Benchmarking a measured portfolio of fast configurations.
- Evaluating additional solvers through the common interface.
- Testing representative, non-confidential manufacturing datasets.
- Investigating material eligibility, kerf, remnants and production
  constraints as separate extensions.

## Data handling

The benchmark uses synthetic datasets stored in `data/synthetic/`.

Local confidential inputs belong in `data/private/`, which is excluded
from version control by the repository's `.gitignore`.

Do not commit client data, credentials or confidential project material.
Before publishing, confirm that no private inputs are already tracked:

```bash
git ls-files -- data/private/
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE)
for the full text.
