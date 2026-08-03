import click
import os
from pathlib import Path
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol
from mstbx.core.MDProtocols.MDMembProtocol import MDProtocolMemb
from mstbx.core.Gromacs.Index import IndexGroup, SOLUTE, SOLVENT_IONS, GromacsIndex
from mstbx.core.Gromacs.Protocol import GromacsProtocol, GromacsProtocolConfig
from mstbx.core.Gromacs.Restraints import DEFAULT_FORCE, DEFAULT_SELECTION, GromacsRestraints, RestraintConfig
from mstbx.core.Gromacs.Runner import GromacsRunner
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Generates configuration files for standard Molecular Dynamics.")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Simulation engine to use.")
@click.option('--env', type=click.Choice(['solution', 'membrane']), required=True, help="System environment.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), help="Input PSF file for NAMD.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), help="Input PDB file for NAMD.")
@click.option('--temperature', default=310.0, help="Temperature in Kelvin. Default 310.")
@click.option('--mdtime', '--md-time', default=100.0, help="Production time in ns. Default 100.")
@click.option('--nvt-time', default=2.0, show_default=True, help="GROMACS NVT equilibration time in ns.")
@click.option('--npt-time', default=5.0, show_default=True, help="GROMACS NPT equilibration time in ns.")
@click.option('--dcdfreq', default=10.0, help="DCD trajectory saving frequency in ps. Default 10.0.")
@click.option('--lparm', '--ligand-parm', type=click.Path(exists=True), help="Ligand parameter file (must be CHARMM .str or .prm format).")
@click.option('--runs-dir', type=click.Path(path_type=Path), default=Path("runs"), show_default=True, help="GROMACS runs directory.")
@click.option('--xtc-frequency', type=float, default=50.0, show_default=True, help="GROMACS XTC frame frequency in ps.")
@click.option('--name-group-index-1', default="Protein_ligand", show_default=True, help="First GROMACS tc-grps index name.")
@click.option('--select-group-index-1', default=SOLUTE, show_default=True, help="First GROMACS MDAnalysis index selection.")
@click.option('--name-group-index-2', default="Water_and_ions", show_default=True, help="Second GROMACS tc-grps index name.")
@click.option('--select-group-index-2', default=SOLVENT_IONS, show_default=True, help="Second GROMACS MDAnalysis index selection.")
@click.option('--select-atoms-to-restraint', default=DEFAULT_SELECTION, show_default=True, help="GROMACS MDAnalysis selection for position restraints.")
@click.option('--force', type=int, default=DEFAULT_FORCE, show_default=True, help="GROMACS restraint force in kJ mol-1 nm-2.")
@click.option('--gmx', default="gmx", show_default=True, help="GROMACS executable used in run_all.sh.")
def md_inputs(engine, env, psf, pdb, temperature, mdtime, nvt_time, npt_time, dcdfreq, lparm, runs_dir, xtc_frequency,
              name_group_index_1, select_group_index_1, name_group_index_2, select_group_index_2,
              select_atoms_to_restraint, force, gmx):
    uxm = UnixMessage()

    if engine == 'gromacs':
        if env != 'solution':
            message = "GROMACS md-inputs currently supports only --env solution."
            uxm.message(message, "error")
            click.echo(message)
            return
        protocol = GromacsProtocolConfig(
            runs_dir=runs_dir,
            temperature=temperature,
            mdtime=mdtime,
            nvt_time=nvt_time,
            npt_time=npt_time,
            xtc_frequency=xtc_frequency,
        )
        GromacsProtocol(protocol).write_all()
        groups = [
            IndexGroup(name_group_index_1, select_group_index_1),
            IndexGroup(name_group_index_2, select_group_index_2),
        ]
        GromacsIndex(runs_dir, groups).write_all()
        restraint = RestraintConfig(runs_dir, select_atoms_to_restraint, force)
        protein_count, ligand_count = GromacsRestraints(restraint).apply_all()
        GromacsRunner(runs_dir, gmx).write_all()
        uxm.message(f"GROMACS inputs generated. Restrained atoms: protein={protein_count}, ligand={ligand_count}.", "info")
        return

    if engine in ['amber', 'openmm']:
        uxm.message(f"Engine '{engine}' is not yet implemented for md-inputs.", "error")
        return

    if not psf or not pdb:
        uxm.message("NAMD md-inputs requires --psf and --pdb.", "error")
        return

    uxm.message(f"Generating {env} configuration for {engine}...", "info")

    if env == 'solution':
        md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
        uxm.makedir(dirs=["01build", "02nvt", "03npt", "04md"])
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt()
        md.md()
        md.restraint()
        md.runner_script()

    elif env == 'membrane':
        md = MDProtocolMemb(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
        uxm.makedir(dirs=["01build", "02nvt", "03npt1", "04npt2", "05md"])
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt1()
        md.npt2()
        md.md()
        md.restraint()
        md.runner_script()

    if lparm:
        os.system(f"cp -rv {lparm} toppar/")

    uxm.message("Configuration generated successfully.", "info")
