[← Back to tutorial index](index.md)

# OpenMM Workflows

### 6. Automated OpenMM Runner Pipeline (Chignolin)
A complete step-by-step example using `openmm-run` to execute minimization, multi-stage equilibration, and microsecond-scale production.

1. **System Assembly & Prep**: Place your topology and coordinates files (e.g., `01build/mol_chignolin.psf` and `01build/mol_chignolin.pdb`) in the workspace.
2. **Generate Templates**: Automatically generate the input protocol configuration files (`eq1.inp`, `eq2.inp`, `prod.inp`):
   ```bash
   mstbx openmm-run --mk-inp
   ```
3. **Unified Equilibration (Step 1)**: Run minimization and NVT equilibration (2 ns) using the generated `02eq1/eq1.inp`:
   ```bash
   mstbx openmm-run -i 02eq1/eq1.inp \
                    -p 01build/mol_chignolin.psf \
                    -c 01build/mol_chignolin.pdb \
                    -orst 02eq1/eq1 \
                    --ns 2.0
   ```
4. **NPT Pressurization (Step 2)**: Continue the simulation to run NPT equilibration (5 ns), passing the restart file (`02eq1/eq1.rst`):
   ```bash
   mstbx openmm-run -i 03eq2/eq2.inp \
                    -p 01build/mol_chignolin.psf \
                    -c 01build/mol_chignolin.pdb \
                    -irst 02eq1/eq1.rst \
                    -orst 03eq2/eq2 \
                    --ns 5.0
   ```
5. **NPT Production Run (Step 3)**: Continue to production dynamics (1000 ns / 1 μs) with automatic coordinate rewrapping enabled:
   ```bash
   mstbx openmm-run -i 04prod/prod.inp \
                    -p 01build/mol_chignolin.psf \
                    -c 01build/mol_chignolin.pdb \
                    -irst 03eq2/eq2.rst \
                    -orst 04prod/prod \
                    --ns 1000.0 \
                    --rewrap
   ```

See [`openmm-run` in the Module Reference](../REFERENCE.md#8-openmm-run---strict-manual-openmm-runner) for the full flag list.

---

[← Back to tutorial index](index.md) · See also: [Module Reference](../REFERENCE.md)
