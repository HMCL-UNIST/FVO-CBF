# Finite-time Velocity Obstacle-based Control Barrier Function

Simulation source code for collision avoidance in fixed-wing UAV flocking via a **Finite-time Velocity Obstacle-based Control Barrier Function (FVO-CBF)**, integrated with the augmented Cucker–Smale (ACS) flocking law under nonholonomic constraints.

**Paper:** under review.

## Methods

| Tag | Method |
|---|---|
| `fvo` | **FVO-CBF (proposed)** — truncated collision cone, state-dependent horizon |
| `vo` | VO-CBF |
| `ma` | MA-VO-CBF (slack variables) |
| `ho` | HOCBF (distance-based) |
| `nominal` | ACS flocking only, no CBF |

## Experiment groups

| Directory | Sweep | Fixed |
|---|---|---|
| `fvo_cbf_agent/` | `N = 5, 10, 15, 20, 25` | `R = 60 m`, `Ds = 40 m` |
| `fvo_cbf_desired/` | `R = 60, 70, 80, 90, 100 m` | `N = 15`, `Ds = 40 m` |
| `fvo_cbf_critical/` | `Ds = 40, 50, 60, 70, 80 m` | `N = 15`, `R = 60 m` |

100 Monte Carlo trials per case per method (5 cases × 5 methods × 100 = 2,500 runs per group).

## Setup

```bash
conda create -n fvo python=3.11
conda activate fvo
pip install numpy scipy matplotlib daqp jupyter

git clone https://github.com/HMCL-UNIST/Finite-time-Velocity-Obstacle-based-Control-Barrier-Function.git
cd Finite-time-Velocity-Obstacle-based-Control-Barrier-Function/fvo_cbf_agent
```

## Run

```bash
# 1. Write control gains and QP settings to parameter/*.npy
jupyter notebook runtime_params.ipynb        # Run All

# 2. Run all 25 jobs (case x method)
python run_agent_win.py                      # in fvo_cbf_agent/
# python run_desired_win.py                  # in fvo_cbf_desired/
# python run_critical_win.py                 # in fvo_cbf_critical/

# 3. Regenerate tables and view figures
jupyter notebook summarize.ipynb
```

Initial conditions used in the paper are already committed under `initial_conditions/`. Run `build_inital_condition.ipynb` only to generate a fresh random set — no seed is fixed anywhere, so regenerating produces different trials and different statistics.

## Output

```
result/<case_id>/<method>/<method>_simulation_data.pkl
logs/<case_id>_<method>.log
logs/summary_<timestamp>.txt
```

Each pickle is a dict of per-trial lists: full state history, applied and nominal control histories, minimum and maximum inter-vehicle distance histories, minimum CBF value history, QP wall time and pure DAQP solve time, initial and final position/velocity standard deviations, the feasibility flag, and the failure reason and time.

`summarize.ipynb` writes eight tables in order: feasibility, failure-reason breakdown, totals per method, position std, velocity std, control deviation `|u_qp - u_nom|`, DAQP solve time (mean / p95 / max), and the overall nominal baseline. Failure reasons are `ok`, `qp_infeasible`, `qp_iter_limit`, `qp_time_limit`, `forward_invariance_fail`, and `collision`.

## Options

Top of `run_<group>_win.py`:

- `MAX_PARALLEL` — concurrent jobs (default `12`; lower for fewer cores)
- `THREADS_PER_PROC` — keep at `"1"` to avoid CPU oversubscription
- `METHODS` — comment out entries to run a subset
- `RUN_SUMMARY = False` — skip the automatic summary

Setup cell of `summarize.ipynb`:

- `CASE_FILTER = 'case0_N5'` — summarize a single case instead of all

`runtime_params.ipynb` writes `beta`, `lamda`, `k1`, `k2`, `qp_max_iter`, `qp_eps_abs`, `qp_time_limit`, and `fi_threshold`. `build_inital_condition.ipynb` writes `STATE_DIM`, `V_CONST`, `class_k1`, `class_k2`, `k_vo`, `margin`, `test_case_num`, the per-case `parameter/<case_id>/` values, `initial_conditions/<case_id>/initial.npy`, and `cases.json`. Edit its `CASES` list to define a different sweep, then Run All.

`class_k2` is used only by `ho` and `ma`; `k_vo` only by `ma`; `nominal_flocking` loads no CBF or QP parameters at all.

Sampling time (`DT_CONTROL = 0.05 s`), terminal time (`T_FINAL = 600 s`), and turn-rate limit (`u_limit = 0.35 rad/s`) are hard-coded inside `run_multi_agent_simulation()` in all five `src/*.ipynb`.
