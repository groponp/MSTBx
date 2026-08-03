# GROMACS 2OI0 Protein-Ligand Test

This folder contains the command template for the 2OI0 protein-ligand workflow.

The script expects the validated CGenFF inputs and force field from the local staging snapshot:

```bash
./RunTest.sh
```

It builds three replicas and writes GROMACS inputs, index groups, restraints, and one `run_all.sh` per replica. It does not execute any simulation.
