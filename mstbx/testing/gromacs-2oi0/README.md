# GROMACS 2OI0 Protein-Ligand Tutorial

This tutorial reproduces the complete MSTBx CHARMM/CGenFF workflow. The CGenFF Web submission is intentionally manual: MSTBx prepares the files, but the user must upload the MOL2 and download the STR returned by the web service.

## 1. Install the required tools

Activate the MSTBx environment and verify that `obabel` and GROMACS are available:

```bash
conda activate mstbx
command -v obabel
gmx --version
```

Install MSTBx in editable mode if needed:

```bash
pip install -e ".[test]"
```

## 2. Generate files for CGenFF Web

The example uses PDB entry 2OI0, chain A, and ligand residue `283`:

```bash
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

This writes `work/cgenff_inputs_2oi0/` containing:

```text
protein_prepared.pdb
ligand_pose.pdb
ligand_for_cgenff.mol2
cgenff_inputs_log.json
```

## 3. Submit the ligand manually to CGenFF Web

Upload `work/cgenff_inputs_2oi0/ligand_for_cgenff.mol2` to the CGenFF Web service. Do not select `Include parameters that are already in CGenFF`. Download the generated STR file and save it exactly as:

```text
work/cgenff_inputs_2oi0/ligand_for_cgenff.str
```

The STR and the selected CHARMM36/CGenFF force field must use compatible CGenFF versions. The packaged default is `charmm36-feb2026_cgenff-5.0.ff`.

## 4. Build the solvated and ionized GROMACS system

After the STR download, continue with:

Run the topology builder explicitly:

```bash
mstbx topogmx \
  --protein work/cgenff_inputs_2oi0/protein_prepared.pdb \
  --ligand-mol2 work/cgenff_inputs_2oi0/ligand_for_cgenff.mol2 \
  --ligand-str work/cgenff_inputs_2oi0/ligand_for_cgenff.str \
  --ligand-resname LIG \
  --forcefield-dir "$(python -c 'from mstbx.core.Gromacs.Build import DEFAULT_FORCEFIELD_DIR; print(DEFAULT_FORCEFIELD_DIR)')" \
  --output-dir runs \
  --box-distance 1.8 \
  --pdb2gmx-ter \
  --pdb2gmx-selection $'0\n0\n' \
  --gmx gmx \
  --overwrite
```

Then generate the protocols, index groups, restraints, and runner:

```bash
mstbx md-inputs --engine gromacs \
  --env solution \
  --runs-dir runs \
  --temperature 310 \
  --nvt-time 2 \
  --npt-time 5 \
  --mdtime 100 \
  --xtc-frequency 50 \
  --name-group-index-1 Protein_ligand \
  --select-group-index-1 "not (resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN)" \
  --name-group-index-2 Water_and_ions \
  --select-group-index-2 "resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN" \
  --select-atoms-to-restraint "name N CA C O and not resname SOL TIP3 TIP3P WAT HOH NA CL K MG CA ZN or resname LIG and not name H*" \
  --gmx gmx
```

These commands create one validated system and do not launch `mdrun`:

```text
runs/
  01build/      # topology, coordinates, ions, and em.mdp
  02nvt/        # nvt.mdp
  03npt/        # npt.mdp
  04md/         # md.mdp
  restraints/   # generated position restraints
  toppar/       # ligand topology and parameters
  run_all.sh    # generated execution script
```

Defaults used by this validation are 1.8 nm box distance, 50,000 EM steps, 2 ns NVT, 5 ns NPT, 100 ns production, 2 fs timestep, and XTC frames every 50 ps. The default restraint selection is protein backbone plus ligand heavy atoms at 5 kcal mol-1 A-2 converted to GROMACS units.

## 5. Inspect, then run

Before running, inspect `runs/01build/topol.top`, `runs/01build/ionized.gro`, the generated restraint files, and the `grompp` commands in `runs/run_all.sh`. When the system is approved:

```bash
cd runs
./run_all.sh
```

The runner honors `GMX`, `NTMPI`, `NTOMP`, and `MDRUN_FLAGS`. For example:

```bash
NTOMP=16 MDRUN_FLAGS="-update cpu -pin on" ./run_all.sh
```

Create independent replicas only after this system passes validation by copying the complete `runs/` directory, not by passing a replica option to MSTBx:

```bash
cp -a runs rep1
cp -a runs rep2
cp -a runs rep3
```

`PrepareCGenFFInputs.sh` and `RunTest.sh` are repository validation helpers only; the tutorial above intentionally exposes every command instead of hiding the workflow inside a script.
