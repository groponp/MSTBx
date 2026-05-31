# MSTBx : Molecular Simulação ToolBox

MSTBx is a specialized toolkit for preparing and generating configuration files for Molecular Dynamics (MD) simulations, with primary support for **NAMD2** and **NAMD3**. It is designed to efficiently handle large-scale systems (millions of atoms) by leveraging the power of **PSFGen** and **VMD**.

## Project Overview

*   **Purpose:** Streamline the preparation of molecular systems (solvation, membrane insertion, ionization) and the generation of standardized MD protocols.
*   **Target Systems:** Proteins in solution, protein-ligand complexes, and membrane proteins.
*   **Architecture:** Modular Python-based library with integrated Tcl script generation for VMD/PSFGen.
*   **Key Dependencies:** Python 3.12, VMD, PSFGen, MDAnalysis, Biopython, NumPy, Pandas.

## Directory Structure

*   `/LIB`: Core library modules.
    *   `Build/`: Classes for system assembly (`BuildSolution`, `BuildMembrane`).
    *   `MDProtocols/`: Logic for generating NAMD configuration files (`MDSolProtocol`, `MDMembProtocol`).
    *   `toppar/`: CHARMM force field topology and parameter files.
    *   `Utils/`: Helper functions for CLI output and file system operations.
*   `/SBx`: Structural Biology extensions, including Colabfold integration.
*   `/AdHocTools`: Scripts for specific tasks like finding disulfide bonds or resetting PSF files.
*   `/DOCK`: Tools for protein-ligand docking preparation.
*   `/Examples`: Reference systems and setup scripts.

## Building and Running

### Environment Setup

The project uses a Conda environment defined in `mstbx.yml`.

```bash
conda env create -f mstbx.yml
conda activate mstbx

# Set the MSTBx environment variable to the project root
export MSTBx=$(pwd)
export PATH=$MSTBx:$PATH
```

### Core Commands

#### 1. Prepare a Solvated System
Use `GenSol.py` to solvate and ionize a system, followed by `GenMDSolConfg.py` to generate the MD protocol.

```bash
# 1. Build the solvated system
python $MSTBx/GenSol.py --psf protein.psf --pdb protein.pdb --salt 0.150 --ofile my_system

# 2. Generate NAMD configuration files (NVT, NPT, MD)
python $MSTBx/GenMDSolConfg.py --psf 01build/my_system.psf --pdb 01build/my_system.pdb --temperature 310 --mdtime 100
```

#### 2. Prepare a Membrane System
Use `GenMemb.py` and `GenMDMembConfg.py` for systems involving lipid bilayers.

```bash
# 1. Build the membrane system
python $MSTBx/GenMemb.py --psf protein_lipid.psf --pdb protein_lipid.pdb --salt 0.150 --ofile my_memb_system

# 2. Generate NAMD configuration files
python $MSTBx/GenMDMembConfg.py --psf 01build/my_memb_system.psf --pdb 01build/my_memb_system.pdb --temperature 310 --mdtime 100
```

## Development Conventions

*   **CLI Argument Parsing:** Uses the `optparse` module.
*   **File Management:** Scripts are designed to work within a specific directory structure (e.g., creating `01build`, `02nvt`, etc.).
*   **VMD Integration:** Many Python scripts generate `.tcl` files and execute them using `vmd -dispdev text -e script.tcl`.
*   **Parameters:** Standard CHARMM force field files are stored in `LIB/toppar` and are automatically copied to the simulation directories by the protocol generators.
*   **Testing:** New modules should be tested against the provided `Examples/` and ideally include a validation step against known stable configurations.
