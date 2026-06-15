# MSTBx : Molecular Simulation ToolBox (v0.8.10-beta)

MSTBx is a modular Python-based ecosystem designed to streamline the preparation, configuration, and translation of Molecular Dynamics (MD) simulations. It leverages the power of **VMD**, **PSFGen**, and **MDAnalysis** to handle systems from small molecules to large-scale complexes (millions of atoms).

## Project Overview

*   **Goal:** Provide a unified CLI interface for MD simulation workflows.
*   **Target Engines:** NAMD2/3 (Primary), with cross-engine translation support (e.g., to GROMACS).
*   **Core Logic:** Located in `mstbx/core/`, utilizing a "Waiter/Chef" architecture where the CLI handles user input and the core modules perform the technical heavy lifting.
*   **Key Dependencies:** Python 3.12, VMD, MDAnalysis, PDBFixer, OpenMM, Biopython.

## CLI Modules Index

*   **`topopsfgen`**: Builds CHARMM-style systems (Solvation, Membrane, SMD).
    *   *Standards:* 18Å cubic padding for solution, 25Å Z-padding for membrane (square XY).
*   **`md-inputs`**: Generates standard MD protocols (NVT, NPT, Production).
*   **`smd-inputs`**: Generates velocity-based pulling protocols aligned to Z-axis.
*   **`metad-inputs`**: Generates Well-Tempered Metadynamics protocols.
*   **`pdbwriter`**: Advanced PDB repair (internal gaps only), S-S bond detection, protonation, and extended CRD generation. Includes a robust validation suite for PDB, PSF, CRD, and MOL2 formats via `--check-mol-format`.
*   **`resetpsf`**: Converts structures to X-PLOR format (required for glycans).
*   **`md-translate`**: Translates coordinates/trajectories between simulation engines.
*   **`colabfold`**: Interface for AI structure prediction via Apptainer.
*   **`mkdocking-cmplx`**: Assembles protein-ligand complexes from docking poses.
*   **`openmm-run`**: Strict Manual OpenMM Runner that executes simulations using CHARMM force fields and restraints.

## Development Standards

*   **Logging:** All console output must follow the format `[LEVEL HH:MM:SS DD/MM/YYYY]`. Use `UnixMessage` or `MSTBxLogger`.
*   **Naming:** Use `--env [solution|membrane|smd]` and `--engine [namd|amber|...]` consistently.
*   **Language:** ALL console output and internal logs must be in **English**.
*   **Geometry:** Always enforce strict box symmetry (Square XY or Cubic) based on the maximum dimension of the molecule.
*   **Git Policy:** Work on feature branches and merge to `main`. Versioning follows `v0.8.x` progression (up to .100) during the Beta phase.

## Environment Management

The project is packaged with `pyproject.toml`.
*   Install for development: `pip install -e .`
*   TAB Completion: Enable via Click completion scripts in `.bashrc` or `.zshrc`.
