[← Back to README](../README.md)

# Module Reference and Technical Documentation

This is the flag-by-flag reference for every MSTBx module. For runnable,
narrated walkthroughs, use the [tutorials index](tutorials/index.md) instead —
this page intentionally does not repeat full worked examples where a tutorial
already covers the same command sequence.

## Engine Architecture

MSTBx keeps topology/system construction separate from protocol generation:

| Engine | Topology/system builder | Standard MD inputs | Runner |
| --- | --- | --- | --- |
| NAMD | `topopsfgen` | `md-inputs --engine namd` | generated NAMD runner |
| GROMACS | `topogmx` | `md-inputs --engine gromacs` | generated `run_all.sh` |
| AMBER | `topotleap` | planned `md-inputs --engine amber` | planned |
| OpenMM | CHARMM-style inputs or translated systems | planned `md-inputs --engine openmm` | `openmm-run` |

This keeps `topo*` commands responsible for topology/system generation and `md-inputs` responsible for engine-specific equilibration and production inputs.

### 1. `topopsfgen` - System Assembly and Solvation

<p align="justify">
The `topopsfgen` module is the primary engine for building CHARMM-style PSF/PDB structures. It handles solvation, ionization, and complex environment assembly (membranes/SMD). It is designed to work seamlessly with initial outputs from the <b>CHARMM-GUI PDBReader</b>, providing a significant speed advantage for subsequent building steps.
</p>

**Technical Details:**
- **Solvation**: Implements cubic or square-XY padding. Default padding is 18.0 Å for solution systems.
- **Ionization**: Uses a randomized placement algorithm to achieve the target ionic strength (Default: 0.150 M NaCl).
- **Membrane**: Aligns the protein within a lipid bilayer (POPC/others) with default 25.0 Å Z-padding.

See [Ubiquitin in Solution](tutorials/namd.md#1-ubiquitin-in-solution) for a full worked example (`testing/ubiquitin` validation set).

### 2. `md-inputs` - Protocol Generation

<p align="justify">
This module generates production-ready configuration files for different simulation engines. It standardizes the Minimization, NVT (Equilibration), NPT (Pressurization), and Production phases.
</p>

**Parameters and Defaults:**
- `--engine`: [namd|amber|gromacs|openmm].
- `--temperature`: Target temperature in Kelvin (Default: 310 K).
- `--mdtime`: Production run time in nanoseconds (Default: 100 ns).
- `--dcdfreq`: Trajectory frame saving frequency in picoseconds (Default: 10.0 ps).

See [Protein-Ligand Complex (BAAT)](tutorials/namd.md#2-protein-ligand-complex-baat) for a full worked example using `--lparm` for ligand parameters.

### 2b. `topogmx` and `md-inputs --engine gromacs` - GROMACS CHARMM/CGenFF Workflow

<p align="justify">
These commands prepare GROMACS systems while preserving the same MSTBx directory nomenclature used by the NAMD solution workflow: `01build`, `02nvt`, `03npt`, `04md`, `restraints`, and `toppar`. The minimization MDP is written inside `01build` so the stage layout remains consistent across engines.
</p>

**Generated layout:**
```text
runs/
  01build/      # topology, coordinates, ionized.gro, em.mdp, index.ndx
  02nvt/        # nvt.mdp
  03npt/        # npt.mdp
  04md/         # md.mdp
  restraints/   # copied position-restraint files
  toppar/       # copied ligand topology/parameters when present
  run_all.sh    # complete GROMACS execution script
```

**Important defaults:**
- `--box-distance`: 1.8 nm.
- `--ligand-resname`: `LIG`.
- EM minimization: 50,000 steps.
- NVT: 2 ns at 2 fs, matching the NAMD solution protocol scheme.
- NPT: 5 ns at 2 fs.
- Production: 100 ns by default.
- XTC writing frequency: 50 ps.
- Default restraint force: 2092 kJ mol-1 nm-2, equivalent to 5 kcal mol-1 A-2.
- Default restrained atoms: protein backbone heavy atoms plus ligand heavy atoms.
- Default CHARMM/CGenFF force field: packaged `charmm36-feb2026_cgenff-5.0.ff`.
- Default CGenFF converter: packaged `cgenff_charmm2gmx_py3.py`.

#### Protonation and selection consistency

- Add `--pdb2gmx-protonation` when HIS, ASP, GLU, LYS, or ARG states must be
  selected interactively. Run `topogmx` in a terminal and answer all prompts.
- `--pdb2gmx-selection` supplies only N-terminal and C-terminal answers; it
  does not replace the residue-protonation prompts.
- CHARMM36 may write `LSN` for the neutral `LYSN` state, along with aliases
  such as `ARGN`, `ASPP`, `GLUP`, `HSD`, `HSE`, and `HSP`. MDAnalysis does not
  classify every alias as `protein`, so use the documented `PROTEIN_SEL` when
  custom groups or restraints follow interactive protonation.
- In protein-ligand systems, define `SOLUTE_SEL` as
  `($PROTEIN_SEL) or resname LIG`, and define the solvent/ion group as
  `not ($SOLUTE_SEL)`. Keep the ligand restraint branch as
  `resname LIG and not name H*`.
- Ligand protonation is decided before CGenFF Web submission. Do not expect
  `pdb2gmx` to change the protonation state of the CGenFF ligand.
- After building, inspect the generated `topol.top`, `ionized.gro`, index
  groups, restraint files, and total charge before running `md-inputs` or
  `mdrun`.

Full worked examples, including the protonation aliases and the
`PROTEIN_SEL`/`SOLUTE_SEL` conventions, are in the
[GROMACS tutorials](tutorials/gromacs.md): [protein-only](tutorials/gromacs.md#7-gromacs-protein-only)
and [protein-ligand with CGenFF](tutorials/gromacs.md#8-gromacs-protein-ligand-with-cgenff).

To run the prepared system later:
```bash
cd runs
./run_all.sh
```

To create independent replicas, copy the complete `runs` directory after validation, for example `cp -a runs rep1`, `cp -a runs rep2`, and `cp -a runs rep3`.

### 3. `smd-inputs` - Steered Molecular Dynamics

<p align="justify">
`smd-inputs` configures velocity-based pulling simulations. It calculates the necessary NAMD Colvars or engine-specific pulling parameters.
</p>

**Key Flags:**
- `--selpull`: VMD selection for the pulling group (e.g., "resname LIG").
- `--selanchor`: VMD selection for the fixed/anchor group (e.g., "protein and backbone").
- `--velocity`: Constant pulling speed in Å/ns (Default: 10.0 Å/ns).
- `--target-center`: Maximum extension distance in Å.

See [Steered Molecular Dynamics (SMD) Pulling](tutorials/namd.md#4-steered-molecular-dynamics-smd-pulling) for a full worked example (`testing/smd` validation set), pulling a ligand 50 Å from the binding site at 5 Å/ns.

### 4. `metad-inputs` - Well-Tempered Metadynamics

<p align="justify">
This module streamlines the configuration of enhanced sampling via <b>Well-Tempered Metadynamics</b> using the NAMD Colvars module. It automates the generation of Gaussian hill parameters and bias scaling.
</p>

**Parameters:**
- `--sel1` & `--sel2`: VMD selections for the two groups defining the distance Collective Variable (CV). (e.g., "segid PROA" and "segid PROB").
- `--hill`: Initial hill height in kcal/mol (Default: 0.1).
- `--width`: Hill width/Sigma (Default: 0.5 Å).
- `--biasT`: Bias temperature for well-tempered scaling (Default: 4000 K).
- `--biasfactor`: Also known as the <i>Delta T</i> factor; it controls the rate at which the hill height decays.

**Example:**
```bash
mstbx metad-inputs --psf complex.psf \
                   --pdb complex.pdb \
                   --sel1 "segid PROA" \
                   --sel2 "segid PROB" \
                   --target-distance 30.0 \
                   --hill 0.2 \
                   --biasT 4000 \
                   --mdtime 500
```
*Logic*: Configures a distance CV between segments A and B. MSTBx generates the `colvars.in` file automatically, setting up the Well-Tempered deposition frequency and Gaussian parameters for a 500 ns run.

### 5. `pdbwriter` - Structure Refinement and CRD Generation

<p align="justify">
Advanced preparation tool for repairing, annotating, and converting coordinate files. It integrates PDBFixer for gap filling, PDB2PQR for protonation, and can generate highly compatible CHARMM-GUI extended `.crd` files.
</p>

**Capabilities:**
- `--fix-structure`: Repairs missing atoms and internal residues.
- `--fix-keep-hetatoms`: Keeps waters, ions, ligands, and other HETATM records during structure repair.
- `--fix-add-hydrogens`: Adds hydrogens during structure repair using `--pH`; by default repair stays heavy-atom-only.
- `--select-atoms`/`--selection-atoms`: Writes only atoms matching an MDAnalysis selection, without invoking PDBFixer or removing HETATM records.
- `--pH`: Runs PDB2PQR/PROPKA at the requested pH (e.g., `--pH 7.4`) and writes the protonated PDB.
- `--ff-out CHARMM`: Uses CHARMM names such as `HSD`, `HSE`, `HSP`, `ASPP`, and `GLUP`; this is the default shared naming scheme for NAMD and CHARMM36/CGenFF in GROMACS.
- `--ff-out AMBER`: Uses AMBER naming instead; select this only for an AMBER-based topology.
- `--prepare-cgenff-inputs`: Prepares `protein_prepared.pdb`, `ligand_pose.pdb`, and `ligand_for_cgenff.mol2` for manual CGenFF Web upload.
- `--ligand-pH`: Sets ligand pH for Open Babel when preparing CGenFF inputs (Default: 7.4).
- `--ssbond`: Heuristic detection of disulfide bridges.
- `--write-ext-crd`: Generates an extended CHARMM-GUI style `.crd` file, retaining high-precision coordinates and matching the exact fixed-width column specifications. Requires both `--input` and `--psf`.
- `--check-mol-format`: Validates the integrity of coordinate and topology files (PDB, PSF, CRD, MOL2). Use with `--mol`. This check is also performed internally whenever `pdbwriter` generates an output file.

See the full [PDBWriter Structure Preparation](tutorials/pdbwriter.md) tutorial for worked examples of every flag above, including RCSB downloads, chain edits, CGenFF preparation, and format validation.

### 6. `resetpsf` - X-PLOR Format Conversion

<p align="justify">
Essential for systems with complex patches (glycans, virtual atoms, or CMAP) that require the X-PLOR PSF format. It safely converts standard CHARMM-GUI structures while preserving system integrity. The module automatically parses and verifies that the `!NATOM` counts perfectly match the input architecture to prevent silent data loss during VMD translations.
</p>

**Example:**
```bash
mstbx resetpsf --psf charmm.psf --pdb charmm.pdb -o system_xplor
```

See [Glycosylated Protein Simulation (1OAN Dimer)](tutorials/namd.md#5-glycosylated-protein-simulation-1oan-dimer) for a full worked example.

### 7. `md-translate` - Engine Interoperability

<p align="justify">
Allows the conversion of NAMD-formatted systems (PSF/COOR/XSC) to other engine formats like GROMACS (TOP/GRO).
</p>

**Example:**
```bash
mstbx md-translate --psf system.psf \
                   --coor system.coor \
                   --xsc system.xsc \
                   --toppar-dir ./toppar \
                   --target gromacs
```

### 8. `openmm-run` - Strict Manual OpenMM Runner

<p align="justify">
A unified simulation runner designed for OpenMM engine workflows using CHARMM-style force fields and restraints. It reads standard CHARMM-GUI inputs, automatically generates required templates, handles high-precision restart checkpoints, and includes smart centering and coordinate rewrapping logic.
</p>

**Key Options:**
- `-i`, `--inp`: Input file (.inp).
- `-p`, `--psf`: Topology file (.psf).
- `-c`, `--pdb`: Coordinates file (.pdb).
- `--mk-inp`: Generates default input templates (`min.inp`, `eq1.inp`, `prod.inp`) and exits.
- `-irst`, `--irst`: Input restart file (.rst).
- `-orst`, `--orst`: Output prefix (default: `output`).
- `--toppar`: Path to parameter files directory (default: `toppar/`).
- `--pbc`: Path to PBC .str setup file (default: `01build/step3_pbcsetup.str`).
- `--platform`: Force platform (e.g. `CUDA`, `OpenCL`, `CPU`).
- `--ns`: Override duration in nanoseconds.
- `--rewrap`: Centering/rewrapping coordinates based on bonds topology.

See [Automated OpenMM Runner Pipeline (Chignolin)](tutorials/openmm.md#6-automated-openmm-runner-pipeline-chignolin) for the full multi-stage worked example.

---

[← Back to README](../README.md) · [Tutorials index](tutorials/index.md)
