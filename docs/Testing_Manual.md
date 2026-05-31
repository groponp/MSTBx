# MSTBx Testing Manual & Debugging Guide

This manual provides a comprehensive set of commands to test and debug every module of MSTBx v0.7.0.

---

## 🛠️ Module 1: autopsfgen
**Goal:** Build systems (solvation, membrane, SMD) using PSFGen/VMD.

### 1.1 Solution System
```bash
mstbx autopsfgen --type sol \
                 --psf step1_pdbreader.psf \
                 --pdb step1_pdbreader.pdb \
                 --salt 0.150 \
                 --ofile system_sol
```
*   **Debug Tip:** Check `01build/psfgen.log` if VMD fails. Ensure `step3_pbcsetup.str` is created with box dimensions.

### 1.2 Membrane System
```bash
mstbx autopsfgen --type memb \
                 --psf step4_lipid.psf \
                 --pdb step4_lipid.pdb \
                 --salt 0.150 \
                 --ofile system_memb
```
*   **Debug Tip:** If the box size feels wrong, verify the `waters` selection in `PSFGenMemb.py`.

### 1.3 SMD System (Steered MD)
```bash
mstbx autopsfgen --type smd-sol \
                 --psf protein.psf \
                 --pdb protein.pdb \
                 --atoms-anchor "segid PROA and resid 1" \
                 --atoms-pull "segid PROA and resid 100" \
                 --extra-space 50
```

---

## ⚙️ Module 2: namdinputs
**Goal:** Generate NAMD configuration files.

### 2.1 Standard Solution Protocol
```bash
mstbx namdinputs --type sol \
                 --psf 01build/system_sol.psf \
                 --pdb 01build/system_sol.pdb \
                 --temperature 310 \
                 --mdtime 10
```

### 2.2 Membrane Protocol
```bash
mstbx namdinputs --type memb \
                 --psf 01build/system_memb.psf \
                 --pdb 01build/system_memb.pdb
```

### 2.3 SMD/Metadynamics
```bash
# SMD
mstbx namdinputs --type smd-sol ... (add --selpull, --selanchor flags)

# Metadynamics
mstbx namdinputs --type metad-sol ... (add --sel1, --sel2 flags)
```

---

## 🧪 Module 3: pdbwriter
**Goal:** Repair, clean, and protonate PDBs.

### 3.1 Full Repair (Internal Gaps + SS Bonds)
```bash
mstbx pdbwriter -i original.pdb -o fixed.pdb --fix --ssbond
```
*   **Debug Tip:** Read `pdbwriter_report.log`. It lists exactly which atoms were added and which gaps were ignored (terminals).

### 3.2 Protonation with Nomenclature
```bash
mstbx pdbwriter -i input.pdb -o protonated.pdb --ph 7.4 --ff-out CHARMM
```

---

## 🧬 Module 4: colabfold & mkdocking-cmplx

### 4.1 ColabFold Prediction
```bash
mstbx colabfold -i ./my_fastas -o ./results
```

### 4.2 Docking Complex
```bash
mstbx mkdocking-cmplx -p protein.pdb -d poses.pdbqt -o complex.pdb
```

---

## 🔍 Consistency Check List
1.  **Box Size:** After `autopsfgen`, check `01build/step3_pbcsetup.str`. The values `A`, `B`, `C` should match the max dimensions of the system + padding.
2.  **HMR:** If using `--hmr`, verify that `01build/system.hmr.psf` exists and masses of Hydrogens are ~3.0.
3.  **Apptainer:** If running `colabfold`, ensure `apptainer/` folder is created in your current directory.
