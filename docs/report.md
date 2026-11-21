# Rectangular packing for metals manufacturing: research and benchmark report

Date: 21 November 2026
Status: Portfolio research prototype and initial comparative evaluation

## Executive summary

This project investigates existing open-source rectangular-packing tools and provides a reusable Python benchmark for comparing them. It was motivated by a research brief concerning the potential extension of GoSmarter.ai’s 1D cutting capabilities to 2D sheet and plate planning. This repository presents the author’s own implementation and analysis, not a delivered production system.

The main software contribution is a benchmark architecture that separates synthetic datasets, solver-specific adapters, shared metrics, validation and analysis. Rectpack and PackingSolver are currently integrated. The architecture is intended to accommodate further solvers without duplicating the complete experimental workflow.

The current pilot CSVs cover 30 synthetic datasets, two rotation settings, 16 Rectpack configurations and one PackingSolver configuration with a 30-second time limit. All 960 Rectpack runs completed. PackingSolver completed 30/30 runs without rotation and 29/30 with rotation; one rotation-enabled run returned no populated solution. The quality comparison therefore uses 30 common orders without rotation and 29 with rotation.

Against the strongest fixed Rectpack configuration by mean sheet count, `MaxRectsBssf / long_side / BBF`, PackingSolver reduced aggregate sheet use from 414 to 402 without rotation (2.90%) and from 387 to 377 with rotation (2.58%). These totals describe separate synthetic orders; they are not measured customer savings.

The trade-off was computation time. The fixed Rectpack baseline had median recorded runtimes of approximately 2.1 and 1.4 milliseconds without and with rotation, respectively. PackingSolver’s corresponding medians were 0.74 and 5.01 seconds, with P95 runtimes around 30 seconds in both settings. These are adapter timings, not complete application response times.

The practical recommendation is to retain a fast Rectpack baseline and evaluate PackingSolver as a higher-computation alternative where lower sheet consumption matters. Additional geometric algorithms are not the immediate priority. Representative data, consistent validation and explicit manufacturing constraints are the next evidence needed before considering a production application.

## 1. Scope and stopping point

The original brief included rectangular and irregular nesting, cutting restrictions, material matching, traceability, remnants, scheduling and scenario planning. This phase deliberately addresses a smaller problem: placing rectangular parts on identical rectangular sheets and comparing completion, sheet consumption and runtime.

| Area | Status |
|---|---|
| Synthetic datasets and JSON persistence | Implemented |
| Rectpack algorithms, sorting and rotation experiments | Implemented and benchmarked |
| PackingSolver rectangle adapter | Implemented and benchmarked |
| Shared metrics and layout representation | Implemented |
| Shared geometric validator | Implemented, with unit tests; invoked by both solver adapters |
| Cross-solver analysis | Implemented in notebook and reusable command-line workflows |
| Manufacturing-specific guillotine feasibility | Not evaluated |
| Irregular nesting | Not experimentally evaluated |
| Material matching, certification and traceability | Not implemented |
| Remnant inventory, scheduling and cost planning | Not implemented |
| Commercial deployment and licensing review | Not completed |

The stopping point is a research prototype with recorded comparative evidence, not completion of the full production-planning brief.

## 2. Software architecture

Reusable code lives in `src/cutting_benchmark/`. Scripts and notebooks select experiments, manage files and present results.

| Component | Responsibility |
|---|---|
| `rectangle_datasets.py` | Reproducible generation and JSON save/load |
| `solvers/rectpack_adapter.py` | Rectpack configuration and execution |
| `solvers/packingsolver_adapter.py` | PackingSolver instance construction and certificate conversion |
| `rectangle_validation.py` | Shared geometric and identity checks |
| `rectangle_metrics.py` | Counts, areas, utilisation and area-bound metrics |
| `benchmark.py` | Execution across datasets, configurations and repeats |
| `comparison.py` | Comparison-input checks and paired sheet-count differences |
| `summaries.py` | Guarded complete-order aggregation and best-observed comparisons |

Parts are represented as `(part_id, width, height)`. Placements use `(bin_id, x, y, width, height, part_id)`, where coordinates identify the bottom-left corner and dimensions describe the placed orientation. Original part identifiers are retained rather than inferred from dimensions, which may be duplicated across different parts.

The benchmark runner accepts a solver callable and configuration dictionaries. This separates solver-specific integration from shared evaluation. It does not remove third-party dependencies or automatically establish that two solver configurations represent the same problem: objectives, stock, rotation and process restrictions must still be checked.

## 3. Experimental design

### 3.1 Dataset matrix

The dataset-generation script defines 30 instances:

- Three profiles: `mixed`, `strips` and `large_and_small`.
- Two order sizes: 35 and 100 parts.
- Five random seeds: 0–4.
- Identical sheets of 2500 × 1250 mm.

Dimensions are integer millimetres. The generator uses a local seeded random-number generator; saved JSON instances allow solvers to use the same inputs.

The profiles sample dimensions relative to sheet width and height:

| Profile | Sampling ranges |
|---|---|
| `mixed` | Width and height each span 8–55% of the corresponding sheet dimension |
| `strips` | Either width 45–95% and height 3–15%, or width 3–15% and height 45–95% |
| `large_and_small` | Either width and height each 45–80%, or each 5–20% |

For profiles with two alternatives, an alternative is selected independently for each part. Within the selected ranges, integer widths and heights are sampled independently. These distributions are synthetic scenarios, not validated manufacturing demand. Every generated part fits individually in its original orientation.

### 3.2 Solvers and configurations

Rectpack uses offline packing with BBF bin selection. Its experiment combines:

- Algorithms: `MaxRectsBssf`, `MaxRectsBaf`, `SkylineBl`, `GuillotineBafSas`.
- Sorting: input order, area, short side and long side.
- Rotation: prohibited or permitted by 90 degrees.

This gives 16 configurations per rotation setting and 960 runs overall.

PackingSolver uses its `BinPacking` objective, one item type per requested part, explicit orientation settings and a configured time limit of 30 seconds. It contributes 60 runs overall. The adapter requires positive integer dimensions and currently supports one physical sheet per exported certificate `BIN` row.

The common baseline assumes compatible material, identical stock geometry and no kerf, clearance, defects or machine constraints. Algorithm names containing “Guillotine” do not establish that the complete experiment evaluates a particular manufacturing process or produces a verified machine cutting sequence.

### 3.3 Environment and repetitions

The author reports development in GitHub Codespaces using Python 3.14.2, Rectpack 0.2.2 and PackingSolver 0.1.1340, installed in the project virtual environment.

The recorded comparison contains one run per dataset and configuration. Although the runner supports repetitions, this experiment does not quantify runtime variability. Hardware specifications and a complete locked dependency environment have not been recorded in the evidence reviewed here. A fresh-environment execution has not been independently verified.

The runner shuffles execution using an execution seed. This controls job order, not solver randomness.

## 4. Metrics, validation and evidence checks

### 4.1 Quality measures

The primary comparison is sheet count for a complete order. Utilisation is packed area divided by total used-sheet area. For the same complete order on identical sheets, fewer sheets and higher overall utilisation are mathematically linked, not independent achievements.

The area lower bound is requested area divided by sheet area, rounded upwards. It ignores geometric incompatibilities. A positive sheet-count gap to this bound is not a proven optimality gap. Conversely, a valid complete layout attaining the area bound establishes optimal sheet count for that instance.

Best-observed comparisons refer only to the tested methods. Dataset means weight orders equally; they are not pooled utilisation or estimated customer savings.

### 4.2 Completion versus geometric validity

The metrics function determines completion by comparing placement count with requested count. Count equality alone does not establish correctness.

The shared validator checks requested and placed identities, orientations, stock dimensions, containment, overlap and stock limits. Touching edges and valid partial layouts are permitted: validity and completion are separate properties.

Both adapters invoke this validator for populated layouts. The current script-generated pilot results record `layout_valid` for both solvers. Older Rectpack CSVs created before validator integration are not retroactively validated. A valid partial layout remains distinct from a complete order.

### 4.3 Timing definition

Rectpack timings include packer construction, loading and packing. PackingSolver timings include instance construction and optimisation. Output extraction and shared metric calculation are excluded; PackingSolver certificate export, parsing and validation are also excluded.

A configured solver budget is not a guaranteed end-to-end wall-clock maximum. Timings therefore support an observed computational trade-off, not a production latency guarantee.

### 4.4 Checks on the saved results

This report update checked the script-generated per-run results in
`results/rectpack/pilot_v1_results.csv` and
`results/packingsolver/pilot_v1_results.csv`. The files contain 960
Rectpack records and 60 PackingSolver records. Earlier raw CSV files are
retained separately and are not inputs to the current command-line
comparison by default.

The checks established:

- All 960 Rectpack rows are complete; 59 of the 60 PackingSolver rows are complete.
- The incomplete PackingSolver result is recorded as `no_solution_returned` for the rotation-enabled configuration.
- No duplicate run identifiers in either file.
- Thirty datasets per configuration and rotation setting in the raw files; the common quality-analysis set excludes the one unsuccessful order for all setups in that rotation setting.
- Agreement of paired metadata: seed, profile, requested part count, sheet dimensions, stock limit, requested area and total part count.
- Both adapters record layout validation for populated results; the unsuccessful PackingSolver row has no populated geometry to validate.

These checks establish consistency of recorded results and metadata, not a fresh solver run or independent verification of all placements.

## 5. Results

### 5.1 Comparison with a fixed baseline

`MaxRectsBssf / long_side / BBF` has the lowest aggregate sheet count among the tested fixed Rectpack configurations in both rotation settings. This baseline was selected after examining this benchmark; its ranking is descriptive and has not been validated on held-out workloads.

| Rotation | Fixed Rectpack total | PackingSolver total | Sheets avoided | Reduction relative to Rectpack |
|---|---:|---:|---:|---:|
| Prohibited | 414 | 402 | 12 | 2.90% |
| Permitted | 387 | 377 | 10 | 2.58% |

The rotation-prohibited totals use 30 independent orders. Rotation-permitted totals use the 29 orders completed by every setup. Orders were not pooled into a single joint packing problem.

| Rotation | PackingSolver uses fewer sheets | Same sheet count | PackingSolver uses more sheets |
|---|---:|---:|---:|
| Prohibited | 10 | 20 | 0 |
| Permitted | 10 | 19 | 0 |

The reduction is concentrated in a subset of orders, not uniformly distributed across every instance. Neither sheet-count reductions nor percentage differences establish monetary savings without stock prices, process costs and representative demand.

### 5.2 Runtime trade-off

| Rotation | Fixed Rectpack median runtime | PackingSolver median runtime |
|---|---:|---:|
| Prohibited | 2.089 ms | 0.738 s |
| Permitted | 1.401 ms | 5.011 s |

Each median is calculated across per-dataset runtimes in the common complete subset. PackingSolver P95 runtimes are approximately 30.1 and 30.1 seconds. The contrast supports retaining a fast heuristic baseline while investigating whether additional computation is worthwhile for selected workloads. Single-run timing observations and incompletely documented hardware limit broader performance claims.

### 5.3 Best Rectpack result selected per dataset

Selecting the best Rectpack sheet count retrospectively for each dataset gives the following comparison:

| Rotation | PackingSolver uses fewer sheets | Same sheet count | PackingSolver uses more sheets |
|---|---:|---:|---:|
| Prohibited | 7 | 23 | 0 |
| Permitted | 7 | 22 | 0 |

Thus some benefits remain even against the hindsight-best Rectpack result. However, retrospective selection is not an implemented portfolio strategy. A deployable portfolio must define which configurations run, when to stop and how to select a result; its timing must include all work performed.

Notebook 04 also selects a single winner by sorting sheet count and then runtime. Those counts describe runtime-tiebroken selections, not all methods tying on material use. They should not replace explicit wins, ties and losses.

### 5.4 Configuration and rotation matter

Configuration choice materially changes Rectpack performance. Compare `comparison_summary_by_mean_sheets.csv` and `comparison_summary_by_workload.csv` for the current setup-by-setup results. Differences are benchmark-specific, not universal algorithm rankings.

On the matched sets, allowing rotation reduces PackingSolver’s total from 402 to 377 sheets, but the rotated result covers one fewer order. Rotation must remain an explicit permission, not an assumed production capability.

## 6. Unsuccessful searches and robustness

The PackingSolver exploration records a diagnostic in which a short budget returned no populated solution and a longer run returned a complete layout. This motivates a distinction between unsuccessful search and proven infeasibility. It is not evidence that a particular larger budget always succeeds.

The current adapter returns `run_status="no_solution_returned"` for an empty exported result. That branch also records zero-valued packing fields and `layout_valid=False`. These values must not be interpreted as a superior zero-sheet plan or proof of geometric invalidity: no populated layout was available to assess.

Before experiments with unsuccessful runs are ranked, report completion and search status separately and exclude unavailable solutions from quality rankings. The command-line comparison script writes a full completion report, then restricts quality comparisons to complete, layout-valid dataset/rotation pairs shared by every supplied setup. In the current pilot, the one unsuccessful rotation-enabled order is therefore excluded from every setup's rotated quality summary.

The summary utility deliberately rejects incomplete orders and repeats with varying quality. Such experiments need an explicit aggregation policy rather than silent averaging.

## 7. Implications and recommended technical direction

### 7.1 Retain interchangeable geometric components

The current evidence supports continuing with existing tools rather than developing a new packing algorithm. Keep datasets, validation, metrics and experiment provenance outside solver-specific code wherever practical.

Two modes merit future evaluation:

- Fast baseline: a fixed Rectpack configuration or an explicitly benchmarked small portfolio.
- Higher-computation search: a time-budgeted PackingSolver run where improved sheet consumption may justify waiting.

This is a proposed strategy, not an implemented fallback, warm start or service architecture. Its value should be measured on representative workloads.

### 7.2 Separate geometry from production planning

For the manufacturing questions motivating the original GoSmarter.ai brief, packing is only one component. A later application must determine eligible stock, preserve inventory and traceability identifiers, enforce process-specific restrictions and report unmet demand.

A small next proof of concept could:

1. Obtain anonymised rectangular orders and stock with dimensions, quantities, material attributes and orientation permissions.
2. Define eligibility and stock-availability rules explicitly.
3. Preserve stock and part identities through solver conversion.
4. Add agreed kerf, margins and spacing rules, without assuming those concepts are interchangeable.
5. Compare the fixed baseline, a measured portfolio and PackingSolver under stated budgets.
6. Record completion, stock consumption, runtime and remaining geometry before introducing cost or remnant-value objectives.

Inventory eligibility rules can restrict which stock is considered; they do not automatically solve allocation across heterogeneous inventories. That would require additional modelling beyond the present identical-sheet adapters.

### 7.3 Readiness assessment

| Component | Assessment | Next evidence needed |
|---|---|---|
| Rectpack adapter | Implemented research baseline with shared validation and mocked tests | Representative workloads and external-solver integration testing |
| PackingSolver adapter | Implemented research integration | Robust status handling, certificate edge cases and deployment measurements |
| Shared benchmark | Reusable experimental foundation | Fresh-environment verification, provenance and repeated timing |
| Metals production application | Outside implemented scope | Eligibility, traceability, process feasibility, costs and scheduling |
| Irregular nesting | Not evaluated | Separate tool assessment and representative experiments |

This report does not establish commercial SaaS suitability. Dependency licensing, deployment and operational obligations require a separate review. OR-Tools, SVGnest and libnest2d were candidates in the original brief, not experimentally evaluated alternatives in this phase.

## 8. Limitations

- Synthetic inputs are not evidence of customer demand, material savings or cutting feasibility.
- The strongest fixed baseline was identified on the same benchmark used to report its performance.
- One observation per configuration does not quantify runtime or solution variability.
- Recorded metadata agreement is not independent verification of underlying placements.
- Older Rectpack results created before validator integration have not been revalidated.
- Lower-bound gaps generally do not prove optimality.
- Adapter timings omit extraction and validation and were not obtained on a documented controlled production host.
- A mixed family of packing heuristics does not constitute a process-specific guillotine-cutting evaluation.
- Material matching, irregular nesting, remnants and scheduling remain unimplemented.
- The complete installation workflow has not been independently reproduced in a fresh environment.

## 9. Prioritised next steps

### Publication and reproducibility

1. Preserve the input datasets and per-run CSVs alongside comparison outputs.
2. Record solver versions, the environment and commands that produced each result file.
3. Verify local installation, tests and command-line workflows in a clean environment.
4. Label historical notebook outputs and keep exploratory sections distinct from current scripts.
5. Add end-to-end checks against the installed solver packages and representative workloads.
6. Retain explicit completion reporting and document exclusions from quality comparisons.

### Future research

1. Test on representative, non-confidential manufacturing workloads.
2. Evaluate repeated runs and an explicit Rectpack portfolio.
3. Add further solver adapters only where they answer a defined comparison question.
4. Investigate process constraints and eligible-stock allocation before broader production planning.
5. Treat irregular nesting, remnant management and scheduling as separate extensions.

These extensions are recommendations, not prerequisites for recognising the present project as a completed initial investigation.

## 10. Evidence and repository map

This documentation update did not rerun a solver. The current pilot
findings were read from the script-generated per-run CSVs and comparison
tables; they remain subject to the single-run and synthetic-data
limitations described above.

- Dataset generation: [`rectangle_datasets.py`](../src/cutting_benchmark/rectangle_datasets.py) and [generation script](../scripts/generate_rectangle_datasets.py).
- Solver integrations: [`solvers/`](../src/cutting_benchmark/solvers/).
- Shared metrics: [`rectangle_metrics.py`](../src/cutting_benchmark/rectangle_metrics.py).
- Layout validation: [`rectangle_validation.py`](../src/cutting_benchmark/rectangle_validation.py).
- Benchmark execution: [`benchmark.py`](../src/cutting_benchmark/benchmark.py).
- Summary policy: [`summaries.py`](../src/cutting_benchmark/summaries.py).
- Command-line runs: [`scripts/`](../scripts/).
- General comparison workflow: [`compare_solver_benchmarks.py`](../scripts/compare_solver_benchmarks.py).
- Main Rectpack workflow: [`rectpack_demo.ipynb`](../notebooks/rectpack_demo.ipynb).
- PackingSolver investigation: [`03_packingsolver_exploration.ipynb`](../notebooks/03_packingsolver_exploration.ipynb).
- Cross-solver analysis: [`04_package_comparison.ipynb`](../notebooks/04_package_comparison.ipynb).
- Saved experiment outputs: [`results/rectpack/`](../results/rectpack/) and [`results/packingsolver/`](../results/packingsolver/).
- Tests: [`tests/`](../tests/).

The current numerical comparison uses:

- `results/rectpack/pilot_v1_results.csv`
- `results/packingsolver/pilot_v1_results.csv`

The current comparison tables are generated by
`scripts/compare_solver_benchmarks.py`. The script discovers compatible
result files or accepts explicit paths, preserves source/configuration
identity, reports completion for all runs and compares quality on matched
complete results. Shared aggregation and paired-comparison logic lives in
`src/cutting_benchmark/summaries.py` and
`src/cutting_benchmark/comparison.py`. Notebook 04 remains an earlier,
path-specific analysis workflow.

Generated numerical evidence is saved under `results/comparison/`. The
comparison script overwrites its named output tables but does not remove
unrelated older files in that directory.

This report is intended to live at `docs/report.md`.
