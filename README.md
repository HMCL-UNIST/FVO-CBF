# Finite-time Velocity Obstacle-based Control Barrier Function

Safety-critical control framework for inter-vehicle collision avoidance in fixed-wing UAV flocking, built on the finite-time velocity obstacle (FVO) principle.

## 🗺️ Overall Architecture

<p align="center">
  <img src="https://github.com/user-attachments/assets/eae29804-7bea-4874-af7c-587f5939dec3" width="100%" alt="Overall architecture of the proposed framework">
</p>

The ACS flocking control law (Section III.C) generates nominal inputs that pursue the flocking objectives but may induce collisions. The proposed FVO-CBF-based safety-critical controller (Section IV.C) minimally modifies these inputs to guarantee collision-free flocking under the strictly positive velocity and turn-rate constraints of fixed-wing UAVs.

## 🎥 Video Demonstration

The video will be uploaded to YouTube.

## 📝 Citation

Citation will be updated upon acceptance.

## 📂 Project Structure

| File | Description |
| --- | --- |
| `runtime_params.ipynb` | Writes control gains and QP settings to `parameter/*.npy` |
| `build_initial_condition.ipynb` | Generates case definitions and randomized initial conditions |
| `summarize.ipynb` | Aggregates simulation results into tables and figures |
| `run_agent_win.py` | Runs all case × method jobs, varying the number of UAVs |
| `run_desired_win.py` | Runs all case × method jobs, varying the desired relative distance |
| `run_critical_win.py` | Runs all case × method jobs, varying the minimum safety distance |

| Directory | Description |
| --- | --- |
| `fvo_cbf_agent/` | Sweep over the number of UAVs |
| `fvo_cbf_desired/` | Sweep over the desired relative distance |
| `fvo_cbf_critical/` | Sweep over the minimum safety distance |
| `parameter/` | Runtime parameters written by the notebooks |
| `initial_conditions/` | Per-case initial states used in the paper |
| `result/` | Simulation outputs (`.pkl`) |
| `logs/` | Per-job logs and summary text files |

## ⚙️ Environment Requirements

Tested on:

- Python: 3.11
- OS: Windows (runner scripts are suffixed `_win`)
- QP solver: [DAQP](https://github.com/darnstrom/daqp)

To replicate the environment:

```bash
conda create -n fvo python=3.11
conda activate fvo
pip install numpy scipy matplotlib daqp jupyter
git clone https://github.com/HMCL-UNIST/FVO-CBF.git
cd FVO-CBF/fvo_cbf_agent
```

## 🚀 How to Run

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

The initial conditions used in the paper are already committed under `initial_conditions/`. Run `build_initial_condition.ipynb` only to generate a fresh random set.

## 📊 Output

```
result/<case_id>/<method>/<method>_simulation_data.pkl
logs/<case_id>_<method>.log
logs/summary_<timestamp>.txt
```

Each pickle is a dict of per-trial lists: full state history, minimum and maximum inter-vehicle distance histories, CBF value histories, DAQP solve time, initial and final position/velocity standard deviations, the feasibility flag, and the failure reason and time.

## 🔧 Options

Top of `run_<group>_win.py`:

| Option | Description |
| --- | --- |
| `MAX_PARALLEL` | Concurrent jobs (default `12`; lower for fewer cores) |
| `THREADS_PER_PROC` | Keep at `"1"` to avoid CPU oversubscription |
| `METHODS` | Comment out entries to run a subset |
| `RUN_SUMMARY` | Set to `False` to skip the automatic summary |

Setup cell of `summarize.ipynb`:

| Option | Description |
| --- | --- |
| `CASE_FILTER` | e.g. `'case0_N5'` to summarize a single case instead of all |

`runtime_params.ipynb` writes `beta`, `lamda`, `k1`, `k2`, `qp_max_iter`, `qp_eps_abs`, `qp_time_limit`, and `fi_threshold`.

`build_initial_condition.ipynb` writes `STATE_DIM`, `V_CONST`, `class_k1`, `class_k2`, `k_vo`, `margin`, `test_case_num`, the per-case `parameter/<case_id>/` values, `initial_conditions/<case_id>/initial.npy`, and `cases.json`. Edit its `CASES` list to define a different sweep, then Run All.
