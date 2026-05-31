# MSTBx (Molecular Simulation ToolBox) v0.8.5

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
*   **Membrane**: `mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150`
    *   *Note: Uses strict XY square box and 25Å default Z-padding.*
*   **SMD**: `mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb --atoms-pull "resid 100" --atoms-anchor "resid 1"`

---

## ⚙️ Simulation Modules (`inputs`)

Automatic generation of NAMD configuration files and an automated **`runner.sh`** script.

*   **`md-inputs`**: Standard MD (NVT, NPT, Production).
*   **`smd-inputs`**: Steered MD (Pulling).
*   **`metad-inputs`**: Well-Tempered Metadynamics.

### Automated Execution
After generating inputs, simply run:
```bash
chmod +x runner.sh
./runner.sh
```
*Edit the control flags (`eq=on`, `md_init=off`) inside the script to manage simulation steps.*

---

## 🧪 Advanced Tools

*   **`pdbwriter`**: Intelligent repair (internal gaps only), S-S bond detection, and protonation.
*   **`md-translate`**: Coordinate/Trajectory translation (e.g., NAMD to GROMACS).
*   **`resetpsf`**: Reset PSF/PDB to X-PLOR format (ideal for glycosylations).
*   **`colabfold`**: Structure prediction via Apptainer/Singularity.
*   **`mkdocking-cmplx`**: Assemble protein-ligand complexes from docking poses.

---

## 📊 Industrial Logging
All modules use a standardized logging format for easy tracking:
`[LEVEL HH:MM:SS DD/MM/YYYY] Message`

---

## 📚 Documentation
*   🇺🇸 [English Wiki](docs/wiki/en/Home.md)
*   🇪🇸 [Wiki en Español](docs/wiki/es/Home.md)
*   🇧🇷 [Wiki em Português](docs/wiki/pt/Home.md)
*   🔬 [**Testing Manual**](docs/Testing_Manual.md)
