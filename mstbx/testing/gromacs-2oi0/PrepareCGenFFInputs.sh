#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python}"
OUTPUT="${OUTPUT:-$HERE/work/cgenff_inputs_2oi0}"

cd "$HERE"
"$PYTHON" -m mstbx.cli pdbwriter \
  --prepare-cgenff-inputs \
  --pdb-id 2OI0 \
  --select-chains A \
  --pdb-ligand-resname 283 \
  --pdb-ligand-chain A \
  --output "$OUTPUT" \
  --ligand-pH 7.4 \
  --overwrite

cat <<EOF

CGenFF Web step:
  1. Upload $OUTPUT/ligand_for_cgenff.mol2.
  2. Do not select "Include parameters that are already in CGenFF".
  3. Download the generated STR file as:
     $OUTPUT/ligand_for_cgenff.str
  4. Keep the CGenFF version compatible with the selected CHARMM36 force field.

After that manual step, run:
  INPUTS_DIR="$OUTPUT" ./RunTest.sh
EOF
