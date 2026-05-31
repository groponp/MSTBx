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
# Peripheral Placement (Positioned 10A from surface)
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10
```

### 1.3 SMD Prepared System
```bash
mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb \
                 --atoms-anchor "resid 1" --atoms-pull "resid 100" --extra-space 50
```

### 1.4 Workflow: Glycosylated Protein
Special handling for glycans and virtual bonds:
1.  **Build**: `mstbx topopsfgen --env solution --psf glyc.psf --pdb glyc.pdb --ofile temp_sys`
2.  **Reset**: `mstbx resetpsf --psf 01build/temp_sys.psf --pdb 01build/temp_sys.pdb --output fixed_glyc`
3.  **Inputs**: `mstbx md-inputs --engine namd --env solution --psf fixed_glyc.psf --pdb fixed_glyc.pdb`

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

### 3.1 PDBWriter (Structure Repair)
```bash
mstbx pdbwriter -i original.pdb -o fixed.pdb --fix --ssbond --ph 7.4
```

### 3.2 MKDocking-Cmplx (Complex Builder)
```bash
mstbx mkdocking-cmplx -p protein.pdb -d docking.pdbqt -o complex.pdb
```

### 3.3 ColabFold (AI Prediction)
```bash
mstbx colabfold -i ./fastas -o ./results
```

---

## 🔍 Quality Assurance Checklist
1.  **Version**: `mstbx --version` (0.8.9-beta).
2.  **Log Format**: `[LEVEL HH:MM:SS DD/MM/YYYY]`.
3.  **Runner Script**: Check `runner.sh` after generation.
4.  **TAB Completion**: Verify TAB works for commands and paths.
