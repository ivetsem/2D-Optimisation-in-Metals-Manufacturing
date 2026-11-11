# 2D Optimisation in Metals Manufacturing

Research and experiments for extending 1D cutting optimisation
to 2D sheet and plate cutting.

## Objectives

- Compare open-source rectangular packing and irregular nesting tools.
- Assess material matching, traceability and remnant reuse.
- Investigate integration with production priorities and scheduling.
- Recommend a practical technical approach.

## Initial experiment

Pack rectangular parts onto rectangular sheets using Rectpack.

Initial assumptions:
- All parts and sheets have compatible material specifications.
- 90-degree rotation is allowed.
- Dimensions are integer millimetres.
- Cutting kerf, edge margins and machine toolpaths are excluded.

## Setup

Python version: 3.14.2

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python scripts/rectpack_demo.py
```

## Repository layout

- `docs/`: research notes, comparison matrix and final report
- `data/sample/`: synthetic input data
- `notebooks/`: exploratory analysis
- `scripts/`: runnable experiments
- `tests/`: validation tests
- `results/`: selected outputs

## Benchmark package

Reusable dataset, solver, benchmark and analysis code lives in
`src/cutting_benchmark/`.

See [the package guide](docs/cutting_benchmark.md) for the workflow,
data formats, assumptions and extension points.

## Data handling

Do not commit client data, credentials or confidential project material.
