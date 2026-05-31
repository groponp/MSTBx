# MSTBx (Development Version)

This README is for testing purposes during the refactor to v0.7.0.

## 🚀 Quick Setup

```bash
# 1. Update environment
conda env update -f mstbx.yml
conda activate mstbx

# 2. Install package in editable mode
pip install -e .
```

## 🧪 Testing Commands

### 1. General Help
```bash
mstbx --help
```

### 2. PDBWriter (Internal Gap Fix & SS Bonds)
```bash
# Replace 'your_protein.pdb' with a real file to test
mstbx pdbwriter -i your_protein.pdb -o fixed.pdb --fix --ssbond
```

### 3. Solvation System
```bash
# Requires .psf and .pdb
mstbx autopsfgen --type sol --psf protein.psf --pdb protein.pdb --ofile test_sol
```

### 4. NAMD Protocol
```bash
# Run after autopsfgen
mstbx namdinputs --type sol --psf 01build/test_sol.psf --pdb 01build/test_sol.pdb
```

## 📁 Repository Structure

*   `mstbx/`: Source code of the package.
*   `docs/`: Multilingual Wiki and documentation.
*   `old.code/`: Original scripts and examples (for reference).
*   `pyproject.toml`: Installation metadata.
*   `mstbx.yml`: Conda environment definition.
