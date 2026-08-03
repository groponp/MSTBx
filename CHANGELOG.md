# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- Added `docs/SCIENTIFIC_BACKGROUND.md`, a literature-cited explanation of the
  physical/chemical rationale behind every MD default MSTBx generates
  (thermostat/barostat choice, PME electrostatics, constraint algorithms,
  restraint force constants, box construction, and CHARMM protonation-state
  chemistry), grounded directly in the GROMACS/NAMD/OpenMM generator source
  code rather than assumed defaults.
- Split the README's inline tutorials into `docs/tutorials/` (one file per
  engine: `pdbwriter.md`, `namd.md`, `gromacs.md`, `openmm.md`, `docking.md`,
  plus an `index.md`) and moved the full command/flag reference into
  `docs/REFERENCE.md`, trimming duplicated worked examples down to
  cross-links. `README.md` is now a short front door with a documentation
  map; `CHANGELOG.md` and `docs/Testing_Manual.md` are the single sources for
  version history and the per-workflow testing checklist instead of being
  duplicated inline in the README.
- Added project-wide CLI matrix tests and short workflow-delegation tests for
  all registered commands, including adversarial option combinations.
- Added real external regressions for PDB2PQR and GROMACS `grompp` compilation
  without launching `mdrun`.
- Updated GROMACS tutorials to use natural MDAnalysis selections (`protein`,
  `not protein`, and `protein or resname LIG`) and validated the protein-only
  tutorial script against a real GROMACS installation.
- Removed workflow-specific logging instructions from the README; logging
  remains an automatic runtime behavior, and README documentation is explicitly
  required to use English.
- Added a dedicated PDBWriter command matrix covering valid operation combinations,
  CRD-only output, CGenFF preparation, and invalid option combinations.
- Added MDAnalysis atom selection to `pdbwriter`, including `--pdb-id`
  download followed by selection while preserving selected HETATM records.
- Unified session logging across CLI tools, PDBWriter, and OpenMM with the
  `MSTBX_LOG_FILE` override and working-directory-aware handlers.
- Added a complete docking-pose tutorial covering PDBQT/PDB inputs, PDBWriter
  cleanup, and GROMACS/NAMD continuation boundaries.
- Expanded the docking tutorial into case studies with navigation links and
  added unit, regression, and adversarial coverage for PDBQT extraction,
  complex construction, and MOL2 validation.
- Hardened `mkdocking-cmplx` and MOL2 validation against missing `MODEL 1`,
  failed conversions, truncated sections, invalid counts, coordinates, and
  out-of-range bond references.
- Added a CHARMM-compatible GROMACS protein selection for non-standard
  protonation names such as `LSN`, `ARGN`, `ASPP`, `GLUP`, and `HSD/HSE/HSP`.
- Extended the protein-ligand GROMACS tutorial with interactive residue
  protonation and explicit `PROTEIN_SEL`/`SOLUTE_SEL` selections.
- Consolidated the GROMACS protonation, CHARMM alias, ligand-protonation, and
  post-build validation rules in the technical documentation.

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
- Added a Conda installation recipe, explicit external-tool checks, version floors for Python dependencies, and wheel packaging for shared CHARMM topology data.
- Made `pdbwriter --pH` execute PDB2PQR/PROPKA with real CHARMM or AMBER naming and corrected extended CHARMM CRD residue-index and mass fields.
- Fixed `pdbwriter --pdb-id ... --select-chains` so download-only mode writes only the requested chains.
- Added project testing policy requiring unit, regression, and adversarial coverage for new workflows.
- Extended the testing policy and automated surface coverage to the complete MSTBx project, including NAMD, OpenMM, structure builders, validators, docking, translation, enhanced sampling, and container helpers.
- Integrated the consolidated OpenMM Runner as the native `mstbx openmm-run` command.
- Created `mstbx/core/MDProtocols/OpenMMRunner.py` containing the core simulation logic (Minimization, NVT/NPT Equilibration, and Production).
- Created the Click interface wrapper in `mstbx/commands/openmm_run.py` to parse all original arguments (`-i`, `-p`, `-c`, `-irst`, `-orst`, `--rewrap`, `--mk-inp`, etc.).
- Added a comprehensive **Complete Step-by-Step Examples & Minitutorials** section with interactive anchor links in the main `README.md`.
- Implemented repository-wide agent guidelines and changelog generation requirements in `.gemini/skills/mstbx-development/SKILL.md`.

### Changed
- Bumped project version to `0.8.10-beta` in `pyproject.toml`, `mstbx/cli.py`, and `GEMINI.md`.
