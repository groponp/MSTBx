# MSTBx (Molecular Simulation ToolBox) v0.8.9-beta

**MSTBx** is a modular Python ecosystem designed to simplify the preparation, configuration, and translation of Molecular Dynamics (MD) simulations. Optimized for large-scale systems and high-performance computing (HPC) workflows.

---

## 🚀 Quick Installation

```bash
# 1. Clone repository
git clone https://github.com/groponp/MSTBx.git
cd MSTBx/

# 2. Setup Conda environment
conda env update -f mstbx.yml
conda activate mstbx

# 3. Install in editable mode
pip install -e .
```

### Enable TAB Autocompletion
```bash
# Bash: echo 'eval "$(_MSTBX_COMPLETE=bash_source mstbx)"' >> ~/.bashrc
# Zsh: echo 'eval "$(_MSTBX_COMPLETE=zsh_source mstbx)"' >> ~/.zshrc
```

---

## 🛠️ Main Modules

### 1. Topology Building (`topopsfgen`)
*   `mstbx topopsfgen --env solution`: Cubic water box (18Å padding).
*   `mstbx topopsfgen --env membrane`: Strict XY square box (25Å Z-padding).
*   `mstbx topopsfgen --env smd`: Oriented system with Z+ tunnel extension.

### 2. Simulation Protocols (`inputs`)
*   `mstbx md-inputs`: Standard equilibration and production.
*   `mstbx smd-inputs`: Velocity-based pulling protocols.
*   `mstbx metad-inputs`: Well-Tempered Metadynamics.

### 3. Advanced Tools
*   `pdbwriter`: PDB fixing and S-S bond detection.
*   `resetpsf`: Conversion to X-PLOR format (required for glycans).
*   `mkdocking-cmplx`: Protein-ligand complex assembly.
*   `md-translate`: Coordinate translation (NAMD to GROMACS).
*   `colabfold`: AI-based structure prediction.

---

## 📖 Real-World Examples

### A. Standard Protein (Ubiquitin)
```bash
# 1. Build Cubic Box (18A padding)
mstbx topopsfgen --env solution --psf ubq.psf --pdb ubq.pdb --salt 0.150

# 2. Generate NAMD files
mstbx md-inputs --engine namd --env solution --psf 01build/mol.psf --pdb 01build/mol.pdb

# 3. Run
./runner.sh
```

### B. Membrane Protein (Aquaporin)
```bash
# 1. Build Square XY Box (25A Z-padding)
mstbx topopsfgen --env membrane --psf aqp.psf --pdb aqp.pdb --salt 0.150

# 2. Generate 4-step Membrane Protocol
mstbx md-inputs --engine namd --env membrane --psf 01build/mol.psf --pdb 01build/mol.pdb
```

### C. Protein-Ligand (BAAT)
```bash
# 1. Assemble Complex
mstbx mkdocking-cmplx -p receptor.pdb -d ligand_pose.pdbqt -o complex.pdb

# 2. Build Solution
mstbx topopsfgen --env solution --psf complex.psf --pdb complex.pdb --salt 0.150

# 3. Inputs with Ligand Parameters (.str/.prm)
mstbx md-inputs --engine namd --env solution --psf 01build/mol.psf --pdb 01build/mol.pdb --ligand-parm ligand.str
```

### D. Glycosylated Protein (1OAN)
```bash
# 1. Reset Topology (X-PLOR format)
mstbx resetpsf --psf 1oan.psf --pdb 1oan.pdb --output reset_1oan

# 2. Build from Reset files
mstbx topopsfgen --env solution --psf reset_1oan.psf --pdb reset_1oan.pdb --salt 0.150
```

---

## 📊 Industrial Logging
Standardized format for tracking: `[LEVEL HH:MM:SS DD/MM/YYYY] Message`

## 📚 Documentation
*   🇺🇸 [English Wiki](docs/wiki/en/Home.md) | 🇪🇸 [Wiki en Español](docs/wiki/es/Home.md) | 🇧🇷 [Wiki em Português](docs/wiki/pt/Home.md)
*   🔬 [**Full Testing Manual**](docs/Testing_Manual.md)
