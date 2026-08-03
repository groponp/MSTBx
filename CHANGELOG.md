# Changelog

All notable changes to this project will be documented in this file.

## [0.8.10-beta] - 2026-06-13

### Added
- Added `mstbx gmx-build` for GROMACS CHARMM/CGenFF system construction using the MSTBx replica layout.
- Added `mstbx gmx-inputs` to generate GROMACS MDPs, MDAnalysis index groups, position restraints, and `run_all.sh`.
- Added `mstbx/core/Gromacs/` modules for build, ligand handling, protocol generation, indexing, restraints, and runner creation.
- Added GROMACS tutorial examples using the `01build`, `02nvt`, `03npt`, `04md`, `restraints`, and `toppar` layout.
- Integrated the consolidated OpenMM Runner as the native `mstbx openmm-run` command.
- Created `mstbx/core/MDProtocols/OpenMMRunner.py` containing the core simulation logic (Minimization, NVT/NPT Equilibration, and Production).
- Created the Click interface wrapper in `mstbx/commands/openmm_run.py` to parse all original arguments (`-i`, `-p`, `-c`, `-irst`, `-orst`, `--rewrap`, `--mk-inp`, etc.).
- Added a comprehensive **Complete Step-by-Step Examples & Minitutorials** section with interactive anchor links in the main `README.md`.
- Implemented repository-wide agent guidelines and changelog generation requirements in `.gemini/skills/mstbx-development/SKILL.md`.

### Changed
- Bumped project version to `0.8.10-beta` in `pyproject.toml`, `mstbx/cli.py`, and `GEMINI.md`.
