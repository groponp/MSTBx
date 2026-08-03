# MSTBx Tutorials Index

These are complete, reproducible step-by-step case studies. Each tutorial
states when the case applies, the required inputs, the commands in execution
order, the generated outputs, and validation/failure notes.

Start with [PDBWriter Structure Preparation](pdbwriter.md) before any engine
tutorial: it is the shared structure-quality step used across NAMD, GROMACS,
OpenMM, and docking workflows.

## By engine

- [0. PDBWriter Structure Preparation](pdbwriter.md)
- [NAMD workflows](namd.md)
  - 1. Ubiquitin in Solution
  - 2. Protein-Ligand Complex (BAAT)
  - 3. Aquaporin Tetramer in POPC Membrane
  - 4. Steered Molecular Dynamics (SMD) Pulling
  - 5. Glycosylated Protein Simulation (1OAN Dimer)
- [OpenMM workflows](openmm.md)
  - 6. Automated OpenMM Runner Pipeline (Chignolin)
- [GROMACS workflows](gromacs.md)
  - 7. GROMACS Protein-Only
  - 8. GROMACS Protein-Ligand with CGenFF
- [Docking workflows](docking.md)
  - 9. Docking Pose to a Protein-Ligand System

## See also

- [Module Reference](../REFERENCE.md) — full command/flag reference for every
  MSTBx module.
- [Testing Manual](../Testing_Manual.md) — verification checklist for each
  workflow.
