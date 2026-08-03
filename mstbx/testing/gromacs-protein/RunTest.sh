#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/home/groponp/miniconda3/envs/mstbx/bin/python}"
GMX="${GMX:-gmx}"

cd "$HERE"
mkdir -p input
if [[ ! -s input/protein_prepared.pdb ]]; then
  "$PYTHON" -m mstbx.cli pdbwriter \
    --fix-structure \
    --pdb-id 1UBQ \
    --select-chains A \
    --output input/protein_prepared.pdb
fi

"$PYTHON" -m mstbx.cli topogmx \
  --protein input/protein_prepared.pdb \
  --output-dir runs \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --pdb2gmx-selection $'1\n1\n' \
  --gmx "$GMX" \
  --overwrite

"$PYTHON" -m mstbx.cli md-inputs --engine gromacs \
  --env solution \
  --runs-dir runs \
  --temperature 310 \
  --nvt-time 2 \
  --npt-time 5 \
  --mdtime 1 \
  --xtc-frequency 50 \
  --name-group-index-1 Protein \
  --select-group-index-1 "protein" \
  --name-group-index-2 Water_and_ions \
  --select-group-index-2 "not protein" \
  --select-atoms-to-restraint "protein and backbone" \
  --gmx "$GMX"

echo "Prepared protein-only GROMACS test in: $PWD/runs"
