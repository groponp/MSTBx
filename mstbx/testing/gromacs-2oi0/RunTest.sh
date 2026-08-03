#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/home/groponp/miniconda3/envs/mstbx/bin/python}"
GMX="${GMX:-gmx}"
INPUTS_DIR="${INPUTS_DIR:-$ROOT/staging/gromacs_prepare/gmxpy_snapshot/2OI0/cgenff_inputs_2oi0}"
STR_FILE="$INPUTS_DIR/ligand_for_cgenff.str"

cd "$HERE"
if [[ ! -s "$STR_FILE" ]]; then
  echo "Missing $STR_FILE" >&2
  echo "Run ./PrepareCGenFFInputs.sh, upload the MOL2 to CGenFF Web, and save the downloaded STR there." >&2
  exit 1
fi

"$PYTHON" -m mstbx.cli topogmx \
  --protein "$INPUTS_DIR/protein_prepared.pdb" \
  --ligand-mol2 "$INPUTS_DIR/ligand_for_cgenff.mol2" \
  --ligand-str "$STR_FILE" \
  --ligand-resname LIG \
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
  --mdtime 100 \
  --xtc-frequency 50 \
  --name-group-index-1 Protein_ligand \
  --select-group-index-1 "not (resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN)" \
  --name-group-index-2 Water_and_ions \
  --select-group-index-2 "resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN" \
  --select-atoms-to-restraint "name N CA C O and not resname SOL TIP3 TIP3P WAT HOH NA CL K MG CA ZN or resname LIG and not name H*" \
  --gmx "$GMX"

echo "Prepared 2OI0 GROMACS test in: $PWD/runs"
