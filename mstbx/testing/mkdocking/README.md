# Docking Pose to a Protein-Ligand System

This tutorial starts with a receptor structure and a pose produced by a docking
program. It covers PDBQT and PDB poses, PDBWriter cleanup, and the boundary
between complex construction and engine-specific topology generation.

## Choose the matching case

Use the case that matches the files you have:

| Situation | Start here | Why |
| --- | --- | --- |
| Vina or another program produced a multi-model `.pdbqt` | [Case 2](#case-study-2-pdbqt-docking-pose) | `MODEL 1` is extracted and converted with Open Babel. |
| Docking produced a ligand `.pdb` | [Case 3](#case-study-3-existing-ligand-pdb) | The pose is already converted, so no PDBQT parsing is needed. |
| The receptor has missing heavy atoms or internal gaps | [Case 1](#case-study-1-receptor-preparation) | Repair before docking and avoid changing the docking receptor afterward. |
| The complex is ready and you need GROMACS | [Case 5](#case-study-5-gromacs-with-cgenff) | The MOL2/STR boundary is explicit and manual. |
| The complex is ready and you need NAMD | [Case 6](#case-study-6-namd-with-a-matching-psf) | A matching PSF and CHARMM parameters are required. |

## Contents

- [Case Study 1: Receptor Preparation](#case-study-1-receptor-preparation)
- [Case Study 2: PDBQT Docking Pose](#case-study-2-pdbqt-docking-pose)
- [Case Study 3: Existing Ligand PDB](#case-study-3-existing-ligand-pdb)
- [Case Study 4: PDBWriter Cleanup and Validation](#case-study-4-pdbwriter-cleanup-and-validation)
- [Case Study 5: GROMACS with CGenFF](#case-study-5-gromacs-with-cgenff)
- [Case Study 6: NAMD with a Matching PSF](#case-study-6-namd-with-a-matching-psf)
- [Validation Checklist](#validation-checklist)

## Case Study 1: Receptor Preparation

For a receptor downloaded from the PDB, use PDBWriter to select the chain and
apply only the structural operations required by the project:

```bash
mstbx pdbwriter --pdb-id 2OI0 \
  --select-chains A \
  --output receptor_raw.pdb \
  --overwrite

mstbx pdbwriter --input receptor_raw.pdb \
  --select-atoms "protein" \
  --ssbond \
  --output receptor_prepared.pdb \
  --overwrite
```

If missing atoms must be repaired, run the explicit structure-fixing workflow
before docking. Do not use `--fix-structure` when the intent is only atom
selection: PDBFixer may add atoms and hydrogens, which changes the input used by
the docking calculation.

## Case Study 2: PDBQT Docking Pose

`mkdocking-cmplx` uses `MODEL 1` from a multi-model PDBQT file. It converts the
pose with Open Babel, removes PDBQT hydrogens, assigns residue name `LIG` and
chain `L`, and writes one combined PDB.

```bash
mstbx mkdocking-cmplx \
  --protein receptor_prepared.pdb \
  --dock vina_out.pdbqt \
  --pH 7.4 \
  --output complex_pose1.pdb
```

The command requires exactly one ligand source. Passing both `--dock` and
`--ligand-pdb`, or neither option, is an error. This command creates a PDB
complex only; it does not create a PSF, a GROMACS topology, or force-field
parameters.

## Case Study 3: Existing Ligand PDB

Use this form when the docking program or a previous conversion already
produced a ligand PDB:

```bash
mstbx mkdocking-cmplx \
  --protein receptor_prepared.pdb \
  --ligand-pdb ligand_pose.pdb \
  --pH 7.4 \
  --output complex_pose1.pdb
```

The ligand is still normalized to `LIG` and chain `L` by the complex builder.
Inspect the result before generating topology files:

```bash
mstbx pdbwriter --mol complex_pose1.pdb --check-mol-format
```

## Case Study 4: PDBWriter Cleanup and Validation

Selections use MDAnalysis syntax. `chainID` is the PDB chain identifier; use
`protein` and residue names when they are more stable than chain labels:

```bash
mstbx pdbwriter \
  --input complex_pose1.pdb \
  --select-atoms "protein or resname LIG" \
  --ssbond \
  --segid PROT,LIG \
  --output complex_prepared.pdb \
  --overwrite

mstbx pdbwriter --mol complex_prepared.pdb --check-mol-format
```

`--select-atoms` does not invoke PDBFixer and does not add atoms. Keep the
ligand as `HETATM` and verify that the selected output still contains the
protein and `LIG` atoms. For a receptor that needs titratable-residue
protonation, use PDBWriter on the receptor before combining the pose and inspect
the resulting hydrogenation rather than applying hydrogenation twice:

```bash
mstbx pdbwriter --input receptor_raw.pdb \
  --pH 7.4 \
  --ff-out CHARMM \
  --output receptor_charmm_ph74.pdb \
  --overwrite
```

## Case Study 5: GROMACS with CGenFF

Generate the protein and ligand inputs required by the CGenFF web service:

```bash
mkdir -p cgenff_inputs
mstbx pdbwriter --prepare-cgenff-inputs \
  --input complex_prepared.pdb \
  --ligand LIG \
  --output cgenff_inputs \
  --ligand-pH 7.4 \
  --overwrite
```

Upload `cgenff_inputs/ligand_for_cgenff.mol2` to the CGenFF web service. Do not
select “Include parameters that are already in CGenFF”. Save the returned
`.str` file in `cgenff_inputs/`.

Generate the GROMACS system with `topogmx`. The terminal and residue choices
are sent to `pdb2gmx` through standard input; adjust the values for the actual
system:

```bash
printf '0\n0\n' | mstbx topogmx \
  --protein cgenff_inputs/protein_prepared.pdb \
  --ligand-mol2 cgenff_inputs/ligand_for_cgenff.mol2 \
  --ligand-str cgenff_inputs/ligand_for_cgenff.str \
  --ligand-resname LIG \
  --forcefield-dir charmm36.ff \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --output-dir runs \
  --overwrite
```

Create engine inputs with natural MDAnalysis selections:

```bash
mstbx md-inputs --engine gromacs \
  --runs-dir runs \
  --select-group-index-1 "protein or resname LIG" \
  --select-group-index-2 "not (protein or resname LIG)" \
  --select-atoms-to-restraint "protein and backbone or resname LIG and not name H*"
```

Before running, inspect `runs/01build/topol.top`, `runs/01build/ionized.gro`,
the generated restraint files, and the generated `run_all.sh`.

## Case Study 6: NAMD with a Matching PSF

`mkdocking-cmplx` intentionally stops at the combined PDB. For NAMD, generate
a PSF whose atom order exactly matches the final PDB and obtain the ligand
CHARMM parameter files from the corresponding parameter-generation workflow:

```bash
mstbx topopsfgen --env solution \
  --psf complex_with_ligand.psf \
  --pdb complex_prepared.pdb \
  --salt 0.150 \
  --padding 18.0 \
  --ofile complex_solvated

mstbx md-inputs --engine namd \
  --pdb complex_solvated.pdb \
  --psf complex_solvated.psf \
  --lparm ligand.prm
```

Do not reuse a PSF generated before changing chain selection, residue names,
protonation, or atom order. Validate the PDB/PSF pair before starting dynamics.

## Validation Checklist

- `mkdocking-cmplx` rejects missing or ambiguous ligand sources.
- A PDBQT without `MODEL 1` must be converted or exported as a single-pose
  file before using the command.
- A GROMACS build requires the `.str` returned by CGenFF and the matching MOL2.
- A NAMD build requires a matching PSF and ligand parameters; the docking
  command does not infer them.
- If coordinates are malformed, repair or rewrite the source structure before
  docking and verify it with `pdbwriter --check-mol-format`.
