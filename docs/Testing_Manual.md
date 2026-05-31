# 🧪 MSTBx v0.8.5: Testing & Debugging Guide

Use this guide to validate every module of the new architecture.

---

## 1. Topology Building (`topopsfgen`)

### 1.1 Solution
```bash
mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --padding 18 --salt 0.150
```
*   **Verification**: Check `01build/step3_pbcsetup.str`. Box dimensions should be ~ protein size + 36Å.

### 1.2 Membrane (Standard - Protein Inside)
```bash
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150
```
*   **Verification**: Default Z-padding is **25Å** per side. Check that the XY box is a perfect square based on max(X,Y).

### 1.3 Membrane (Peripheral - Protein Outside)
```bash
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10 --salt 0.150
```
*   **Verification**: The protein should be positioned 10Å above the membrane surface before solvation.

### 1.4 SMD
```bash
mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb --atoms-anchor "resid 1" --atoms-pull "resid 100" --extra-space 60
```

---

## 2. Simulation Protocols (`inputs`)

### 2.1 Standard MD
```bash
mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
```
*   **Verification**: `--dcdfreq` is in **ps**. 10.0 ps = 5000 steps (at 2fs).

### 2.2 Automated Execution (`runner.sh`)
After running any `inputs` command, check your folder for `runner.sh`.
```bash
chmod +x runner.sh
./runner.sh
```
*   **Debugging**: If NAMD fails, the script will stop immediately. Check `nvt.log` or `md.log`.

---

## 3. Specialized Tools

### 3.1 PDBWriter
```bash
mstbx pdbwriter -i in.pdb -o fixed.pdb --fix --ssbond --ph 7.0
```
*   **Verification**: Check `pdbwriter_report.log` for a list of repaired residues and detected S-S bonds.

### 3.2 ResetPSF (X-PLOR)
```bash
mstbx resetpsf --psf glycosylated.psf --pdb coords.pdb --output reset_sys
```

### 3.3 Translation
```bash
mstbx md-translate --psf sys.psf --coor res.coor --xsc res.xsc --toppar-dir ./toppar
```

---

## 🔍 Consistency Checklist
1.  **Version**: `mstbx --version` should be `0.8.5`.
2.  **Logs**: Output should be formatted as `[LEVEL HH:MM:SS DD/MM/YYYY]`.
3.  **TAB Completion**: Type `mstbx topop[TAB]` to test command completion.
