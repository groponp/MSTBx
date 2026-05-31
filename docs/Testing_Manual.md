# 🧪 MSTBx v0.8.6: Testing & Debugging Guide

Comprehensive guide to validate every module in MSTBx.

---

## 1. Topology Building (`topopsfgen`)

### 1.1 Standard Solution
```bash
mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --padding 18 --salt 0.150
```

### 1.2 Membrane System
```bash
# Standard Insertion
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150
# Peripheral Placement
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10
```

### 1.3 SMD Prepared System
```bash
mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb --atoms-anchor "resid 1" --atoms-pull "resid 100" --extra-space 60
```

---

## 2. Simulation Protocols (`inputs`)

### 2.1 Standard MD (Solution & Membrane)
```bash
# Solution
mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
# Membrane (4-step protocol)
mstbx md-inputs --engine namd --env membrane --psf 01build/sys.psf --pdb 01build/sys.pdb
```

### 2.2 Steered MD (SMD)
```bash
mstbx smd-inputs --engine namd --env solution \
                 --psf 01build/sys.psf --pdb 01build/sys.pdb \
                 --selpull "resid 100" --selanchor "resid 1" --target-center 50 --kforce 1.5
```

### 2.3 Metadynamics (MetaD)
```bash
mstbx metad-inputs --engine namd --env solution \
                   --psf 01build/sys.psf --pdb 01build/sys.pdb \
                   --sel1 "segid PROA" --sel2 "segid PROB" --target-distance 60
```

---

## 3. Specialized Tools

### 3.1 PDBWriter (Structure Repair)
```bash
mstbx pdbwriter -i original.pdb -o fixed.pdb --fix --ssbond --ph 7.4 --ff-out CHARMM
```
*   **Verification**: Inspect `pdbwriter_report.log`.

### 3.2 MKDocking-Cmplx (Complex Builder)
```bash
mstbx mkdocking-cmplx -p protein.pdb -d docking.pdbqt -o complex.pdb --ph 7.4
```

### 3.3 MD-Translate (Conversion)
```bash
mstbx md-translate --psf sys.psf --coor restart.coor --xsc restart.xsc --toppar-dir ./toppar --target gromacs
```

### 3.4 ResetPSF (X-PLOR)
```bash
mstbx resetpsf --psf step1.psf --pdb step1.pdb --output reset_sys
```

### 3.5 ColabFold (AI Prediction)
```bash
mstbx colabfold -i ./fastas -o ./results
```

---

## 🔍 Quality Assurance Checklist
1.  **Version Consistency**: Run `mstbx --version`, should be `0.8.6`.
2.  **Log Format**: Messages must be `[LEVEL HH:MM:SS DD/MM/YYYY]`.
3.  **Runner Script**: Ensure `runner.sh` is created and executable after any `inputs` command.
4.  **TAB Completion**: Verify TAB works for both subcommands and file paths.
