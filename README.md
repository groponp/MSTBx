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

## 🛠️ Topology Modules (`topopsfgen`)

System building with granular padding control and accurate PBC reporting.
Usage: `mstbx topopsfgen --env [solution|membrane|smd] [OPTIONS]`

*   **Solution**: `mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --salt 0.150`
*   **Membrane**: `mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150`
*   **SMD (Oriented)**: `mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb --atoms-pull "resid 100" --atoms-anchor "resid 1"`

### 🧬 Glycosylated Proteins (Advanced Workflow)
For proteins with glycans and virtual bonds, follow this **Reset-then-Build** pipeline:

1.  **Reset to X-PLOR**: (Handles virtual bonds/glycosylation patches first)
    `mstbx resetpsf --psf step1.psf --pdb step1.pdb --output reset_glyc`
2.  **Build Environment**: (Use the reset files as input)
    `mstbx topopsfgen --env solution --psf reset_glyc.psf --pdb reset_glyc.pdb --salt 0.150`
3.  **Generate MD Protocols**:
    `mstbx md-inputs --engine namd --env solution --psf 01build/macromol150mM.psf --pdb 01build/macromol150mM.pdb`

---

## ⚙️ Simulation Modules (`inputs`)

Automatic generation of NAMD configuration files and an automated **`runner.sh`** script.

### 1. Standard MD (`md-inputs`)
*   *Solution*: `mstbx md-inputs --engine namd --env solution --psf sys.psf --pdb sys.pdb`
*   *Membrane*: `mstbx md-inputs --engine namd --env membrane --psf sys.psf --pdb sys.pdb`

### 2. Steered MD (`smd-inputs`)
*   **Default**: `mstbx smd-inputs --engine namd --env solution --psf sys.psf --pdb sys.pdb --selpull "resid 100" --target-center 50`
*   **Custom Folder**: `mstbx smd-inputs --engine namd --env solution --psf sys.psf --pdb sys.pdb --colvar-input ./my_smd_setup/`

### 3. Metadynamics (`metad-inputs`)
*   **Default**: `mstbx metad-inputs --engine namd --env solution --psf sys.psf --pdb sys.pdb --sel1 "segid PROA" --sel2 "segid PROB"`

---

## 🧪 Advanced Tools

*   **`pdbwriter`**: Intelligent repair (internal gaps only), S-S bond detection, and protonation.
*   **`resetpsf`**: Reset PSF/PDB to X-PLOR format (ideal for glycosylations).
*   **`md-translate`**: Coordinate/Trajectory translation (e.g., NAMD to GROMACS).
*   **`colabfold`**: Structure prediction via Apptainer/Singularity.
*   **`mkdocking-cmplx`**: Assemble protein-ligand complexes from docking poses.

---

## 📊 Industrial Logging
All modules use a standardized logging format:
`[LEVEL HH:MM:SS DD/MM/YYYY] Message`

---

## 📚 Documentation
*   🇺🇸 [English Wiki](docs/wiki/en/Home.md) | 🇪🇸 [Wiki en Español](docs/wiki/es/Home.md) | 🇧🇷 [Wiki em Português](docs/wiki/pt/Home.md)
*   🔬 [**Full Testing Manual**](docs/Testing_Manual.md)
