# MSTBx Project Plan

This file records the implemented workflow decisions and the project rules that
must remain stable. It is written as a handover document for future changes.

## Completed Work

### Documentation and project structure

- Added complete step-by-step tutorials for PDBWriter, protein-only GROMACS,
  protein-ligand GROMACS/CGenFF, docking poses, NAMD system continuation, and
  OpenMM workflows.
- Organized the docking tutorial as case studies with links for PDBQT input,
  ligand PDB input, receptor repair, PDBWriter cleanup, GROMACS, and NAMD.
- Moved `Module Reference and Technical Documentation` after the tutorials and
  development standards in the main README.
- Added explicit tutorial requirements: explain the starting files, identify
  the applicable case, show commands in execution order, describe generated
  files, and document validation and common failures.
- Kept README and tutorial documentation in English.
- Added `PROJECT.md` with source-derived behavior for GROMACS, PDBWriter,
  docking complex construction, MOL2 validation, and testing policy.

### GROMACS workflow

- Implemented the CHARMM36/CGenFF GROMACS workflow with the MSTBx layout:
  `01build`, `02nvt`, `03npt`, `04md`, `restraints`, `toppar`, and `run_all.sh`.
- Preserved the validated defaults: 1.8 nm box distance, 50,000 EM steps,
  2 fs timestep, 2 ns NVT, 5 ns NPT, 100 ns production, and 50 ps XTC output.
- Kept CGenFF Web submission manual. MSTBx prepares MOL2 and protein/ligand
  inputs but does not automate the web service or invent an STR file.
- Added interactive terminal and residue protonation through
  `--pdb2gmx-ter --pdb2gmx-protonation`.
- Documented that `--pdb2gmx-selection` supplies only terminal answers and
  cannot replace HIS/ASP/GLU/LYS/ARG protonation prompts.
- Added the shared CHARMM-compatible `PROTEIN_SELECTION` aliases for states
  that MDAnalysis does not classify as `protein`, including `LSN`, `LYSN`,
  `ARGN`, `ASPP`, `GLUP`, `HSD`, `HSE`, and `HSP` forms.
- Added `PROTEIN_SEL` and `SOLUTE_SEL` examples for protein-ligand systems so
  protonated protein residues remain separate from `resname LIG`.
- Updated position restraints to recognize the same protein aliases and keep
  ligand restraints limited to ligand heavy atoms.
- Replicas are created by copying a validated complete system directory; MSTBx
  does not manage replicas internally.

### Docking and MOL2 validation

- `mkdocking-cmplx` accepts exactly one ligand source: a docking PDBQT or an
  already converted ligand PDB.
- PDBQT input requires a usable `MODEL 1`; that model is extracted and passed to
  Open Babel.
- Docking ligands are normalized to `HETATM`, residue name `LIG`, and chain `L`.
- `mkdocking-cmplx` writes a combined PDB only. PSF files, GROMACS topology,
  CGenFF parameters, and NAMD parameter files remain engine-specific outputs.
- Open Babel failures and invalid input files are reported as CLI errors.
- Generated MOL2 files are validated before the complex is written. Validation
  checks MOLECULE/ATOM/BOND sections, counts, atom numbering, coordinates, and
  bond references.
- Temporary docking conversion files are isolated under the output directory
  and are removed after the build.

### PDBWriter and structure preparation

- `pdbwriter --pdb-id` downloads the official RCSB structure when requested.
- `--select-atoms` uses MDAnalysis selections without invoking PDBFixer and
  preserves selected HETATM records.
- `--fix-structure` repairs missing heavy atoms and strictly internal residues;
  terminal gaps are not silently rebuilt.
- Hydrogens are not added during repair unless `--fix-add-hydrogens` is passed.
- `--fix-keep-hetatoms` preserves waters, ions, and ligands during repair.
- `--pH` with `--ff-out CHARMM` produces CHARMM-compatible names such as
  `HSD`, `HSE`, `HSP`, `ASPP`, and `GLUP` for downstream CHARMM/NAMD/GROMACS
  workflows.
- Extended CHARMM CRD output and PDB/PSF/CRD/MOL2 format validation are tested.

### Testing and validation completed

- Added unit, regression, and adversarial tests for docking pose extraction,
  complex construction, invalid ligand sources, and MOL2 validation.
- Added an adversarial regression proving that MDAnalysis excludes `LSN` from
  the bare `protein` selection and that `PROTEIN_SELECTION` includes it.
- Added tutorial regressions for interactive protonation, CGenFF manual steps,
  selection aliases, command order, and documentation links.
- Latest full test result: `84 passed, 2 skipped`.
- Latest published change: `e1557a8` for the protein-ligand interactive
  protonation tutorial; subsequent documentation consolidation is published in
  `427506e`.

## Tasks

## Rules

### Documentation

- All README, tutorial, and command help documentation must be written in
  English.
- Every tutorial must be a reproducible step-by-step case study, not only a
  list of flags or a wrapper script.
- Each tutorial must explain when the case applies, required inputs, command
  order, generated outputs, validation steps, and common failure modes.
- Tutorials must provide internal links or an index when they contain multiple
  cases.
- Do not hide manual external boundaries such as CGenFF Web submission.

### Architecture

- Keep Click wrappers in `mstbx/commands/` limited to argument validation,
  user-facing messages, and delegation.
- Keep processing logic in `mstbx/core/` without Click or direct stdin logic.
- Prefer existing project abstractions and shared constants over duplicated
  workflow-specific selections.
- `topo*` commands build topology and solvated systems; `md-inputs` creates
  engine-specific protocols, indices, restraints, and runners.

### GROMACS

- Use the MSTBx directory layout and defaults documented above.
- Use `1.8` nm for the default solute-box distance.
- Use 50,000 EM steps and a 2 fs timestep unless the user explicitly changes
  the protocol.
- Use MDAnalysis selections for index groups and restraints, not ad hoc atom
  numbering or `gmx make_ndx` as the primary workflow.
- When interactive CHARMM protonation is enabled, never use bare `protein` for
  custom groups without checking protonation aliases. Use `PROTEIN_SEL`.
- In protein-ligand systems, keep protein aliases and `resname LIG` separate;
  use `SOLUTE_SEL` for the complete solute group.
- Apply default restraints to protein backbone heavy atoms and ligand heavy
  atoms only, with the documented 5 kcal mol-1 equivalent force.
- Define ligand protonation before CGenFF Web submission and preserve the same
  MOL2/STR identity through topology generation.
- Inspect total charge, `topol.top`, `ionized.gro`, index groups, and restraint
  files before running dynamics.
- Do not manage replicas inside preparation scripts; copy a validated system.

### Structure and force fields

- Do not add hydrogens with PDBFixer before `pdb2gmx` unless explicitly needed.
- Do not use atom selection as a substitute for structure repair.
- Use matching CGenFF and CHARMM36 versions for MOL2, STR, and force-field data.
- Do not select `Include parameters that are already in CGenFF` when uploading
  a ligand to CGenFF Web.
- Preserve ligand `HETATM` records and verify residue naming before generating
  topology files.

### Testing

- Every workflow change requires unit, regression, and adversarial coverage in
  proportion to its risk.
- Tests must verify defaults, file formats, command order, invalid combinations,
  malformed inputs, and missing metadata where applicable.
- The default test suite must not launch long MD production runs.
- External GROMACS/PDB2PQR tests may compile or validate short inputs but must
  not silently start production dynamics.
- Run tests from the project environment before committing documentation or
  workflow changes.
- Preserve unrelated user-generated files and never reset or delete them.
