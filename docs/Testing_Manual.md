# 🧪 MSTBx v0.8.9: Testing & Debugging Guide

Comprehensive guide to validate every module in MSTBx.

---

## 1. Topology Building (`topopsfgen`)

### 1.1 Standard Solution
```bash
mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --padding 18 --salt 0.150
```

### 1.2 Membrane System
```bash
# Standard Insertion (25A default Z-padding)
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150
# Peripheral Placement (Positioned 10A from surface)
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10
```

### 1.3 SMD Prepared System
```bash
mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb \
                 --atoms-anchor "resid 1" --atoms-pull "resid 100" --extra-space 50
```

---

## 2. Simulation Protocols (`inputs`)

### 2.1 Standard MD
```bash
# Solution
mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
# Membrane (4-step protocol: NVT -> NPT1 -> NPT2 -> MD)
mstbx md-inputs --engine namd --env membrane --psf 01build/sys.psf --pdb 01build/sys.pdb
```

### 2.2 Steered MD (SMD)
```bash
# Default (Auto-calculates time based on velocity)
mstbx smd-inputs --engine namd --env solution \
                 --psf 01build/sys.psf --pdb 01build/sys.pdb \
                 --selpull "resid 100" --selanchor "resid 1" --target-center 50 --velocity 10.0
```

### 2.3 Metadynamics (MetaD)
```bash
mstbx metad-inputs --engine namd --env solution \
                   --psf 01build/sys.psf --pdb 01build/sys.pdb \
                   --sel1 "segid PROA" --sel2 "segid PROB" --target-distance 60
```

### 2.4 Advanced Colvars Control (Custom Folder)
Provide a directory containing `smd.in` (or `wtmetad.in`) and all required PDBs:
```bash
# Custom SMD
mstbx smd-inputs --engine namd --env solution --psf sys.psf --pdb sys.pdb \
                 --colvar-input ./my_custom_smd_setup/ --target-center 50

# Custom Metadynamics
mstbx metad-inputs --engine namd --env solution --psf sys.psf --pdb sys.pdb \
                   --colvar-input ./my_custom_metad_folder/
```
*   **Verification**: The script will validate that `atomsFile` dependencies exist in the folder and copy everything to `04md/`.

---

## 3. Specialized Tools

### 3.1 PDBWriter
```bash
mstbx pdbwriter -i in.pdb -o fixed.pdb --fix --ssbond --ph 7.4
```

### 3.2 ResetPSF (X-PLOR / Glycans)
```bash
mstbx resetpsf --psf glycosylated.psf --pdb coords.pdb --output reset_sys
```

---

## 🔍 Quality Assurance Checklist
1.  **Version Consistency**: Run `mstbx --version`, should be `0.8.9`.
2.  **Log Format**: Messages must be `[LEVEL HH:MM:SS DD/MM/YYYY]`.
3.  **Colvars Validation**: If using `--colvar-input`, check terminal for `[WARNING]` about missing file dependencies.
4.  **Runner Script**: Ensure `runner.sh` is created and executable with correct step activation.
