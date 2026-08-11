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

100 Monte Carlo trials per case per method (2,500 simulations per group).

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

The runners are cross-platform despite the `_win` suffix, and are the recommended entry point — they pre-create the output directories and print a per-case feasibility summary. `.sh` alternatives are provided but do not create the directories.

Initial conditions used in the paper are already committed under `initial_conditions/`. Run `build_inital_condition.ipynb` only to generate a fresh random set (no fixed seed, so results will differ slightly).

## Output

```
result/<case_id>/<method>/<method>_simulation_data.pkl
logs/summary_<timestamp>.txt
```

Each pickle holds, per trial: state and control histories, minimum inter-vehicle distance, minimum CBF value, QP solve times, feasibility flag, failure reason.

## Options

Top of `run_<group>_win.py`:

- `MAX_PARALLEL` — concurrent jobs (default `12`; lower for fewer cores)
- `THREADS_PER_PROC` — keep at `"1"` to avoid CPU oversubscription
- `METHODS` — comment out entries to run a subset
- `RUN_SUMMARY = False` — skip the automatic summary

Simulation parameters live in `runtime_params.ipynb`; case and CBF parameters (`V_CONST = 20 m/s`, class-K gains, `CASES`) in `build_inital_condition.ipynb`. Sampling time (`0.05 s`), terminal time (`600 s`), and turn-rate limit (`0.35 rad/s`) are set inside `run_multi_agent_simulation()` in each `src/*.ipynb`.

## Notes

- `ModuleNotFoundError: cvxpy` — legacy import in some `src/*.ipynb`; unused since all QPs use DAQP. Delete the line or `pip install cvxpy`.
- `RuntimeError: CASE_ID env var must be set` — `src/*.ipynb` are not standalone; launch them through a runner.
