# 🧪 MSTBx v0.8.6: Testing & Debugging Guide

Use this guide to validate every module of the new architecture.

---

## 1. Topology Building (`topopsfgen`)

### 1.1 Solution
```bash
mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --padding 18 --salt 0.150
```

### 1.2 Membrane (Standard - Protein Inside)
```bash
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150
```
*   **Verification**: Default Z-padding is **25Å** per side. XY box is a perfect square.

### 1.3 Membrane (Peripheral - Protein Outside)
```bash
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10 --salt 0.150
```

---

## 2. Simulation Protocols (`inputs`)

### 2.1 Standard MD (Solution)
```bash
mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
```

### 2.2 Standard MD (Membrane)
```bash
mstbx md-inputs --engine namd --env membrane --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
```
*   **Verification**: Check if `02nvt`, `03npt1`, `04npt2`, and `05md` folders are created.
*   **Check**: Ensure `step6.1`, `step6.2` style equilibration logic is correctly mapped to NVT, NPT1, and NPT2.

### 2.3 Automated Execution (`runner.sh`)
```bash
chmod +x runner.sh
./runner.sh
```

---

## 3. Specialized Tools

### 3.1 PDBWriter
```bash
mstbx pdbwriter -i in.pdb -o fixed.pdb --fix --ssbond --ph 7.0
```

### 3.2 ResetPSF (X-PLOR)
```bash
mstbx resetpsf --psf glycosylated.psf --pdb coords.pdb --output reset_sys
```

---

## 🔍 Consistency Checklist
1.  **Version**: `mstbx --version` should be `0.8.6`.
2.  **Logs**: Format should be `[LEVEL HH:MM:SS DD/MM/YYYY]`.
3.  **TAB Completion**: Test with `mstbx topop[TAB]`.
