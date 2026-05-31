# MSTBx (Development Version)

This README is for testing purposes during the refactor to v0.7.6.

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

### 2. Standard MD Inputs
```bash
# Standard solution
mstbx md-inputs --engine namd --type sol --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 5.0
```

### 3. SMD Inputs
```bash
mstbx smd-inputs --engine namd --psf 01build/sys.psf --pdb 01build/sys.pdb \
                 --selpull "resid 100" --selanchor "resid 1" --target-center 50
```

### 4. Metadynamics Inputs
```bash
mstbx metad-inputs --engine namd --psf 01build/sys.psf --pdb 01build/sys.pdb \
                   --sel1 "segid PROA" --sel2 "segid PROB"
```

## 🔄 How to Update
```bash
pip install --upgrade -e .
```
