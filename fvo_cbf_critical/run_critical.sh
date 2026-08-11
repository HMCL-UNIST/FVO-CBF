#!/bin/bash
# ==============================================================================
# run_critical.sh - Group B: Critical-distance sweep (N=10, desired=80)
# Parallelized: 5 methods run concurrently per case; cases are sequential.
# Terminal shows key progress + per-case summary + final reason-breakdown table.
# Full output goes to logs/<case>_<method>.log.
# ==============================================================================
cd "$(dirname "$0")"

if [ ! -f "cases.json" ]; then
    echo "[ERROR] cases.json not found. Run build_inital_condition.ipynb first."
    exit 1
fi

mkdir -p logs

echo ""
echo "========================================"
echo " Group B: Critical-distance sweep (N=15, desired=80)"
echo "========================================"
python3 -c "
import json, numpy as np
with open('cases.json') as f:
    cases = json.load(f)
print(f'  test_case_num per case = {int(np.load(\"parameter/test_case_num.npy\"))}')
print(f'  margin                 = {float(np.load(\"parameter/margin.npy\")):.1e}')
print(f'  class_k1               = {float(np.load(\"parameter/class_k1.npy\")):.4f}')
print(f'  class_k2               = {float(np.load(\"parameter/class_k2.npy\")):.4f}')
print(f'  V_CONST                = {float(np.load(\"parameter/V_CONST.npy\")):.1f}')
print(f'  qp_max_iter            = {int(np.load(\"parameter/qp_max_iter.npy\"))}')
print(f'  qp_eps_abs             = {float(np.load(\"parameter/qp_eps_abs.npy\")):.0e}')
print(f'  qp_time_limit          = {float(np.load(\"parameter/qp_time_limit.npy\"))} s')
print(f'  cases ({len(cases)}):')
for c in cases:
    print(f'    - {c[\"case_id\"]}: N={c[\"N_AGENTS\"]}, desired={c[\"desired_distance\"]}, critical={c[\"critical_distance\"]}')
"

declare -A TAGS=(
    [vo_cbf_part]=VO
    [fvo_cbf_part]=FVO
    [ho_cbf_part]=HO
    [ma_cbf_vo_part]=MA
    [nominal_flocking]=NOM
)

METHODS=(vo_cbf_part fvo_cbf_part ho_cbf_part ma_cbf_vo_part nominal_flocking)
TOTAL_CASES=$(python3 -c "import json; print(len(json.load(open('cases.json'))))")

FILTER='Running simulation for test case|Feasible cases|Feasibility Rate'

START_ALL=$(date +%s)

# ----- Throttled parallel dispatch (MAX_PARALLEL concurrent tasks) -----
MAX_PARALLEL=10

declare -A PID_CASE
declare -A CASE_REMAINING
FAIL_COUNT=0
CASES_DONE=0
RUNNING=0

# Handle one finished process: update counters, print per-case summary when case completes
_handle_one_finished() {
    local fpid=""
    if wait -n -p fpid; then :; else FAIL_COUNT=$((FAIL_COUNT + 1)); fi
    [ -z "$fpid" ] && return
    local cid="${PID_CASE[$fpid]}"
    unset 'PID_CASE[$fpid]'
    RUNNING=$((RUNNING - 1))
    CASE_REMAINING[$cid]=$((CASE_REMAINING[$cid] - 1))
    if [ "${CASE_REMAINING[$cid]}" -eq 0 ]; then
        CASES_DONE=$((CASES_DONE + 1))
        echo ""
        echo "---- Case $cid summary ($CASES_DONE/$TOTAL_CASES) ----"
        CASE_ID="$cid" python3 <<'PYCASE'
import os, pickle
from collections import Counter
cid = os.environ['CASE_ID']
METHODS = [('VO','vo'),('FVO','fvo'),('HO','ho'),('MA','ma'),('NOM','nominal')]
for tag, m in METHODS:
    p = f'result/{cid}/{m}/{m}_simulation_data.pkl'
    if not os.path.exists(p):
        print(f'   {tag:>4}: no pkl')
        continue
    try:
        with open(p,'rb') as fp: d = pickle.load(fp)
        fl = d.get(f'{m}_feasibility_list', [])
        rl = d.get(f'{m}_failure_reason_list', [])
        ok = sum(1 for x in fl if x); tot = len(fl)
        rate = f'{ok/tot*100:.1f}%' if tot else 'N/A'
        c = Counter(r for r in rl if r is not None and r != 'ok')
        parts = ', '.join(f'{k}={v}' for k,v in sorted(c.items())) if c else 'all ok'
        print(f'   {tag:>4}: {ok:>3}/{tot:<3} ({rate:>6})  {parts}')
    except Exception as e:
        print(f'   {tag:>4}: err: {e}')
PYCASE
    fi
}

echo ""
echo "================================================"
echo " Throttled parallel: MAX_PARALLEL=$MAX_PARALLEL per SH"
echo " Total tasks: $TOTAL_CASES cases × ${#METHODS[@]} methods = $((TOTAL_CASES * ${#METHODS[@]}))"
echo "================================================"

for CI in $(seq $((TOTAL_CASES - 1)) -1 0); do
    CASE_ID=$(python3 -c "import json; print(json.load(open('cases.json'))[$CI]['case_id'])")
    CASE_N=$(python3 -c "import json; print(json.load(open('cases.json'))[$CI]['N_AGENTS'])")
    CASE_D=$(python3 -c "import json; print(json.load(open('cases.json'))[$CI]['desired_distance'])")
    CASE_C=$(python3 -c "import json; print(json.load(open('cases.json'))[$CI]['critical_distance'])")

    echo "## Dispatching $CASE_ID (N=$CASE_N, d=$CASE_D, c=$CASE_C)"
    CASE_REMAINING[$CASE_ID]=${#METHODS[@]}

    for M in "${METHODS[@]}"; do
        # Throttle: wait if at MAX_PARALLEL
        while [ $RUNNING -ge $MAX_PARALLEL ]; do
            _handle_one_finished
        done
        # Dispatch
        TAG="${TAGS[$M]}"
        PREFIX="[${CASE_ID}/${TAG}] "
        (
            OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
                python3 -u run_one_method.py "src/${M}.ipynb" "$CASE_ID" 2>&1 \
                | stdbuf -oL -eL sed "s|^|${PREFIX}|" \
                | grep -E --line-buffered "${FILTER}"
        ) &
        PID_CASE[$!]="$CASE_ID"
        RUNNING=$((RUNNING + 1))
    done
done

# Drain remaining
while [ $RUNNING -gt 0 ]; do
    _handle_one_finished
done

TOTAL_ELAPSED=$(($(date +%s) - START_ALL))

# ----- Final summary: feasibility table + full reason-breakdown table -----
echo ""
echo "=================================================================="
echo " All simulations complete! Total elapsed: $((TOTAL_ELAPSED / 60))m $((TOTAL_ELAPSED % 60))s"
echo "=================================================================="

SUMMARY_PATH="logs/summary_$(date +%Y%m%d_%H%M%S).txt"
SUMMARY_OUTPUT="$SUMMARY_PATH" python3 -c "
import json
nb = json.load(open('summarize.ipynb'))
ns = {}
for cell in nb['cells']:
    if cell['cell_type'] != 'code': continue
    src = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
    exec(src, ns)
"

echo " Results:   result/<case_id>/<method>/"
echo " Summary:   $SUMMARY_PATH   (regen anytime: open summarize.ipynb in Jupyter)"
echo "=================================================================="
