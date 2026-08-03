# GROMACS 2OI0 Protein-Ligand Test

This folder contains the command template for the 2OI0 protein-ligand workflow.

The script expects the validated CGenFF inputs and force field from the local staging snapshot:

```bash
./RunTest.sh
```

It builds one complete system and writes GROMACS inputs, index groups, restraints, and `run_all.sh`. It does not execute any simulation. Copy the full output directory later if independent replicas are needed.
