#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PYTHON="${PYTHON:-/home/groponp/miniconda3/envs/mstbx/bin/python}"
GMX="${GMX:-gmx}"

mkdir -p input
curl -L "https://files.rcsb.org/download/1UBQ.pdb" -o input/1ubq.pdb
awk '/^(ATOM|TER)/ {print} END {print "END"}' input/1ubq.pdb > input/protein_prepared.pdb

"$PYTHON" -m mstbx.cli gmx-build \
  --protein input/protein_prepared.pdb \
  --output-dir runs \
  --replicas 3 \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --pdb2gmx-selection $'1\n1\n' \
  --gmx "$GMX" \
  --overwrite

"$PYTHON" -m mstbx.cli gmx-inputs \
  --runs-dir runs \
  --replicas 3 \
  --temperature 310 \
  --mdtime 1 \
  --xtc-frequency 50 \
  --name-group-index-1 Protein_ligand \
  --select-group-index-1 "not (resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN)" \
  --name-group-index-2 Water_and_ions \
  --select-group-index-2 "resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN" \
  --select-atoms-to-restraint "name N CA C O and not resname SOL TIP3 TIP3P WAT HOH NA CL K MG CA ZN or resname LIG and not name H*" \
  --gmx "$GMX"

echo "Prepared protein-only GROMACS test in: $PWD/runs"
