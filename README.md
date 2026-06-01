# MSTBx: Molecular Simulation ToolBox (v0.8.9-beta)

<p align="center">
  <img src="logo.png" width="400" alt="MSTBx Logo">
</p>

## Introduction

MSTBx is a high-performance, modular Python-based ecosystem designed to streamline the preparation, configuration, and execution of Molecular Dynamics (MD) simulations. Built with a "Waiter/Chef" architecture, MSTBx provides a unified Command Line Interface (CLI) that automates complex tasks involving VMD, PSFGen, and MDAnalysis.

While web-based system builders are convenient, they often struggle with massive systems or complex high-throughput requirements. MSTBx is engineered for efficiency, capable of preparing systems with millions of atoms (such as the SARS-CoV-2 Spike protein) in a fraction of the time required by conventional tools.

## Core Philosophies

1. **Efficiency**: Optimized for large-scale complexes where automation is critical.
2. **Reproducibility**: Parameter-driven configuration ensures consistent protocol generation.
3. **Engine Versatility**: Native support for NAMD 2/3, with expanding capabilities for GROMACS, AMBER, and OpenMM.
4. **Standardization**: Enforces strict geometric symmetries and nomenclature across all modules.

---

## Installation

### 1. Environment Management (Conda)
It is highly recommended to use a dedicated environment to isolate dependencies (Python >= 3.12):

```bash
conda create -n mstbx python=3.12
conda activate mstbx

git clone git@github.com:groponp/MSTBx.git
cd MSTBx
pip install -e .
```

### 2. Persistent Shell Completion
To enable robust TAB completion for all MSTBx modules, add the following to your `~/.zshrc` (or `~/.bashrc`):

```bash
# MSTBx CLI Completion
eval "$(_MSTBX_COMPLETE=zsh_source $HOME/miniconda3/envs/mstbx/bin/mstbx)"
```

---

## Module Reference and Technical Documentation

### 1. `topopsfgen` - System Assembly and Solvation

The `topopsfgen` module is the primary engine for building CHARMM-style PSF/PDB structures. It handles solvation, ionization, and complex environment assembly (membranes/SMD).

**Technical Details:**
- **Solvation**: Implements cubic or square-XY padding. Default padding is 18.0 Å for solution systems.
- **Ionization**: Uses a randomized placement algorithm to achieve the target ionic strength (Default: 0.150 M NaCl).
- **Membrane**: Aligns the protein within a lipid bilayer (POPC/others) with default 25.0 Å Z-padding.

**Example: Ubiquitin in Water**
Based on the `testing/ubiquitin` validation set:
```bash
mstbx topopsfgen --env solution \
                 --psf step1_pdbreader.psf \
                 --pdb step1_pdbreader.pdb \
                 --salt 0.150 \
                 --padding 18.0 \
                 --ofile ubq_solvated
```
*Logic*: This command reads the initial PSF/PDB (prepared via CHARMM-GUI PDBReader), adds an 18 Å water buffer in all directions, and ionizes to 150 mM NaCl. Output files will be prefixed with `ubq_solvated`.

### 2. `md-inputs` - Protocol Generation

This module generates production-ready configuration files for different simulation engines. It standardizes the Minimization, NVT (Equilibration), NPT (Pressurization), and Production phases.

**Parameters and Defaults:**
- `--engine`: [namd|amber|gromacs|openmm].
- `--temperature`: Target temperature in Kelvin (Default: 310 K).
- `--mdtime`: Production run time in nanoseconds (Default: 100 ns).
- `--dcdfreq`: Trajectory frame saving frequency in picoseconds (Default: 10.0 ps).

**Example: Protein-Ligand Complex (BAAT)**
Based on the `testing/baat` validation set:
```bash
mstbx md-inputs --engine namd \
                --env solution \
                --psf 01build/baat.psf \
                --pdb 01build/baat.pdb \
                --lparm tyl.prm \
                --temperature 310 \
                --mdtime 100 \
                --dcdfreq 20.0
```
*Logic*: Generates a NAMD protocol for a protein-ligand system. Note the use of `--lparm` to include the specific ligand parameter file (`tyl.prm`). The output includes a step-by-step pipeline (Minimization -> NVT -> NPT -> Production).

### 3. `smd-inputs` - Steered Molecular Dynamics

`smd-inputs` configures velocity-based pulling simulations. It calculates the necessary NAMD Colvars or engine-specific pulling parameters.

**Key Flags:**
- `--selpull`: VMD selection for the pulling group (e.g., "resname LIG").
- `--selanchor`: VMD selection for the fixed/anchor group (e.g., "protein and backbone").
- `--velocity`: Constant pulling speed in Å/ns (Default: 10.0 Å/ns).
- `--target-center`: Maximum extension distance in Å.

**Example: Pulling Validation**
Based on the `testing/smd` validation set:
```bash
mstbx smd-inputs --psf system.psf \
                 --pdb system.pdb \
                 --selpull "resname LIG" \
                 --selanchor "protein and backbone" \
                 --target-center 50.0 \
                 --velocity 5.0 \
                 --temperature 310
```
*Logic*: This prepares a protocol to pull a ligand 50 Å away from the binding site at a slow velocity of 5 Å/ns to minimize non-equilibrium artifacts.

### 4. `metad-inputs` - Well-Tempered Metadynamics

This module streamlines the configuration of enhanced sampling via Metadynamics.

**Parameters:**
- `--hill`: Initial hill height in kcal/mol (Default: 0.1).
- `--width`: Hill width/Sigma (Default: 0.5 Å).
- `--biasT`: Bias temperature for well-tempered scaling (Default: 4000 K).

**Example:**
```bash
mstbx metad-inputs --psf complex.psf \
                   --pdb complex.pdb \
                   --sel1 "segid PROA" \
                   --sel2 "segid PROB" \
                   --target-distance 30.0 \
                   --hill 0.2 \
                   --mdtime 500
```

### 5. `pdbwriter` - Structure Refinement

Advanced preparation tool for repairing and annotating PDB files. It integrates PDBFixer for gap filling and PDB2PQR for protonation.

**Capabilities:**
- `--fix`: Repairs missing atoms and internal residues.
- `--ph`: Sets target pH for protonation (e.g., `--ph 7.4`).
- `--ssbond`: Heuristic detection of disulfide bridges.

**Example:**
```bash
mstbx pdbwriter -i raw.pdb -o refined.pdb --fix --ph 7.4 --ssbond
```

### 6. `resetpsf` - X-PLOR Format Conversion

Essential for systems with complex patches (glycans, virtual atoms, or CMAP) that require the X-PLOR PSF format.

**Example:**
```bash
mstbx resetpsf --psf charmm.psf --pdb charmm.pdb -o system_xplor
```

### 7. `md-translate` - Engine Interoperability

Allows the conversion of NAMD-formatted systems (PSF/COOR/XSC) to other engine formats like GROMACS (TOP/GRO).

**Example:**
```bash
mstbx md-translate --psf system.psf \
                   --coor system.coor \
                   --xsc system.xsc \
                   --toppar-dir ./toppar \
                   --target gromacs
```

---

## Development Standards

MSTBx follows strict internal standards to ensure reliability:
- **Logging**: All output is timestamped: `[LEVEL HH:MM:SS DD/MM/YYYY]`.
- **Naming**: Consistent flags across all modules (`--env`, `--engine`, `--psf`, `--pdb`).
- **Safety**: Automated box symmetry checks to prevent periodic boundary condition artifacts.

## Author
**Ropón-Palacios G.**  
Department of Physics, UNESP.  
[georcki.ropon@unesp.br](mailto:georcki.ropon@unesp.br)

## License
MSTBx is licensed under the **MIT License**.
