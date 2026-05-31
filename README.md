# MSTBx (Development Version)

This README is for testing purposes during the refactor to v0.7.2.

## 🚀 Quick Setup

```bash
# 1. Update environment
conda env update -f mstbx.yml
conda activate mstbx

# 2. Install package in editable mode
pip install -e .
```

### 3. Enable Autocomplete (Recommended)
To enable TAB completion for `mstbx` commands, run:

**For Bash:**
```bash
echo 'eval "$(_MSTBX_COMPLETE=bash_source mstbx)"' >> ~/.bashrc
source ~/.bashrc
```

**For Zsh:**
```bash
echo 'eval "$(_MSTBX_COMPLETE=zsh_source mstbx)"' >> ~/.zshrc
source ~/.zshrc
```

## 🧪 Testing Modules

### 1. General Help (Lists all modules)
```bash
mstbx --help
```

### 2. pdbwriter (Repair & Cleaning)
```bash
mstbx pdbwriter -i your_protein.pdb -o fixed.pdb --fix --ssbond
```

### 3. autopsfgen (System Building)
```bash
mstbx autopsfgen --type sol --psf protein.psf --pdb protein.pdb --ofile test_sol
```

### 4. namdinputs (Configuration Generation)
```bash
mstbx namdinputs --type sol --psf 01build/test_sol.psf --pdb 01build/test_sol.pdb
```

## 🔄 How to Update
If you pull new changes or dependencies are updated:
```bash
pip install --upgrade -e .
```

## 📁 Repository Structure
*   `mstbx/`: Source code.
*   `docs/`: Multilingual Wiki.
*   `old.code/`: Legacy scripts and original examples.
