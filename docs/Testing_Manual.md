# 🧪 MSTBx v0.8.9-beta: Testing & Debugging Guide

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
# Peripheral Placement
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10
```

### 1.3 SMD Prepared System
```bash
mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb \
                 --atoms-anchor "resid 1" --atoms-pull "resid 100" --extra-space 50
```

### 1.4 Workflow: Glycosylated Protein (Reset-then-Build)
Correct pipeline for handling virtual bonds in glycans:
1.  **Reset**: (First step to fix topology)
    `mstbx resetpsf --psf glyc.psf --pdb glyc.pdb --output reset_glyc`
2.  **Build**: (Use the reset files as inputs)
    `mstbx topopsfgen --env solution --psf reset_glyc.psf --pdb reset_glyc.pdb --ofile solvated_glyc`
3.  **Inputs**: (Final step)
    `mstbx md-inputs --engine namd --env solution --psf 01build/solvated_glyc.psf --pdb 01build/solvated_glyc.pdb`

---

## 2. Simulation Protocols (`inputs`)

### 2.1 Standard MD (Solution & Membrane)
```bash
# Solution
mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
# Membrane (4-step protocol: NVT -> NPT1 -> NPT2 -> MD)
mstbx md-inputs --engine namd --env membrane --psf 01build/sys.psf --pdb 01build/sys.pdb
```

### 2.2 Steered MD (SMD)
```bash
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

---

## 3. Specialized Tools

### 3.1 PDBWriter
```bash
mstbx pdbwriter -i original.pdb -o fixed.pdb --fix --ssbond --ph 7.4
```

### 3.2 ResetPSF
```bash
mstbx resetpsf --psf glyc.psf --pdb glyc.pdb --output reset_sys
```

---

## 🔍 Quality Assurance Checklist
1.  **Version**: `mstbx --version` (0.8.9-beta).
2.  **Log Format**: `[LEVEL HH:MM:SS DD/MM/YYYY]`.
3.  **Runner Script**: Ensure `runner.sh` is generated and executable.
4.  **TAB Completion**: Verify paths can be completed with TAB.
