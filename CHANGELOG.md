# Changelog

All notable changes to this project will be documented in this file.

## [0.8.10-beta] - 2026-06-13

### Added
- Integrated the consolidated OpenMM Runner as the native `mstbx openmm-run` command.
- Created `mstbx/core/MDProtocols/OpenMMRunner.py` containing the core simulation logic (Minimization, NVT/NPT Equilibration, and Production).
- Created the Click interface wrapper in `mstbx/commands/openmm_run.py` to parse all original arguments (`-i`, `-p`, `-c`, `-irst`, `-orst`, `--rewrap`, `--mk-inp`, etc.).
- Added a comprehensive **Complete Step-by-Step Examples & Minitutorials** section with interactive anchor links in the main `README.md`.
- Implemented repository-wide agent guidelines and changelog generation requirements in `.gemini/skills/mstbx-development/SKILL.md`.

### Changed
- Bumped project version to `0.8.10-beta` in `pyproject.toml`, `mstbx/cli.py`, and `GEMINI.md`.
