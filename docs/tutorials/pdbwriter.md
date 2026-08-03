[← Back to tutorial index](index.md)

### 0. PDBWriter Structure Preparation
Use `pdbwriter` as the first structure-quality step before `topopsfgen` or `topogmx`. The normal practice is to repair missing heavy atoms and strictly internal residues, then let the selected simulation engine add hydrogens. Do not add hydrogens with PDBFixer before `pdb2gmx` unless that is explicitly required by a separate workflow.

1. **Inspect all options and defaults**:
   ```bash
   mstbx pdbwriter --help
   ```
   The input coordinate file is supplied with `--input`/`-i`; `--output`/`-o` is the output file or directory. Use `--pdb-id` instead of `--input` when the official RCSB record should be downloaded internally. With only `--pdb-id`, PDBWriter downloads `<pdb-id>.pdb` to the current directory; use `--output` to choose another path and `--overwrite` to replace it. `--select-chains` accepts comma-separated chain IDs and is applied during download as well.
2. **Download a PDB without processing it**:
   ```bash
   mstbx pdbwriter --pdb-id 1AKI
   mstbx pdbwriter --pdb-id 1AKI --output input/1aki.pdb --overwrite
   ```
   The first form only downloads the official RCSB PDB file and does not run PDBFixer or protonation.
3. **Repair a local structure**:
   ```bash
   mstbx pdbwriter \
     --input raw.pdb \
     --output prepared.pdb \
     --fix-structure \
     --select-chains A \
     --internal-only
   ```
   `--internal-only` is the safe default: terminal gaps are not rebuilt automatically. For an official structure with SEQRES, download and repair it directly:
   ```bash
   mstbx pdbwriter \
     --pdb-id 1UBQ \
     --output 1ubq_fixed.pdb \
     --fix-structure \
     --select-chains A
   ```
4. **Select a protein and ligand without fixing the structure**:
   ```bash
   mstbx pdbwriter \
     --input complex.pdb \
     --select-atoms "protein or resname X" \
     --output protein_ligand.pdb
   ```
   This uses MDAnalysis directly. For PDB chain identifiers, use the MDAnalysis keyword `chainID`, and use `name` for atom-name patterns:
   ```bash
   mstbx pdbwriter \
     --input complex.pdb \
     --select-atoms "chainID A B and not name H*" \
     --output heavy_atoms.pdb
   ```
   `--select-atoms` does not call PDBFixer, so selected HETATM records remain available. An empty or invalid MDAnalysis selection stops with an error.
   To assign CHARMM segment IDs, use one value for all segments or one comma-separated value per segment:
   ```bash
   mstbx pdbwriter \
     --input bc.pdb \
     --segid PROB,PROC \
     --output bc_charmm.pdb
   ```
5. **Repair while preserving ligands, waters, or ions**:
   ```bash
   mstbx pdbwriter \
     --pdb-id 2OI0 \
     --output 2oi0_fixed.pdb \
     --fix-structure \
     --fix-keep-hetatoms \
     --select-chains A
   ```
   Use `--fix-keep-hetatoms` before ligand extraction. Without it, PDBFixer removes HETATM records by default. Use `--fix-add-hydrogens` only when the downstream workflow requires PDBFixer-generated hydrogens:
   ```bash
   mstbx pdbwriter \
     --input raw.pdb \
     --output prepared_ph74.pdb \
     --fix-structure \
     --fix-add-hydrogens \
     --pH 7.4
   ```
6. **Request pH/force-field nomenclature and disulfide detection**:
   ```bash
   mstbx pdbwriter \
     --input prepared.pdb \
     --output annotated.pdb \
     --pH 7.4 \
     --ff-out CHARMM \
     --ssbond
   ```
   `--ff-out` accepts `CHARMM` or `AMBER`. With `CHARMM`, PDB2PQR runs with CHARMM input/output naming and applies PROPKA titration states. `--ssbond` detects close CYS SG pairs and writes SSBOND records. Review the generated report and the structure before simulation.
7. **Apply chain, residue, and segment edits**:
   ```bash
   mstbx pdbwriter \
     --input prepared.pdb \
     --output edited.pdb \
     --rename-chain A:B \
     --rename-chain C:D \
     --renumber 1 \
     --segid PROT
   ```
   `--rename-chain` may be repeated, `--renumber` sets the starting residue number, and `--segid` sets the segment identifier.
8. **Generate and validate an extended CHARMM CRD**:
   ```bash
   mstbx pdbwriter \
     --input step3_input.pdb \
     --psf step3_input.psf \
     --output step3_input.crd \
     --write-ext-crd

   mstbx pdbwriter \
     --mol step3_input.crd \
     --check-mol-format
   ```
   `--mol` is validation input only and must be combined with `--check-mol-format`. The same validator accepts PDB, PSF, CRD, and MOL2 files.
9. **Prepare CGenFF Web inputs**:
   ```bash
   mstbx pdbwriter \
     --prepare-cgenff-inputs \
     --pdb-id 2OI0 \
     --select-chains A \
     --pdb-ligand-resname 283 \
     --pdb-ligand-chain A \
     --output cgenff_inputs_2oi0 \
     --ligand-pH 7.4 \
     --overwrite
   ```
   For an external ligand PDB, replace the source ligand selectors with `--ligand ligand_pose.pdb`. `--ligand-pH` controls Open Babel MOL2 preparation and defaults to 7.4. Upload the generated MOL2 manually to CGenFF Web and save the returned STR separately.

After this tutorial, use `input/prepared.pdb` or the corresponding edited output as the `--protein` input for `topogmx`. If a local PDB has no SEQRES, prefer `--pdb-id` for reliable internal-gap detection.

---

[← Back to tutorial index](index.md) · Next: [NAMD workflows](namd.md) · [GROMACS workflows](gromacs.md)
