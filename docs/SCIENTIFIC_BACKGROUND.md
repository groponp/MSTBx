[← Back to README](../README.md)

# Scientific Background

This page explains **why** MSTBx runs each simulation stage the way it does —
the physics and chemistry behind the defaults documented in the
[Module Reference](REFERENCE.md), not just the flags that set them. Every
algorithm and constant named below was confirmed by reading the generator
code itself (`mstbx/core/Gromacs/Protocol.py`, `mstbx/core/Gromacs/Build.py`,
`mstbx/core/Gromacs/Restraints.py`, `mstbx/core/MDProtocols/MDSolProtocol.py`,
`mstbx/core/MDProtocols/MDMembProtocol.py`, `mstbx/core/MDProtocols/OpenMMRunner.py`)
rather than assumed from textbook defaults, per the project's source-first
policy in [`PLAN.md`](../PLAN.md). Where a value is a tool default MSTBx does
not override, this page says so explicitly instead of presenting it as an
MSTBx choice.

## Contents

- [The four-stage pipeline](#the-four-stage-pipeline)
- [Energy minimization](#energy-minimization)
- [Thermostat: NVT equilibration](#thermostat-nvt-equilibration)
- [Barostat: NPT equilibration and production](#barostat-npt-equilibration-and-production)
- [Electrostatics and van der Waals treatment](#electrostatics-and-van-der-waals-treatment)
- [Constraints and the integration timestep](#constraints-and-the-integration-timestep)
- [Position restraints](#position-restraints)
- [Periodic boundary conditions and box size](#periodic-boundary-conditions-and-box-size)
- [Protonation states](#protonation-states)
- [Force fields and water model](#force-fields-and-water-model)
- [Cross-engine consistency](#cross-engine-consistency)
- [References](#references)

---

## The four-stage pipeline

Every MSTBx protocol — GROMACS (`md-inputs --engine gromacs`), NAMD
(`md-inputs --engine namd`), and OpenMM (`openmm-run`) — follows the same
physical logic, in the same order, because each stage removes one specific
source of artifact before the next stage is trusted:

1. **Energy minimization (EM)** removes steric clashes and bad geometry left
   over from structure preparation (missing-atom rebuilding, docking poses,
   protonation) that would otherwise produce enormous forces and an unstable
   integrator on the first dynamics step.
2. **NVT equilibration** brings the system to the target temperature under
   constant volume, while position restraints hold the solute close to its
   input geometry so the surrounding solvent/ions can relax around it without
   the solute itself unfolding in response to an unequilibrated solvent shell.
3. **NPT equilibration** relaxes the box to the correct density at the target
   pressure, now that temperature is stable. Density equilibrates on a
   different (typically slower) timescale than temperature, which is why NPT
   is a separate stage after NVT rather than pressure and temperature coupling
   being turned on simultaneously from a cold, badly-packed system.
4. **Production dynamics** removes the restraints (or in GROMACS's case, keeps
   them only if the user explicitly re-enables `-DPOSRES`) and integrates the
   physically relevant trajectory used for analysis.

## Energy minimization

- **GROMACS**: steepest-descent minimization (`integrator = steep`),
  `emtol = 1000.0` kJ mol⁻¹ nm⁻¹, `nsteps = 50000` maximum steps
  (`mstbx/core/Gromacs/Protocol.py`). Steepest descent is deliberately
  conservative — it always moves downhill on the potential energy surface,
  which is what is needed when starting forces may be very large (e.g. a
  rebuilt loop or a docking pose with clashing atoms) and a more
  aggressive optimizer (e.g. conjugate gradient) could overshoot.
- **NAMD**: a 50,000-step `minimize` call is embedded inside the NVT
  configuration file itself rather than written as a separate stage
  (`mstbx/core/MDProtocols/MDSolProtocol.py`); NAMD's built-in minimizer is
  conjugate-gradient/line-search based.
- **OpenMM**: uses OpenMM's `minimizeEnergy` (an L-BFGS-based optimizer, not
  steepest descent or conjugate gradient), run in 10 blocks with
  `tolerance = 100.0` kJ mol⁻¹ nm⁻¹ by default in the generated `eq1.inp`
  template (`mstbx/core/MDProtocols/OpenMMRunner.py`).

All three engines minimize before applying any thermostat/barostat, because
Newtonian dynamics on an unminimized structure can produce forces large
enough to move atoms multiple Ångströms in a single 2 fs step, well past the
point where the fixed 2 fs timestep and hydrogen-bond constraints described
below remain numerically stable.

## Thermostat: NVT equilibration

A thermostat couples the system to a heat bath at the target temperature so
kinetic energy fluctuates around the value implied by the equipartition
theorem, `⟨KE⟩ = (3/2)N k_B T`, rather than drifting with integration error.

| Engine | Algorithm | Key parameters (as generated) |
| --- | --- | --- |
| GROMACS | `v-rescale` (Bussi–Donadio–Parrinello velocity rescaling) | `tau_t = 1.0` ps, two coupling groups, `ref_t = <temperature>` |
| NAMD | Langevin thermostat | `langevindamping 1.0` ps⁻¹, `langevinHydrogen off` |
| OpenMM | `LangevinIntegrator` (default) or `LangevinMiddleIntegrator` | friction `1` ps⁻¹, `dt = 0.002` ps |

`v-rescale` is a stochastic velocity-rescaling thermostat that generates a
correct canonical (NVT) ensemble, unlike the plain Berendsen thermostat it
was designed to replace, which does not sample the canonical distribution
correctly (Bussi et al., 2007). NAMD and OpenMM instead couple every particle
to an implicit Langevin heat bath via a friction/random-force pair, which
also yields the canonical ensemble but additionally acts as the stochastic
part of the integrator itself, not just a coupling scheme.

Default target temperature across all three engines is 310 K (`--temperature`,
`mstbx/commands/md_inputs.py`), i.e. physiological temperature (37 °C), the
standard choice unless the user's system specifically requires another value.

## Barostat: NPT equilibration and production

A barostat couples the box volume to a target pressure so that the density
converges to the value consistent with the force field at that
temperature/pressure, instead of staying frozen at whatever (likely
imperfect) volume the system was built with.

| Engine | Algorithm | Key parameters (as generated) |
| --- | --- | --- |
| GROMACS | `C-rescale` (stochastic cell rescaling) | isotropic, `tau_p = 5.0` ps, `compressibility = 4.5e-5` bar⁻¹, `ref_p = 1.0` bar |
| NAMD | Langevin piston barostat | target `1.01325` bar; solution: `period 200.0`, `decay 100.0`, `useflexiblecell no`; membrane: `period 50.0`, `decay 25.0`, `useflexiblecell yes` |
| OpenMM | `MonteCarloBarostat` (isotropic default; `MonteCarloMembraneBarostat` / `MonteCarloAnisotropicBarostat` selectable) | only active when `pcouple = yes`; `p_freq = 25` (NPT stage) / `100` (production) |

Pressure coupling is deliberately **off during NVT** in all three engines and
turned on only once the temperature has stabilized, since coupling both
simultaneously from a cold, badly-packed box makes it harder to separate a
genuine density artifact from a temperature-equilibration artifact.

The NAMD membrane protocol's `useflexiblecell yes` (vs. `no` for solution
systems) is a real, physically meaningful difference the code makes: a lipid
bilayer needs its box cross-section (X/Y) to fluctuate independently of its
normal (Z) to reach the correct area-per-lipid, whereas an isotropic solution
box does not.

Target pressure across GROMACS/NAMD is 1 atm (`1.01325` bar / `ref_p = 1.0`
bar), the standard reference condition.

## Electrostatics and van der Waals treatment

Long-range electrostatics use **Particle Mesh Ewald (PME)** in all three
engines — the standard method for computing Coulomb interactions correctly
under periodic boundary conditions without an artificial real-space cutoff,
which would otherwise introduce large errors for a system containing charged
side chains, ions, and a polar solvent.

| Engine | Coulomb | van der Waals | Cutoff scheme |
| --- | --- | --- | --- |
| GROMACS | PME, `rcoulomb = 1.2` nm | Force-switch, `rvdw_switch = 1.0` nm, `rvdw = 1.2` nm | Verlet, `nstlist = 20`, `rlist = 1.2` nm |
| NAMD | PME, `PMEGridspacing 1` Å | `vdwForceSwitching on`, `switchdist 10.0` Å, `cutoff 12.0` Å | `pairlistdist 14.0` Å |
| OpenMM | PME, `ewaldErrorTolerance = 0.0005` | Force-switch (custom `CustomNonbondedForce`), `r_on = 1.0` nm, `r_off = 1.2` nm | driven by `nonbondedCutoff = r_off` |

The switch distances (10 Å / 1.0 nm inner, 12 Å / 1.2 nm outer) match across
all three engines. The **force-switching** scheme (rather than a hard cutoff
or a plain switching function) is the van der Waals treatment CHARMM force
fields were parameterized against (Steinbach & Brooks, 1994); using a
different vdW treatment with a CHARMM force field is a known source of
systematic error, which is why MSTBx keeps it consistent across engines
instead of leaving it at each engine's own default.

GROMACS `fourierspacing`/`pme-order` and the EM-stage `emstep` are **not**
set by MSTBx (`mstbx/core/Gromacs/Protocol.py`, `Build.py`); those take
whatever default the installed GROMACS/`grompp` version ships with.

## Constraints and the integration timestep

All three engines run a 2 fs (`0.002` ps) integration timestep with hydrogen
bond lengths constrained rather than left to vibrate freely:

| Engine | Constraint algorithm | Scope |
| --- | --- | --- |
| GROMACS | LINCS | `constraints = h-bonds` |
| NAMD | rigid bonds (SHAKE-equivalent) | `rigidbonds all` |
| OpenMM | selectable, default `HBonds` (`None`/`AllBonds`/`HAngles` also available) | bonds to hydrogen |

Bond vibrations involving hydrogen are the fastest motion in a classical
biomolecular force field (period on the order of 10 fs for a C–H stretch).
The integration timestep must be small enough to resolve the fastest motion
in the system (roughly timestep ≤ period / 10), which would otherwise limit
every engine to a ≤1 fs step. Constraining bonds to hydrogen removes that
fast motion from the dynamics entirely, which is what allows a 2 fs step —
doubling the number of steps obtainable per unit of wall-clock time — without
introducing the energy-conservation errors a naively larger unconstrained
timestep would cause.

## Position restraints

Position restraints hold selected atoms near a reference position with a
harmonic potential, `U = k(x - x₀)²`, during equilibration so the solvent can
relax around a structure that does not itself move — without them, an
imperfectly packed initial solvation shell can distort the solute before the
surrounding water/ions have had time to equilibrate.

**The restraint force constant is deliberately matched across all three
engines**, confirmed directly in each generator's source:

- GROMACS: `DEFAULT_FORCE = round(5.0 * 4.184 * 100)` = **2092 kJ mol⁻¹ nm⁻²**
  (`mstbx/core/Gromacs/Restraints.py`)
- NAMD: `beta` column set to `5` under `constraintScaling 1.0`, i.e.
  **5 kcal mol⁻¹ Å⁻²** (`mstbx/core/MDProtocols/MDSolProtocol.py`)
- OpenMM: `k_strict = 2092.0` kJ mol⁻¹ nm⁻², explicitly commented in the code
  as "equivalent to 5.0 kcal/mol/A^2" (`mstbx/core/MDProtocols/OpenMMRunner.py`)

5 kcal mol⁻¹ Å⁻² ≡ 2092 kJ mol⁻¹ nm⁻² is a standard CHARMM-GUI-style
restraint strength: strong enough to keep the solute close to its input
coordinates during equilibration, weak enough that it does not prevent local
sidechain relaxation.

**Default restrained atoms** are protein backbone heavy atoms (N, CA, C, O)
plus ligand heavy atoms — GROMACS's `DEFAULT_SELECTION` explicitly includes
`resname LIG and not name H*`; NAMD's VMD selection restrains
`protein and backbone` plus `segid HETA`/`segname CAR.*` heavy atoms as the
ligand equivalent. **OpenMM's default template selection is
`protein and backbone` only** — it does not add an explicit ligand heavy-atom
term the way the GROMACS and NAMD generators do, so a ligand present in an
OpenMM run needs its own `--rest-sel`/equivalent restraint selection if the
same protein+ligand behavior is required; this is a genuine difference
between the three code paths, not a documentation gap.

Production dynamics drops restraints in all three engines (OpenMM's
generated production template explicitly sets `rest = no`).

## Periodic boundary conditions and box size

**GROMACS** builds its own box at `topogmx` time: `gmx editconf -d
<box-distance> -bt cubic` sets a **cubic** box whose edge is at least
`--box-distance` (default **1.8 nm**) from the solute in every direction
(`mstbx/core/Gromacs/Build.py`). This is an edge-to-solute distance, not a
box-edge-to-box-edge distance. The 1.8 nm default sits 0.6 nm beyond the
1.2 nm van der Waals/Coulomb cutoff used by the same protocol
(`Protocol.py`): the extra margin exists because the solute is not static —
during equilibration and production it translates, rotates, and breathes, and
the solute-to-image distance must stay above the cutoff throughout the run,
not just at t=0. Too small a margin risks the solute interacting with its own
periodic image (a minimum-image-convention violation); too large a margin
wastes solvent atoms and simulation time for no physical benefit.

**NAMD and OpenMM do not build a box in the `md-inputs`/`openmm-run` stage.**
Both read box vectors from a pre-existing `step3_pbcsetup.str`
(CHARMM-GUI-style) file (`mstbx/core/MDProtocols/MDSolProtocol.py`,
`mstbx/core/MDProtocols/OpenMMRunner.py`), or, for OpenMM, from an OpenMM
restart state when continuing a run. That file is produced earlier, during
`topopsfgen`'s solvation step (18.0 Å default padding for solution systems,
25.0 Å default Z padding for membrane systems, per the
[Module Reference](REFERENCE.md#1-topopsfgen---system-assembly-and-solvation)) —
box construction for the NAMD/OpenMM path therefore happens once, at system
assembly, rather than being re-derived at protocol-generation time.

## Protonation states

`pdbwriter --pH --ff-out CHARMM` and interactive `pdb2gmx` protonation both
resolve the same underlying chemistry: several titratable side chains have a
pKa close enough to physiological pH that their protonation state is not
implied by the amino acid identity alone, and PROPKA/PDB2PQR or `pdb2gmx`
must pick one. CHARMM naming encodes the chosen tautomer/protonation state
directly in the residue name:

| CHARMM name(s) | Residue | Chemical meaning |
| --- | --- | --- |
| `HSD` | Histidine | Neutral, proton on Nδ1 (the "delta" tautomer) |
| `HSE` | Histidine | Neutral, proton on Nε2 (the "epsilon" tautomer) |
| `HSP`, `HSPM`, `HISH` | Histidine | Doubly protonated, net +1 charge (both ring nitrogens protonated) |
| `ASPP` | Aspartate | Protonated (neutral) carboxylic acid side chain, instead of the default deprotonated carboxylate |
| `GLUP` | Glutamate | Protonated (neutral) carboxylic acid side chain |
| `LYSN`, `LSN` | Lysine | Deprotonated (neutral) amine, instead of the default protonated, +1 ammonium |
| `ARGN` | Arginine | Deprotonated (neutral) guanidinium — chemically rare at physiological pH, only relevant at high pH or in specific active-site contexts |
| `CYS2` | Cysteine | Disulfide-bonded (oxidized), distinct from free thiol `CYS` |

This is why `PLAN.md` and the [GROMACS tutorials](tutorials/gromacs.md) treat
the bare MDAnalysis `protein` keyword as unsafe once interactive protonation
is used: MDAnalysis's built-in `protein` selection recognizes standard
residue names, and several of the names above (confirmed adversarially for
`LSN`, see `PLAN.md`) fall outside that set even though they are still
protein residues chemically. `PROTEIN_SEL`, documented in the
[Module Reference](REFERENCE.md#protonation-and-selection-consistency),
exists to close that gap for custom index groups and restraints.

The histidine tautomer choice in particular is not cosmetic: HSD vs. HSE
changes which ring nitrogen carries the hydrogen bond donor capability,
which can matter for binding-site or catalytic-triad histidines specifically
— this is exactly the kind of case where `--pdb2gmx-protonation`'s
interactive, residue-by-residue prompts are appropriate instead of a
non-interactive default.

## Force fields and water model

- **Packaged force field**: `charmm36-feb2026_cgenff-5.0.ff`
  (`mstbx/core/Gromacs/Build.py`), CHARMM36 additive protein/lipid parameters
  combined with CGenFF 5.0 small-molecule parameters, so protein and
  CGenFF-parameterized ligands share one consistent, mutually compatible
  parameter set.
- **Water model**: GROMACS `pdb2gmx` is invoked with `-water tip3p`
  explicitly (`Build.py`) — **TIP3P**, the water model CHARMM force fields
  are parameterized against, even though the packaged force field directory
  also ships SPC/SPC-E/TIP4P/TIP5P topology files as alternatives that MSTBx
  does not select by default.
- **NAMD/OpenMM**: parameters are loaded from the packaged
  `mstbx/core/toppar/` CHARMM36(m) set (`par_all36m_prot.prm`,
  `par_all36_lipid.prm`, `par_all36_cgenff.prm`, `toppar_water_ions.str`).
  Water model for these two engines is implicit in the input PSF/topology
  (typically CHARMM-GUI TIP3P output) rather than asserted by MSTBx's own
  code.
- **Ionization**: `gmx genion -neutral -conc 0.15` — a hardcoded 0.15 M
  neutralizing salt concentration (`Build.py`), matching the `--salt 0.150`
  default used by `topopsfgen` for the NAMD path.

## Cross-engine consistency

MSTBx deliberately matches several physical parameters across GROMACS, NAMD,
and OpenMM so that switching engines for the same system does not silently
change the physics:

| Quantity | GROMACS | NAMD | OpenMM |
| --- | --- | --- | --- |
| Timestep | 2 fs | 2 fs | 2 fs |
| Restraint force | 2092 kJ mol⁻¹ nm⁻² | 5 kcal mol⁻¹ Å⁻² | 2092 kJ mol⁻¹ nm⁻² |
| vdW switch window | 1.0–1.2 nm | 10–12 Å | 1.0–1.2 nm |
| Electrostatics | PME | PME | PME |
| H-bond constraints | LINCS | rigid bonds | HBonds |
| Target pressure | 1.0 bar | 1.01325 bar | user-set (`p_ref`) |

The one parameter that is **not** matched is box construction: only GROMACS
builds and controls box size directly in the reviewed code path (see
[Periodic boundary conditions and box size](#periodic-boundary-conditions-and-box-size));
NAMD and OpenMM inherit the box from the earlier `topopsfgen` step.

---

## References

Algorithms:

- Bussi, G.; Donadio, D.; Parrinello, M. *Canonical sampling through velocity
  rescaling.* J. Chem. Phys. **2007**, 126, 014101.
  [DOI: 10.1063/1.2408420](https://doi.org/10.1063/1.2408420) — GROMACS
  `v-rescale` thermostat.
- Bernetti, M.; Bussi, G. *Pressure control using stochastic cell rescaling.*
  J. Chem. Phys. **2020**, 153, 114107.
  [DOI: 10.1063/5.0020514](https://doi.org/10.1063/5.0020514) — GROMACS
  `C-rescale` barostat.
- Feller, S. E.; Zhang, Y.; Pastor, R. W.; Brooks, B. R. *Constant pressure
  molecular dynamics simulation: The Langevin piston method.* J. Chem. Phys.
  **1995**, 103, 4613–4621.
  [DOI: 10.1063/1.470648](https://doi.org/10.1063/1.470648) — NAMD Langevin
  piston barostat.
- Essmann, U.; Perera, L.; Berkowitz, M. L.; Darden, T.; Lee, H.; Pedersen,
  L. G. *A smooth particle mesh Ewald method.* J. Chem. Phys. **1995**, 103,
  8577–8593. [DOI: 10.1063/1.470117](https://doi.org/10.1063/1.470117) — PME
  electrostatics (all three engines).
- Hess, B.; Bekker, H.; Berendsen, H. J. C.; Fraaije, J. G. E. M. *LINCS: A
  linear constraint solver for molecular simulations.* J. Comput. Chem.
  **1997**, 18, 1463–1472.
  [DOI: 10.1002/(SICI)1096-987X(199709)18:12%3C1463::AID-JCC4%3E3.0.CO;2-H](https://doi.org/10.1002/(SICI)1096-987X(199709)18:12%3C1463::AID-JCC4%3E3.0.CO;2-H)
  — GROMACS bond-constraint algorithm.
- Ryckaert, J.-P.; Ciccotti, G.; Berendsen, H. J. C. *Numerical integration of
  the cartesian equations of motion of a system with constraints:
  molecular dynamics of n-alkanes.* J. Comput. Phys. **1977**, 23, 327–341.
  [DOI: 10.1016/0021-9991(77)90098-5](https://doi.org/10.1016/0021-9991(77)90098-5)
  — SHAKE, the constraint family NAMD's `rigidbonds` and OpenMM's `HBonds`
  belong to.
- Leimkuhler, B.; Matthews, C. *Rational construction of stochastic numerical
  methods for molecular sampling.* Appl. Math. Res. Express **2013**,
  2013, 34–56.
  [DOI: 10.1093/amrx/abs010](https://doi.org/10.1093/amrx/abs010) — the
  "middle" (BAOAB-type) Langevin scheme behind OpenMM's
  `LangevinMiddleIntegrator`.
- Steinbach, P. J.; Brooks, B. R. *New spherical-cutoff methods for
  long-range forces in macromolecular simulation.* J. Comput. Chem. **1994**,
  15, 667–683.
  [DOI: 10.1002/jcc.540150702](https://doi.org/10.1002/jcc.540150702) —
  force-switching van der Waals treatment used by all three engines.
- Páll, S.; Hess, B. *A flexible algorithm for calculating pair interactions
  on SIMD architectures.* Comput. Phys. Commun. **2013**, 184, 2641–2650.
  [DOI: 10.1016/j.cpc.2013.06.003](https://doi.org/10.1016/j.cpc.2013.06.003)
  — GROMACS Verlet cutoff scheme.

Force fields and solvent model:

- MacKerell, A. D. et al. *All-atom empirical potential for molecular
  modeling and dynamics studies of proteins.* J. Phys. Chem. B **1998**, 102,
  3586–3616.
  [DOI: 10.1021/jp973084f](https://doi.org/10.1021/jp973084f) — original
  CHARMM protein force field.
- Best, R. B.; Zhu, X.; Shim, J.; Lopes, P. E. M.; Mittal, J.; Feig, M.;
  MacKerell, A. D. *Optimization of the additive CHARMM all-atom protein
  force field targeting improved sampling of the backbone φ, ψ and
  side-chain χ1 and χ2 dihedral angles.* J. Chem. Theory Comput. **2012**, 8,
  3257–3273. [DOI: 10.1021/ct300400x](https://doi.org/10.1021/ct300400x) —
  CHARMM36 backbone/side-chain corrections.
- Huang, J.; Rauscher, S.; Nawrocki, G.; Ran, T.; Feig, M.; de Groot, B. L.;
  Grubmüller, H.; MacKerell, A. D. *CHARMM36m: an improved force field for
  folded and intrinsically disordered proteins.* Nat. Methods **2017**, 14,
  71–73. [DOI: 10.1038/nmeth.4067](https://doi.org/10.1038/nmeth.4067) — the
  "m" backbone correction packaged in `mstbx/core/toppar/`.
- Vanommeslaeghe, K. et al. *CHARMM general force field: A force field for
  drug-like molecules compatible with the CHARMM all-atom additive
  biological force fields.* J. Comput. Chem. **2010**, 31, 671–690.
  [DOI: 10.1002/jcc.21367](https://doi.org/10.1002/jcc.21367) — CGenFF,
  ligand parameterization via CGenFF Web.
- Jorgensen, W. L.; Chandrasekhar, J.; Madura, J. D.; Impey, R. W.; Klein,
  M. L. *Comparison of simple potential functions for simulating liquid
  water.* J. Chem. Phys. **1983**, 79, 926–935.
  [DOI: 10.1063/1.445869](https://doi.org/10.1063/1.445869) — TIP3P water
  model.

Protonation and structure preparation tools used by `pdbwriter`:

- Olsson, M. H. M.; Søndergaard, C. R.; Rostkowski, M.; Jensen, J. H.
  *PROPKA3: Consistent treatment of internal and surface residues in
  empirical pKa predictions.* J. Chem. Theory Comput. **2011**, 7, 525–537.
  [DOI: 10.1021/ct100578z](https://doi.org/10.1021/ct100578z)
- Dolinsky, T. J.; Nielsen, J. E.; McCammon, J. A.; Baker, N. A. *PDB2PQR: an
  automated pipeline for the setup of Poisson-Boltzmann electrostatics
  calculations.* Nucleic Acids Res. **2004**, 32, W665–W667.
  [DOI: 10.1093/nar/gkh381](https://doi.org/10.1093/nar/gkh381)

Engines and libraries:

- Abraham, M. J. et al. *GROMACS: High performance molecular simulations
  through multi-level parallelism from laptops to supercomputers.*
  SoftwareX **2015**, 1–2, 19–25.
  [DOI: 10.1016/j.softx.2015.06.001](https://doi.org/10.1016/j.softx.2015.06.001)
- Phillips, J. C. et al. *Scalable molecular dynamics on CPU and GPU
  architectures with NAMD.* J. Chem. Phys. **2020**, 153, 044130.
  [DOI: 10.1063/5.0014475](https://doi.org/10.1063/5.0014475)
- Eastman, P. et al. *OpenMM 7: Rapid development of high performance
  algorithms for molecular dynamics.* PLoS Comput. Biol. **2017**, 13,
  e1005659.
  [DOI: 10.1371/journal.pcbi.1005659](https://doi.org/10.1371/journal.pcbi.1005659)
- Michaud-Agrawal, N.; Denning, E. J.; Woolf, T. B.; Beckstein, O.
  *MDAnalysis: A toolkit for the analysis of molecular dynamics
  simulations.* J. Comput. Chem. **2011**, 32, 2319–2327.
  [DOI: 10.1002/jcc.21787](https://doi.org/10.1002/jcc.21787) — atom
  selections used throughout `pdbwriter`, index groups, and restraints.
- O'Boyle, N. M.; Banck, M.; James, C. A.; Morley, C.; Vandermeersch, T.;
  Hutchison, G. R. *Open Babel: An open chemical toolbox.* J. Cheminform.
  **2011**, 3, 33.
  [DOI: 10.1186/1758-2946-3-33](https://doi.org/10.1186/1758-2946-3-33) —
  PDBQT/MOL2 conversion in `mkdocking-cmplx` and `--prepare-cgenff-inputs`.

---

[← Back to README](../README.md) · [Tutorials index](tutorials/index.md) · [Module Reference](REFERENCE.md)
