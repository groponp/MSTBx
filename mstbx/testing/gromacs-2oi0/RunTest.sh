#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PYTHON="${PYTHON:-/home/groponp/miniconda3/envs/mstbx/bin/python}"
GMX="${GMX:-gmx}"
SOURCE="${SOURCE:-$ROOT/staging/gromacs_prepare/gmxpy_snapshot/2OI0/cgenff_inputs_2oi0}"

"$PYTHON" -m mstbx.cli topogmx \
  --protein "$SOURCE/protein_prepared.pdb" \
  --ligand-mol2 "$SOURCE/ligand_for_cgenff.mol2" \
  --ligand-str "$SOURCE/ligand_for_cgenff.str" \
  --ligand-resname LIG \
  --output-dir runs \
  --replicas 3 \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --pdb2gmx-selection $'1\n1\n' \
  --gmx "$GMX" \
  --overwrite

"$PYTHON" -m mstbx.cli md-inputs --engine gromacs \
  --env solution \
  --runs-dir runs \
  --replicas 3 \
  --temperature 310 \
  --mdtime 100 \
  --xtc-frequency 50 \
  --name-group-index-1 Protein_ligand \
  --select-group-index-1 "not (resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN)" \
  --name-group-index-2 Water_and_ions \
  --select-group-index-2 "resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN" \
  --select-atoms-to-restraint "name N CA C O and not resname SOL TIP3 TIP3P WAT HOH NA CL K MG CA ZN or resname LIG and not name H*" \
  --gmx "$GMX"

echo "Prepared 2OI0 GROMACS test in: $PWD/runs"
