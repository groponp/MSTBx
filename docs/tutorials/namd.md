[← Back to tutorial index](index.md)

# NAMD Workflows

These tutorials build CHARMM-style PSF/PDB systems with `topopsfgen` and
generate NAMD protocols with `md-inputs --engine namd`, `smd-inputs`, or
`resetpsf` for specific cases. Run [PDBWriter Structure Preparation](pdbwriter.md)
first if the starting structure needs repair.

- [1. Ubiquitin in Solution](#1-ubiquitin-in-solution)
- [2. Protein-Ligand Complex (BAAT)](#2-protein-ligand-complex-baat)
- [3. Aquaporin Tetramer in POPC Membrane](#3-aquaporin-tetramer-in-popc-membrane)
- [4. Steered Molecular Dynamics (SMD) Pulling](#4-steered-molecular-dynamics-smd-pulling)
- [5. Glycosylated Protein Simulation (1OAN Dimer)](#5-glycosylated-protein-simulation-1oan-dimer)

---

### 1. Ubiquitin in Solution
A complete workflow starting from standard CHARMM-GUI PDBReader outputs to assemble and generate NAMD protocols for a protein in water.

1. **Workspace Setup**: Create a folder named `ubiquitin` and place `step1_pdbreader.pdb` and `step1_pdbreader.psf` inside.
2. **System Assembly**: Solvate the protein and add 0.150 M NaCl salt with an 18 Å padding:
   ```bash
   mstbx topopsfgen --env solution \
                    --psf step1_pdbreader.psf \
                    --pdb step1_pdbreader.pdb \
                    --salt 0.150 \
                    --padding 18.0 \
                    --ofile ubq
   ```
3. **Protocol Generation**: Generate standard NAMD simulation configuration files for 100 ns at 310 K:
   ```bash
   mstbx md-inputs --engine namd \
                   --env solution \
                   --psf 01build/ubq.psf \
                   --pdb 01build/ubq.pdb \
                   --temperature 310 \
                   --mdtime 100
   ```

---

### 2. Protein-Ligand Complex (BAAT)
Configure molecular dynamics for a protein bound to a small molecule ligand, incorporating external parameter files.

1. **Workspace Setup**: Create a folder named `baat` and gather complex files `step1_pdbreader.pdb`, `step1_pdbreader.psf`, and the ligand parameter stream/parameter file `tyl.prm`.
2. **System Assembly**: Solvate and ionize the complex system:
   ```bash
   mstbx topopsfgen --env solution \
                    --psf step1_pdbreader.psf \
                    --pdb step1_pdbreader.pdb \
                    --salt 0.150 \
                    --ofile baat
   ```
3. **Protocol Generation**: Generate NAMD configurations, specifying the path to the ligand parameters (`--lparm`):
   ```bash
   mstbx md-inputs --engine namd \
                   --env solution \
                   --psf 01build/baat.psf \
                   --pdb 01build/baat.pdb \
                   --lparm tyl.prm \
                   --temperature 310 \
                   --mdtime 100
   ```

---

### 3. Aquaporin Tetramer in POPC Membrane
Build and simulate a large membrane protein system using CHARMM-GUI Membrane Builder inputs.

1. **Workspace Setup**: Create a folder named `aqp` and extract your membrane builder coordinates/topology (`step4_lipid.psf` and `step4_lipid.pdb`).
2. **System Assembly**: Assemble the system with lipids and correct water/ion buffers:
   ```bash
   mstbx topopsfgen --env membrane \
                    --psf step4_lipid.psf \
                    --pdb step4_lipid.pdb \
                    --salt 0.150 \
                    --ofile aqp
   ```
3. **Protocol Generation**: Generate membrane-specific NAMD equilibration and production inputs:
   ```bash
   mstbx md-inputs --engine namd \
                   --env membrane \
                   --psf 01build/aqp.psf \
                   --pdb 01build/aqp.pdb \
                   --temperature 310 \
                   --mdtime 100
   ```

---

### 4. Steered Molecular Dynamics (SMD) Pulling
Assemble and configure pulling simulations to pull a ligand out of a binding pocket along the Z axis.

1. **System Assembly**: Solvate the system while adding extra space along the pulling direction (Z axis):
   ```bash
   mstbx topopsfgen --env smd \
                    --psf complex.psf \
                    --pdb complex.pdb \
                    --atoms-pull "resname LIG" \
                    --atoms-anchor "protein and backbone" \
                    --extra-space 50 \
                    --ofile smd_sys
   ```
2. **Protocol Generation**: Configure the pulling velocity (e.g. 5 Å/ns) and anchors:
   ```bash
   mstbx smd-inputs --psf 01build/smd_sys.psf \
                    --pdb 01build/smd_sys.pdb \
                    --selpull "resname LIG" \
                    --selanchor "protein and backbone" \
                    --target-center 50.0 \
                    --velocity 5.0
   ```

---

### 5. Glycosylated Protein Simulation (1OAN Dimer)
A robust workflow to handle glycosylated systems by converting topology/coordinates first before system assembly.

1. **PSF Reset**: Convert the raw initial structures (e.g. `step1_pdbreader` from CHARMM-GUI) to X-PLOR format to support glycan structures:
   ```bash
   mstbx resetpsf --psf step1_pdbreader.psf \
                  --pdb step1_pdbreader.pdb \
                  --output reset
   ```
2. **System Assembly**: Solvate and ionize the reset structures using `topopsfgen`:
   ```bash
   mstbx topopsfgen --env solution \
                    --psf reset.psf \
                    --pdb reset.pdb \
                    --salt 0.150 \
                    --ofile mol
   ```
3. **Protocol Generation**: Generate the simulation configuration files for the solvated system:
   ```bash
   mstbx md-inputs --engine namd \
                   --env solution \
                   --psf 01build/mol.psf \
                   --pdb 01build/mol.pdb
   ```

---

[← Back to tutorial index](index.md) · See also: [Scientific Background](../SCIENTIFIC_BACKGROUND.md) · [Module Reference](../REFERENCE.md)
