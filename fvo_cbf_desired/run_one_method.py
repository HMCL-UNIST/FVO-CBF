#!/usr/bin/env python3
"""
run_one_method.py  <notebook_path> <case_id>

Executes the given notebook's code cells (up to and including the last
pickle.dump cell) in a fresh Python namespace, with CASE_ID env var set.
"""
import sys
import os
import json


def main():
    if len(sys.argv) != 3:
        print("usage: run_one_method.py <notebook_path> <case_id>", file=sys.stderr)
        sys.exit(2)

    notebook_path = sys.argv[1]
    os.environ['CASE_ID'] = sys.argv[2]

    import matplotlib
    matplotlib.use('Agg')

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']

    last_pkl = -1
    for i, cell in enumerate(cells):
        src = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
        if 'pickle.dump' in src:
            last_pkl = i

    code_blocks = []
    for i, cell in enumerate(cells):
        if last_pkl >= 0 and i > last_pkl:
            break
        if cell['cell_type'] != 'code':
            continue
        src = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
        src = src.strip()
        if not src:
            continue
        lines = [l for l in src.split('\n') if not l.strip().startswith('%')]
        src = '\n'.join(lines).strip()
        if src:
            code_blocks.append(src)

    ns = {}
    for bi, code in enumerate(code_blocks):
        exec(compile(code, f"{notebook_path}:cell{bi}", 'exec'), ns)
        sys.stdout.flush()


if __name__ == '__main__':
    main()
