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
./PrepareCGenFFInputs.sh
```

This writes `work/cgenff_inputs_2oi0/` containing:

```text
protein_prepared.pdb
ligand_pose.pdb
ligand_for_cgenff.mol2
cgenff_inputs_log.json
```

The command is equivalent to:

```bash
mstbx pdbwriter --prepare-cgenff-inputs \
  --input ../../../staging/gromacs_prepare/gmxpy_snapshot/2OI0/cgenff_inputs_2oi0/2oi0.pdb \
  --select-chains A \
  --pdb-ligand-resname 283 \
  --pdb-ligand-chain A \
  --output work/cgenff_inputs_2oi0 \
  --ligand-pH 7.4 \
  --overwrite
```

## 3. Submit the ligand manually to CGenFF Web

Upload `work/cgenff_inputs_2oi0/ligand_for_cgenff.mol2` to the CGenFF Web service. Do not select `Include parameters that are already in CGenFF`. Download the generated STR file and save it exactly as:

```text
work/cgenff_inputs_2oi0/ligand_for_cgenff.str
```

The STR and the selected CHARMM36/CGenFF force field must use compatible CGenFF versions. The packaged default is `charmm36-feb2026_cgenff-5.0.ff`.

## 4. Build the solvated and ionized GROMACS system

After the STR download, continue with:

```bash
INPUTS_DIR="$PWD/work/cgenff_inputs_2oi0" ./RunTest.sh
```

`RunTest.sh` runs `topogmx` first, then `md-inputs`. It creates one validated system and does not launch `mdrun`:

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

Before running, inspect the generated topology and the `grompp` commands in `runs/run_all.sh`. When the system is approved:

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
