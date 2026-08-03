[← Back to tutorial index](index.md)

### 9. Docking Pose to a Protein-Ligand System

Every tutorial follows the same rule: explain the starting files, identify the
case in which the workflow applies, show commands in execution order, state
what each command creates, and finish with validation and failure cases. Use
the case-study guide for docking at
[`mstbx/testing/mkdocking/README.md`](../../mstbx/testing/mkdocking/README.md).

Use `mkdocking-cmplx` to combine a receptor with a docking pose. It accepts
either a PDBQT result or an already converted ligand PDB, and exactly one
ligand source is required:

```bash
mstbx mkdocking-cmplx \
  --protein receptor_prepared.pdb \
  --dock vina_out.pdbqt \
  --pH 7.4 \
  --output complex_pose1.pdb

mstbx mkdocking-cmplx \
  --protein receptor_prepared.pdb \
  --ligand-pdb ligand_pose.pdb \
  --pH 7.4 \
  --output complex_pose1.pdb
```

For PDBQT, `MODEL 1` is used and the pose is converted with Open Babel. The
ligand is normalized to residue `LIG` and chain `L`. The command writes a
combined PDB only; it does not create a PSF, topology, or ligand parameters.

Clean and validate the complex with PDBWriter using an MDAnalysis selection:

```bash
mstbx pdbwriter --input complex_pose1.pdb \
  --select-atoms "protein or resname LIG" \
  --ssbond --segid PROT,LIG \
  --output complex_prepared.pdb --overwrite
mstbx pdbwriter --mol complex_prepared.pdb --check-mol-format
```

For GROMACS, prepare the CGenFF inputs, upload the MOL2 manually to the CGenFF
web service, save the returned STR file, and then run `topogmx`:

```bash
mstbx pdbwriter --prepare-cgenff-inputs \
  --input complex_prepared.pdb --ligand LIG \
  --output cgenff_inputs --ligand-pH 7.4 --overwrite
printf '0\n0\n' | mstbx topogmx \
  --protein cgenff_inputs/protein_prepared.pdb \
  --ligand-mol2 cgenff_inputs/ligand_for_cgenff.mol2 \
  --ligand-str cgenff_inputs/ligand_for_cgenff.str \
  --ligand-resname LIG --forcefield-dir charmm36.ff \
  --box-distance 1.8 --pdb2gmx-ter --output-dir runs --overwrite
```

For NAMD, obtain a PSF with the same atom order as `complex_prepared.pdb` and
matching ligand CHARMM parameters, then use `topopsfgen` and `md-inputs`.
The complete docking workflow and common errors are documented in
[`mstbx/testing/mkdocking/README.md`](../../mstbx/testing/mkdocking/README.md).

---

[← Back to tutorial index](index.md) · See also: [GROMACS workflows](gromacs.md) · [NAMD workflows](namd.md) · [PDBWriter Structure Preparation](pdbwriter.md)
