# 🧪 MSTBx v0.8.9-beta: Testing & Debugging Guide

Comprehensive guide to validate every module using provided examples.

---

## 1. Environment Building (`topopsfgen`)

### 1.1 Solution (Ubiquitin)
*   **Command**: `mstbx topopsfgen --env solution --psf testing/ubiquitin/step1.psf --pdb testing/ubiquitin/step1.pdb`
*   **Verification**: Check `01build/step3_pbcsetup.str`. Values `A`, `B`, and `C` must be equal (Cubic Box).

### 1.2 Membrane (Aquaporin)
*   **Command**: `mstbx topopsfgen --env membrane --psf testing/aqp/step4_lipid.psf --pdb testing/aqp/step4_lipid.pdb`
*   **Verification**: 
    - Check `01build/step3_pbcsetup.str`. `A` must equal `B` (Square XY).
    - `C` padding should be exactly 25.0 Å from protein/lipids.

### 1.3 SMD (Steered MD)
*   **Command**: `mstbx topopsfgen --env smd --psf testing/smd/step1.psf --pdb testing/smd/step1.pdb --atoms-pull "resid 76" --atoms-anchor "resid 1"`
*   **Verification**: Box must be extended in Z+.

---

## 2. Simulation Protocols (`inputs`)

### 2.1 Membrane Protocol (AQP)
*   **Command**: `mstbx md-inputs --engine namd --env membrane --psf 01build/mol.psf --pdb 01build/mol.pdb`
*   **Verification**: Folders `02nvt`, `03npt1`, `04npt2`, and `05md` must be created with specialized configs.

### 2.2 Protein-Ligand (BAAT)
*   **Command**: `mstbx md-inputs --engine namd --env solution --psf 01build/mol.psf --pdb 01build/mol.pdb --ligand-parm testing/baat/tyl.prm`
*   **Verification**: Check `02nvt/nvt.confg` for `parameters ../toppar/tyl.prm`.

---

## 3. Specialized Tools

### 3.1 PDBWriter
*   **Command**: `mstbx pdbwriter -i protein.pdb -o fixed.pdb --fix --ssbond`
*   **Logs**: Check `pdbwriter_report.log` for a list of repaired residues and disulfide bonds.

### 3.2 ResetPSF (1OAN Glycans)
*   **Command**: `mstbx resetpsf --psf testing/1oan-pH7-resetpsf/step1.psf --pdb testing/1oan-pH7-resetpsf/step1.pdb --output reset_1oan`
*   **Verification**: Resulting PSF must be in X-PLOR format.

---

## 🔍 Quality Assurance Checklist
1.  **Logging**: Terminal output must follow `[LEVEL HH:MM:SS DD/MM/YYYY]` format.
2.  **Versioning**: `mstbx --version` must return `0.8.9-beta`.
3.  **Runner**: `runner.sh` must be executable and contain `eq=on` flags.
