# ==============================================================================
# run_agent_win.py - Windows port of run_agent.sh (full feature parity).
#
# Implements everything run_desired.sh does:
#   1. Prints parameter / case info at startup.
#   2. Runs every (case x method) job in parallel, throttled by MAX_PARALLEL.
#   3. Pre-creates result/<case>/<tag>/ so notebooks can save (notebooks
#      themselves do NOT makedirs -> this is why results were not being saved).
#   4. Prints a per-case summary (feasibility + failure-reason breakdown) when
#      all methods of that case finish.
#   5. After everything, auto-runs summarize.ipynb -> logs/summary_<ts>.txt.
#   6. Live status line + per-job logs in logs/<case>_<tag>.log.
#
# Usage (from the fvo_cbf_desired project root, fvo env active):
#     conda activate fvo
#     python run_agent_win.py
# ==============================================================================
import os
import re
import sys
import json
import time
import pickle
import subprocess
from collections import Counter
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

MAX_PARALLEL = 12          # concurrent jobs (you have 16 cores)
THREADS_PER_PROC = "1"     # BLAS/OpenMP threads per job
RUN_SUMMARY = True         # auto-run summarize.ipynb at the end

# (notebook_basename, result-folder tag)
METHODS = [
    ("vo_cbf_part",      "vo"),
    ("fvo_cbf_part",     "fvo"),
    ("ho_cbf_part",      "ho"),
    ("ma_cbf_vo_part",   "ma"),
    ("nominal_flocking", "nominal"),
]

# METHODS = [
#     ("fvo_cbf_part",     "fvo"),
#     ("nominal_flocking", "nominal"),
# ]

PCT_RE  = re.compile(r"Progress:\s*t=[0-9.]+/[0-9.]+s\s*\(([0-9.]+)%\)")
CASE_RE = re.compile(r"test case\s*(\d+)", re.IGNORECASE)


def print_startup(cases):
    import numpy as np
    def L(name, fmt=str):
        try:
            return fmt(np.load(f"parameter/{name}.npy"))
        except Exception:
            return "N/A"
    print("========================================")
    print(" Agent-count sweep (Windows runner)")
    print("========================================")
    print(f"  test_case_num per case = {L('test_case_num', lambda v: int(v))}")
    print(f"  margin                 = {L('margin', lambda v: float(v))}")
    print(f"  class_k1               = {L('class_k1', lambda v: float(v))}")
    print(f"  class_k2               = {L('class_k2', lambda v: float(v))}")
    print(f"  V_CONST                = {L('V_CONST', lambda v: float(v))}")
    print(f"  qp_max_iter            = {L('qp_max_iter', lambda v: int(v))}")
    print(f"  qp_eps_abs             = {L('qp_eps_abs', lambda v: float(v))}")
    print(f"  qp_time_limit          = {L('qp_time_limit', lambda v: float(v))}")
    print(f"  cases ({len(cases)}):")
    for c in cases:
        print(f"    - {c['case_id']}: N={c['N_AGENTS']}, "
              f"desired={c['desired_distance']}, critical={c['critical_distance']}")
    print("========================================", flush=True)


def per_case_summary(cid):
    """Print feasibility + failure-reason breakdown for one finished case."""
    print(f"\n---- Case {cid} summary ----")
    for tag, m in [("VO", "vo"), ("FVO", "fvo"), ("HO", "ho"),
                   ("MA", "ma"), ("NOM", "nominal")]:
        p = os.path.join("result", cid, m, f"{m}_simulation_data.pkl")
        if not os.path.exists(p):
            print(f"   {tag:>4}: no pkl")
            continue
        try:
            with open(p, "rb") as fp:
                d = pickle.load(fp)
            fl = d.get(f"{m}_feasibility_list", [])
            rl = d.get(f"{m}_failure_reason_list", [])
            ok = sum(1 for x in fl if x)
            tot = len(fl)
            rate = f"{ok/tot*100:.1f}%" if tot else "N/A"
            c = Counter(r for r in rl if r is not None and r != "ok")
            parts = ", ".join(f"{k}={v}" for k, v in sorted(c.items())) if c else "all ok"
            print(f"   {tag:>4}: {ok:>3}/{tot:<3} ({rate:>6})  {parts}")
        except Exception as e:
            print(f"   {tag:>4}: err: {e}")
    sys.stdout.flush()


def run_summary():
    if not os.path.isfile("summarize.ipynb"):
        print(" [summary] summarize.ipynb not found; skipping.")
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join("logs", f"summary_{ts}.txt")
    env = os.environ.copy()
    env["SUMMARY_OUTPUT"] = summary_path
    driver = (
        "import json\n"
        "nb = json.load(open('summarize.ipynb', encoding='utf-8'))\n"
        "ns = {}\n"
        "for cell in nb['cells']:\n"
        "    if cell['cell_type'] != 'code':\n"
        "        continue\n"
        "    src = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']\n"
        "    exec(compile(src, 'summarize.ipynb', 'exec'), ns)\n"
    )
    print(f"\n [summary] running summarize.ipynb -> {summary_path}", flush=True)
    try:
        subprocess.run([sys.executable, "-c", driver], env=env, check=True)
        print(f" [summary] saved: {summary_path}", flush=True)
    except subprocess.CalledProcessError as e:
        print(f" [summary] FAILED (exit {e.returncode}). Open summarize.ipynb in Jupyter.",
              flush=True)


def main():
    if not os.path.isfile("cases.json"):
        print("[ERROR] cases.json not found. Run build_inital_condition.ipynb first.")
        sys.exit(1)

    with open("cases.json", encoding="utf-8") as f:
        cases = json.load(f)
    case_ids = [c["case_id"] for c in cases]

    os.makedirs("logs", exist_ok=True)
    print_startup(cases)

    # --- KEY FIX: pre-create result/<case>/<tag>/ so notebooks can save ---
    for cid in case_ids:
        for _, tag in METHODS:
            os.makedirs(os.path.join("result", cid, tag), exist_ok=True)

    jobs = [(cid, nb, tag) for cid in case_ids for nb, tag in METHODS]
    print(f" Total jobs: {len(jobs)}  |  MAX_PARALLEL={MAX_PARALLEL}  |  threads/job={THREADS_PER_PROC}",
          flush=True)

    base_env = os.environ.copy()
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        base_env[v] = THREADS_PER_PROC

    running = {}
    pending = list(jobs)
    finished = {}
    start_all = time.time()

    # track remaining methods per case, to print per-case summary on completion
    case_remaining = {cid: len(METHODS) for cid in case_ids}
    case_summarized = set()

    def jk(cid, tag):
        return f"{cid}/{tag}"

    def launch(cid, nb_name, tag):
        logpath = os.path.join("logs", f"{cid}_{tag}.log")
        logf = open(logpath, "w", encoding="utf-8")
        env = base_env.copy()
        env["CASE_ID"] = cid
        proc = subprocess.Popen(
            [sys.executable, "-u", "run_one_method.py", f"src/{nb_name}.ipynb", cid],
            stdout=logf, stderr=subprocess.STDOUT, env=env,
        )
        running[jk(cid, tag)] = dict(proc=proc, logf=logf, logpath=logpath, cid=cid, tag=tag)

    def read_progress(logpath):
        pct, case = 0, None
        try:
            with open(logpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    m = PCT_RE.search(line)
                    if m:
                        pct = float(m.group(1))
                    c = CASE_RE.search(line)
                    if c:
                        case = int(c.group(1))
        except FileNotFoundError:
            pass
        return pct, case

    while pending or running:
        while pending and len(running) < MAX_PARALLEL:
            cid, nb_name, tag = pending.pop(0)
            launch(cid, nb_name, tag)

        time.sleep(3)

        for key in list(running.keys()):
            info = running[key]
            ret = info["proc"].poll()
            if ret is not None:
                info["logf"].close()
                finished[key] = "DONE" if ret == 0 else f"EXIT{ret}"
                cid = info["cid"]
                del running[key]
                case_remaining[cid] -= 1
                if case_remaining[cid] == 0 and cid not in case_summarized:
                    case_summarized.add(cid)
                    per_case_summary(cid)

        wall = time.time() - start_all
        wm, ws = int(wall // 60), int(wall % 60)
        active = []
        for key, info in running.items():
            pct, case = read_progress(info["logpath"])
            lbl = f"{key}:{int(pct)}%"
            if case is not None:
                lbl += f"(c{case})"
            active.append(lbl)
        print(f"[{wm:02d}:{ws:02d}] done {len(finished)}/{len(jobs)} | running: "
              + (" ".join(active) if active else "(none)"), flush=True)

    total = time.time() - start_all
    tm, ts = int(total // 60), int(total % 60)
    print("\n==================================================================")
    print(f" All simulations complete! Total elapsed: {tm}m {ts}s")
    print("==================================================================")
    for cid in case_ids:
        parts = [f"{tag}:{finished.get(jk(cid, tag), '??')}" for _, tag in METHODS]
        print(f"  {cid}: " + " | ".join(parts))
    print(" Results: result/<case_id>/<method>/   |   Logs: logs/<case>_<method>.log")

    if RUN_SUMMARY:
        run_summary()
    else:
        print(" To regenerate the summary table, open summarize.ipynb in Jupyter.")
    print("==================================================================")


if __name__ == "__main__":
    main()
