# GROMACS Protein-Only Tutorial

This tutorial prepares a protein-only GROMACS system with the CHARMM36 force field. It deliberately contains no ligand, CGenFF, ligand topology, or ligand restraint.

## 1. Install and verify the environment

```bash
conda activate mstbx
pip install -e ".[test]"
gmx --version
```

The default MSTBx force field is packaged with the project. A user-provided CHARMM36 directory can be passed to `topogmx` with `--forcefield-dir` when needed.

## 2. Obtain and prepare the protein

The validation example uses ubiquitin, PDB ID `1UBQ`, chain A. The script downloads the official RCSB structure and asks `pdbwriter` to repair missing atoms/residues conservatively before writing a protein-only PDB:

```bash
mkdir -p input
mstbx pdbwriter \
  --fix-structure \
  --pdb-id 1UBQ \
  --select-chains A \
  --output input/protein_prepared.pdb
```

`pdbwriter --fix-structure` keeps only internal missing-residue repair by default, does not add hydrogens unless requested, and removes heterogens. GROMACS `pdb2gmx` adds the force-field hydrogens in the next step.

If you already inspected a local PDB and it contains missing heavy atoms or internal residues, repair that file before `topogmx`:

```bash
mstbx pdbwriter \
  --input raw_protein.pdb \
  --fix-structure \
  --select-chains A \
  --output input/protein_prepared.pdb
```

For reliable internal-gap detection, prefer an official RCSB input with SEQRES, for example `--pdb-id 1UBQ`. Do not add hydrogens with `--fix-add-hydrogens` in this GROMACS workflow; let `pdb2gmx` create hydrogens using the selected force field. If the structure has only terminal gaps, review them biologically rather than automatically rebuilding them.

## 3. Build, solvate, and ionize the system

```bash
mstbx topogmx \
  --protein input/protein_prepared.pdb \
  --output-dir runs \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --pdb2gmx-selection $'0\n0\n' \
  --gmx gmx \
  --overwrite
```

The `--pdb2gmx-selection` text is consumed only when `--pdb2gmx-ter` asks for N-terminal and C-terminal choices. For a different protein, choose the terminal states appropriate to its biology. Omit both flags to use the force-field defaults non-interactively.

## 4. Generate protocols, natural index groups, and restraints

```bash
mstbx md-inputs --engine gromacs \
  --env solution \
  --runs-dir runs \
  --temperature 310 \
  --nvt-time 2 \
  --npt-time 5 \
  --mdtime 1 \
  --xtc-frequency 50 \
  --name-group-index-1 Protein_ligand \
  --select-group-index-1 "not (resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN)" \
  --name-group-index-2 Water_and_ions \
  --select-group-index-2 "resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN" \
  --select-atoms-to-restraint "name N CA C O and not resname SOL TIP3 TIP3P WAT HOH NA CL K MG CA ZN" \
  --gmx gmx
```

The selections are MDAnalysis selections evaluated against `runs/01build/ionized.gro`. The first group contains the solute, the second contains solvent and ions, and the default protein-only restraint selects backbone heavy atoms at 5 kcal mol-1 A-2 converted to GROMACS units. The generated layout is:

```text
runs/
  01build/      # topol.top, ionized.gro, index.ndx, em.mdp
  02nvt/        # nvt.mdp
  03npt/        # npt.mdp
  04md/         # md.mdp
  restraints/   # protein position restraints
  toppar/       # empty for protein-only systems
  run_all.sh
```

Defaults are 50,000 EM steps, 2 ns NVT, 5 ns NPT, 100 ns production, 2 fs timestep, and trajectory frames every 50 ps. This tutorial uses `--mdtime 1` to keep the validation short.

## 5. Inspect and run

The commands above are the complete tutorial and stop before `mdrun`. Inspect `runs/01build/topol.top`, `runs/01build/ionized.gro`, the restraint file, and the generated `runs/run_all.sh`. Run only after inspection:

```bash
cd runs
./run_all.sh
```

For independent replicas, first validate this complete system and then copy the entire `runs/` directory:

```bash
cp -a runs rep1
cp -a runs rep2
cp -a runs rep3
```

`RunTest.sh` is a repository validation helper; it is not required to reproduce the tutorial commands above.
