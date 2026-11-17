# Rectangular packing for metals manufacturing: research and benchmark report

Date: 17 November 2026  
Status: Portfolio research prototype and initial comparative evaluation

## Executive summary

This project investigates existing open-source rectangular-packing tools and provides a reusable Python benchmark for comparing them. It was motivated by a research brief concerning the potential extension of GoSmarter.ai’s 1D cutting capabilities to 2D sheet and plate planning. This repository presents the author’s own implementation and analysis, not a delivered production system.

The main software contribution is a benchmark architecture that separates synthetic datasets, solver-specific adapters, shared metrics, validation and analysis. Rectpack and PackingSolver are currently integrated. The architecture is intended to accommodate further solvers without duplicating the complete experimental workflow.

The recorded experiment covers 30 synthetic datasets, two rotation settings, 16 Rectpack configurations and one PackingSolver configuration with a 30-second time budget. All 1,020 recorded runs completed their orders. PackingSolver matched or improved on every tested Rectpack configuration on each matched dataset and rotation setting.

Against the strongest fixed Rectpack configuration by mean sheet count, `MaxRectsBssf / long_side / BBF`, PackingSolver reduced aggregate sheet use from 414 to 404 without rotation (2.42%) and from 398 to 391 with rotation (1.76%). These totals describe separate synthetic orders; they are not measured customer savings.

The trade-off was computation time. The fixed Rectpack baseline had median recorded runtimes of approximately 2.2 and 3.1 milliseconds without and with rotation, respectively. PackingSolver’s corresponding medians were 1.2 and 7.3 seconds. These are adapter timings, not complete application response times.

The practical recommendation is to retain a fast Rectpack baseline and evaluate PackingSolver as a higher-computation alternative where lower sheet consumption matters. Additional geometric algorithms are not the immediate priority. Representative data, consistent validation and explicit manufacturing constraints are the next evidence needed before considering a production application.

## 1. Scope and stopping point

The original brief included rectangular and irregular nesting, cutting restrictions, material matching, traceability, remnants, scheduling and scenario planning. This phase deliberately addresses a smaller problem: placing rectangular parts on identical rectangular sheets and comparing completion, sheet consumption and runtime.

| Area | Status |
|---|---|
| Synthetic datasets and JSON persistence | Implemented |
| Rectpack algorithms, sorting and rotation experiments | Implemented and benchmarked |
| PackingSolver rectangle adapter | Implemented and benchmarked |
| Shared metrics and layout representation | Implemented |
| Shared geometric validator | Implemented, with unit tests; invoked by the PackingSolver adapter |
| Cross-solver analysis | Implemented as exploratory notebook analysis; underlying CSV comparisons checked for this report |
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

The PackingSolver adapter invokes this validator, and all 60 saved PackingSolver rows record `layout_valid=True`. The supplied Rectpack adapter does not invoke it. Therefore historic Rectpack results are complete by their recorded counts, but are not claimed here to have been independently revalidated with the shared validator. Layouts were not reconstructed from the summary CSVs during this report update.

### 4.3 Timing definition

Rectpack timings include packer construction, loading and packing. PackingSolver timings include instance construction and optimisation. Output extraction and shared metric calculation are excluded; PackingSolver certificate export, parsing and validation are also excluded.

A configured solver budget is not a guaranteed end-to-end wall-clock maximum. Timings therefore support an observed computational trade-off, not a production latency guarantee.

### 4.4 Checks on the saved results

This report update checked the saved per-run results in
`results/rectpack/rectpack_benchmark_raw.csv` and
`results/packingsolver/packingsolver_benchmark_raw.csv`.
The files contain 960 Rectpack records and 60 PackingSolver records.

The checks established:

- 960 Rectpack rows and 60 PackingSolver rows, all marked complete.
- No duplicate run identifiers in either file.
- Thirty datasets per Rectpack configuration and rotation setting, with matched PackingSolver coverage.
- Agreement of paired metadata: seed, profile, requested part count, sheet dimensions, stock limit, requested area and total part count.
- PackingSolver used no more sheets than Rectpack in all 960 matched configuration-level comparisons.

These checks establish consistency of recorded results and metadata, not a fresh solver run or independent verification of all placements.

## 5. Results

### 5.1 Comparison with a fixed baseline

`MaxRectsBssf / long_side / BBF` has the lowest aggregate sheet count among the tested fixed Rectpack configurations in both rotation settings. This baseline was selected after examining this benchmark; its ranking is descriptive and has not been validated on held-out workloads.

| Rotation | Fixed Rectpack total | PackingSolver total | Sheets avoided | Reduction relative to Rectpack |
|---|---:|---:|---:|---:|
| Prohibited | 414 | 404 | 10 | 2.42% |
| Permitted | 398 | 391 | 7 | 1.76% |

Totals are calculated directly from integer sheet counts over 30 independent orders. Orders were not pooled into a single joint packing problem.

| Rotation | PackingSolver uses fewer sheets | Same sheet count | PackingSolver uses more sheets |
|---|---:|---:|---:|
| Prohibited | 9 | 21 | 0 |
| Permitted | 7 | 23 | 0 |

The reduction is concentrated in a subset of orders, not uniformly distributed across every instance. Neither sheet-count reductions nor percentage differences establish monetary savings without stock prices, process costs and representative demand.

### 5.2 Runtime trade-off

| Rotation | Fixed Rectpack median runtime | PackingSolver median runtime |
|---|---:|---:|
| Prohibited | 2.172 ms | 1.208 s |
| Permitted | 3.075 ms | 7.250 s |

Each median is calculated over 30 recorded runs. The contrast supports retaining a fast heuristic baseline while investigating whether additional computation is worthwhile for selected workloads. Single-run timing observations and incompletely documented hardware limit broader performance claims.

### 5.3 Best Rectpack result selected per dataset

Selecting the best Rectpack sheet count retrospectively for each dataset gives the following comparison:

| Rotation | PackingSolver uses fewer sheets | Same sheet count | PackingSolver uses more sheets |
|---|---:|---:|---:|
| Prohibited | 6 | 24 | 0 |
| Permitted | 4 | 26 | 0 |

Thus some benefits remain even against the hindsight-best Rectpack result. However, retrospective selection is not an implemented portfolio strategy. A deployable portfolio must define which configurations run, when to stop and how to select a result; its timing must include all work performed.

Notebook 04 also selects a single winner by sorting sheet count and then runtime. Those counts describe runtime-tiebroken selections, not all methods tying on material use. They should not replace explicit wins, ties and losses.

### 5.4 Configuration and rotation matter

Configuration choice materially changes Rectpack performance. Without rotation, `GuillotineBafSas` uses 416 sheets in total with long-side sorting versus 509 with short-side sorting. With rotation, the corresponding totals are 402 and 486. These are benchmark-specific differences, not universal algorithm rankings.

Allowing rotation reduces PackingSolver’s total from 404 to 391 sheets (3.22%) and the fixed Rectpack baseline from 414 to 398 (3.86%). Rotation must remain an explicit permission, not an assumed production capability.

## 6. Unsuccessful searches and robustness

The PackingSolver exploration records a diagnostic in which a short budget returned no populated solution and a longer run returned a complete layout. This motivates a distinction between unsuccessful search and proven infeasibility. It is not evidence that a particular larger budget always succeeds.

The current adapter returns `run_status="no_solution_returned"` for an empty exported result. That branch also records zero-valued packing fields and `layout_valid=False`. These values must not be interpreted as a superior zero-sheet plan or proof of geometric invalidity: no populated layout was available to assess.

Before experiments with unsuccessful runs are ranked, report completion and search status separately and exclude unavailable solutions from quality rankings. Use common eligible datasets or clearly report differing coverage. The current comparison notebook calculates some quality summaries before filtering completion; this needs hardening for future mixed-success experiments, but does not alter this all-complete result set.

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
| Rectpack adapter | Implemented research baseline | Shared validation, integration tests and representative workloads |
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
- Historic Rectpack results have not been revalidated with the shared validator.
- Lower-bound gaps generally do not prove optimality.
- Adapter timings omit extraction and validation and were not obtained on a documented controlled production host.
- A mixed family of packing heuristics does not constitute a process-specific guillotine-cutting evaluation.
- Material matching, irregular nesting, remnants and scheduling remain unimplemented.
- The complete installation workflow has not been independently reproduced in a fresh environment.

## 9. Prioritised next steps

### Publication and reproducibility

1. Preserve the raw result files alongside the notebooks so the reported
   comparisons can be reproduced.
2. Record solver versions, the environment and the commands producing each result file.
3. Verify local installation, tests and the supported notebook workflow in a clean environment.
4. Correct historical notebook state and label exploratory sections explicitly.
5. Apply shared validation to Rectpack outputs in future runs and add targeted adapter/runner tests.
6. Harden comparison logic for unsuccessful runs and document any exclusions.

### Future research

1. Test on representative, non-confidential manufacturing workloads.
2. Evaluate repeated runs and an explicit Rectpack portfolio.
3. Add further solver adapters only where they answer a defined comparison question.
4. Investigate process constraints and eligible-stock allocation before broader production planning.
5. Treat irregular nesting, remnant management and scheduling as separate extensions.

These extensions are recommendations, not prerequisites for recognising the present project as a completed initial investigation.

## 10. Evidence and repository map

No new solver benchmark was run to write this update. Results were recomputed from the supplied per-run CSVs and interpreted against the implementation and notebooks.

- Dataset generation: [`rectangle_datasets.py`](../src/cutting_benchmark/rectangle_datasets.py) and [generation script](../scripts/generate_rectangle_datasets.py).
- Solver integrations: [`solvers/`](../src/cutting_benchmark/solvers/).
- Shared metrics: [`rectangle_metrics.py`](../src/cutting_benchmark/rectangle_metrics.py).
- Layout validation: [`rectangle_validation.py`](../src/cutting_benchmark/rectangle_validation.py).
- Benchmark execution: [`benchmark.py`](../src/cutting_benchmark/benchmark.py).
- Summary policy: [`summaries.py`](../src/cutting_benchmark/summaries.py).
- Main Rectpack workflow: [`rectpack_demo.ipynb`](../notebooks/rectpack_demo.ipynb).
- PackingSolver investigation: [`03_packingsolver_exploration.ipynb`](../notebooks/03_packingsolver_exploration.ipynb).
- Cross-solver analysis: [`04_package_comparison.ipynb`](../notebooks/04_package_comparison.ipynb).
- Saved experiment outputs: [`results/rectpack/`](../results/rectpack/) and [`results/packingsolver/`](../results/packingsolver/).
- Tests: [`tests/`](../tests/).

The numerical comparison uses:

- `results/rectpack/rectpack_benchmark_raw.csv`
- `results/packingsolver/packingsolver_benchmark_raw.csv`

The comparison tables are generated by
`notebooks/04_package_comparison.ipynb` from the saved per-run benchmark
results. Shared aggregation and paired-comparison logic lives in
`src/cutting_benchmark/summaries.py` and
`src/cutting_benchmark/comparison.py`.

Generated numerical evidence is saved under `results/comparison/`,
alongside a manifest recording input hashes and analysis provenance.

This report is intended to live at `docs/report.md`.