[← Back to tutorial index](index.md)

# GROMACS Workflows

These tutorials build CHARMM36/CGenFF GROMACS systems with `topogmx` and
generate protocol/index/restraint/runner files with
`md-inputs --engine gromacs`. Run [PDBWriter Structure Preparation](pdbwriter.md)
first if the starting structure needs repair. See
[Scientific Background](../SCIENTIFIC_BACKGROUND.md) for why each default
(box distance, EM steps, restraint force, protonation aliases) is set the way
it is.

- [7. GROMACS Protein-Only](#7-gromacs-protein-only)
- [8. GROMACS Protein-Ligand with CGenFF](#8-gromacs-protein-ligand-with-cgenff)

---

### 7. GROMACS Protein-Only
A complete GROMACS workflow for a protein without a ligand. This path does not use CGenFF, ligand files, or ligand restraints.

1. **Prepare the protein**:
   ```bash
   cd mstbx/testing/gromacs-protein
   mkdir -p input
   mstbx pdbwriter \
     --fix-structure \
     --pdb-id 1UBQ \
     --select-chains A \
     --output input/protein_prepared.pdb
   ```
   If a local PDB is used and contains missing heavy atoms or internal residues, repair it first:
   ```bash
   mstbx pdbwriter \
     --input raw_protein.pdb \
     --fix-structure \
     --select-chains A \
     --output input/protein_prepared.pdb
   ```
   Use an official RCSB structure with SEQRES when possible. Do not use `--fix-add-hydrogens`; `pdb2gmx` adds CHARMM36 hydrogens in the next step. Review terminal gaps manually instead of rebuilding them automatically.
2. **Build, solvate, and ionize the system**:
   ```bash
   mstbx topogmx \
     --protein input/protein_prepared.pdb \
     --output-dir runs \
     --box-distance 1.8 \
     --pdb2gmx-ter \
     --pdb2gmx-selection $'0\n0\n' \
     --gmx gmx \
     --overwrite
   ```
3. **Generate minimization, NVT, NPT, production, index, restraints, and runner files**:
   If interactive protonation produced CHARMM names such as `LSN` (the
   `LYSN` state), do not use `protein` alone in a custom MDAnalysis selection.
   Use the explicit compatibility selection below:
   ```bash
   PROTEIN_SEL='(protein or resname ARGN ARGN1 ARGN2 ARGN3 ASPH ASPP CYS2 GLUH GLUP HISD HIS1 HISE HISH HSD HSE HSP HSPM LYSN LSN)'
   ```
   ```bash
   mstbx md-inputs --engine gromacs \
     --env solution \
     --runs-dir runs \
     --temperature 310 \
     --nvt-time 2 \
     --npt-time 5 \
     --mdtime 1 \
     --xtc-frequency 50 \
     --name-group-index-1 Protein \
     --select-group-index-1 "$PROTEIN_SEL" \
     --name-group-index-2 Water_and_ions \
     --select-group-index-2 "not ($PROTEIN_SEL)" \
     --select-atoms-to-restraint "$PROTEIN_SEL and name N CA C O" \
     --gmx gmx
   ```
4. **Inspect and run**:
   ```bash
   find runs -maxdepth 2 -type f | sort
   cd runs
   ./run_all.sh
   ```

The default output has `01build`, `02nvt`, `03npt`, `04md`, `restraints`, `toppar`, and `run_all.sh`. The validation example uses 50,000 EM steps, 2 ns NVT, 5 ns NPT, 1 ns production, a 2 fs timestep, and XTC frames every 50 ps.

**Interactive protonation variant:** use this case when the protonation state
of HIS, ASP, GLU, LYS, or ARG must be selected residue by residue. Run the
command in a terminal and answer every `pdb2gmx` prompt; do not pipe the
non-interactive `--pdb2gmx-selection` input into this variant because that
input only covers terminal choices:

```bash
mstbx topogmx \
  --protein input/protein_prepared.pdb \
  --output-dir runs_interactive \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --pdb2gmx-protonation \
  --gmx gmx \
  --overwrite
```

The prompts first ask for N-terminal and C-terminal states and then show the
available protonation states for titratable residues. Record the choices in the
run log and inspect the resulting total charge in `runs_interactive/01build`
before generating MD inputs. Use the non-interactive selection form only after
those choices have been intentionally recorded and tested for the same protein.

### 8. GROMACS Protein-Ligand with CGenFF
A complete GROMACS workflow for a protein-ligand system. MSTBx prepares the files for CGenFF Web, the user obtains the STR manually, and only then does `topogmx` build the solvated system.

1. **Prepare inputs for CGenFF Web**:
   ```bash
   cd mstbx/testing/gromacs-2oi0
   mkdir -p work/cgenff_inputs_2oi0
   mstbx pdbwriter --prepare-cgenff-inputs \
     --pdb-id 2OI0 \
     --select-chains A \
     --pdb-ligand-resname 283 \
     --pdb-ligand-chain A \
     --output work/cgenff_inputs_2oi0 \
     --ligand-pH 7.4 \
     --overwrite
   ```
   If the protein has missing heavy atoms or internal residues, repair it before this extraction and preserve the ligand:
   ```bash
   mstbx pdbwriter \
     --fix-structure \
     --fix-keep-hetatoms \
     --pdb-id 2OI0 \
     --select-chains A \
     --output work/2oi0_fixed.pdb
   ```
   In that case, replace `--pdb-id 2OI0` in the preparation command with `--input work/2oi0_fixed.pdb`. Do not use `--fix-add-hydrogens`; `pdb2gmx` handles protein hydrogens later. Upload `work/cgenff_inputs_2oi0/ligand_for_cgenff.mol2`, do not select `Include parameters that are already in CGenFF`, and save the downloaded result as `work/cgenff_inputs_2oi0/ligand_for_cgenff.str`. This manual web step cannot be automated by MSTBx.
2. **Build the 2OI0 system** after the STR is present:
   ```bash
   mstbx topogmx \
     --protein work/cgenff_inputs_2oi0/protein_prepared.pdb \
     --ligand-mol2 work/cgenff_inputs_2oi0/ligand_for_cgenff.mol2 \
     --ligand-str work/cgenff_inputs_2oi0/ligand_for_cgenff.str \
     --ligand-resname LIG \
     --output-dir runs \
     --box-distance 1.8 \
     --pdb2gmx-ter \
     --pdb2gmx-selection $'1\n1\n'
   ```
   **Interactive residue-protonation variant:** if HIS, ASP, GLU, LYS, or ARG
   states must be chosen manually, use a new output directory and answer the
   terminal prompts directly:
   ```bash
   mstbx topogmx \
     --protein work/cgenff_inputs_2oi0/protein_prepared.pdb \
     --ligand-mol2 work/cgenff_inputs_2oi0/ligand_for_cgenff.mol2 \
     --ligand-str work/cgenff_inputs_2oi0/ligand_for_cgenff.str \
     --ligand-resname LIG \
     --output-dir runs_interactive \
     --box-distance 1.8 \
     --pdb2gmx-ter \
     --pdb2gmx-protonation \
     --gmx gmx \
     --overwrite
   ```
   Do not pipe `--pdb2gmx-selection` into this variant. That option only
   supplies N-terminal and C-terminal answers; `--pdb2gmx-protonation` adds
   residue-by-residue HIS/ASP/GLU/LYS/ARG prompts. The ligand is not
   protonated by `pdb2gmx`; its protonation must be fixed before the CGenFF Web
   submission and kept consistent with the returned STR.
3. **Write protocols, index, restraints, and runner**: NVT and NPT times are given in ns, following the same time convention used by the NAMD tutorials.
   ```bash
   PROTEIN_SEL='(protein or resname ARGN ARGN1 ARGN2 ARGN3 ASPH ASPP CYS2 GLUH GLUP HISD HIS1 HISE HISH HSD HSE HSP HSPM LYSN LSN)'
   SOLUTE_SEL="($PROTEIN_SEL) or resname LIG"
   mstbx md-inputs --engine gromacs \
     --env solution \
     --runs-dir runs \
     --temperature 310 \
     --nvt-time 2 \
     --npt-time 5 \
     --mdtime 100 \
     --xtc-frequency 50 \
     --name-group-index-1 Protein_ligand \
     --select-group-index-1 "$SOLUTE_SEL" \
     --name-group-index-2 Water_and_ions \
     --select-group-index-2 "not ($SOLUTE_SEL)" \
     --select-atoms-to-restraint "$PROTEIN_SEL and name N CA C O or resname LIG and not name H*" \
     --gmx gmx
   ```
4. **Inspect and run the system later**:
   ```bash
   cd runs
   ./run_all.sh
   ```

Create replicas only after the system is validated by copying the full directory, for example `cp -a runs rep1`, `cp -a runs rep2`, and `cp -a runs rep3`. MSTBx deliberately does not manage replicas internally.

The repository scripts under `mstbx/testing/gromacs-2oi0/` validate this same sequence, but the tutorial intentionally shows each command explicitly.

---

[← Back to tutorial index](index.md) · See also: [Scientific Background](../SCIENTIFIC_BACKGROUND.md) · [Module Reference](../REFERENCE.md#2b-topogmx-and-md-inputs---engine-gromacs---gromacs-charmmcgenff-workflow) · [Docking workflows](docking.md)
