# MSTBx (Molecular Simulation ToolBox) v0.8.7

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

## 🛠️ Topology Modules (`topopsfgen`)

System building with granular padding control and accurate PBC reporting.
Usage: `mstbx topopsfgen --env [solution|membrane|smd] [OPTIONS]`

*   **Solution**: `mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --salt 0.150`
*   **Membrane (Standard)**: `mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150`
*   **Membrane (Peripheral)**: `mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --mol-outside --z-distance 10`
*   **SMD (Oriented)**: 
    ```bash
    mstbx topopsfgen --env smd --psf protein.psf --pdb protein.pdb \
                     --atoms-pull "resid 100" --atoms-anchor "resid 1" --extra-space 50
    ```
    *   *Note: Aligns protein to Z-axis and extends the box in Z+ for pulling.*

---

## ⚙️ Simulation Modules (`inputs`)

Automatic generation of NAMD configuration files and an automated **`runner.sh`** script.

### 1. Standard MD (`md-inputs`)
*   *Solution*: `mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb`
*   *Membrane*: `mstbx md-inputs --engine namd --env membrane --psf 01build/sys.psf --pdb 01build/sys.pdb`

### 2. Steered MD (`smd-inputs`)
```bash
mstbx smd-inputs --engine namd --env solution \
                 --psf 01build/sys.psf --pdb 01build/sys.pdb \
                 --selpull "resid 100" --selanchor "resid 1" --target-center 50
```

### 3. Metadynamics (`metad-inputs`)
```bash
mstbx metad-inputs --engine namd --env solution \
                   --psf 01build/sys.psf --pdb 01build/sys.pdb \
                   --sel1 "segid PROA" --sel2 "segid PROB" --target-distance 60
```

### Automated Execution
After generating any input, simply run:
```bash
chmod +x runner.sh
./runner.sh
```

---

## 🧪 Advanced Tools

### PDBWriter (Repair & Clean)
`mstbx pdbwriter -i original.pdb -o fixed.pdb --fix --ssbond --ph 7.4`

### Complex Builder (Docking)
`mstbx mkdocking-cmplx -p protein.pdb -d ligand.pdbqt -o complex.pdb`

### Coordinate Translation
`mstbx md-translate --psf sys.psf --coor restart.coor --xsc restart.xsc --toppar-dir ./toppar`

### Reset PSF (X-PLOR / Glycans)
`mstbx resetpsf --psf complex.psf --pdb complex.pdb --output reset_sys`

### ColabFold Prediction
`mstbx colabfold -i ./input_fastas -o ./predictions`

---

## 📊 Industrial Logging
All modules use a standardized logging format:
`[LEVEL HH:MM:SS DD/MM/YYYY] Message`

---

## 📚 Documentation
*   🇺🇸 [English Wiki](docs/wiki/en/Home.md) | 🇪🇸 [Wiki en Español](docs/wiki/es/Home.md) | 🇧🇷 [Wiki em Português](docs/wiki/pt/Home.md)
*   🔬 [**Full Testing Manual**](docs/Testing_Manual.md)
