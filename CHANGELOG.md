# Changelog

All notable changes to this project will be documented in this file.

## [0.8.10-beta] - 2026-06-13

### Added
- Added `mstbx topogmx` for GROMACS CHARMM/CGenFF topology and system construction using the MSTBx system layout.
- Added GROMACS support to `mstbx md-inputs --engine gromacs` for MDPs, MDAnalysis index groups, position restraints, and `run_all.sh`.
- Added `mstbx/core/Gromacs/` modules for build, ligand handling, protocol generation, indexing, restraints, and runner creation.
- Added GROMACS tutorial examples using the `01build`, `02nvt`, `03npt`, `04md`, `restraints`, and `toppar` layout.
- Added automated unit, regression, and adversarial tests for the GROMACS workflow and PDBFixer repair policy.
- Added unit, regression, and adversarial coverage for CGenFF Web input preparation, including malformed/ambiguous inputs and overwrite protection.
- Added complete GROMACS tutorials for both protein-only systems and protein-ligand systems, including the manual CGenFF Web upload/download boundary.
- Added tutorial 0 for complete `pdbwriter` structure preparation, validation, repair, editing, CRD, and CGenFF input options.
- Added project testing policy requiring unit, regression, and adversarial coverage for new workflows.
- Extended the testing policy and automated surface coverage to the complete MSTBx project, including NAMD, OpenMM, structure builders, validators, docking, translation, enhanced sampling, and container helpers.
- Integrated the consolidated OpenMM Runner as the native `mstbx openmm-run` command.
- Created `mstbx/core/MDProtocols/OpenMMRunner.py` containing the core simulation logic (Minimization, NVT/NPT Equilibration, and Production).
- Created the Click interface wrapper in `mstbx/commands/openmm_run.py` to parse all original arguments (`-i`, `-p`, `-c`, `-irst`, `-orst`, `--rewrap`, `--mk-inp`, etc.).
- Added a comprehensive **Complete Step-by-Step Examples & Minitutorials** section with interactive anchor links in the main `README.md`.
- Implemented repository-wide agent guidelines and changelog generation requirements in `.gemini/skills/mstbx-development/SKILL.md`.

### Changed
- Bumped project version to `0.8.10-beta` in `pyproject.toml`, `mstbx/cli.py`, and `GEMINI.md`.
