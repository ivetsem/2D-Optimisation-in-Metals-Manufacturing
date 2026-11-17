# Initial research: 2D optimisation for metals manufacturing

**Project:** GoSmarter.ai — 2D Optimisation Challenge  
**Date:** 17 November 2026  
**Status:** Initial rectangle-packing investigation and proof-of-concept benchmark  
**Evidence:** Synthetic datasets, implementation work and benchmark summaries supplied for this investigation.

## Executive findings

Two open-source libraries, RectPack and PackingSolver, have been integrated into a reusable rectangle-packing benchmark. Both completed all tested datasets under the final benchmark settings. PackingSolver matched or improved upon every tested RectPack configuration on sheet count for each dataset and rotation setting. RectPack returned results in milliseconds, compared with seconds for PackingSolver.

The strongest **single fixed RectPack configuration by mean sheet count** was `MaxRectsBssf` with long-side sorting and BBF bin selection. Relative to that configuration, PackingSolver reduced total sheet use across the 30 datasets from 414 to 404 without rotation, and from 398 to 391 with rotation: approximately **2.4% and 1.8%**, respectively. These are benchmark-specific material-quantity reductions, not established customer cost savings.

The recommended next step is not to develop a new geometric algorithm. Retain a fast RectPack baseline, investigate PackingSolver as a higher-quality optimisation option, and introduce representative manufacturing data and constraints incrementally. No production-readiness conclusion is justified yet.

## Scope and stopping point

The brief covers a much wider space than this initial implementation: rectangular and irregular nesting, cutting restrictions, material matching, traceability, remnants, scheduling, costs and scenarios.

Work completed here focuses on **rectangular parts packed onto identical rectangular sheets**, comparing material use and runtime under controlled conditions. It provides a working geometric proof of concept and an extensible evaluation framework, rather than a complete metals production-planning application.

| Area | Status at this stopping point |
|---|---|
| RectPack algorithms, sorting and rotation | Implemented and benchmarked |
| PackingSolver rectangle integration | Implemented and benchmarked |
| Shared metrics and layout representation | Implemented |
| Solver-independent geometric validator | Implemented and unit-tested; used in PackingSolver adapter |
| Cross-tool comparison | Initial descriptive analysis completed |
| Guillotine manufacturing feasibility | Not evaluated as a process-specific cutting model |
| Irregular nesting | Not experimentally evaluated |
| Material matching, traceability and remnants | Requirements identified; not implemented |
| Scheduling, costs and production sequencing | Not implemented |
| Licensing and commercial SaaS review | Outstanding; no legal/commercial clearance claimed |

## Benchmark design

### Dataset matrix

The supplied tables cover 30 synthetic datasets, each tested with and without 90-degree rotation:

- Three profiles: `large_and_small`, `mixed` and `strips`.
- Two order sizes: 35 and 100 requested parts.
- Five seeds: 0–4.
- Identical sheets with dimensions 2500 × 1250 in consistent input units.

The dataset IDs establish the dimensions but not their physical unit. Interpret them as millimetres only after confirming that convention in the dataset documentation. Profile names describe the generator categories; precise dimension distributions should be taken from the generator rather than inferred from these names.

### Tested methods

RectPack used offline packing with BBF bin selection. The comparison covers four algorithms, four sorting rules and two rotation settings:

| Setting | Values |
|---|---|
| Algorithms | `MaxRectsBssf`, `MaxRectsBaf`, `SkylineBl`, `GuillotineBafSas` |
| Sorting | Input order, area, short side, long side |
| Rotation | Prohibited / permitted |
| PackingSolver objective | `BinPacking` |
| PackingSolver budget | 30 seconds per final benchmark run |

Each method–rotation combination has 30 result rows. The initial comparison uses one observation per dataset and configuration. It therefore measures observed outcomes, not runtime variability or statistical significance.

PackingSolver was installed as version `0.1.1340` under Python `3.14.2`. The RectPack version and hardware details should be recorded alongside the saved raw results before rerunning or publishing the benchmark externally.

### Implementation and validation

The `cutting_benchmark` package separates dataset generation, solver adapters, metrics, benchmarking and summaries. Both adapters produce placements as `(bin_id, x, y, width, height, part_id)` and retain original part identities.

The PackingSolver adapter builds one item type per requested part, applies explicit rotation rules, exports a temporary CSV certificate and converts that certificate into the shared representation. The current adapter requires integer dimensions and one physical sheet per certificate `BIN` row.

The shared validator checks part identity, allowed dimensions and orientation, containment, overlap, sheet dimensions and stock limits. Touching edges and valid partial layouts are permitted. Tests deliberately include invalid layouts so that a passing test confirms rejection of the intended error.

**Validation caveat:** the supplied RectPack adapter calculates metrics but does not call the new validator. The shared validator is available for RectPack, but this report does not assume that all historic RectPack outputs have been revalidated. Count-based completion alone does not prove layout validity.

### Metrics and timing

The primary metric is the number of sheets required to complete an order. Utilisation is packed area divided by total used-sheet area. For the **same complete order on identical sheets**, fewer sheets and higher utilisation are mathematically equivalent objectives. If two methods use the same sheet count on that order, their overall utilisation must also be the same, apart from numerical rounding.

Mean utilisation across datasets weights each dataset equally; it is not pooled material utilisation across the whole benchmark. Mean sheet count also mixes different order sizes, so profile- and workload-specific analysis remains important.

The area lower bound is the ceiling of requested area divided by one sheet's area. It ignores geometric incompatibilities and is not generally a proof of optimality. However, a valid complete packing that attains that bound is optimal for sheet count.

Both adapters' recorded `runtime_seconds` include construction/loading and packing or optimisation, but exclude output extraction and metric calculation. PackingSolver's CSV export and geometric validation are also outside its timed section. These figures are therefore **not full application end-to-end runtimes**. The 30-second setting is a solver budget, not a guaranteed wall-clock maximum.

## Results by method

Every row in the supplied method summary reports 30 complete runs out of 30. The following table highlights PackingSolver, the strongest fixed RectPack configuration by mean sheet count, and a particularly fast competitive alternative.

| Rotation | Method | Mean sheets | Median sheets | Best or tied / 30 | Mean time | Median time | Mean utilisation |
|---|---|---:|---:|---:|---:|---:|---:|
| No | PackingSolver, 30 s | 13.467 | 9.5 | 30 | 10.684 s | 1.208 s | 72.65% |
| No | MaxRectsBssf, long side | 13.800 | 10.0 | 21 | 3.194 ms | 2.172 ms | 68.68% |
| No | GuillotineBafSas, long side | 13.867 | 10.0 | 18 | 2.508 ms | 1.635 ms | 67.68% |
| Yes | PackingSolver, 30 s | 13.033 | 9.0 | 30 | 11.508 s | 7.250 s | 73.97% |
| Yes | MaxRectsBssf, long side | 13.267 | 9.5 | 23 | 3.799 ms | 3.075 ms | 71.34% |
| Yes | GuillotineBafSas, long side | 13.400 | 9.5 | 19 | 2.906 ms | 2.366 ms | 70.58% |

### Strongest fixed configuration

PackingSolver achieved the lowest mean sheet count and matched the observed minimum on every dataset in both rotation settings. This is **best observed among tested methods**, not a general proof that every returned solution is globally optimal.

Within RectPack, `MaxRectsBssf / long_side / BBF` is the strongest fixed choice by mean sheet count and best-or-tied frequency. `GuillotineBafSas / long_side / BBF` is slightly faster but uses more sheets overall.

| Rotation | Fixed RectPack total | PackingSolver total | Sheets avoided | Reduction relative to RectPack |
|---|---:|---:|---:|---:|
| No | 414 | 404 | 10 | 2.42% |
| Yes | 398 | 391 | 7 | 1.76% |

Totals are reconstructed from 30 runs and the supplied rounded means. They should be confirmed directly from raw integer sheet counts when finalising the analysis.

Sorting materially affects performance. For example, without rotation, `GuillotineBafSas` changes from 13.867 mean sheets with long-side sorting to 16.967 with short-side sorting. With rotation, those means are 13.400 and 16.200. Selecting a library alone is therefore insufficient: configuration matters.

### Interpreting winner counts

The per-dataset winner table was produced by sorting on sheet count and then runtime, before selecting one row per dataset and rotation setting. Its counts answer:

> Which method had the lowest sheet count, breaking ties using the shortest measured runtime?

They do **not** count all methods tying on material use.

| Rotation | PackingSolver selected | RectPack selected | PackingSolver best or tied |
|---|---:|---:|---:|
| No | 6 | 24 | 30 / 30 |
| Yes | 4 | 26 | 30 / 30 |

This explains why `GuillotineBafSas / long_side` appears as the selected winner 14 times without rotation and 13 times with rotation, even though `MaxRectsBssf / long_side` has a better mean sheet count. Guillotine often wins the runtime tie-break on shared-quality solutions; it is not the strongest fixed configuration overall.

The counts suggest that a portfolio of RectPack configurations can often match PackingSolver quickly, while PackingSolver adds material-use improvements on a subset of cases. A portfolio must be benchmarked as an actual strategy: hindsight selection of the best method per dataset is not a deployable algorithm, and its runtime must include every configuration tried.

## Dataset-level observations

### Geometry changes the attainable utilisation

The selected solutions for `large_and_small` datasets have utilisation of approximately 44–58%, whereas several `mixed` and `strips` solutions exceed 85–90%. Low utilisation alone does not establish poor optimisation: large incompatible dimensions can force substantial unused area even in a minimum-sheet packing.

These differences support analysing results by profile and part count rather than relying only on an overall mean. They do not yet establish a causal explanation for each individual packing; visual inspection and lower bounds are needed for that.

### Illustrative results

| Dataset suffix | Rotation | Selected result | Utilisation | Interpretation |
|---|---|---:|---:|---|
| `mixed_n100_seed1` | Yes | PackingSolver: 10 sheets | 97.15% | High-density result selected despite a 29.74 s runtime; inspect paired RectPack rows to quantify savings |
| `mixed_n35_seed3` | Both | PackingSolver: 4 sheets | 92.73% | Selected in both rotation settings; result reaches the area lower bound |
| `strips_n100_seed3` | No / Yes | PackingSolver: 8 / 7 sheets | 81.60% / 93.26% | Rotation reduces the best observed sheet count by one |
| `large_and_small_n100_seed1` | No / Yes | RectPack: 39 / 38 sheets | 50.89% / 52.22% | Fast RectPack configurations attain the observed minimum |

Dataset suffixes omit the common `rect_v1_` prefix and `sheet2500x1250` component.

For `mixed_n35_seed3`, four sheets at 92.73% utilisation imply requested area greater than three sheet areas. Consequently, fewer than four sheets are impossible, and this particular complete result is sheet-count optimal by the area bound. This reasoning does not imply optimality for all other benchmark rows.

### Rotation benefits both approaches

Allowing rotation reduced PackingSolver's aggregate sheet count from 404 to 391 across the 30 datasets, about 3.2%. The strongest fixed RectPack configuration improved from 414 to 398, about 3.9%.

These benefits apply only where rotation is operationally permitted. A production system must respect any directional finish, grain, rolling-direction or part-specific restrictions instead of assuming unrestricted rotation.

## Runtime and unsuccessful searches

A diagnostic on `large_and_small_n100_seed1` returned no populated solution with a five-second setting; reported elapsed time was approximately 9.17 seconds. A longer-budget run returned all 100 parts on 38 sheets after approximately 10.53 seconds and reported equal primal and dual bounds.

This demonstrated the need to distinguish **no solution returned** from **proven infeasible**. Every part fitted individually with rotation, and stock allowed one sheet per part, so the instance was feasible irrespective of whether the short search returned a solution.

The adapter was updated to record an empty-result outcome rather than aborting the entire benchmark. Invalid layouts and unsupported certificate conversions remain errors. The final 30-second experiments all returned complete results.

**Reporting correction:** the current empty-result branch uses zero-valued quality fields and `layout_valid=False`. A missing layout is neither a valid zero-sheet solution nor necessarily an invalid geometric layout. Before analysing experiments containing such rows, exclude them from quality rankings and preferably change unavailable fields to missing values and use an explicit status. This issue does not change the current all-successful comparison.

## Implications for GoSmarter.ai

### Recommended architecture

Use the solver as a replaceable geometric optimisation component behind a shared application-level contract. Keep inventory eligibility, traceability, job metadata, validation and reporting outside solver-specific code wherever practical.

Two service levels are worth testing:

- **Fast preview:** a selected RectPack configuration, or a measured small portfolio, for interactive planning.
- **Improved plan:** a time-budgeted PackingSolver run where additional computation may reduce sheet consumption.

This is a proposed architecture, not yet an implemented fallback or warm-start mechanism. Before adopting it, measure whether material improvements justify compute and waiting time on representative workloads.

### Readiness assessment

| Component | Current assessment | Required next work |
|---|---|---|
| RectPack adapter | Working research baseline | Revalidate historic layouts, pin dependencies, test representative production data |
| PackingSolver adapter | Working research integration | Add bound/status metadata, robust unsuccessful-run records, certificate edge cases and performance evaluation |
| Shared benchmark | Reusable experimental foundation | Record environment, verify paired coverage, add repetitions and durable progress saving |
| Metals planning application | Significant application development required | Material eligibility, traceability, remnants, process feasibility, priorities and costs |
| Irregular nesting and custom scheduling | Not evaluated in this phase | Separate tool assessment and representative proof of concept |

Neither integration should be described as production-ready for metals manufacturing solely because it completed these synthetic instances. Licensing, dependency obligations, deployment behaviour and commercial SaaS suitability require a separate review.

## Proposed manufacturing proof of concept

Keep the next milestone small: rectangular orders assigned to compatible stock, followed by a validated nesting plan.

1. Obtain an anonymised production sample with part dimensions, quantities, grade, thickness and permitted orientations.
2. Model a limited sheet inventory with dimensions, availability, material attributes and traceability IDs.
3. Enforce material and certification eligibility as hard constraints. Preserve the selected stock ID through every placement.
4. Add process-specific edge margins, clearance and kerf rules; confirm their meaning with manufacturing stakeholders rather than treating all spacing as interchangeable.
5. Compare the strongest fixed RectPack baseline, a measured RectPack portfolio and PackingSolver under explicit budgets.
6. Record sheet use, actual stock cost, runtime, remaining material and unmet demand. Do not call all unused area reusable offcut: remnant geometry and handling rules matter.

A later phase can introduce job priorities, due dates, machine capacity, sequencing and scenario planning. Irregular nesting and guillotine cutting should be evaluated as distinct problem variants, rather than assumed to follow automatically from unrestricted rectangle packing.

## Limitations and next evidence

- Synthetic profiles are not evidence of customer material savings or production feasibility.
- One observation per configuration does not quantify runtime variability.
- Different geometric algorithm families were compared for an unrestricted packing baseline; this is not a fair process-specific guillotine comparison.
- The original RectPack results should be passed through the shared validator before stronger correctness claims.
- Summary averages conceal dataset-level savings; retain paired raw rows and report wins, ties and losses explicitly.
- Best-or-tied scores refer to the tested methods, not global optima.
- Mean utilisation is an unweighted mean across orders, not pooled utilisation.
- Runtime excludes extraction and validation and was not measured on a documented controlled production host.
- Licensing, maintained-version assessment and SaaS deployment review remain incomplete.
- OR-Tools, SVGnest and libnest2d were identified in the brief but were not experimentally evaluated in this phase.

## Suggested meeting narrative

> We now have a working, reproducible rectangle-packing baseline with interchangeable solver adapters. PackingSolver produced the best observed material-use results on every test, allowing ties. Against the strongest single RectPack configuration, aggregate sheet use improved by approximately 2%. RectPack returned solutions in milliseconds and frequently matched that quality. The next decision is which production constraints and representative customer cases to add—not whether we need to invent a nesting algorithm from scratch.

## Evidence and repository map

The empirical results in this report come from the supplied method summary, runtime-tiebroken per-dataset winner table and diagnostic solver output. No new benchmark was run to write this report.

- Dataset generation: `src/cutting_benchmark/rectangle_datasets.py` and `scripts/generate_rectangle_datasets.py`.
- Shared metrics: `src/cutting_benchmark/rectangle_metrics.py`.
- Shared validation: `src/cutting_benchmark/rectangle_validation.py`.
- Solver integrations: `src/cutting_benchmark/solvers/`.
- Benchmark orchestration: `src/cutting_benchmark/benchmark.py`.
- Experiments: `notebooks/`.
- Saved evidence: `results/rectpack/` and `results/packingsolver/`.
- Validator tests: `tests/test_rectangle_validation.py`.

Before circulating externally, confirm physical units, dependency versions, hardware, repeat handling and full paired raw-data coverage. Retain the raw tables alongside this report so every aggregate can be reproduced.
