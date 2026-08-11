# Finite-time-Velocity-Obstacle-based-Control-Barrier-Function

This repository contains the simulation source code for **collision avoidance in fixed-wing UAV flocking via a Finite-time Velocity Obstacle-based Control Barrier Function (FVO-CBF)**. It implements the proposed method alongside the comparison baseline methods described in our paper.

---

## Paper

Under review, will be updated later.

---

## Overview

The project is an expansion of the series of Multi-Agent Systems (MAS) research in **HMCL**. It provides a safety-critical control framework in which the FVO-CBF is integrated with the augmented Cucker–Smale (ACS) flocking control law, so that a swarm of fixed-wing UAVs achieves flocking objectives without inter-vehicle collisions under nonholonomic constraints (non-zero minimum airspeed and bounded turn rate).

Five methods are implemented and compared under an identical safety-critical control structure:

| Tag | Method | Description |
|---|---|---|
| `fvo` | **FVO-CBF (Proposed)** | Truncated collision cone with state-dependent look-ahead horizon |
| `vo` | VO-CBF | Conventional velocity obstacle-based CBF |
| `ma` | MA-VO-CBF | Multi-agent VO-CBF using slack variables |
| `ho` | HOCBF | Distance-based high-order CBF |
| `nominal` | ACS | Nominal flocking control only (no CBF), reference baseline |

The repository is organized into three independent experiment groups, each corresponding to one sweep of the sensitivity analysis:

| Directory | Sweep | Fixed parameters |
|---|---|---|
| `fvo_cbf_agent/` | Number of UAVs `N = [5, 10, 15, 20, 25]` | `R = 60 m`, `Ds = 40 m` |
| `fvo_cbf_desired/` | Desired relative distance `R = [60, 70, 80, 90, 100] m` | `N = 15`, `Ds = 40 m` |
| `fvo_cbf_critical/` | Minimum safe distance `Ds = [40, 50, 60, 70, 80] m` | `N = 15`, `R = 60 m` |

Each group runs **100 Monte Carlo trials per case per method** (5 cases × 5 methods × 100 runs = 2,500 simulations per group).

---

## Repository Structure

```
Finite-time-Velocity-Obstacle-based-Control-Barrier-Function/
├── fvo_cbf_agent/            # Group A: number-of-UAVs sweep
├── fvo_cbf_desired/          # Group B: desired-relative-distance sweep
├── fvo_cbf_critical/         # Group C: minimum-safe-distance sweep
└── README.md
```

Every group shares the same internal layout:

```
fvo_cbf_<group>/
├── src/
│   ├── fvo_cbf_part.ipynb        # Proposed FVO-CBF
│   ├── vo_cbf_part.ipynb         # VO-CBF baseline
│   ├── ma_cbf_vo_part.ipynb      # MA-VO-CBF baseline
│   ├── ho_cbf_part.ipynb         # HOCBF baseline
│   └── nominal_flocking.ipynb    # ACS flocking only
├── parameter/                    # Shared *.npy + per-case parameter/<case_id>/
├── initial_conditions/           # Pre-generated initial states (committed)
├── cases.json                    # Case manifest consumed by the runner
├── runtime_params.ipynb          # ACS + QP solver parameters -> parameter/*.npy
├── build_inital_condition.ipynb  # Regenerates parameter/<case_id>/ and initial_conditions/
├── run_one_method.py             # Executes one (case, method) job
├── run_<group>_win.py            # Batch runner (recommended)
├── run_<group>.sh                # Batch runner (bash alternative)
├── summarize.ipynb               # Aggregates result/ into the paper tables
├── result/                       # Created at runtime: result/<case_id>/<method>/*.pkl
└── logs/                         # Created at runtime: per-job logs + summary_<ts>.txt
```

---

## Getting Started

### Prerequisites

Ensure you have Anaconda installed on your system.

```bash
conda create -n fvo python=3.11
conda activate fvo
pip install numpy scipy matplotlib daqp jupyter
```

The quadratic program in the safety-critical control is solved with the **DAQP** active-set solver.

### Installation

Clone this repository to your local machine using:

```bash
git clone https://github.com/HMCL-UNIST/Finite-time-Velocity-Obstacle-based-Control-Barrier-Function.git
```

---

## Running the Simulation

All commands below are executed **from inside one experiment group directory**, e.g.:

```bash
cd Finite-time-Velocity-Obstacle-based-Control-Barrier-Function/fvo_cbf_agent
```

### Step 1. Set the runtime parameters

Open `runtime_params.ipynb` in Jupyter and **Run All**. This writes the ACS control gains and QP solver settings into `parameter/*.npy`.

```bash
jupyter notebook runtime_params.ipynb
```

### Step 2. (Optional) Regenerate the initial conditions

The initial conditions used in the paper are **already committed** under `initial_conditions/`, so you can skip this step to reproduce the reported numbers exactly.

Only run `build_inital_condition.ipynb` if you want a fresh set of random initial states. Note that no random seed is fixed, so regenerating will produce different trials and therefore slightly different statistics.

### Step 3. Run the simulation

```bash
python run_agent_win.py
```

Despite the `_win` suffix, this runner is fully cross-platform (Windows / Linux / macOS) and is the **recommended** entry point: it pre-creates the `result/<case_id>/<method>/` directories, dispatches all 25 jobs with throttled parallelism, prints a live progress line and a per-case feasibility summary, and automatically produces the final summary table when everything finishes.

Use the corresponding runner in each group:

| Group | Command |
|---|---|
| `fvo_cbf_agent/` | `python run_agent_win.py` |
| `fvo_cbf_desired/` | `python run_desired_win.py` |
| `fvo_cbf_critical/` | `python run_critical_win.py` |

A bash alternative (`run_agent.sh`, etc.) is also provided.

> **Note:** the `.sh` runners do not pre-create the output directories. If you use them, create the folders first, otherwise the notebooks will fail when saving results:
> ```bash
> for c in $(python3 -c "import json;print(' '.join(x['case_id'] for x in json.load(open('cases.json'))))"); do
>     mkdir -p result/$c/{vo,fvo,ho,ma,nominal}
> done
> ```

### Step 4. Inspect the results

The runner writes `logs/summary_<timestamp>.txt`, which contains the feasibility rates, the failure-reason breakdown, the QP cost `||u* - u_n||`, and the QP solve times for every case and method.

To regenerate the tables at any time, or to view the accompanying figures interactively, open:

```bash
jupyter notebook summarize.ipynb
```

---

## Configuration Options

### Runner settings (`run_<group>_win.py`)

1. **Parallel Processing Workers**: set `MAX_PARALLEL` to the number of concurrent (case × method) jobs. The default is `12`; lower it if you have fewer CPU cores or limited memory. For example: `MAX_PARALLEL = 8`.
2. **Threads per Job**: `THREADS_PER_PROC` caps the BLAS/OpenMP threads inside each job. Keep it at `"1"` so that the parallel jobs do not oversubscribe the CPU.
3. **Method Selection**: comment out entries in the `METHODS` list to run only a subset of the controllers. For example, to run only the proposed method and the nominal baseline:
   ```python
   METHODS = [
       ("fvo_cbf_part",     "fvo"),
       ("nominal_flocking", "nominal"),
   ]
   ```
4. **Automatic Summary**: set `RUN_SUMMARY = False` to skip the automatic execution of `summarize.ipynb` at the end of the batch.

### Simulation parameters (`runtime_params.ipynb`)

| Variable | Description | Value |
|---|---|---|
| `beta` | Decay rate of the ACS alignment weight | `0.25` |
| `lamda` | Weighting factor of the alignment term | `1` |
| `k1`, `k2` | ACS flocking control gains | `0.3`, `0.02` |
| `qp_max_iter` | DAQP iteration limit | `100` |
| `qp_eps_abs` | DAQP primal/dual tolerance | `1e-6` |
| `qp_time_limit` | Time limit per QP solve (s) | `0.05` |
| `fi_threshold` | Forward-invariance violation threshold | `-1e-4` |

### Case and CBF parameters (`build_inital_condition.ipynb`)

| Variable | Description | Value |
|---|---|---|
| `V_CONST` | Constant airspeed (m/s) | `20.0` |
| `class_k1`, `class_k2` | Extended class-K gains | `0.1`, `0.1` |
| `margin` | Numerical robustness constant | `1e-4` |
| `test_case_num` | Monte Carlo trials per case | `100` |
| `CASES` | Case list `(case_id, N, R, Ds)` | see per-group table above |

Edit the `CASES` list to define a different sweep, then **Run All** to write the matching `parameter/<case_id>/`, `initial_conditions/<case_id>/`, and `cases.json`.

The sampling time (`0.05 s`), terminal time (`600 s`), and turn-rate limit (`0.35 rad/s`) are defined inside `run_multi_agent_simulation()` in each `src/*.ipynb`.

---

## Output

```
result/<case_id>/<method>/<method>_simulation_data.pkl
logs/<case_id>_<method>.log
logs/summary_<timestamp>.txt
```

Each pickle stores, for every Monte Carlo trial, the full state history, the applied and nominal control histories, the minimum inter-vehicle distance, the minimum CBF value, the QP solve times, the feasibility flag, and the failure reason.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'cvxpy'`** — `cvxpy` is a legacy import left in `src/vo_cbf_part.ipynb`, `src/ho_cbf_part.ipynb`, and `src/ma_cbf_vo_part.ipynb`; it is not used because all QPs are solved with DAQP. Either delete the `import cvxpy as cp` line or run `pip install cvxpy`.
- **`FileNotFoundError: result/<case_id>/<method>/...`** — the output directories were not created. Use `run_<group>_win.py`, or create them manually as shown in Step 3.
- **`RuntimeError: CASE_ID env var must be set`** — the `src/*.ipynb` notebooks are not meant to be run standalone in Jupyter. Launch them through the runner, or set `CASE_ID` manually before executing, e.g. `CASE_ID=case0_N5 python run_one_method.py src/fvo_cbf_part.ipynb case0_N5`.
