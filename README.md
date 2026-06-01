# MSTBx: Molecular Simulation ToolBox (v0.8.9-beta)

MSTBx is a modular Python-based ecosystem designed to streamline the preparation, configuration, and translation of Molecular Dynamics (MD) simulations. It leverages the power of **VMD**, **PSFGen**, and **MDAnalysis** to handle systems from small molecules to large-scale complexes (millions of atoms).

## 🚀 Key Features

*   **Unified CLI:** A single entry point for all MD preparation tasks.
*   **Engine Agnostic:** Supports NAMD (Primary), AMBER, GROMACS, and OpenMM.
*   **Automation:** Automates solvation, ionization, and configuration file generation.
*   **Complex Systems:** Specialized protocols for membrane proteins and protein-ligand complexes.
*   **AI Integration:** Interface for ColabFold via Apptainer/Singularity.

## 📦 Installation

### 1. Using Conda (Recommended)
It is highly recommended to use a dedicated Conda environment to manage dependencies:

```bash
# Create and activate the environment
conda create -n mstbx python=3.12
conda activate mstbx

# Clone the repository
git clone git@github.com:groponp/MSTBx.git
cd MSTBx

# Install in development mode
pip install -e .
```

### 2. Shell Completion (Zsh)
To enable TAB completion for `mstbx` commands without needing to activate the conda environment every time, add the following to your `~/.zshrc`:

```bash
# MSTBx Completion (replace path if your conda is installed elsewhere)
eval "$(_MSTBX_COMPLETE=zsh_source $HOME/miniconda3/envs/mstbx/bin/mstbx)"
```

Then, reload your configuration:
```bash
source ~/.zshrc
```

---

## 🛠 Command Reference & Examples

### 1. `topopsfgen`
Builds CHARMM-style systems (Solvation, Membrane, SMD).

**Usage Examples:**
*   **Detailed Solvation:**
    ```bash
    mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --salt 0.150 --padding 18.0 --ofile solvated_system
    ```
*   **Membrane System with custom padding:**
    ```bash
    mstbx topopsfgen --env membrane --psf protein.psf --pdb protein.pdb --salt 0.15 --padding 25.0 --ofile membrane_complex
    ```
*   **SMD Preparation with extended Z-axis:**
    ```bash
    mstbx topopsfgen --env smd --psf system.psf --pdb system.pdb --pad-z-pos 50.0 --extra-space 20.0 --ofile smd_ready
    ```

### 2. `md-inputs`
Generates standard MD protocols (Minimization, NVT, NPT, Production).

**Usage Examples:**
*   **NAMD Production (200ns) at 310K:**
    ```bash
    mstbx md-inputs --engine namd --env solution --psf ionized.psf --pdb ionized.pdb --temperature 310 --mdtime 200 --dcdfreq 50.0
    ```
*   **GROMACS Membrane with ligand parameters:**
    ```bash
    mstbx md-inputs --engine gromacs --env membrane --psf step4_lipid.psf --pdb step4_lipid.pdb --temperature 310 --mdtime 100 --lparm ligand.str
    ```

### 3. `smd-inputs`
Generates velocity-based pulling protocols (Steered Molecular Dynamics).

**Usage Examples:**
*   **High-precision pulling:**
    ```bash
    mstbx smd-inputs --engine namd --psf system.psf --pdb system.pdb --selpull "resname LIG" --selanchor "protein and backbone" --target-center 45.0 --velocity 5.0 --temperature 310 --dcdfreq 1.0
    ```

### 4. `metad-inputs`
Generates Well-Tempered Metadynamics protocols.

**Usage Examples:**
*   **Custom Metadynamics setup:**
    ```bash
    mstbx metad-inputs --psf complex.psf --pdb complex.pdb --sel1 "segid PROA" --sel2 "segid PROB" --target-distance 30.0 --hill 0.2 --hillfreq 1000 --width 0.5 --temperature 310 --mdtime 500
    ```

### 5. `pdbwriter`
Advanced PDB preparation (Fix, Protonate, Edit, SSBOND).

**Usage Examples:**
*   **Fix missing atoms and protonate at pH 7.4:**
    ```bash
    mstbx pdbwriter -i input.pdb -o fixed.pdb --fix --ph 7.4
    ```
*   **Detect Disulfide Bonds and rename chains:**
    ```bash
    mstbx pdbwriter -i protein.pdb -o clean.pdb --ssbond --rename-chain "A:P"
    ```

### 6. `mkdocking-cmplx`
Assembles protein-ligand complexes from docking poses (Vina/Gnina).

**Usage Examples:**
*   **Build complex from Vina output:**
    ```bash
    mstbx mkdocking-cmplx --protein receptor.pdb --dock poses.pdbqt --output final_complex.pdb
    ```

### 7. `md-translate`
Translates NAMD systems to other engines (e.g., GROMACS).

**Usage Examples:**
*   **NAMD to GROMACS conversion:**
    ```bash
    mstbx md-translate --psf system.psf --coor system.coor --xsc system.xsc --toppar-dir ./toppar --target gromacs
    ```

### 8. `colabfold`
Interface for AI structure prediction via Apptainer.

**Usage Examples:**
*   **Run batch prediction:**
    ```bash
    mstbx colabfold -i ./fasta_files -o ./results --sif ./apptainer/colabfold.sif
    ```

### 9. `resetpsf`
Converts structures to X-PLOR format (required for glycans/virtual bonds).

**Usage Examples:**
*   **Reset PSF/PDB:**
    ```bash
    mstbx resetpsf --psf charmm_system.psf --pdb charmm_system.pdb -o xplor_ready
    ```

---

## 📜 Development Standards

*   **Logging:** All console output follows the format `[LEVEL HH:MM:SS DD/MM/YYYY]`.
*   **Naming:** Consistent flags across modules (`--env`, `--engine`, `--psf`, `--pdb`).
*   **Geometry:** Strict box symmetry (Square XY or Cubic) based on the maximum dimension.

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
